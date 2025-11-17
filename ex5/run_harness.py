import sys
import os
import json
import zipfile
import subprocess
import shutil
import difflib
import time

# --- Constants ---
ZIP_FILE_NAME = "ex5.zip"
SCRIPT_TO_TEST = "wordsearch.py"
JSON_DATA_FILE = "tests.json"
REPORT_FILE_NAME = "test_report.md"
TEMP_DIR = "test_temp_files"
TIMEOUT_SECONDS = 10

# --- Emojis ---
PASS_MARK = "✅"
FAIL_MARK = "🔴"
ERROR_MARK = "⚠️"
TIMEOUT_MARK = "⏱️"

# --- ASCII Art ---
CROWN_ART = r"""
                                        ******                                        
                                        ******                                        
                                        ******                                        
                                          **                                          
                                          **                                          
                             **           **           **                             
                           ******        ****        ******                           
                           ******        ****        ******                           
            *****           ****         ****         ****           *****            
            ******           ***         ****         ***           *******           
  **        *****            ***        ******        ***            *****        **  
*****         **             ****       ******       ****             **         *****
******        ***            ****      ********      ****            ***        ******
 ***          ****          ******     ********     ******          ****          *** 
   **         *****         *******   **********   *******         *****         **   
   **        *******        ******************************        *******        **   
    **       ********      ********************************      ********       **    
    ***     **********    **********************************    **********     ***    
    *****   **************************************************************   *****    
     ****************************************************************************     
     ****************************************************************************     
      **************************************************************************      
      **************************************************************************      
      **************************************************************************      
       ************************************************************************       
       ************************************************************************       
       ************************************************************************       
        **********************************************************************        
        **********************************************************************        
        **********************************************************************        
        *********************                             ********************        
         *******       ****************************************       *******         
               ********************************************************               
          **************                                      **************          
          ******                                                      ******          
"""

def get_base_path():
    """Gets the path of the script/EXE, for finding external files."""
    if getattr(sys, 'frozen', False):
        # We are running in a bundle (pyinstaller)
        return os.path.dirname(sys.executable)
    else:
        # We are running in a normal Python environment
        return os.path.dirname(os.path.abspath(__file__))


def get_data_path(filename):
    """Gets the path of a bundled data file (like tests.json)."""
    if getattr(sys, 'frozen', False):
        # Path to data in bundle
        return os.path.join(sys._MEIPASS, filename)
    else:
        # Path to data in source
        return os.path.join(get_base_path(), filename)


