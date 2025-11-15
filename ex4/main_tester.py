import json
import importlib
import sys
import os
import tempfile
import zipfile
from datetime import datetime
from typing import Any, Dict, List
import traceback
import shutil


class TestRunner:
    def __init__(self, test_file="main_cases.json", output_file="game_simulation_results.txt", modules_zip="ex4.zip"):
        self.test_file = test_file
        self.output_file = output_file
        self.modules_zip = modules_zip

        self.failures = []
        self.passed = 0
        self.failed = 0

        self.temp_dir = None

        # prepare ZIP modules
        if self.modules_zip:
            self._prepare_modules_from_zip()

    def __del__(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _prepare_modules_from_zip(self):
        if not os.path.exists(self.modules_zip):
            print(f"Error: ZIP file '{self.modules_zip}' not found.")
            sys.exit(1)

        self.temp_dir = tempfile.mkdtemp(prefix="modules_")
        with zipfile.ZipFile(self.modules_zip, 'r') as z:
            z.extractall(self.temp_dir)

        sys.path.insert(0, self.temp_dir)

    # -------------------------------------------------------
    def load_test_cases(self):
        try:
            with open(self.test_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            print(f"Error: could not load {self.test_file}")
            sys.exit(1)

    # -------------------------------------------------------
    # Utilities for Battleship helper replacement
    # -------------------------------------------------------
    def cell_name_to_loc(self, name):
        name = name.strip().upper()
        col = ord(name[0]) - ord('A')
        row = int(name[1:]) - 1
        return (row, col)

    def prepare_test_helper(self, th, spec):
        th.NUM_ROWS = spec["rows"]
        th.NUM_COLUMNS = spec["columns"]
        th.SHIP_SIZES = tuple(spec["ship_sizes"])

        th.INPUT_QUEUE = list(spec.get("input_text", []))
        th._input_index = 0

        # deterministic computer ship placement
        raw_sp = spec.get("computer_ship_placements", [])
        th.SHIP_PLACEMENTS = [
            self.cell_name_to_loc(x) if isinstance(x, str) else tuple(x)
            for x in raw_sp
        ]
        th._ship_index = 0

        # deterministic computer torpedoes
        raw_ts = spec.get("computer_torpedo_sequence", [])
        th.TORPEDO_SEQUENCE = [
            self.cell_name_to_loc(x) if isinstance(x, str) else tuple(x)
            for x in raw_ts
        ]
        th._torpedo_index = 0

        if hasattr(th, "reset"):
            th.reset()

    # -------------------------------------------------------
    def import_battleship_with_test_helper(self, spec):
        """
        Imports battleship.py but replaces module 'helper'
        with 'test_helper' from ex4.zip
        """

        try:
            test_helper = importlib.import_module("test_helper")
        except Exception:
            print("❌ Could not import test_helper from ex4.zip")
            sys.exit(1)

        # Override helper
        sys.modules["helper"] = test_helper

        # Apply test-case configuration to helper
        self.prepare_test_helper(test_helper, spec)

        # Import fresh battleship
        if "battleship" in sys.modules:
            del sys.modules["battleship"]

        return importlib.import_module("battleship"), test_helper

    # -------------------------------------------------------
    def capture_output(self, func):
        from io import StringIO

        old_stdout = sys.stdout
        sys.stdout = captured = StringIO()

        try:
            func()
            out = captured.getvalue()
        finally:
            sys.stdout = old_stdout

        return out

    # -------------------------------------------------------
    def run_single_test(self, spec: Dict) -> Dict:
        test_name = spec["test_name"]

        result = {
            "test_name": test_name,
            "passed": False,
            "error": None,
            "expected_output": spec.get("expected_output", ""),
            "actual_output": "",
            "input_text": spec.get("input_text", []),
            "computer_ship_placements": spec.get("computer_ship_placements", []),
            "computer_torpedo_sequence": spec.get("computer_torpedo_sequence", [])
        }

        try:
            battleship, th = self.import_battleship_with_test_helper(spec)

            # Always test the main()
            func = getattr(battleship, spec["function"], None)
            if func is None:
                raise Exception(f"Function {spec['function']} not found in battleship.py")

            actual = self.capture_output(func)
            result["actual_output"] = actual.strip()

            expected = spec.get("expected_output", "").strip()
            if actual.strip() == expected:
                result["passed"] = True
            else:
                result["error"] = "Output mismatch"

        except Exception as e:
            result["error"] = "Exception"
            result["traceback"] = traceback.format_exc()

        return result

    def format_failure_report(self, r: Dict) -> str:
        lines = [
            "=" * 80,
            f"FAILED: {r['test_name']}",
            "",
            f"Error Type: {r['error']}",
            ""
        ]

        if r.get("input_text"):
            lines.append(f"Simulated Input: {repr(r['input_text'])}")

        if r.get("computer_ship_placements"):
            lines.append(f"Simulated Computer Ship Placements: {repr(r['computer_ship_placements'])}")

        if r.get("computer_torpedo_sequence"):
            lines.append(f"Simulated Computer Torpedo Sequence: {repr(r['computer_torpedo_sequence'])}")
            lines.append("")

        if "traceback" in r:
            lines.append("Traceback:")
            lines.append(r["traceback"])
            lines.append("")

        if r["error"] == "Output mismatch":
            lines.append("Expected Output:")
            lines.append(r["expected_output"])
            lines.append("")
            lines.append("Actual Output:")
            lines.append(r["actual_output"])

        lines.append("")
        return "\n".join(lines)

    # -------------------------------------------------------
    def write_failure_report(self):
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write("TEST FAILURE REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Failures: {self.failed}\n\n")

            if not self.failures:
                f.write("No failures! All tests passed.\n")
                return

            for fail in self.failures:
                f.write(self.format_failure_report(fail))

    # -------------------------------------------------------
    def run_all_tests(self):

        tests = self.load_test_cases()
        print(f"Running {len(tests)} tests...\n")

        for spec in tests:
            r = self.run_single_test(spec)
            if r["passed"]:
                self.passed += 1
                print(f"✓ PASS: {spec['test_name']}")
            else:
                self.failed += 1
                print(f"✗ FAIL: {spec['test_name']}")
                self.failures.append(r)

        self.write_failure_report()

        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"\nReport written to: {self.output_file}")


if __name__ == "__main__":
    print("\nStarting Battleship test suite...\n")

    runner = TestRunner(
        test_file="main_cases.json",
        output_file="game_simulation_results.txt",
        modules_zip="ex4.zip"
    )
    runner.run_all_tests()

    input("\nPress Enter to exit...")
