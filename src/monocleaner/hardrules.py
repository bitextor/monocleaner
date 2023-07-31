from unicodedata import category as cat
from timeit import default_timer
from fastspell import FastSpell
from inspect import getmembers
import unicodedata
import argparse
import logging
import regex
import sys
import re
import os

try:
    from . import __version__
    from .util import logging_setup, check_positive
except (SystemError, ImportError):
    from monocleaner import __version__
    from util import logging_setup, check_positive

tbl_non_alpha = [chr(i) for i in range(sys.maxunicode) if not cat(chr(i)).startswith('L')]
tbl_non_alpha = str.maketrans('', '', ''.join(tbl_non_alpha))
regex_blank = regex.compile("[ \u00A0]")
regex_alpha = regex.compile("[[:alpha:]]")
regex_numbers = regex.compile("[[:digit:]]")
regex_url = regex.compile(r"(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)")
#regex_breadcrumbs = regex.compile("([ ][-/»][ ]|[|<>→←]|[ ][:][:][ ])")
regex_breadcrumbs1 = regex.compile("([ ][-/][ ]|[<>*]|[ ][:][ ])")
regex_breadcrumbs2 = regex.compile("([ ][»][ ]|[|→←•·¬])")
regex_unicode_noise = regex.compile("[\x80-\xFF]{3,}")
regex_unicode_noise_relaxed = regex.compile("[\x80-\xFF]{7,}")
regex_spaces_noise = regex.compile("([ ]\D){4,}[ ]")
regex_paren = r"\[|\]|\(|\)|{|}|⟨|⟩"
regex_unwanted = regex.compile("[+*]")
regex_inconditional = regex.compile("=\"")
regex_escaped_unicode = regex.compile("[\\\\][xu][0-9a-fA-F]{2,}")
#regex_glued_words = regex.compile("\b[[:alpha:]]*[[:lower:]][[:upper:]][[:alpha:]]*)
regex_glued_words = regex.compile("([[:alpha:]]*[[:upper:]]{1}[[:lower:]]+){3}")
regex_repeated_words = regex.compile(r"(?i)(\b\S+(.+))\s+\b\1\b")
regex_repeated_without_words = regex.compile(r"(.+)\1")
safe_noise_detection_langs = {"en", "es", "fr", "pl", "de", "it", "pt", "nl", "cs", "ro", "fi", "lv", "et", "bg", "hr", "da", "hu", "ga", "eu", "gl", "sl", "sv", "mt", "sk", "is", "lt", "nb", "nn", "no"}

#similar_pairs = [{"es","ca"}, {"es","gl"}, {"pt","gl"}, {"no","nn"}, {"no", "da"}]
atilde_langs = {"pt"}
acumflex_langs = {"cy", "fr", "fa", "it", "pt", "tr", "vi",}
CJK = {"zh", "ja", "ko"}


