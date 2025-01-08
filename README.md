
# monocleaner

![License](https://img.shields.io/badge/License-GPLv3-blue.svg)

Monocleaner is a Python tool that aims to detect disfluent sentences in a monolingual corpus.
Each sentence is assigned a fluency score between 0 and 1, with higher scores indicating more fluency.
In addition to a continuous score, several handwritten rules assign a score of 0 to obviously poor sentences.

Although a training tool (`monocleaner-train`) is provided, you may want to use the available ready-to-use language packages.
Please, visit https://github.com/bitextor/monocleaner-data/releases/latest or use `monocleaner-download` to download the latest language packages.

## Citation

If you find Monocleaner useful, please consider citing the following papers:

> V. M. Sánchez-Cartagena, M. Bañón, S. Ortiz-Rojas and G. Ramírez-Sánchez,\
> "[Prompsit's submission to WMT 2018 Parallel Corpus Filtering shared task](http://www.statmt.org/wmt18/pdf/WMT116.pdf)",\
>in *Proceedings of the Third Conference on Machine Translation, Volume 2: Shared Task Papers*.\
>Brussels, Belgium: Association for Computational Linguistics, October 2018

```latex
@InProceedings{prompsit:2018:WMT,
  author    = { V\'{i}ctor M. S\'{a}nchez-Cartagena and Marta Ba{\~n}\'{o}n and Sergio Ortiz-Rojas and Gema Ram\'{i}rez-S\'{a}nchez},
  title     = {Prompsit's submission to WMT 2018 Parallel Corpus Filtering shared task},
  booktitle = {Proceedings of the Third Conference on Machine Translation, Volume 2: Shared Task Papers},
  month     = {October},
  address   = {Brussels, Belgium},
  publisher = {Association for Computational Linguistics}
}
```

## Installation & Requirements
Monocleaner uses [FastSpell](https://github.com/mbanon/fastspell) that requires `python-dev`:
```bash
sudo apt install python-dev
```

Monocleaner can be installed using `pip`:

```bash
pip install monocleaner git+https://github.com/MSeal/cython_hunspell@2.0.3
```

Monocleaner requires the [KenLM](https://github.com/kpu/kenlm) Python bindings with support for 7-gram language models. You can easily install it by running the following command:
```
pip install --config-settings="--build-option=--max_order=7" https://github.com/kpu/kenlm/archive/master.zip
```

To be able to train Monocleaner models, the rest of the KenLM toolkit needs to be installed in addition to the Python bindings:
```bash
git clone https://github.com/kpu/kenlm
cd kenlm
mkdir -p build && cd build
cmake .. -DKENLM_MAX_ORDER=7 -DCMAKE_INSTALL_PREFIX:PATH=/your/prefix/path
make -j all install
```

After installation, two binary files (`monocleaner-train` and `monocleaner`) will be located in your `python/installation/prefix/bin` directory. This is usually `$HOME/.local/bin` or `/usr/local/bin/`.

## Scoring
`monocleaner` aims to detect disfluent sentences in a monolingual corpus.
Each sentence is assigned a fluency score between 0 and 1, with higher scores indicating more fluency.
In addition to a continuous score, several handwritten `hardrules` assign a score of 0 to obviously poor sentences.

The input file (monolingual corpus) must contain one sentence per line text.
The generated output file will contain the same lines adding a column containing the Monocleaner fluency score.

This tool can be run with
```bash
monocleaner [-h]
            [--scol SCOL]
            [--disable_lang_ident] 
            [--disable_hardrules]
            [--disable_minimal_length]
            [--disable_hbs]
            [--score_only]
            [--annotated_output]
            [--add_lang_ident]
            [--detect_script]
            [--run_all_rules]
            [--debug]
            [-q]
            [-v]
            model_dir [input] [output]
```
If input and output are omitted, it will read from stdin and write to stdout.

The output file will contain the following columns which will appear in the strict order indicated below depending on the previous parameters:

| Column | Value            | Parameters                    |
| ------ | ---------------- | ----------------------------- | 
|   1    | Sentence         | Disabled by --score_only      |
|   2    | Score            |  -                            |
|   3    | Language Code    | Enabled by --add_lang_ident   |
|   4    | Hardrule Tag     | Enabled by --annotated_output |

### Parameters
* Positional arguments:
  * `model_dir`: Directory where the model is stored.
  * `input`: Input text file, one sentence per line. When omitted jointly with output, it will read from stdin.
  * `output`: Output tab-separated text file adding monocleaner score. When omitted output will be written to stdout.
* Optional arguments:
  * `--scol`: Sentence column (starting in 1) (default: 1)
  * `--disable_lang_ident`: Disables language identification in hardrules. (default: False)
  * `--disable_hardrules`: Disables the hardrules filtering (only monocleaner fluency scoring is applied) (default: False)
  * `--disable_minimal_length` : Don't apply minimal length rule (default: False).
  * `--disable_hbs`: Don't group Serbo-Croatian under 'hbs' tag. (default: False)
  * `--score_only`: Only output one column which is the monocleaner score (default: False)
  * `--annotated_output`: Add hardrules annotation for each sentence. (default: False)
  * `--add_lang_ident`: Add another column with the identified language if it's not disabled. (default: False)
  * `--detect_script`: Detect writing script with FastSpell (only Serbo-Croatian is supported) (default: False)
  * `--run_all_rules`: Run all hardrules for each sentence instead of stopping at the first one discarded. (default: False)
* Logging:
  * `--debug`: Debug logging mode (default: False)
  * `-q, --quiet`: Silent logging mode (default: False)
  * `-v, --version`: show version of this script and exit

### Example
```bash
monocleaner models/es mono.es.txt mono.es.scored.txt
```

This will use the Spanish model located at `models/es`, read `mono.es.txt` file and write the sentences to `mono.es.scored.txt` adding the monocleaner score column.

## Monocleaner hard-rules
`monocleaner-hardrules` is an optional pre-filtering step for obvious noise based on rules and incorrect language identified by [FastSpell](https://github.com/mbanon/fastspell). It can be used integrated into the `monocleaner` endpoint, or separately.

### Cleaning
`monocleaner-hardrules` aims at detecting obvious noisey sentences in a monolingual corpus. Sentences that are considered noisy will be tagged with a `0` and the rest will be tagged with a `1`. By default, the input monolingual file must contain at least one column with the sentences needed to be cleaned. If more columns are present, the column index of the sentences desired to be cleaned can be customized via the `--scol` parameter.

By default, the generated output file will contain the same lines and columns that the original input file has, however, an extra column containing the Monocleaner hard-rules score is always added. The amount of newly inserted columns will vary depending on which parameters are enabled.

This tool can be run with:
```bash
monocleaner-hardrules [-h]
            [--scol SCOL]
            [--disable_lang_ident]
            [--disable_minimal_length]
            [--disable_hbs]
            [--score_only]
            [--add_lang_ident]
            [--detect_script]
            [--annotated_output]
            [--run_all_rules]
            [--debug]
            [-q]
            [-v]
            language [input] [output]
```

The output file will contain the following columns which will appear in the strict order indicated below depending on the previous parameters:

| Column | Value            | Parameters                    |
| ------ | ---------------- | ----------------------------- | 
|   1    | Sentence         | Disabled by --score_only      |
|   2    | Score            |  -                            |
|   3    | Language Code    | Enabled by --add_lang_ident   |
|   4    | Hardrule Tag     | Enabled by --annotated_output |

### Parameters
* Positional arguments:
  * `language`: Language code of corpus in ISO 639-1 format (2-char code).
  * `input`: Input text file, one sentence per line. When omitted jointly with output, it will read from stdin.
  * `output`: Output tab-separated text file adding monocleaner score. When omitted output will be written to stdout.
* Optional arguments:
  * `--scol`: Sentence column (starting in 1) (default: 1)
  * `--disable_lang_ident`: Disables language identification in hardrules. (default: False)
  * `--disable_minimal_length` : Don't apply minimal length rule (default: False).
  * `--disable_hbs`: Don't group Serbo-Croatian under 'hbs' tag. (default: False)
  * `--score_only`: Only output one column which is the monocleaner score (default: False)
  * `--add_lang_ident`: Add another column with the identified language if it's not disabled. (default: False)
  * `--detect_script`: Detect writing script with FastSpell (only Serbo-Croatian is supported) (default: False)
  * `--annotated_output`: Add hardrules annotation for each sentence. (default: False)
  * `--run_all_rules`: Run all hardrules for each sentence instead of stopping at the first one discarded. (default: False)
* Logging:
  * `--debug`: Debug logging mode (default: False)
  * `-q, --quiet`: Silent logging mode (default: False)
  * `-v, --version`: show version of this script and exit

### Example
```bash
monocleaner-hardrules en mono.en.txt mono.en.scored.txt
```

### Understanding annotated output
When using the `--annotated_output` flag, an extra column with each sentence's evaluation is added to the output. If the evaluation returns the `keep` tag (with score column: 1), it means that the sentence is considered good and passed all filters. However, any other tag value (with score column: 0) in the extra column means that the sentence should be rejected. The rejection reasons, their meaning, and the order in which hard-rules are applied, is shown below:

```
no_empty	Sentence is empty
no_titles	All words in source sentence or target sentence are uppercased or in titlecase
not_too_long	Sentence is more than 1024 characters long
not_too_short	Sentence is less than	3 words long
no_bad_encoding	Source sentence or target sentence contains mojibake
no_only_symbols	The ratio of non-alphabetic characters in source sentence is more than 90%
no_only_numbers	The ratio of numeric characters in source sentence is too high
no_urls	There are URLs (disabled by default)
no_breadcrumbs	There are more than 2 breadcrumb characters in the sentence
no_unicode_noise	Too many characters from unwanted unicode in source sentence
no_space_noise	Too many consecutive single characters separated by spaces in the sentence (excludes digits)
no_paren	Too many parenthesis or brackets in sentence
no_literals	Unwanted literals: "Re:","{{", "%s", "}}", "+++", "***", '=\"'
no_escaped_unicode	There is unescaped unicode characters in sentence
no_glued_words	There are words in the sentence containing too many uppercased characters between lowercased characters
no_repeated_words There are more than 1 consecutive words repeated
no_wrong_language	Sentence is not in the desired language specifide in the cleaning command
```


___

![Connecting Europe Facility](https://www.paracrawl.eu/images/logo_en_cef273x39.png)

All documents and software contained in this repository reflect only the authors' view. The Innovation and Networks Executive Agency of the European Union is not responsible for any use that may be made of the information it contains.
