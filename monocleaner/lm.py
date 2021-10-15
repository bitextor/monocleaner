from tempfile import TemporaryFile, NamedTemporaryFile
from sacremoses import MosesPunctNormalizer
from subprocess import PIPE
from enum import Enum
import typing
import kenlm
import subprocess
import shutil
import argparse
import logging
import numpy
import regex
import random
import sys
import os

try:
    from .util import shuffle_file
    from .tokenizer import Tokenizer
except (SystemError, ImportError):
    from util import shuffle_file
    from tokenizer import Tokenizer


class LMType(Enum):
    #Needed for argparse
    PLACEHOLDER='PLACEHOLDER'
    CHARACTER='CHARACTER'

    def __str__(self):
        return self.value


class UnicodeWordClassifier:
    regex_basic_latin      = regex.compile("^[\p{InBasic_Latin}]+$")
    regex_latin_supplement = regex.compile("^[\p{InLatin-1_Supplement}\p{InBasic_Latin}]+$")
    regex_latin_extended = regex.compile("^[\p{InLatin-1_Supplement}\p{InBasic_Latin}\p{InLatin_Extended-A}\p{InLatin_Extended-B}]+$")
    regex_arabic           = regex.compile("^[\p{Arabic}]+$")
    regex_greek            = regex.compile("^[\p{Greek}]+$")
    regex_cyrillic         = regex.compile("^[\p{Cyrillic}]+$")
    regexes =[ ('BASIC_LATIN',regex_basic_latin) , ('LATIN_SUPPLEMENT',regex_latin_supplement) ,  ('LATIN_EXTENDED',regex_latin_extended),
            ('ARABIC',regex_arabic), ('GREEK',regex_greek), ('CYRILIC',regex_cyrillic)]

    @classmethod
    def classify_word(cls, word):
        for name, r in cls.regexes:
            if r.match(word):
                return name
        return "OTHER"


class LMStats:
    def __init__(self, clean_mean: float, clean_stddev: float, noisy_mean: float, noisy_stddev: float):
        self.clean_mean = clean_mean
        self.clean_stddev = clean_stddev
        self.noisy_mean = noisy_mean
        self.noisy_stddev = noisy_stddev
        self._compute_limits()

    def _compute_limits(self):
        self.upper_limit = self.clean_mean+self.clean_stddev
        self.middle_point = self.clean_mean + (self.noisy_mean - self.clean_mean)/2
        self.lower_limit = self.noisy_mean-self.noisy_stddev

    def perplexity_to_score(self, perp: float):
        if perp > self.upper_limit:
            return 1.0
        if perp < self.lower_limit:
            return 0.0
        if perp < self.middle_point:
            return 0.5 - ((perp - self.middle_point) / (self.lower_limit - self.middle_point))*0.5
        else:
            return 1 - ((perp - self.upper_limit) / (self.middle_point - self.upper_limit))*0.5


class LMFluencyFilter:

    def __init__(self, lm_type: LMType , language: str, tokenizer_command):
        """
            lm_type: LMType
            language: language code
            tokenizer_command: tokenizer full command (with flags if needed)
        """

        self.language = language
        self.tokenizer = Tokenizer(tokenizer_command, self.language)
        self.normalizer = MosesPunctNormalizer(lang=self.language)
        self.type = lm_type
        self.scoring_stats = None

    @classmethod
    def _ispunctuation(cls, t):
        return all( not c.isalnum() for c in t)

    @classmethod
    def _replace_placeholder(cls, t):
        if t.isalpha():
            unicodeGroup = UnicodeWordClassifier.classify_word(t)
            if t.islower():
                return "TOKEN:ALPHA:LOWER:"+unicodeGroup
            elif t.istitle():
                return "TOKEN:ALPHA:TITLE:"+unicodeGroup
            elif t.isupper():
                return "TOKEN:ALPHA:UPPER:"+unicodeGroup
            else:
                return "TOKEN:ALPHA:MIXED:"+unicodeGroup
        else:
            if t.isnumeric():
                return "TOKEN:NUMERIC"
            elif cls._ispunctuation(t):
                return t
            else:
                return "TOKEN:MIXED"

    @classmethod
    def _estimate_kenlm(cls, corpus: str, lm_file: str, params: str):
        output = subprocess.run("lmplz "+params+" < "+corpus+" > "+lm_file+".arpa", shell=True, stderr=PIPE, stdout=PIPE)
        cls.__print_output(output)
        output = subprocess.run("build_binary "+lm_file+".arpa "+ lm_file, shell=True, stderr=PIPE, stdout=PIPE)
        cls.__print_output(output)

    def load(self, lm_path: str, stats: LMStats = None):
        self.lm_path = lm_path
        self.lm = kenlm.LanguageModel(self.lm_path)
        self.scoring_stats = stats