class Hardrules():

    def __init__(self, args):
        self.language = args.language
        self.disable_minimal_length = args.disable_minimal_length
        self.fastspell = args.fastspell
        self.detect_script = args.detect_script
        self.disable_lang_ident = args.disable_lang_ident

        # Get all rule names to be called in a loop as functions
        self.rules = {n: f for n, f in getmembers(self) if n.startswith('c_')}

    def c_no_empty(self, sentence):
        return sentence != ""

    def c_no_titles(self, sentence):    
        return len(sentence.strip().split(" ")) > 1

    def c_not_too_long(self, sentence):
        return len(sentence) < 1024

    def c_not_too_short(self, sentence):
        if self.disable_minimal_length:
            return True

        # for Chinese, Japanese and Korean characters rather than words are used
        if self.language in CJK:
            return len(sentence) >= 3

        """ Counts number of whitespace, requires >= 2 (3 words) """
        return len(regex_blank.findall(sentence)) >= 2

    def c_no_bad_encoding(self, sentence):
        if self.language not in atilde_langs and 'Ã' in sentence:
            return False
        if self.language not in acumflex_langs and 'Â' in sentence:
            return False
        return True

    def c_no_only_symbols(self, sentence):
        return len(regex_alpha.findall(sentence)) / len(sentence) > 0.1

    def c_no_only_numbers(self, sentence):
        threshold = 0.5
        if self.language in CJK:
            threshold = 0.7
        return len(regex_numbers.findall(sentence)) / len(sentence) < threshold

    def c_no_urls(self, sentence):
        return len(regex_url.findall(sentence)) == 0

    def c_no_breadcrumbs(self, sentence):
        return len(regex_breadcrumbs1.findall(sentence)) < 3 \
                or len(regex_breadcrumbs2.findall(sentence)) < 2

    def c_no_unicode_noise(self, sentence):
        # Icelandic can have words with three or four high unicode values like 'þýðir'
        # Finish sometimes too
        if self.language in ('is', 'fi'):
            return len(regex_unicode_noise_relaxed.findall(sentence)) == 0
        else:
            return len(regex_unicode_noise.findall(sentence)) == 0

    def c_no_space_noise(self, sentence):
        return len(regex_spaces_noise.findall(sentence)) == 0

    def c_no_paren(self, sentence):
        if len(re.findall(regex_paren, sentence)): #there are parentheses
            char_count = {i: sentence.count(i) for i in set(sentence)}
            
            if (((char_count.get("[") or 0) + (char_count.get("]") or 0)) > 6 ) or (char_count.get("[") or 0) != (char_count.get("]") or 0): #max 6 [ or ], having the same [ and ] 
                return False            
            if (((char_count.get("{") or 0) + (char_count.get("}") or 0)) > 6 ) or (char_count.get("{") or 0) != (char_count.get("}") or 0): #max than 6 { or }, having the same { and }
                return False           
            if (((char_count.get("⟨") or 0) + (char_count.get("⟩") or 0)) > 6 ) or (char_count.get("⟨") or 0) != (char_count.get("⟩") or 0): #max than 6 ⟨ or ⟩, having the same ⟨ and ⟩            
                return False
            
            opening_paren = char_count.get("(") or 0
            closing_paren = char_count.get(")") or 0
            if opening_paren == closing_paren: #any amount of  () is allowed, as long as there are the same amount of  ( and )
                return True
            else:
                return False
        return True    

    def c_no_literals(self, sentence):
        return not any(l in sentence for l in ["Re:","{{", "%s", "}}", "+++", "***", '=\"'])

    def c_no_escaped_unicode(self, sentence):
        return len(regex_escaped_unicode.findall(sentence)) == 0

    def c_no_glued_words(self, sentence):
        return regex_glued_words.search(sentence) == None

    def c_no_repeated_words(self, sentence):
        our_regex = regex_repeated_without_words
        if self.language in safe_noise_detection_langs:
            our_regex = regex_repeated_words

        min_chars = 7
        if self.language in CJK:
            min_chars = 4

        count = 0
        for match_obj in regex.finditer(our_regex, sentence):
            matching = match_obj.group().strip()
            # if match does not have a minimum length continue without discarding
            if len(matching) > min_chars:
                r2 = regex.search("[[:alpha:]]", matching)
                if r2:
                    # if a certain count of repeated patterns has been reached, then return False
                    count += 1
                    if count >= 1:
                        return False

        return True

    def z_no_wrong_language(self, sentence):
        if not self.disable_lang_ident:
            # Obtain fastspell prediction, lowercasing helps in small langs
            langid = self.fastspell.getlang(sentence.lower())

            # Separate langid from the detected script (only Serbo-Croatian is supported)
            if self.detect_script:
                langid_no_suffix = langid.split('_')[0]
            else:
                langid_no_suffix = langid
                
            # Return language identified, else, return self.language
            if langid_no_suffix != self.language:
                return langid_no_suffix, False
        return self.language, True


'''
def c_unwanted(sentence):
    return len(regex_unwanted.findall(sentence)) < 5

def c_inconditional(sentence):
    return len(regex_inconditional.findall(sentence)) < 1

'''


def wrong_segment(sentence, args, hardrules):
    if args.disable_hardrules:
        return 'keep'

    discarded = []

    for rule_name in hardrules.rules:
        rule = getattr(hardrules, rule_name)
        result = rule(sentence)

        # If rule applied fails, then only add the rule name to discarded
        if not result:
            discarded.append(rule_name.replace('c_', '', 1))
        
        # If user doesn't want to run all rules, stop after the first one that fails
        if not result and not args.run_all_rules:
            return ''.join(discarded)

    if discarded == []:
        return 'keep'
    return '+'.join(discarded)


