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

from pyparsing import results


class TestRunner:
    def __init__(self, test_file: str = "test_cases.json", output_file: str = "test_failures.txt",
                 modules_zip: str = None):
        """
        Initialize the test runner.

        Args:
            test_file: JSON file containing test cases
            output_file: File to write test failures
            modules_zip: Optional ZIP file containing Python modules
        """
        self.test_file = test_file
        self.output_file = output_file
        self.modules_zip = modules_zip
        self.failures = []
        self.passed = 0
        self.failed = 0
        self.temp_dir = None

        # If a ZIP file is provided, extract it and add to sys.path
        if self.modules_zip:
            self._prepare_modules_from_zip()

    def __del__(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _prepare_modules_from_zip(self):
        """Extract ZIP file containing modules and add it to sys.path."""
        if not os.path.exists(self.modules_zip):
            print(f"Error: ZIP file '{self.modules_zip}' not found.")
            sys.exit(1)

        self.temp_dir = tempfile.mkdtemp(prefix="modules_")
        with zipfile.ZipFile(self.modules_zip, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)

        # Add extracted directory to sys.path for importlib to find modules
        sys.path.insert(0, self.temp_dir)
        print(f"✅ Extracted modules to: {self.temp_dir}")

    def load_test_cases(self) -> List[Dict]:
        """Load test cases from bundled JSON or from current directory."""
        # Handle PyInstaller onefile mode
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS  # temp folder PyInstaller uses
        else:
            base_path = os.path.dirname(__file__)

        test_path = os.path.join(base_path, self.test_file)

        try:
            with open(test_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Test file '{test_path}' not found.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in '{test_path}'.")
            sys.exit(1)

    def import_function(self, module_name: str, function_name: str):
        """Dynamically import a function from a module."""
        try:
            module = importlib.import_module(module_name)
            return getattr(module, function_name)
        except ModuleNotFoundError:
            raise ImportError(f"Module '{module_name}' not found.")
        except AttributeError:
            raise ImportError(f"Function '{function_name}' not found in module '{module_name}'.")

    def capture_output(self, func, args, kwargs, input_text=None):
        """Execute function and capture both return value and printed output."""
        from io import StringIO
        import sys

        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        old_stdin = None

        if input_text is not None:
            old_stdin = sys.stdin
            if isinstance(input_text, list):
                input_text = '\n'.join(str(x) for x in input_text)
            sys.stdin = StringIO(input_text)

        try:
            return_value = func(*args, **kwargs)
            printed_output = captured_output.getvalue()
        finally:
            sys.stdout = old_stdout
            if old_stdin is not None:
                sys.stdin = old_stdin

        return return_value, printed_output

    def compare_values(self, actual: Any, expected: Any) -> bool:
        """Compare two values with type flexibility."""
        if actual is None and expected is None:
            return True
        if actual is None or expected is None:
            return False
        if isinstance(actual, (list, tuple)) and isinstance(expected, (list, tuple)):
            if len(actual) != len(expected):
                return False
            return all(self.compare_values(a, e) for a, e in zip(actual, expected))
        return actual == expected

    def run_single_test(self, test_case: Dict) -> Dict:
        """Run a single test case."""
        test_name = test_case.get('test_name', 'Unnamed Test')
        module_name = test_case.get('module')
        function_name = test_case.get('function')
        args = test_case.get('args', [])
        kwargs = test_case.get('kwargs', {})
        input_text = test_case.get('input_text', None)
        expected_return = test_case.get('expected_return', None)
        expected_output = test_case.get('expected_output', "")

        result = {
            'test_name': test_name,
            'passed': False,
            'error': None,
            'actual_return': None,
            'actual_output': None,
            'expected_return': expected_return,
            'expected_output': expected_output,
            'input_text': input_text,
            'args': args
        }

        try:
            func = self.import_function(module_name, function_name)
            actual_return, actual_output = self.capture_output(func, args, kwargs, input_text)
            result['actual_return'] = actual_return
            result['actual_output'] = actual_output

            return_match = self.compare_values(actual_return, expected_return)
            output_match = False
            if isinstance(expected_output, list):
                for e_o in expected_output:
                    output_match = (actual_output.strip() == e_o.strip()) or output_match
            else:
                output_match = actual_output.strip() == expected_output.strip()

            result['passed'] = return_match and output_match
            if not return_match:
                result['error'] = 'Return value mismatch'
            elif not output_match:
                result['error'] = 'Output mismatch'

        except Exception as e:
            result['error'] = f"Exception: {str(e)}"
            result['traceback'] = traceback.format_exc()

        return result

    def format_failure_report(self, result: Dict) -> str:
        """Format a failure report for a single test."""
        lines = ["=" * 80, f"FAILED: {result['test_name']}", "" ,f"Error Type: {result['error']}"]
        if result.get('input_text'):
            lines.append(f"Simulated Input: {repr(result['input_text'])}")
            lines.append("")
        if result.get('args'):
            lines.append(f"Simulated Arguments: {repr(result['args'])}")
            lines.append("")
        if 'traceback' in result:
            lines.append("Traceback:")
            lines.append(result['traceback'])
            lines.append("")
        if result['error'] == 'Return value mismatch':
            lines.append(f"Expected Return: {repr(result['expected_return'])}")
            lines.append(f"Actual Return:   {repr(result['actual_return'])}")
        if result['error'] == 'Output mismatch':
            lines.append(f"Expected Output:\n{result['expected_output']}")
            lines.append(f"\nActual Output:\n{result['actual_output']}")
        lines.append("")
        return "\n".join(lines)

    def run_all_tests(self):
        """Run all tests and generate report."""
        test_cases = self.load_test_cases()
        print(f"Running {len(test_cases)} tests...\n")

        for test_case in test_cases:
            result = self.run_single_test(test_case)
            if result['passed']:
                self.passed += 1
                print(f"✓ PASS: {result['test_name']}")
            else:
                self.failed += 1
                print(f"✗ FAIL: {result['test_name']}")
                self.failures.append(result)

        self.write_failure_report()
        print("\n" + "=" * 80)
        print(f"TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"\nFailure report written to: {self.output_file}")

    def write_failure_report(self):
        """Write all failures to the output file."""
        with open(self.output_file, 'w') as f:
            f.write(f"TEST FAILURE REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Failures: {self.failed}\n\n")
            if self.failures:
                for failure in self.failures:
                    f.write(self.format_failure_report(failure))
            else:
                f.write("No failures! All tests passed.\n")


# Example usage
if __name__ == "__main__":
    print("\nStarting test run...\n")

    # Run the tests
    runner = TestRunner(test_file="test_cases.json", output_file="test_failures.txt", modules_zip="ex3.zip")
    runner.run_all_tests()
    input("Press Enter to finish...")
