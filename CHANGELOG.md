# Changelog

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
