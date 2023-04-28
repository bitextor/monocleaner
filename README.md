
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
python3 -m pip install monocleaner
```

Monocleaner requires the [KenLM](https://github.com/kpu/kenlm) Python bindings with support for 7-gram language models. You can easily install it by running the following commands:

```bash
git clone https://github.com/kpu/kenlm
cd kenlm
pip install --config-settings="--build-option=--max_order=7" .
mkdir -p build && cd build
cmake .. -DKENLM_MAX_ORDER=7 -DCMAKE_INSTALL_PREFIX:PATH=/your/prefix/path
make -j all install
```

The remaining extra modules required by Monocleaner will be automatically downloaded and installed/upgraded (if required) with the first command.

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
            [--disable_minimal_length]
            [--disable_hardrules]
            [--score_only]
            [--annotated_output]
            [--add_lang_ident]
            [--debug]
            [-q]
            model_dir [input] [output]
```
If input and output are omitted, it will read from stdin and write to stdout.

### Parameters
* Positional arguments:
  * `model_dir`: Directory where the model is stored.
  * `input`: Input text file, one sentence per line. When omitted jointly with output, it will read from stdin.
  * `output`: Output tab-separated text file adding monocleaner score. When omitted output will be written to stdout.
* Optional arguments:
  * `--score_only`: Only output one column which is the monocleaner score (default: False)
  * `--add_lang_ident`: Add another column with the identified language if it's not disabled.
  * `--disable_hardrules`: Disables the hardrules filtering (only monocleaner fluency scoring is applied) (default: False)
  * `--disable_minimal_length` : Don't apply minimal length rule (default: False).
* Logging:
  * `-q, --quiet`: Silent logging mode (default: False)
  * `--debug`: Debug logging mode (default: False)
  * `-v, --version`: show version of this script and exit

### Example
```bash
monocleaner models/es mono.es.txt mono.es.scored.txt
```

This will use the Spanish model located at `models/es`, read `mono.es.txt` file and write the sentences to `mono.es.scored.txt` adding the monocleaner score column.

___

![Connecting Europe Facility](https://www.paracrawl.eu/images/logo_en_cef273x39.png)

All documents and software contained in this repository reflect only the authors' view. The Innovation and Networks Executive Agency of the European Union is not responsible for any use that may be made of the information it contains.
