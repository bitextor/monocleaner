from argparse import ArgumentParser
from timeit import default_timer
from fastspell import FastSpell
import logging
import yaml
import sys
import os

try:
    from .lm import *
    from .util import logging_setup, check_if_folder, check_positive
    from .hardrules import wrong_segment
except (SystemError, ImportError):
    from lm import *
    from util import logging_setup, check_if_folder, check_positive
    from hardrules import wrong_segment

__author__ = "Jaume Zaragoza"
__version__ = "Version 1.0.0 # 2021-11-18 # Initial release # Jaume Zaragoza"
__version__ = "Version 1.1.0 # 2021-03-07 # Add lang ident column # Jaume Zaragoza"

def initialization():
    parser = ArgumentParser()
    parser.add_argument("model_dir", type=check_if_folder, help="Model directory to store LM file and metadata.")
    parser.add_argument("input", type=argparse.FileType('r'), nargs='?', help="Input file. If omitted, read from 'stdin'.")
    parser.add_argument("output", type=argparse.FileType('w'), nargs='?', help="Output tab-separated text file adding monocleaner score. When omitted output will be written to stdout.")
    parser.add_argument("--scol", default=1, type=check_positive, help ="Sentence column (starting in 1)")
    parser.add_argument("--disable_lang_ident", action='store_true', help="Disables language identification in hardrules")
    parser.add_argument("--disable_hardrules", action='store_true', help='Disables the hardrules filtering (only monocleaner fluency scoring is applied)')
    parser.add_argument("--disable_minimal_length", action='store_true', help="Don't apply minimal length (3 words) rule")
    parser.add_argument("--score_only", action='store_true', help="Only print the score for each sentence, omit all fields")
    parser.add_argument("--add_lang_ident", action='store_true', help="Add another column with the identified language if it's not disabled.")
    parser.add_argument("--annotated_output", action='store_true', help="Add hardrules annotation for each sentence")
    parser.add_argument("--debug", action='store_true')
    parser.add_argument("-q", "--quiet", action='store_true')
    parser.add_argument('-v', '--version', action='version', version="%(prog)s " + __version__, help="show version of this script and exit")

    args = parser.parse_args()

    args.metadata = args.model_dir + '/metadata.yaml'
    if args.output == None:
        args.output = sys.stdout
    if args.input == None:
        args.input = sys.stdin

    logging_setup(args)
    load_model(args)
    logging.debug(args)
    return args

def load_model(args):
    with open(args.metadata) as file_:
        metadata = yaml.safe_load(file_)
        args.language = metadata["language"]
        args.lm_type = LMType[metadata["lm_type"]]
        args.lm_file = args.model_dir + '/' + metadata["lm_file"]
        args.language = metadata["language"]
        if "tokenizer_command" in metadata:
            args.tokenizer_command = metadata["tokenizer_command"]
        else:
            args.tokenizer_command = None

        args.ff = LMFluencyFilter(args.lm_type, args.language, args.tokenizer_command)
        stats = LMStats(metadata["clean_mean_perp"],
                        metadata["clean_stddev_perp"],
                        metadata["noisy_mean_perp"],
                        metadata["noisy_stddev_perp"])
        args.ff.load(args.lm_file, stats)

        if args.disable_lang_ident:
            args.fastspell = None
        else:
            args.fastspell = FastSpell.FastSpell(args.language, mode="aggr")

def perform_scoring(args):
    time_start = default_timer()
    logging.info("Start scoring text")

    nline = 0
    langid = None
    for line in args.input:
        nline += 1
        parts = line.rstrip("\n").split("\t")

        if len(parts) >= args.scol:
            sentence = parts[args.scol-1]
        else:
            logging.error(f" scol ({args.scol}) index above column number ({len(parts)}) on line {nline}")
            continue

        # Hardrules and fluency score
        tag = wrong_segment(sentence, args)
        if tag == "keep":
            score = args.ff.score(sentence)
        else:
            score = 0

        # Language identification
        if not args.disable_lang_ident and args.add_lang_ident:
            langid = args.fastspell.getlang(sentence)

        # always print score
        # print sentence when no score_only
        # print hardrule annotation if requested
        # print identified language if requested
        if not args.score_only:
            args.output.write(line.rstrip("\n") + '\t')
        if langid is not None:
            args.output.write(langid + '\t')
        if tag != "keep":
            args.output.write(f"{score}")
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
    args = initialization()
    perform_scoring(args)
