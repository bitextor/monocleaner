# Changelog

## Unreleased
### Added
- Add option to detect Serbo-Croatian script with FastSpell.

### Changed
- Update FastSpell to `0.4`.
- Call FastSpell only one time when `--add_lang_ident`

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