def wsl_path(windows_path):
    """Converts a Windows path to its WSL equivalent."""
    abs_path = os.path.abspath(windows_path)
    drive = abs_path[0].lower()
    path_no_drive = abs_path[2:].replace('\\', '/')
    return f"/mnt/{drive}{path_no_drive}"


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
    ZIP_FILE_PATH = os.path.join(BASE_DIR, ZIP_FILE_NAME)

    print("--- Automated Test Harness ---")

    # --- 1. Setup (Clean old files) ---
    print("1. Cleaning up old files...")
    if os.path.exists(TEMP_DIR_PATH):
        shutil.rmtree(TEMP_DIR_PATH)
    os.makedirs(TEMP_DIR_PATH)

    report_path = os.path.join(BASE_DIR, REPORT_FILE_NAME)
    if os.path.exists(report_path):
        os.remove(report_path)

    # --- 2. Unzip ex5.zip ---
    print(f"2. Locating and unzipping {ZIP_FILE_NAME}...")
    if not os.path.exists(ZIP_FILE_PATH):
        print(f"\n{ERROR_MARK} FATAL ERROR: Cannot find {ZIP_FILE_NAME}")
        print(f"Please place {ZIP_FILE_NAME} in the same folder as this executable.")
        input("Press Enter to exit.")
        return

    try:
        with zipfile.ZipFile(ZIP_FILE_PATH, 'r') as z:
            z.extract(SCRIPT_TO_TEST, TEMP_DIR_PATH)
        wordsearch_script_path = os.path.join(TEMP_DIR_PATH, SCRIPT_TO_TEST)
        if not os.path.exists(wordsearch_script_path):
            raise FileNotFoundError
        print(f"   Successfully unzipped {SCRIPT_TO_TEST}")
    except Exception as e:
        print(f"\n{ERROR_MARK} FATAL ERROR: Failed to unzip {SCRIPT_TO_TEST} from {ZIP_FILE_NAME}.")
        print(f"   Error: {e}")
        input("Press Enter to exit.")
        return

    # --- 3. Load tests.json ---
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
            # --- Create temp files for this test ---
            wordlist_file = os.path.join(TEMP_DIR_PATH, f"words_{test_name}.txt")
            matrix_file = os.path.join(TEMP_DIR_PATH, f"matrix_{test_name}.txt")
            actual_file = os.path.join(TEMP_DIR_PATH, f"actual_{test_name}.txt")

            with open(wordlist_file, "w") as f:
                f.write(test["wordlist_content"])
            with open(matrix_file, "w") as f:
                f.write(test["matrix_content"])

            # --- Convert paths to WSL format ---
            cmd = [
                "wsl.exe", "python3",
                wsl_path(wordsearch_script_path),
                wsl_path(wordlist_file),
                wsl_path(matrix_file),
                wsl_path(actual_file),
                test["directions"]
            ]

            # --- Run the command ---
            start_time = time.time()
            result = subprocess.run(cmd, timeout=TIMEOUT_SECONDS, capture_output=True, text=True, encoding='utf-8')
            duration = time.time() - start_time

            if result.returncode != 0:
                status_line = f"## {ERROR_MARK} Test: {test_name} - SCRIPT ERROR"
                report_content = f"**Script failed with a runtime error.**\n**Duration:** {duration:.2f}s\n"
                report_content += "### Stderr:\n```\n" + (result.stderr or "No stderr") + "\n```\n"
            else:
                # Script ran, now compare output
                with open(actual_file, 'r', encoding='utf-8') as f:
                    actual_content = f.read()

                expected_lines = [line for line in test["expected_output_content"].strip().split('\n') if line.strip()]
                actual_lines = [line for line in actual_content.strip().split('\n') if line.strip()]

                # Sort for comparison
                expected_sorted = sorted(expected_lines)
                actual_sorted = sorted(actual_lines)

                if actual_sorted == expected_sorted:
                    status_line = f"## {PASS_MARK} Test: {test_name} - PASS"
                    report_content = f"**Duration:** {duration:.2f}s\n"
                    passed_tests += 1
                else:
                    status_line = f"## {FAIL_MARK} Test: {test_name} - FAIL"

                    # --- Create Side-by-Side HTML Diff ---
                    d = difflib.HtmlDiff(wrapcolumn=80)
                    html_diff = d.make_table(expected_sorted, actual_sorted, "Expected (Sorted)", "Actual (Sorted)")

                    # Add a little style to make it look nice and fixed-width
                    style = """
<style>
    table.diff {font-family: 'Courier New', monospace; border-collapse: collapse; width: 100%;}
    .diff_header {text-align: center; font-weight: bold; background-color: #f0f0f0;}
    .diff td {padding: 3px; white-space: pre-wrap; vertical-align: top;}
    .diff_next, .diff_chg, .diff_add, .diff_sub {background-color: #f8f8f8;}
    td.diff_sub {background-color: #ffe6e6;}
    td.diff_add {background-color: #e6ffe6;}
</style>
"""

                    report_content = f"**Output did not match expected.**\n**Duration:** {duration:.2f}s\n"
                    report_content += f"### Differences (Side-by-Side)\n{style}\n{html_diff}\n"

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

    # --- 6. Final Output (Crown or Summary) ---
    if total_tests > 0 and passed_tests == total_tests:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(CROWN_ART)
        print("Congratulations! You passed all the tests!")
    else:
        print("\n---")
        print(f"Test run complete. {passed_tests} / {total_tests} passed.")
        print(f"Report saved to: {os.path.join(BASE_DIR, REPORT_FILE_NAME)}")

    input("Press Enter to exit.")


if __name__ == "__main__":
    main()