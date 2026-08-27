import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory

from rew_converter.detect_encoding import detect_file_encoding
from rew_converter.rew_converter import Converter, main, output_path_for_format


class ConverterTests(unittest.TestCase):
    PROJECT_ROOT = Path(__file__).parent.parent

    def test_converts_at_file_using_frequency_and_db_columns(self) -> None:
        with TemporaryDirectory() as directory:
            input_path = Path(directory) / "measurement.at"
            output_path = Path(directory) / "measurement.txt"
            input_path.write_text(
                "AudioTool Spectrum File\tColumns are: Hz, Volts, dB\n"
                "10\t0.5\t-3.25\n"
                "20\t0.7\t1.5\n",
                encoding="ascii",
            )

            converter = Converter(str(input_path), str(output_path))
            converter.load_data()
            converter.converter_full_res()

            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                "* Hz SPL(dB)\n10 -3.25\n20 1.5\n",
            )

    def test_accepts_swp_file_with_additional_columns(self) -> None:
        with TemporaryDirectory() as directory:
            input_path = Path(directory) / "measurement.swp"
            output_path = Path(directory) / "measurement.txt"
            input_path.write_text(
                "AudioTool Spectrum File\tColumns are: Hz, Volts, dB, peakVolts, valleyVolts\n"
                "10\t0.5\t-3.25\t0.6\t0.1\n",
                encoding="ascii",
            )

            converter = Converter(str(input_path), str(output_path))
            converter.load_data()
            converter.converter_full_res()

            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                "* Hz SPL(dB)\n10 -3.25\n",
            )

    def test_stops_at_second_data_block(self) -> None:
        with TemporaryDirectory() as directory:
            input_path = Path(directory) / "measurement.at"
            output_path = Path(directory) / "measurement.txt"
            input_path.write_text(
                "AudioTool Spectrum File\tColumns are: Hz, Volts, dB\n"
                "10\t0.5\t-3.25\n"
                "20\t0.7\t1.5\n"
                "1/3 Octave Data: Columns are Frequency(Hz), dB\n"
                "20.0\t99.0\n",
                encoding="ascii",
            )

            converter = Converter(str(input_path), str(output_path))
            converter.load_data()
            converter.converter_full_res()

            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                "* Hz SPL(dB)\n10 -3.25\n20 1.5\n",
            )

    def test_invalid_input_does_not_overwrite_existing_output(self) -> None:
        with TemporaryDirectory() as directory:
            input_path = Path(directory) / "measurement.csv"
            output_path = Path(directory) / "measurement.txt"
            input_path.write_text("not an AudioTool file", encoding="ascii")
            output_path.write_text("previous conversion\n", encoding="utf-8")

            converter = Converter(str(input_path), str(output_path))
            with self.assertRaises(ValueError):
                converter.load_data()

            self.assertEqual(
                output_path.read_text(encoding="utf-8"), "previous conversion\n"
            )

    def test_verify_extension_is_case_insensitive(self) -> None:
        with TemporaryDirectory() as directory:
            input_path = Path(directory) / "measurement.AT"
            input_path.write_text("header\n10\t0\t1\n", encoding="ascii")

            self.assertTrue(Converter(str(input_path), "output.txt").verify_extension())

    def test_converter_requires_loaded_data(self) -> None:
        with TemporaryDirectory() as directory:
            output_path = Path(directory) / "measurement.txt"

            with self.assertRaises(ValueError):
                Converter("measurement.at", str(output_path)).converter_full_res()

            self.assertFalse(output_path.exists())

    def test_converter_rejects_unsupported_output_suffix(self) -> None:
        with TemporaryDirectory() as directory:
            input_path = Path(directory) / "measurement.at"
            output_path = Path(directory) / "measurement.zma"
            input_path.write_text("header\n10\t0\t1\n", encoding="ascii")

            converter = Converter(str(input_path), str(output_path))
            converter.load_data()

            with self.assertRaises(ValueError):
                converter.converter_full_res()

            self.assertFalse(output_path.exists())

    def test_converter_skips_blank_and_short_rows(self) -> None:
        with TemporaryDirectory() as directory:
            input_path = Path(directory) / "measurement.at"
            output_path = Path(directory) / "measurement.txt"
            input_path.write_text("header\n\n10\t0\n20\t0\t1\n", encoding="ascii")

            converter = Converter(str(input_path), str(output_path))
            converter.load_data()
            converter.converter_full_res()

            self.assertEqual(
                output_path.read_text(encoding="utf-8"), "* Hz SPL(dB)\n20 1\n"
            )

    def test_empty_input_is_rejected_without_creating_output(self) -> None:
        with TemporaryDirectory() as directory:
            input_path = Path(directory) / "measurement.at"
            output_path = Path(directory) / "measurement.txt"
            input_path.write_text("", encoding="ascii")

            converter = Converter(str(input_path), str(output_path))
            converter.load_data()

            with self.assertRaises(ValueError):
                converter.converter_full_res()

            self.assertFalse(output_path.exists())

    def test_main_returns_zero_and_reports_success(self) -> None:
        with TemporaryDirectory() as directory:
            input_path = Path(directory) / "measurement.at"
            input_path.write_text("header\n10\t0\t1\n", encoding="ascii")
            stdout = StringIO()

            with redirect_stdout(stdout):
                result = main([str(input_path)])

            self.assertEqual(result, 0)
            self.assertIn("Conversion complete", stdout.getvalue())
            self.assertTrue((Path(directory) / "measurement.txt").exists())

    def test_main_returns_one_and_reports_failure(self) -> None:
        stdout = StringIO()

        with redirect_stdout(stdout):
            result = main(["missing.csv"])

        self.assertEqual(result, 1)
        self.assertIn("Conversion failed", stdout.getvalue())

    def test_detect_file_encoding_reads_file_without_import_side_effects(self) -> None:
        with TemporaryDirectory() as directory:
            input_path = Path(directory) / "measurement.at"
            input_path.write_bytes(b"header\n10\t0\t1\n")

            result = detect_file_encoding(str(input_path))

            self.assertEqual(result["encoding"], "ascii")

    def test_converts_real_at_fixture(self) -> None:
        self._assert_fixture_conversion("1tercodeoitava.at", 5)

    def test_converts_real_swp_fixture(self) -> None:
        self._assert_fixture_conversion("sweep.swp", 3)

    def test_converts_medicao2_values_from_db_column(self) -> None:
        with TemporaryDirectory() as directory:
            input_path = Path(directory) / "Medicao2.at"
            output_path = Path(directory) / "measurement.txt"
            copyfile(self.PROJECT_ROOT / "Medicao2.at", input_path)

            converter = Converter(str(input_path), str(output_path))
            converter.load_data()
            converter.converter_full_res()
            output_lines = output_path.read_text(encoding="utf-8").splitlines()

            self.assertEqual(len(output_lines), 8193)
            self.assertEqual(output_lines[1], "0.0 0.0")
            self.assertEqual(output_lines[2], "2.691650390625 0.0")
            self.assertEqual(output_lines[4096], "11022.308349609375 47.19904927529247")
            self.assertEqual(output_lines[-1], "22047.308349609375 0.0")

    def test_main_derives_txt_output_name_from_input(self) -> None:
        with TemporaryDirectory() as directory:
            input_path = Path(directory) / "Medicao2.at"

            copyfile(self.PROJECT_ROOT / "Medicao2.at", input_path)

            result = main([str(input_path)])

            self.assertEqual(result, 0)
            self.assertTrue((Path(directory) / "Medicao2.txt").exists())

    def test_main_generates_csv_output_with_input_base_name(self) -> None:
        with TemporaryDirectory() as directory:
            input_path = Path(directory) / "Medicao2.at"

            copyfile(self.PROJECT_ROOT / "Medicao2.at", input_path)

            result = main([str(input_path), "--format", "csv"])
            output_path = Path(directory) / "Medicao2.csv"

            self.assertEqual(result, 0)
            self.assertTrue(output_path.exists())
            self.assertEqual(
                output_path.read_text(encoding="utf-8").splitlines()[0], "Hz,SPL(dB)"
            )

    def test_main_rejects_unsupported_output_format(self) -> None:
        with TemporaryDirectory() as directory:
            input_path = Path(directory) / "Medicao2.at"
            copyfile(self.PROJECT_ROOT / "Medicao2.at", input_path)

            with self.assertRaises(SystemExit) as error:
                main([str(input_path), "--format", "zma"])

            self.assertEqual(error.exception.code, 2)
            self.assertFalse((Path(directory) / "Medicao2.zma").exists())

    def test_output_path_for_format_rejects_unsupported_format(self) -> None:
        with self.assertRaises(ValueError):
            output_path_for_format("Medicao2.at", ".frd")

    def _assert_fixture_conversion(self, fixture_name: str, column_count: int) -> None:
        with TemporaryDirectory() as directory:
            input_path = Path(directory) / fixture_name
            output_path = Path(directory) / "measurement.txt"
            copyfile(self.PROJECT_ROOT / fixture_name, input_path)

            converter = Converter(str(input_path), str(output_path))
            converter.load_data()
            converter.converter_full_res()
            output_lines = output_path.read_text(encoding="utf-8").splitlines()
            first_data = output_lines[1].split()

            self.assertEqual(len(first_data), 2)
            self.assertGreater(len(output_lines), 1)
            self.assertEqual(
                len(input_path.read_text(encoding="ascii").splitlines()[1].split("\t")),
                column_count,
            )
            self.assertEqual(len(output_lines), 2049)
            frequencies = [float(line.split()[0]) for line in output_lines[1:]]
            self.assertEqual(frequencies, sorted(frequencies))
            self.assertEqual(frequencies[-1], 22039.2333984375)


if __name__ == "__main__":
    unittest.main()