#    def _sentence_split(self, sentence: str):
#        return self.splitter([sentence])

    def _tokenize(self, sentence):
        sentence = self.normalizer.normalize(sentence)

        if self.type != LMType.CHARACTER:
            tokline = " ".join(self.tokenizer.tokenize(sentence))
        else:
            tokline = " ".join([ "SPACE" if c == " " else c for c in sentence  ])
        return tokline

    def _introduce_placeholders(self, sentence):
        if self.type != LMType.PLACEHOLDER:
            return sentence
        else:
            toks = self._replace_placeholder(sentence)
            return " ".join(toks)

    def train_lm(self, text_path: str):
        tokenized_f = NamedTemporaryFile("w", delete=False)
        placeholderized_f = NamedTemporaryFile("w", delete=False)

        #Tokenize text
        with open(text_path) as input_f:
            for line in input_f:
                #line = line.rstrip("\n")
                tokline = self._tokenize(line)
                tokenized_f.write(tokline)
                tokenized_f.write("\n")
        tokenized_f.close()

        #Perform placeholder replacement if needed
        with open(tokenized_f.name) as tokenized_ff:
            for line in tokenized_ff:
                line = line.rstrip("\n")
                with_placeholders = self._introduce_placeholders(line)
                logging.debug("Processed training example: {}".format(with_placeholders))
                placeholderized_f.write(with_placeholders)
                placeholderized_f.write("\n")
        placeholderized_f.close()

        #Estimate LM
        lm_file = NamedTemporaryFile(delete=False)
        lm_file.close()

        if self.type == LMType.CHARACTER:
            params="-o 7 --discount_fallback"
        else:
            params="-o 7 --discount_fallback"

        self._estimate_kenlm(placeholderized_f.name, lm_file.name, params)
        self.lm_path = lm_file.name

        self.lm = kenlm.LanguageModel(self.lm_path)

        #Remove temporary files
        os.remove(tokenized_f.name) 
        os.remove(placeholderized_f.name)

    def copy_lm(self, dst: str):
        shutil.copyfile(self.lm_path, dst)

    def cleanup(self):
        os.remove(self.lm_path)

    def _raw_score(self, sentence: str):
        return self.lm.score(sentence)

    @classmethod
    def __print_output(cls, output):
        if output.returncode != 0:
            logging.error(output.stderr.decode())
            logging.error(output.stdout.decode())
            raise SystemExit()
        else:
            logging.debug(output.stderr.decode())
            logging.debug(output.stdout.decode())

    def estimate_threshold(self, dev_corpus: str):
        scores=[]
        with open(dev_corpus) as corpus_f:
            for line in corpus_f:
                line = line.rstrip("\n")
                scores.append(self.raw_score(line))
        return numpy.mean(scores),numpy.std(scores)

    def raw_score(self, sentence: str):
        #We need to preprocess the sentence in the same way as when training the LM
        #sents= self._sentence_split(sentence)
        #processed_sents=[self._introduce_placeholders(self._tokenize(s)) for s in sents]
        processed_sent = self._introduce_placeholders(self._tokenize(sentence))
        logging.debug("Scoring: {}".format(processed_sent))

        raw_score= self._raw_score(processed_sent)

        #Normalize score
        #return sum(raw_scores)/(sum([len(s.split()) for s in processed_sents]) + len(processed_sents) ) # We divide by total number of tokens + 1 for each sentence (taken from kenlm perplexity method)
        return raw_score/(sum([len(processed_sent.split())]) +1) #the same, but assuming only 1 sentence

    def score(self, sentence: str):
        return self.scoring_stats.perplexity_to_score(self.raw_score(sentence))

    def train(self, lm_train: str, clean: str, noisy: str, lm_out: str) -> LMStats:
        # Check that KenLM is correctly installed
        output = subprocess.run("lmplz", shell=True, stderr=PIPE, stdout=PIPE)
        if output.returncode == 127:
            logging.error("KenLM is not installed, please check Monocleaner installation instructions on how to do so. If you already done this, check that the -DCMAKE_INSTALL_PREFIX:PATH points to your environment path.")
            logging.error("stderr: " + output.stderr.decode())
            logging.error("stdout: " + output.stdout.decode())
            raise SystemExit()

        try:
            self.train_lm(lm_train)
            clean_mean, clean_stddev = self.estimate_threshold(clean)
            noisy_mean, noisy_stddev = self.estimate_threshold(noisy)
            self.scoring_stats = LMStats(clean_mean, clean_stddev, noisy_mean, noisy_stddev)
            self.copy_lm(lm_out)
        finally:
            self.cleanup()

        return self.scoring_stats


