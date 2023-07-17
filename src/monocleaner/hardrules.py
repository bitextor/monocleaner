from unicodedata import category as cat
from timeit import default_timer
from fastspell import FastSpell
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


def c_no_empty(args, sentence):
    return sentence != ""

def c_no_titles(args, sentence):    
    return not len(sentence.strip().split(" ")) > 1

def c_not_too_long(args, sentence):
    return len(sentence) < 1024

def c_not_too_short(args, sentence):
    if args.disable_minimal_length:
        return True

    # for Chinese, Japanese and Korean characters rather than words are used
    if args.language in CJK:
        return len(sentence) >= 3

    """ Counts number of whitespace, requires >= 2 (3 words) """
    return len(regex_blank.findall(sentence)) >= 2

def c_lang_id(args, sentence):
    if not args.disable_lang_ident:
        # Obtain fastspell prediction, lowercasing helps in small langs
        langid = args.fastspell.getlang(sentence.lower())

        # Separate langid from the detected script (only Serbo-Croatian is supported)
        if args.detect_script:
            langid_no_suffix = langid.split('_')[0]
        else:
            langid_no_suffix = langid
            
        # Return language identified, else, return args.language
        if langid_no_suffix != args.language:
            return langid_no_suffix, False
    return args.language, True

def c_no_bad_encoding(args, sentence):
    if args.language not in atilde_langs and 'Ã' in sentence:
        return False
    if args.language not in acumflex_langs and 'Â' in sentence:
        return False
    return True

def c_no_only_symbols(args, sentence):
    return len(regex_alpha.findall(sentence)) / len(sentence) > 0.1

def c_no_only_numbers(args, sentence):
    threshold = 0.5
    if args.language in CJK:
        threshold = 0.7
    return len(regex_numbers.findall(sentence)) / len(sentence) < threshold

def c_no_urls(args, sentence):
    return len(regex_url.findall(sentence)) == 0

def c_no_breadcrumbs(args, sentence):
    return len(regex_breadcrumbs1.findall(sentence)) < 3 \
            or len(regex_breadcrumbs2.findall(sentence)) < 2

def c_no_unicode_noise(args, sentence):
    # Icelandic can have words with three or four high unicode values like 'þýðir'
    # Finish sometimes too
    if args.language in ('is', 'fi'):
        return len(regex_unicode_noise_relaxed.findall(sentence)) == 0
    else:
        return len(regex_unicode_noise.findall(sentence)) == 0

def c_no_space_noise(args, sentence):
    return len(regex_spaces_noise.findall(sentence)) == 0

def c_no_paren(args, sentence):
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

def c_no_literals(args, sentence):
    return not any(l in sentence for l in ["Re:","{{", "%s", "}}", "+++", "***", '=\"'])

def c_no_escaped_unicode(args, sentence):
    return len(regex_escaped_unicode.findall(sentence)) == 0

def c_no_glued_words(args, sentence):
    return regex_glued_words.search(sentence) == None

def c_no_repeated_words(args, sentence):
    our_regex = regex_repeated_without_words
    if args.language in safe_noise_detection_langs:
        our_regex = regex_repeated_words

    min_chars = 7
    if args.language in CJK:
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

'''
def c_different_language(left, right, left_lang, right_lang):
    if left_lang =="nb":
        left_lang="no"

    if right_lang=="nb":
        right_lang="no"
        

    l_reliable = False
    l_bytes = 0
    l_details = ()
 
    try:
        l_reliable, l_bytes, l_details = pycld2.detect(left)
    except:
        return False # encoding error -> noise

    r_reliable = False
    r_bytes = 0
    r_details = ()

    try:
        r_reliable, r_bytes, r_details = pycld2.detect(right)
    except:
        return False # encoding error -> noise
        
    if l_reliable and r_reliable and l_details[0][1] != r_details[0][1]:    
        return True
    elif not l_reliable or not r_reliable:
        return True
    else:
        #both langs are reliable at this point, and the identified language is the same for left and right
        identified = l_details[0][1]
        if (identified in [left_lang, right_lang]  and {left_lang, right_lang} in similar_pairs):
            return True
        else:    
            return False
'''
'''        
def c_reliable_long_language(sentence, language):
    if language=="nb":
        language = "no"
        
    reliable = False
    bytes = 0
    details = ()
    
    try:
        reliable, bytes, details = pycld2.detect(sentence)
    except:
        return True # encoding error -> noise
    
    if len(sentence) > 30 and reliable and details[0][1] != language:
        if {language, details[0][1]} in similar_pairs:
            return True
        else:
            return False
    else:
        return True
'''

