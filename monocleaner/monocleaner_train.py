from argparse import ArgumentParser
import logging

try:
    from .lm import *
    from .util import logging_setup
except (SystemError, ImportError):
    from lm import *
    from util import logging_setup

def initialization():
    parser = ArgumentParser()
    parser.add_argument("train", type=str, help="Training corpus. One sentence per line monolingual data.")
    parser.add_argument("model_dir", type=str, help="Model directory to store LM file and metadata.")
    parser.add_argument("-l", "--language", type=str, required=True, help="Language code of the model.")
    parser.add_argument("--dev_size", default=4000, type=int, help="Number of sentences used to estimate mean and stddev perplexity on noisy and clean text. Extracted from training the training corpus.")
    parser.add_argument("--lm_type", default=LMType.CHARACTER, type=lambda t: LMType[t], choices=list(LMType))
    parser.add_argument("--tokenizer_command", default=None, help="Tokenizer command to replace Moses tokenizer when using PLACEHOLDER LMType.")
    parser.add_argument("--debug", action='store_true')
    parser.add_argument("-q", "--quiet", action='store_true')

    args = parser.parse_args()
    args.lm_file_name = 'lm.' + args.language
    args.lm_file_path = args.model_dir + '/' + args.lm_file_name

    logging_setup(args)
    logging.debug(args)

    return args

def write_metadata(stats: LMStats, args):
    ''' Write lm file and perplexity stats to metadata file '''
    with open(args.model_dir + '/metadata.yaml', 'w+') as out:
        out.write(f"language: {args.language}\n")
        out.write(f"lm_file: {args.lm_file_name}\n")
        out.write(f"lm_type: CHARACTER\n")
        out.write(f"clean_mean_perp: {stats.clean_mean}\n")
        out.write(f"clean_stddev_perp: {stats.clean_stddev}\n")
        out.write(f"noisy_mean_perp: {stats.noisy_mean}\n")
        out.write(f"noisy_stddev_perp: {stats.noisy_stddev}\n")

def perform_training(args):
    logging.info("Shuffling input text")
    with open(args.train) as f_:
        train_file, dev_file = shuffle_lm_training(f_, args.dev_size)
        dev_noisy = shuffle_chars(dev_file)

    try:
        # Train language model
        ff = LMFluencyFilter(args.lm_type, args.language, args.tokenizer_command)
        logging.info("Training LM")
        ff.train(train_file, dev_file, dev_noisy, args.lm_file_path)

        # Compute mean and stddev stats of noisy and clean text
        clean_mean, clean_stdev = ff.estimate_threshold(dev_file)
        noisy_mean, noisy_stdev = ff.estimate_threshold(dev_noisy)
        stats = LMStats(clean_mean, clean_stdev, noisy_mean, noisy_stdev)
        logging.info("Perplexity stats")
        logging.info(f"Clean mean: {clean_mean}")
        logging.info(f"Clean std dev: {clean_stdev}")
        logging.info(f"Noisy mean: {noisy_mean}")
        logging.info(f"Noisy std dev: {noisy_mean}")

        # Write stats and lm_file path to metadata
        write_metadata(stats, args)
        logging.info(f"Model and metadata saved at: {args.model_dir}")
    finally:
        os.remove(train_file)
        os.remove(dev_file)
        os.remove(dev_noisy)

if __name__ == "__main__":
    args = initialization()
    perform_training(args)
