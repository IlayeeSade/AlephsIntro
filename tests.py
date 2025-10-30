import json
import importlib
import sys
from datetime import datetime
from typing import Any, Dict, List
import traceback

class TestRunner:
    def __init__(self, test_file: str = "test_cases.json", output_file: str = "test_failures.txt"):
        """
        Initialize the test runner.

        Args:
            test_file: JSON file containing test cases
            output_file: File to write test failures
        """
        self.test_file = test_file
        self.output_file = output_file
        self.failures = []
        self.passed = 0
        self.failed = 0

    def load_test_cases(self) -> List[Dict]:
        """Load test cases from JSON file."""
        try:
            with open(self.test_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Test file '{self.test_file}' not found.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in '{self.test_file}'.")
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
        """
        Execute function and capture both return value and printed output.
        Optionally simulate user input.

        Args:
            func: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            input_text: String or list of strings to simulate user input

        Returns:
            tuple: (return_value, printed_output)
        """
        from io import StringIO
        import sys

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        # Simulate stdin if input_text is provided
        old_stdin = None
        if input_text is not None:
            old_stdin = sys.stdin
            # Convert list to newline-separated string
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
        # Handle None cases
        if actual is None and expected is None:
            return True
        if actual is None or expected is None:
            return False

        # Handle lists/tuples
        if isinstance(actual, (list, tuple)) and isinstance(expected, (list, tuple)):
            if len(actual) != len(expected):
                return False
            return all(self.compare_values(a, e) for a, e in zip(actual, expected))

        # Direct comparison
        return actual == expected

    def run_single_test(self, test_case: Dict) -> Dict:
        """
        Run a single test case.

        Returns:
            Dict with test results
        """
        test_name = test_case.get('test_name', 'Unnamed Test')
        module_name = test_case.get('module')  # e.g., "f1"
        function_name = test_case.get('function')  # e.g., "my_function"

        # Input arguments
        args = test_case.get('args', [])
        kwargs = test_case.get('kwargs', {})

        # Simulated user input
        input_text = test_case.get('input_text', None)

        # Expected values
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
            'input_text': input_text
        }

        try:
            # Import the function
            func = self.import_function(module_name, function_name)

            # Run function and capture output (with simulated input if provided)
            actual_return, actual_output = self.capture_output(func, args, kwargs, input_text)

            result['actual_return'] = actual_return
            result['actual_output'] = actual_output

            # Compare return values
            return_match = self.compare_values(actual_return, expected_return)

            # Compare printed output (strip whitespace for comparison)
            output_match = False
            if type(expected_output) is list:
                for e_o in expected_output:
                    output_match = (actual_output.strip() == e_o.strip()) or output_match
            else:
                output_match = actual_output.strip() == expected_output.strip()

            # Test passes if both match
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
        lines = []
        lines.append("=" * 80)
        lines.append(f"FAILED: {result['test_name']}")
        lines.append("=" * 80)
        lines.append(f"Error Type: {result['error']}")
        lines.append("")

        if result.get('input_text'):
            lines.append(f"Simulated Input: {repr(result['input_text'])}")
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

        # Write failures to file
        self.write_failure_report()

        # Print summary
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
            f.write(f"Total Failures: {self.failed}\n")
            f.write("\n")

            if self.failures:
                for failure in self.failures:
                    f.write(self.format_failure_report(failure))
            else:
                f.write("No failures! All tests passed.\n")


# Example usage
if __name__ == "__main__":
    print("\nTo use this framework:")
    print("1. Edit test_cases.json with your actual test cases")
    print("2. Run: python test_framework.py")
    print("\nStarting test run...\n")

    # Run the tests
    runner = TestRunner(test_file="test_cases.json", output_file="test_failures.txt")
    runner.run_all_tests()