#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Code copied with modifications from https://github.com/hplt-project/sacremoses
# MIT License; Copyright (c) 2020 alvations
#

import re
import regex

from itertools import chain


class MosesPunctNormalizer:
    """
    This is a Python port of the Moses punctuation normalizer from
    https://github.com/moses-smt/mosesdecoder/blob/master/scripts/tokenizer/normalize-punctuation.perl
    """

    EXTRA_WHITESPACE = [  # lines 21 - 30
        (re.compile(r"\r"), r""),
        (re.compile(r"\("), r" ("),
        (re.compile(r"\)"), r") "),
        (re.compile(r" +"), r" "),
        (re.compile(r"\) ([.!:?;,])"), r")\g<1>"),
        (re.compile(r"\( "), r"("),
        (re.compile(r" \)"), r")"),
        (re.compile(r"(\d) %"), r"\g<1>%"),
        (re.compile(r" :"), r":"),
        (re.compile(r" ;"), r";"),
    ]

    NORMALIZE_UNICODE_IF_NOT_PENN = [  # lines 33 - 34
        (re.compile(r"`"), r"'"),
        (re.compile(r"''"), r' " ')
    ]

    NORMALIZE_UNICODE = [  # lines 37 - 50
        (re.compile("„"), r'"'),
        (re.compile("“"), r'"'),
        (re.compile("”"), r'"'),
        (re.compile("–"), r"-"),
        (re.compile("—"), r" - "),
        (re.compile(r" +"), r" "),
        (re.compile("´"), r"'"),
        (re.compile("([a-zA-Z])‘([a-zA-Z])"), r"\g<1>'\g<2>"),
        (re.compile("([a-zA-Z])’([a-zA-Z])"), r"\g<1>'\g<2>"),
        (re.compile("‘"), r"'"),
        (re.compile("‚"), r"'"),
        (re.compile("’"), r"'"),
        (re.compile(r"''"), r'"'),
        (re.compile("´´"), r'"'),
        (re.compile("…"), r"..."),
    ]

    FRENCH_QUOTES = [  # lines 52 - 57
        (re.compile("\u00A0«\u00A0"), r'"'),
        (re.compile("«\u00A0"), r'"'),
        (re.compile("«"), r'"'),
        (re.compile("\u00A0»\u00A0"), r'"'),
        (re.compile("\u00A0»"), r'"'),
        (re.compile("»"), r'"'),
    ]

    HANDLE_PSEUDO_SPACES = [  # lines 59 - 67
        (re.compile("\u00A0%"), r"%"),
        (re.compile("nº\u00A0"), "nº "),
        (re.compile("\u00A0:"), r":"),
        (re.compile("\u00A0ºC"), " ºC"),
        (re.compile("\u00A0cm"), r" cm"),
        (re.compile("\u00A0\\?"), "?"),
        (re.compile("\u00A0\\!"), "!"),
        (re.compile("\u00A0;"), r";"),
        (re.compile(",\u00A0"), r", "),
        (re.compile(r" +"), r" "),
    ]

    EN_QUOTATION_FOLLOWED_BY_COMMA = [(re.compile(r'"([,.]+)'), r'\g<1>"')]

    DE_ES_FR_QUOTATION_FOLLOWED_BY_COMMA = [
        (re.compile(r',"'), r'",'),
        (re.compile(r'(\.+)"(\s*[^<])'), r'"\g<1>\g<2>'),  # don't fix period at end of sentence
    ]

    DE_ES_CZ_CS_FR = [
        (re.compile("(\\d)\u00A0(\\d)"), r"\g<1>,\g<2>"),
    ]

    OTHER = [
        (re.compile("(\\d)\u00A0(\\d)"), r"\g<1>.\g<2>"),
    ]

    # Regex substitutions from replace-unicode-punctuation.perl
    # https://github.com/moses-smt/mosesdecoder/blob/master/scripts/tokenizer/replace-unicode-punctuation.perl
    REPLACE_UNICODE_PUNCTUATION = [
        (re.compile("，"), ","),
        (re.compile(r"。\s*"), ". "),
        (re.compile("、"), ","),
        (re.compile("”"), '"'),
        (re.compile("“"), '"'),
        (re.compile("∶"), ":"),
        (re.compile("："), ":"),
        (re.compile("？"), "?"),
        (re.compile("《"), '"'),
        (re.compile("》"), '"'),
        (re.compile("）"), ")"),
        (re.compile("！"), "!"),
        (re.compile("（"), "("),
        (re.compile("；"), ";"),
        (re.compile("」"), '"'),
        (re.compile("「"), '"'),
        (re.compile("０"), "0"),
        (re.compile("１"), "1"),
        (re.compile("２"), "2"),
        (re.compile("３"), "3"),
        (re.compile("４"), "4"),
        (re.compile("５"), "5"),
        (re.compile("６"), "6"),
        (re.compile("７"), "7"),
        (re.compile("８"), "8"),
        (re.compile("９"), "9"),
        (re.compile(r"．\s*"), ". "),
        (re.compile("～"), "~"),
        (re.compile("’"), "'"),
        (re.compile("…"), "..."),
        (re.compile("━"), "-"),
        (re.compile("〈"), "<"),
        (re.compile("〉"), ">"),
        (re.compile("【"), "["),
        (re.compile("】"), "]"),
        (re.compile("％"), "%"),
    ]

    CONTROL_CHARS = regex.compile(r"\p{C}")

    def __init__(
        self,
        lang="en",
        penn=True,
        norm_quote_commas=True,
        norm_numbers=True,
        pre_replace_unicode_punct=False,
        post_remove_control_chars=False,
    ):
        """
        :param language: The two-letter language code.
        :type lang: str
        :param penn: Normalize Penn Treebank style quotations.
        :type penn: bool
        :param norm_quote_commas: Normalize quotations and commas
        :type norm_quote_commas: bool
        :param norm_numbers: Normalize numbers
        :type norm_numbers: bool
        """
        self.substitutions = [
            self.EXTRA_WHITESPACE,
            self.NORMALIZE_UNICODE,
            self.FRENCH_QUOTES,
            self.HANDLE_PSEUDO_SPACES,
        ]

        if penn:  # Adds the penn substitutions after extra_whitespace regexes.
            self.substitutions.insert(1, self.NORMALIZE_UNICODE_IF_NOT_PENN)

        if norm_quote_commas:
            if lang == "en":
                self.substitutions.append(self.EN_QUOTATION_FOLLOWED_BY_COMMA)
            elif lang in ["de", "es", "fr"]:
                self.substitutions.append(self.DE_ES_FR_QUOTATION_FOLLOWED_BY_COMMA)

        if norm_numbers:
            if lang in ["de", "es", "cz", "cs", "fr"]:
                self.substitutions.append(self.DE_ES_CZ_CS_FR)
            else:
                self.substitutions.append(self.OTHER)

        self.substitutions = list(chain(*self.substitutions))

        self.pre_replace_unicode_punct = pre_replace_unicode_punct
        self.post_remove_control_chars = post_remove_control_chars

    def normalize(self, text):
        """
        Returns a string with normalized punctuation.
        """
        # Optionally, replace unicode puncts BEFORE normalization.
        if self.pre_replace_unicode_punct:
            text = self.replace_unicode_punct(text)

        # Actual normalization.
        for regexp, substitution in self.substitutions:
            # print(regexp, substitution)
            text = regexp.sub(substitution, str(text))
            # print(text)

        # Optionally, replace unicode puncts BEFORE normalization.
        if self.post_remove_control_chars:
            text = self.remove_control_chars(text)

        return text.strip()

    def replace_unicode_punct(self, text):
        for regexp, substitution in self.REPLACE_UNICODE_PUNCTUATION:
            text = regexp.sub(substitution, str(text))
        return text

    def remove_control_chars(self, text):
        return CONTROL_CHARS.sub("", text)