def shuffle_lm_training(input: typing.TextIO, dev_size: int ) -> (str,str,str,str):
    dev = NamedTemporaryFile("w", delete=False)
    train = NamedTemporaryFile("w", delete=False)

    logging.debug("Shuffling and creating dev set")
    with TemporaryFile("w+") as shuf:
        #Shuffle the independent files
        shuffle_file(input, shuf)

        #read them and split between dev and train
        shuf.seek(0)

        for i in range(dev_size):
            line = shuf.readline()
            dev.write(line)

        for line in shuf:
            train.write(line)

    dev.close()
    train.close()

    return train.name, dev.name

#Randomizes sentences' characters in a file
def shuffle_chars(input_file_path):
    logging.debug("Shuffling {0} to get noisy corpus".format(input_file_path))
    noisy_file = NamedTemporaryFile("w+", delete=False)
    logging.debug("Writing noisy file to {0}".format(noisy_file.name))
    with open (input_file_path,  "r+") as i:
        for line in i:
            s = line.strip()
            noisy_file.write(''.join(random.sample(s,len(s)))+"\n")

        i.flush()
        i.seek(0)

        noisy_file.flush()
        noisy_file.seek(0)

    return noisy_file.name

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--language",required=True)
    parser.add_argument("--lm_type",type=lambda t: LMType[t], choices=list(LMType),required=True)
    parser.add_argument("--train",action='store_true')
    parser.add_argument("--score",action='store_true')
    parser.add_argument("--stats",action='store_true')
    parser.add_argument("--normalize_score",action='store_true')
    parser.add_argument("--corpus")
    parser.add_argument("--lm_file")
    parser.add_argument("--stats_dev")

    parser.add_argument("--tokenizer_command", default=None)

    parser.add_argument("--debug",action='store_true')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    ff = None

    if args.train:
        args.stats = False

        logging.info("Shuffling input text")
        with open(args.corpus) as f_:
            train_file, dev_file = shuffle_lm_training(f_, 2000)
            dev_noisy = shuffle_chars(dev_file)
        try:
            ff = LMFluencyFilter(args.lm_type, args.language, args.tokenizer_command)
            logging.info("Training LM")
            ff.train(train_file, dev_file, dev_noisy, args.lm_file)
        finally:
            os.remove(train_file)
            os.remove(dev_file)
            os.remove(dev_noisy)

    if args.score:
        ff = LMFluencyFilter(args.lm_type, args.language, args.tokenizer_command)
        ff.load(args.lm_file)
        with open(args.corpus) as corpus_f:
            for line in corpus_f:
                line = line.rstrip("\n")
                print(ff.raw_score(line))

    if args.stats:
        ff = LMFluencyFilter(args.lm_type, args.language, args.tokenizer_command)
        ff.load(args.lm_file)
        mean, stdev = ff.estimate_threshold(args.corpus)
        print("Stats: {} {}".format(mean, stdev))

    if args.normalize_score:
        logging.info("Shuffling input text")
        with open(args.stats_dev) as f_:
            train_file, dev_file = shuffle_lm_training(f_, 2000)
            dev_noisy = shuffle_chars(dev_file)
        if ff is None:
            ff = LMFluencyFilter(args.lm_type, args.language, args.tokenizer_command)
            ff.load(args.lm_file)

        clean_mean, clean_stddev = ff.estimate_threshold(dev_file)
        noisy_mean, noisy_stddev = ff.estimate_threshold(dev_noisy)
        stats = LMStats(clean_mean, clean_stddev, noisy_mean, noisy_stddev)

        with open(args.corpus) as corpus_f:
            for i, line in enumerate(corpus_f):
                line = line.rstrip("\n")
                parts = line.split("\t")
                try:
                    print(stats.perplexity_to_score(float(parts[-1])))
                except ValueError as e:
                    print(i, file=sys.stderr)
                    print(parts, file=sys.stderr)
                    print(line, file=sys.stderr)
                    raise e
