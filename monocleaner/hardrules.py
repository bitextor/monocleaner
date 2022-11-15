import unicodedata
import logging
import regex
import sys

tbl_non_alpha = [chr(i) for i in range(sys.maxunicode) if not unicodedata.category(chr(i)).startswith('L')]
tbl_non_alpha = str.maketrans('', '', ''.join(tbl_non_alpha))
regex_blank = regex.compile("[ \u00A0]")
regex_alpha = regex.compile("[[:alpha:]]")
regex_url = regex.compile('((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]|\((:?[^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')
#regex_breadcrumbs = regex.compile("([ ][-/»][ ]|[|<>→←]|[ ][:][:][ ])")
regex_breadcrumbs1 = regex.compile("([ ][-/][ ]|[<>*]|[ ][:][ ])")
regex_breadcrumbs2 = regex.compile("([ ][»][ ]|[|→←•·¬])")
regex_unicode_noise = regex.compile("[\x80-\xFF]{3,}")
regex_spaces_noise = regex.compile("([ ].){4,}[ ]")
regex_paren = regex.compile("[][(){}]")
regex_unwanted = regex.compile("[+*]")
regex_inconditional = regex.compile("=\"")
regex_escaped_unicode = regex.compile("[\\\\]u[0-9a-fA-F]{3,}")
#regex_glued_words = regex.compile("\b[[:alpha:]]*[[:lower:]][[:upper:]][[:alpha:]]*)
regex_glued_words = regex.compile("([[:alpha:]]*[[:upper:]]{1}[[:lower:]]+){3}")
safe_noise_detection_langs = {"en", "es", "fr", "pl", "de", "it", "pt", "nl", "cs", "ro", "fi", "lv", "et", "bg", "hr", "da", "hu", "ga", "eu", "gl", "sl", "sv", "mt", "sk"}

safe_noise_detection_langs = {"en", "es", "fr", "pl", "de", "it", "pt", "nl", "cs", "ro", "fi", "lv", "et", "bg", "hr", "da", "hu", "ga", "eu", "gl", "sl", "sv", "mt", "sk", "is", "lt", "nb", "nn", "no"}
#similar_pairs = [{"es","ca"}, {"es","gl"}, {"pt","gl"}, {"no","nn"}, {"no", "da"}]
atilde_langs = {"pt"}
acumflex_langs = {"cy", "fr", "fa", "it", "pt", "tr", "vi",}

def c_identical_alpha(left, right):
    left = left.translate(tbl_non_alpha)
    right = right.translate(tbl_non_alpha)
    return left.casefold() != right.casefold()

def c_minimal_length(sentence):
    """ Counts number of whitespace, requires >= 2 (3 words) """
    return len(regex_blank.findall(sentence)) >= 2

def c_length(left, right):
    return 0.5 <= float(len(left))/float(len(right)) <= 2.0

def c_length_bytes(left, right):
    return 0.5 <= float(len(left.encode("utf8")))/float(len(right.encode("utf8"))) <= 2.0
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
def c_no_bad_encoding(sentence, lang):
    if lang not in atilde_langs and 'Ã' in sentence:
        return False
    if lang not in acumflex_langs and 'Â' in sentence:
        return False
    return True

def c_alpha(sentence):
    return len(regex_alpha.findall(sentence)) > 0
    
def c_majority_alpha(sentence):
    return float(len(regex_alpha.findall(sentence))) / float(len(sentence)) >= 0.5

def c_no_urls(sentence):
    return sum([len("".join(i)) for i in regex_url.findall(sentence)]) < 15

#def c_no_breadcrumbs(sentence):
#    return len(regex_breadcrumbs.findall(sentence)) < 3


def c_no_breadcrumbs1(sentence):
    return len(regex_breadcrumbs1.findall(sentence)) < 3  

def c_no_breadcrumbs2(sentence):
    return len(regex_breadcrumbs2.findall(sentence)) < 2  

def c_no_noise(sentence):
    return len(regex_unicode_noise.findall(sentence)) == 0
    
def c_no_space_noise(sentence):
    return len(regex_spaces_noise.findall(sentence)) == 0
    
def c_no_paren(sentence):
    return len(regex_paren.findall(sentence)) < 10

def c_unwanted(sentence):
    return len(regex_unwanted.findall(sentence)) < 5

def c_inconditional(sentence):
    return len(regex_inconditional.findall(sentence)) < 1

def c_no_literals(literals, sentence):
    return not any(l in sentence for l in literals)

def c_no_escaped_unicode(sentence):
    return len(regex_escaped_unicode.findall(sentence)) == 0

def c_no_glued_words(sentence):
    return regex_glued_words.search(sentence) == None

def c_no_porn(left, right, model, side, porn_tokenizer):
    if side == "sl":
        tok = porn_tokenizer.tokenize(left.lower())
    else:
        tok = porn_tokenizer.tokenize(right.lower())
    return model.predict(porn_tokenizer.detokenize(tok))[0][0] == '__label__negative'

def wrong_segment(sent, args):
    if args.disable_hardrules:
        return "keep"
    if not sent:
        return "c_no_empty"
    if len(sent) >= 1024:
        return "len(sent) >= 1024"
    elif not c_no_literals(["Re:"], sent):
        return "c_no_literals(['Re:'], sent)"
    elif not args.disable_minimal_length and not c_minimal_length(sent):
        return "c_minimal_length"
    elif not c_majority_alpha(sent):
        return "c_majority_alpha"
    elif not c_no_urls(sent):
        return "c_no_urls"
    #elif not c_no_breadcrumbs(sent):    
    #    return "c_no_breadcrumbs"
    elif not c_no_breadcrumbs1(sent):
        return "c_no_breadcrumbs1"
    elif not c_no_breadcrumbs2(sent):
        return "c_no_breadcrumbs2"
    elif not c_no_glued_words(sent):
        return "c_no_glued_words"
    elif args.language in safe_noise_detection_langs and not c_no_noise(sent):
        return "args.language in safe_noise_detection_langs and not c_no_noise" 
    elif not c_no_space_noise(sent):
        return "c_no_space_noise"
    elif not c_no_paren(sent):
        return "c_no_paren"
    elif not c_unwanted(sent):
        return "c_unwanted"
    elif not c_inconditional(sent):
        return "c_inconditional"
    elif not c_no_escaped_unicode(sent):
        return "c_no_escaped_unicode"
    elif not c_no_literals(["{{", "%s", "}}"], sent):
        return 'c_no_literals(["{{", "%s", "}}"], sent)'
    elif not c_no_bad_encoding(sent, args.language):
        return 'c_no_bad_encoding(["Â","Ã"])'
    elif sent.istitle():
        return 'sent.istitle()'
#    elif (not args.disable_lang_ident and not  c_reliable_long_language(sent, args.language)):
#        return "c_reliable_long_language"
#    elif (not args.disable_lang_ident and not  args.fastspell.getlang(sent.lower())==args.language):
#        return "c_wrong_language"
#    elif not args.disable_porn_removal and porn_removal != None and not c_no_porn(sent, right, porn_removal, args.metadata_yaml['porn_removal_side'], porn_tokenizer):
#        return "c_no_porn"
    return "keep"
