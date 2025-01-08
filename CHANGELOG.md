# Changelog

## v1.6.4
- Use models v1.0 download URL for retrocompatibility.

## v1.6.3
- Fix inconsistent rule naming for not_too_long and missing_columns.

## v1.6.2
- Fix divison by 0 error on empty sentences.
- Fixed rules that were giving false positives on empty sentences (no  titles, wrong language)
- For performance, long setences (>1024 chars.) are ignored by default, only "not_too_long" is outputed. Added "--dont_ignore_long" flag to override this
behaviour.

## v1.6.1

### Changed
- `monocleaner-hardrules` now supports `--run_all_rules`

## v1.6
### Added
- `monocleaner-hardrules` is now a standalone script.

### Changed
- Updated Readme

## v1.5
### Added
- `monocleaner-download` quiet mode.

### Changed
- Precompile punctuation normalization regular expressions for better speed.

## v1.4
### Changed
- Update FastSpell to 0.9.1.

## v1.3 2023-03-15
### Added
- Add option to detect Serbo-Croatian script with FastSpell.

### Changed
- Update FastSpell to `0.8`.
    - Better coverage for Icelandic.
    - Automatic installation of dictionaries.
- Call FastSpell only one time when `--add_lang_ident`
- Migrate to pyproject and src/ code structure.

### Fixed
- Discarding sentences as wrong\_language when detect script is enabled.
- Discarding sentences as wrong\_language when hardrules is disabled.
- Always printing lang id regardless of `--add_lang_ident` true or false.

## v1.2 2022-11-14
### Changed
- Request FastSpell to tag all Serbo-Croatian variants under `hbs`.

## v1.1.0 2022-03-07
### Added
- `--add_lang_ident` to append a column with identified language code.

### Changed
- FastSpell mode to aggressive.

### Fixed

## v1.0.0 2021-11-18

### Added
- Monocleaner training script to train fluency filter models.
- FastSpell for language identification.

### Changed
- Monolingual character-based fluency filter.
- Monolingual hardrules version.

### Fixed
