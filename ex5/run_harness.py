import sys
import os
import json
import subprocess
import shutil
import difflib
import time
import random
import ascii_art
import fail_art

# --- Constants ---
SCRIPT_TO_TEST = "wordsearch.py"
JSON_DATA_FILE = "tests.json"
REPORT_FILE_NAME = "test_report.md"
TEMP_DIR = "test_temp_files"
TIMEOUT_SECONDS = 4

# --- Emojis ---
PASS_MARK = "✅"
FAIL_MARK = "🔴"
ERROR_MARK = "⚠️"
TIMEOUT_MARK = "⏱️"


def get_base_path():
    """Gets the path of the script/EXE, for finding external files."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


def get_data_path(filename):
    """Gets the path of a bundled data file (like tests.json)."""
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, filename)
    else:
        return os.path.join(get_base_path(), filename)


def wsl_path(windows_path):
    """Converts a Windows path to its WSL equivalent."""
    abs_path = os.path.abspath(windows_path)
    drive = abs_path[0].lower()
    path_no_drive = abs_path[2:].replace('\\', '/')
    return f"/mnt/{drive}{path_no_drive}"


def create_text_diff(expected_lines, actual_lines):
    """
    Creates a smart side-by-side comparison.
    It inserts gaps so that matching lines stay aligned.
    """
    # Use SequenceMatcher to find the "longest common subsequence"
    # This ensures that if a line exists in both, we align them.
    matcher = difflib.SequenceMatcher(None, expected_lines, actual_lines)

    # Calculate column width
    max_len = 0
    for line in expected_lines:
        max_len = max(max_len, len(line))
    for line in actual_lines:
        max_len = max(max_len, len(line))

    col_width = max(20, min(max_len + 2, 60))

    output = []
    header = f"{'EXPECTED'.ljust(col_width)} | ACTUAL"
    output.append(header)
    output.append("-" * len(header))

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            # The lines match in this range. Print them side-by-side.
            for i in range(i1, i2):
                line = expected_lines[i]
                trunc = (line[:col_width - 3] + '..') if len(line) > col_width else line
                output.append(f"{trunc.ljust(col_width)} | {line}")

        elif tag == 'replace':
            # Lines are different. Try to print them side-by-side, marking them.
            range_len = max(i2 - i1, j2 - j1)
            for k in range(range_len):
                exp_txt = expected_lines[i1 + k] if i1 + k < i2 else ""
                act_txt = actual_lines[j1 + k] if j1 + k < j2 else ""

                exp_cell = (exp_txt[:col_width - 3] + '..') if len(exp_txt) > col_width else exp_txt
                output.append(f"{exp_cell.ljust(col_width)} | {act_txt} <--")

        elif tag == 'delete':
            # Exists in Expected, but MISSING in Actual
            for i in range(i1, i2):
                line = expected_lines[i]
                exp_cell = (line[:col_width - 3] + '..') if len(line) > col_width else line
                output.append(f"{exp_cell.ljust(col_width)} | (MISSING) <--")

        elif tag == 'insert':
            # Exists in Actual, but NOT in Expected (Extra output)
            for j in range(j1, j2):
                line = actual_lines[j]
                output.append(f"{''.ljust(col_width)} | {line} <--")

    return "\n".join(output)


def write_report(lines, base_dir, passed, total):
    """Writes the final markdown report."""
    report_path = os.path.join(base_dir, REPORT_FILE_NAME)
    print(f"\nWriting report to {report_path}...")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Wordsearch Test Report - {time.ctime()}\n\n")
        f.write("## 📝 Summary\n")
        f.write(f"**{passed} / {total} tests passed.**\n\n")
        f.write("---\n\n")
        f.write("\n\n---\n\n".join(lines))


def main():
    BASE_DIR = get_base_path()
    TEMP_DIR_PATH = os.path.join(BASE_DIR, TEMP_DIR)

    print("--- Automated Test Harness ---")

    # --- 1. Setup ---
    print("1. Cleaning up old files...")
    if os.path.exists(TEMP_DIR_PATH):
        shutil.rmtree(TEMP_DIR_PATH)
    os.makedirs(TEMP_DIR_PATH)

    report_path = os.path.join(BASE_DIR, REPORT_FILE_NAME)
    if os.path.exists(report_path):
        os.remove(report_path)

    # --- 2. Find Script ---
    print("2. Locating script to test...")
    wordsearch_script_path = os.path.join(BASE_DIR, SCRIPT_TO_TEST)

    if os.path.exists(wordsearch_script_path):
        print(f"   Found file: {SCRIPT_TO_TEST}. Proceeding...")
    else:
        print(f"\n{ERROR_MARK} FATAL ERROR: Cannot find {SCRIPT_TO_TEST}.")
        print(f"Please place {SCRIPT_TO_TEST} in the same folder as this executable.")
        input("Press Enter to exit.")
        return

    # --- 3. Load Tests ---
    print("3. Loading test definitions...")
    try:
        json_path = get_data_path(JSON_DATA_FILE)
        with open(json_path, 'r') as f:
            tests = json.load(f)
        print(f"   Loaded {len(tests)} test(s).")
    except Exception as e:
        print(f"\n{ERROR_MARK} FATAL ERROR: Failed to load bundled {JSON_DATA_FILE}.")
        print(f"   Error: {e}")
        input("Press Enter to exit.")
        return

    # --- 4. Run Tests ---
    print("4. Running tests...")
    total_tests = len(tests)
    passed_tests = 0
    report_lines = []

    for test in tests:
        test_name = test["test_name"]
        print(f"--- Running: {test_name}", end='')

        status_line = f"## {ERROR_MARK} Test: {test_name} - ERROR"
        report_content = ""

        try:
            # Create temp files
            wordlist_file = os.path.join(TEMP_DIR_PATH, f"words_{test_name}.txt")
            matrix_file = os.path.join(TEMP_DIR_PATH, f"matrix_{test_name}.txt")
            actual_file = os.path.join(TEMP_DIR_PATH, f"actual_{test_name}.txt")

            with open(wordlist_file, "w") as f:
                f.write(test["wordlist_content"])
            with open(matrix_file, "w") as f:
                f.write(test["matrix_content"])

            cmd = [
                "wsl.exe", "python3",
                wsl_path(wordsearch_script_path),
                wsl_path(wordlist_file),
                wsl_path(matrix_file),
                wsl_path(actual_file),
                test["directions"]
            ]

            start_time = time.time()
            result = subprocess.run(cmd, timeout=TIMEOUT_SECONDS, capture_output=True, text=True, encoding='utf-8')
            duration = time.time() - start_time

            if result.returncode != 0:
                status_line = f"## {ERROR_MARK} Test: {test_name} - SCRIPT ERROR"
                report_content = f"**Script failed with a runtime error.**\n**Duration:** {duration:.2f}s\n"
                report_content += "### Stderr:\n```\n" + (result.stderr or "No stderr") + "\n```\n"
            else:
                with open(actual_file, 'r', encoding='utf-8') as f:
                    actual_content = f.read()

                expected_lines = [line for line in test["expected_output_content"].strip().split('\n') if line.strip()]
                actual_lines = [line for line in actual_content.strip().split('\n') if line.strip()]

                # SORT FIRST to ignore random output order
                expected_sorted = sorted(expected_lines)
                actual_sorted = sorted(actual_lines)

                if actual_sorted == expected_sorted:
                    status_line = f"## {PASS_MARK} Test: {test_name} - PASS"
                    report_content = f"**Duration:** {duration:.2f}s\n"
                    passed_tests += 1
                else:
                    status_line = f"## {FAIL_MARK} Test: {test_name} - FAIL"

                    # USE SMART DIFF on the sorted lists
                    text_diff = create_text_diff(expected_sorted, actual_sorted)

                    report_content = f"**Output did not match expected.**\n**Duration:** {duration:.2f}s\n"
                    report_content += f"### Differences (Side-by-Side)\n```text\n{text_diff}\n```\n"

        except subprocess.TimeoutExpired as e:
            status_line = f"## {TIMEOUT_MARK} Test: {test_name} - TIMEOUT"
            report_content = f"**Test exceeded {TIMEOUT_SECONDS} second limit.**\n"
        except Exception as e:
            report_content = f"**Test harness failed with a Python error:**\n```\n{e}\n```\n"

        print(f" -> {status_line.split(' ')[-1]}")
        report_lines.append(f"{status_line}\n\n{report_content}")

    # --- 5. Final Report & Cleanup ---
    write_report(report_lines, BASE_DIR, passed_tests, total_tests)
    print("5. Cleaning up temporary files...")
    shutil.rmtree(TEMP_DIR_PATH)

    # --- 6. Output Art ---
    if 0 < total_tests == passed_tests:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(random.choice(ascii_art.SUCCESS_OPTIONS))
        print("Congratulations! You passed all the tests!")
    else:
        os.system('cls' if os.name == 'nt' else 'clear')

        print(random.choice(fail_art.FAILURE_OPTIONS))
        print("\n---")
        print(f"Test run complete. {passed_tests} / {total_tests} passed.")
        print(f"Report saved to: {os.path.join(BASE_DIR, REPORT_FILE_NAME)}")

    input("Press Enter to exit.")


if __name__ == "__main__":
    main()