def initialization():
    parser = argparse.ArgumentParser()
    parser.add_argument("language", type=str, help="Language code of corpus in ISO 639-1 format (2-char code).")
    parser.add_argument("input", type=argparse.FileType('r'), nargs='?', help="Input file. If omitted, read from 'stdin'.")
    parser.add_argument("output", type=argparse.FileType('w'), nargs='?', help="Output tab-separated text file adding monocleaner score. When omitted output will be written to stdout.")
    parser.add_argument("--scol", default=1, type=check_positive, help ="Sentence column (starting in 1)")
    parser.add_argument("--disable_lang_ident", action='store_true', help="Disables language identification in hardrules")
    parser.add_argument("--disable_minimal_length", action='store_true', help="Don't apply minimal length (3 words) rule")
    parser.add_argument("--disable_hbs", action='store_true', help="Don't group Serbo-Croatian under 'hbs' tag")
    parser.add_argument("--score_only", action='store_true', help="Only print the score for each sentence, omit all fields")
    parser.add_argument("--add_lang_ident", action='store_true', help="Add another column with the identified language if it's not disabled")
    parser.add_argument("--detect_script", action='store_true', help="Detect writing script with FastSpell (only Serbo-Croatian is supported)")
    parser.add_argument("--annotated_output", action='store_true', help="Add hardrules annotation for each sentence")
    parser.add_argument("--run_all_rules", action='store_true', help="Run all hardrules for each sentence instead of stopping at the first one discarded")
    parser.add_argument("--debug", action='store_true')
    parser.add_argument("-q", "--quiet", action='store_true')
    parser.add_argument('-v', '--version', action='version', version="%(prog)s " + __version__, help="show version of this script and exit")

    args = parser.parse_args()

    if args.output == None:
        args.output = sys.stdout
    if args.input == None:
        args.input = sys.stdin

    logging_setup(args)
    logging.debug(args)
    
    if args.disable_lang_ident:
        args.fastspell = None
    else:
        args.fastspell = FastSpell(args.language, mode="aggr",
                                    hbs=not args.disable_hbs,
                                    script=args.detect_script)
        
    # Language identification sanity checks
    if args.disable_lang_ident:
        args.add_lang_ident = False
    else:
        if args.add_lang_ident:
            args.disable_lang_ident = False
    
    # This is just to skip over the disable_hardrules parameter
    # which can be enabled only from the monocleaner endpoint
    args.disable_hardrules = False
    
    return args

def main():
    args = initialization()
    
    time_start = default_timer()
    logging.info("Start hardruling text")
    
    # TODO: add wrong_segment as method in hardrules
    hardrules = Hardrules(args)
    
    nline = 0
    for line in args.input:
        nline += 1
        parts = line.rstrip("\n").split("\t")

        if len(parts) >= args.scol:
            sentence = parts[args.scol-1]
        else:
            logging.error(f" scol ({args.scol}) index above column number ({len(parts)}) on line {nline}")
            continue
        
        hr_result = wrong_segment(line, args, hardrules)
        tag = hr_result
        langid = args.language
        
        # Language identification rule and output
        if not args.disable_lang_ident:
            # If run all rules is enabled, run the identification method.
            # If it doesn't pass, then set the tag accordingly if other hardrules have failed.
            if args.run_all_rules:
                langid, res = hardrules.z_no_wrong_language(line)

                if not res:
                    if tag == 'keep':
                        tag = 'no_wrong_language'
                    else:
                        tag += '+no_wrong_language'
            else:
                # If run all rules is disabled, then only run identification method when all other hardrules have passed
                if tag == 'keep':
                    langid, res = hardrules.z_no_wrong_language(line)
                    
                    if not res:
                        tag = 'no_wrong_language'
        
        score = 1
        if tag != "keep":
            score = 0
        
        # print sentence when no score_only
        # print score
        # print hardrule annotation if requested
        # print identified language if requested
        if not args.score_only:
            args.output.write(line.rstrip("\n") + '\t')
        args.output.write("{0}".format(score))
        if args.add_lang_ident:
            args.output.write('\t' + langid)
        if args.annotated_output:
            args.output.write('\t' + tag)
        args.output.write("\n")
        
    # Print elapsed time and avg speed
    logging.info("Finished")
    elapsed_time = default_timer() - time_start
    logging.info(f"Input lines: {nline} rows")
    logging.info(f"Elapsed time {elapsed_time:.2f} s")
    logging.info(f"Troughput: {int((nline * 1.0) / elapsed_time)} rows/s")

    if args.output.name == '<stdout>':
        logging.info(f"Output file: {args.output.name}")
    else:
        logging.info(f"Output file: {os.path.abspath(args.output.name)}")

if __name__ == "__main__":
    main()