'''
def c_unwanted(sentence):
    return len(regex_unwanted.findall(sentence)) < 5

def c_inconditional(sentence):
    return len(regex_inconditional.findall(sentence)) < 1

'''


def wrong_segment(sentence, args, hardrules_call = False):
    '''
    elif not c_unwanted(sent):
        return "c_unwanted"
    elif not c_inconditional(sent):
        return "c_inconditional"
    '''
    
    if args.disable_hardrules:
        return "keep"

    if not c_no_empty(args, sentence):
        return 'no_empty'
    elif c_no_titles(args, sentence):
        return 'no_titles'
    elif not c_not_too_long(args, sentence):
        return 'not_too_long'
    elif not c_not_too_short(args, sentence):
        return 'not_too_short'
    elif not c_no_bad_encoding(args, sentence):
        return 'no_bad_encoding'
    elif not c_no_only_symbols(args, sentence):
        return 'no_only_symbols'
    elif not c_no_only_numbers(args, sentence):
        return 'no_only_numbers'
    elif not c_no_urls(args, sentence):
        return 'no_urls'
    elif not c_no_breadcrumbs(args, sentence):
        return 'no_breadcrumbs'
    elif not c_no_unicode_noise(args, sentence):
        return 'no_unicode_noise'
    elif not c_no_space_noise(args, sentence):
        return 'no_space_noise'
    elif not c_no_paren(args, sentence):
        return 'no_paren'
    elif not c_no_literals(args, sentence):
        return 'no_literals'
    elif not c_no_escaped_unicode(args, sentence):
        return 'no_escaped_unicode'
    elif not c_no_glued_words(args, sentence):
        return 'no_glued_words'
    elif not c_no_repeated_words(args, sentence):
        return 'no_repeated_words'

    # Language identification is done only if it is enabled and 
    # the call is being made from the hardrules endpoint
    if hardrules_call and not args.disable_lang_ident:
        langid, fails_lang = c_lang_id(args, sentence)
        if not fails_lang:
            return langid, 'c_wrong_language'

    return "keep"






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
    
    # This is just to skip over the disable_hardrules parameter
    # that can be enabled from the monocleaner endpoint
    args.disable_hardrules = False
    
    return args

def main():
    args = initialization()
    
    time_start = default_timer()
    logging.info("Start hardruling text")
    
    nline = 0
    for line in args.input:
        nline += 1
        parts = line.rstrip("\n").split("\t")

        if len(parts) >= args.scol:
            sentence = parts[args.scol-1]
        else:
            logging.error(f" scol ({args.scol}) index above column number ({len(parts)}) on line {nline}")
            continue
        
        hr_result = wrong_segment(line, args, hardrules_call = True)
        langid = args.language
        tag = hr_result
        
        # Language identification output
        if type(hr_result) is tuple:
            langid = hr_result[0]
            tag = hr_result[1]
        
        #print("{} - {} - {}".format(type(hr_result), langid, tag))
        
        score = 1
        if tag != "keep":
            score = 0
        
        # print score
        # print sentence when no score_only
        # print hardrule annotation if requested
        # print identified language if requested
        if not args.score_only:
            args.output.write(line.rstrip("\n") + '\t')
        if tag != "keep":
            args.output.write(f"{score}")
        if args.add_lang_ident:
            args.output.write('\t' + langid)
        else:
            args.output.write(f"{score:.3f}")
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
