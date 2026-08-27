# REW Converter

Converts spectrum measurements exported by AudioTool into text files that can
be imported into [Room EQ Wizard (REW)](https://www.roomeqwizard.com/).

The converter reads AudioTool `.at` and `.swp` files and extracts the
frequency (`Hz`) and SPL (`dB`) columns from the full-resolution data block.

## Features

- Supports AudioTool `.at` and `.swp` input files.
- Generates `.txt` output by default.
- Generates `.csv` output when requested.
- Derives the output name from the input name.
- Preserves the input directory and base name.
- Ignores additional columns, such as voltage and peak/valley values.
- Ignores subsequent octave data blocks in the AudioTool file.
- Rejects unsupported output formats before creating an output file.
- Does not create or overwrite output when the input is invalid.

## Requirements

- Python 3.12 or 3.13
- [Poetry](https://python-poetry.org/)

## Installation

Clone the repository and install the project dependencies:

```powershell
poetry install
```

Run commands through Poetry with `poetry run`.

## Usage

### TXT output

TXT is the default output format:

```powershell
poetry run python -m rew_converter.rew_converter Medicao2.at
```

This command generates `Medicao2.txt` in the same directory as `Medicao2.at`.

The TXT output uses two whitespace-separated columns:

```text
* Hz SPL(dB)
0.0 0.0
2.691650390625 0.0
```

### CSV output

Select CSV explicitly with `--format csv`:

```powershell
poetry run python -m rew_converter.rew_converter Medicao2.at --format csv
```

This command generates `Medicao2.csv` with the following structure:

```csv
Hz,SPL(dB)
0.0,0.0
2.691650390625,0.0
```

The output filename is always derived from the input filename. The CLI does
not accept a separate output path.

### Help

```powershell
poetry run python -m rew_converter.rew_converter --help
```

## Input format

The input must be an existing `.at` or `.swp` file encoded as ASCII.

The converter expects the first data block to contain tab-separated rows with
at least three columns:

| Column | Meaning | Output |
| --- | --- | --- |
| 1 | Frequency | `Hz` |
| 2 | Voltage or another AudioTool value | Ignored |
| 3 | SPL level | `SPL(dB)` |
| 4+ | Optional AudioTool values | Ignored |

The first line is treated as the AudioTool header. When another textual data
header is found, the converter stops processing the file. This prevents
`1/3 Octave` or `1/6 Octave` data from being appended after the full-resolution
frequencies and causing an import error in REW.

## Supported output formats

Currently implemented:

- `.txt`
- `.csv`

The following REW extensions are intentionally not implemented by this
project:

- `.frd`
- `.dat`
- `.zma`
- `.cal`

Changing a file extension is not enough to convert between these formats. Each
format may have a different data model, number of columns and header contract.
For example, `.zma` is generally used for impedance data, while `.cal` is used
for calibration data. They are not equivalent to an SPL frequency response.

## Development

Run the complete test suite:

```powershell
poetry run pytest
```

Run tests with line and branch coverage:

```powershell
poetry run pytest --cov --cov-report=term-missing
```

The project enforces a minimum coverage of 95% for the `rew_converter` package.

Run static analysis with Pyright:

```powershell
poetry run pyright rew_converter tests
```

## Build

On Windows, run the included build script:

```powershell
compile.bat
```

The script uses PyInstaller to generate a standalone executable and resolves
project files relative to the script location.

## Project structure

```text
rew-converter/
├── rew_converter/
│   ├── __init__.py
│   ├── detect_encoding.py
│   └── rew_converter.py
├── tests/
│   └── test_converter.py
├── compile.bat
├── pyproject.toml
└── README.md
```

## License

No license has been declared in the project yet. Add a license before
redistributing the repository or its generated binaries.
