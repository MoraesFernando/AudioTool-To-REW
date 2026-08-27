"""Convert AudioTool spectrum files to the REW text format."""

from argparse import ArgumentParser
import csv
from pathlib import Path
from os.path import exists, splitext


class Converter:
    """Convert AudioTool files to the REW text format.

    Attributes:
        input_file: Path to the AudioTool input file.
        output_file: Path where the REW output file will be written.
        data: Lines loaded from the input file.
    """

    def __init__(self, input_file: str, output_file: str):
        self.input_file = input_file
        self.output_file = output_file
        self.data = []

    def verify_extension(self) -> bool:
        """Return whether the input exists and has a supported extension."""
        extension = splitext(self.input_file)[1].lower()
        return exists(self.input_file) and extension in {".at", ".swp"}

    def load_data(self) -> None:
        """Load and validate the input file.

        Raises:
            ValueError: If the input does not exist or has an unsupported
                extension.
            UnicodeDecodeError: If the file is not encoded as ASCII.
        """
        if not self.verify_extension():
            raise ValueError("Input must be an existing .at or .swp file")

        with open(self.input_file, "r", encoding="ascii") as file:
            self.data = file.readlines()

    def converter_full_res(self) -> None:
        """Write the loaded data in REW full-resolution format.

        Raises:
            ValueError: If no input data has been loaded.
        """
        if not self.data:
            raise ValueError("No input data loaded")

        output_format = Path(self.output_file).suffix.lower()
        if output_format not in {".txt", ".csv"}:
            raise ValueError("Output format must be .txt or .csv")

        with open(self.output_file, "w", encoding="utf-8") as out:
            writer = csv.writer(out, lineterminator="\n")
            if output_format == ".csv":
                writer.writerow(["Hz", "SPL(dB)"])
            else:
                out.write("* Hz SPL(dB)\n")

            for i, line in enumerate(self.data):
                if i == 0:
                    continue
                parts = line.strip().split("\t")
                if not parts or not parts[0]:
                    continue
                try:
                    float(parts[0])
                except ValueError:
                    break
                if len(parts) >= 3:
                    hz = parts[0]
                    spl = parts[2]
                    if output_format == ".csv":
                        writer.writerow([hz, spl])
                    else:
                        out.write(f"{hz} {spl}\n")


def output_path_for_format(input_file: str, output_format: str) -> str:
    """Return an output path using the input stem and selected format.

    Args:
        input_file: Path to the AudioTool input file.
        output_format: Output extension with or without a leading dot.

    Returns:
        The input path with its extension replaced by ``.txt`` or ``.csv``.

    Raises:
        ValueError: If the output format is not supported.
    """
    normalized_format = output_format.lower().lstrip(".")
    if normalized_format not in {"txt", "csv"}:
        raise ValueError("Output format must be txt or csv")
    return str(Path(input_file).with_suffix(f".{normalized_format}"))


def main(arguments: list[str] | None = None) -> int:
    """Run the command-line converter.

    Args:
        arguments: Optional command-line arguments without the program name.

    Returns:
        Zero on success, or one when conversion fails.
    """
    parser = ArgumentParser(description="Convert AudioTool files to REW format")
    parser.add_argument("input_file", help="Path to the input AudioTool file")
    parser.add_argument(
        "--format",
        choices=["txt", "csv"],
        default="txt",
        help="Output format (default: txt)",
    )
    args = parser.parse_args(arguments)
    try:
        output_file = output_path_for_format(args.input_file, args.format)
        converter = Converter(args.input_file, output_file)
        converter.load_data()
        converter.converter_full_res()
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Conversion failed: {error}")
        return 1

    print("Conversion complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
