import sys
import os
import subprocess
import glob
import math

# ================= CONFIGURATION =================
# Colors for pretty printing
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

PROGRAM = "kmeans_pp.py"
SETUP_FILE = "setup.py"
TEST_DIR = "tests"

# Tolerance for float comparison
EPSILON_TOLERANCE = 0.0001

# ================= HELPER FUNCTIONS =================

def log(msg, color=RESET):
    print(f"{color}{msg}{RESET}")

def compile_extension():
    """
    Compiles the C extension using setup.py.
    """
    log(">> Compiling C extension...", CYAN)
    cmd = [sys.executable, SETUP_FILE, "build_ext", "--inplace"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        log("Compilation FAILED!", RED)
        print(result.stderr)
        sys.exit(1)
    
    log("Compilation SUCCESS!", GREEN)

def create_dummy_files():
    """
    Creates small dummy files for logic testing (Error handling).
    """
    with open("dummy_1.csv", "w") as f:
        f.write("1,1.0,2.0\n2,3.0,4.0\n3,5.0,6.0\n")
    with open("dummy_2.csv", "w") as f:
        f.write("1,1.0,2.0\n2,3.0,4.0\n3,5.0,6.0\n")

def remove_dummy_files():
    """Cleans up dummy files."""
    for f in ["dummy_1.csv", "dummy_2.csv"]:
        if os.path.exists(f):
            os.remove(f)

def check_output_match(generated, expected_file):
    """
    Compares generated output string with the content of expected_file.
    Handles float comparison with tolerance.
    """
    try:
        with open(expected_file, 'r') as f:
            expected_lines = f.read().strip().splitlines()
    except FileNotFoundError:
        return False, f"Missing expected file: {expected_file}"

    gen_lines = generated.strip().splitlines()

    # Filter out empty lines
    gen_lines = [line.strip() for line in gen_lines if line.strip()]
    expected_lines = [line.strip() for line in expected_lines if line.strip()]

    if len(gen_lines) != len(expected_lines):
        return False, f"Line count mismatch. Got {len(gen_lines)}, Expected {len(expected_lines)}"

    # Compare first line (Indices) - exact match required
    # NOTE: Since seed is fixed (1234), indices should be identical.
    if gen_lines[0] != expected_lines[0]:
        return False, f"Indices mismatch.\nGot: {gen_lines[0]}\nExp: {expected_lines[0]}"

    # Compare Centroids (Floats)
    for i in range(1, len(gen_lines)):
        gen_vals = gen_lines[i].split(',')
        exp_vals = expected_lines[i].split(',')

        if len(gen_vals) != len(exp_vals):
            return False, f"Dimension mismatch at line {i+1}"

        for j in range(len(gen_vals)):
            try:
                g = float(gen_vals[j])
                e = float(exp_vals[j])
                if abs(g - e) > EPSILON_TOLERANCE:
                     return False, f"Value mismatch at line {i+1}, dim {j+1}: {g} vs {e}"
            except ValueError:
                return False, f"Non-numeric value found: {gen_vals[j]}"
    
    return True, "Perfect Match"

def run_test_case(name, args, expected_msg=None, expected_ret_code=0, validation_file=None):
    """
    Runs a single test case.
    """
    cmd = [sys.executable, PROGRAM] + args
    
    print(f"Running {name}...", end=" ")
    
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except subprocess.TimeoutExpired:
        log("TIMEOUT [FAIL]", RED)
        return False

    # Check Return Code
    if res.returncode != expected_ret_code:
        log(f"[FAIL] (Return Code: {res.returncode}, Expected: {expected_ret_code})", RED)
        print(f"Stderr: {res.stderr}")
        print(f"Stdout: {res.stdout}")
        return False

    # Check Specific Error Message (if applicable)
    if expected_msg:
        # We check both stdout and stderr (assignment says print, usually stdout, but print_error might use stderr in some implementations)
        output = res.stdout + res.stderr
        if expected_msg not in output:
            log(f"[FAIL] (Expected message '{expected_msg}' not found)", RED)
            print(f"Output received:\n{output}")
            return False
    
    # Check File Validation (if applicable)
    if validation_file:
        success, reason = check_output_match(res.stdout, validation_file)
        if not success:
            log(f"[FAIL] ({reason})", RED)
            # print(f"Generated Output:\n{res.stdout}") # Uncomment for debug
            return False

    log("[PASS]", GREEN)
    return True

def run_valgrind_check(args):
    """
    Runs the program with Valgrind to check for C-level memory leaks.
    """
    log("\n>> Running VALGRIND Memory Check...", CYAN)
    
    # Check if valgrind exists
    if subprocess.call(["which", "valgrind"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
        log("Valgrind not found! Skipping memory check.", YELLOW)
        return

    valgrind_cmd = [
        "valgrind",
        "--leak-check=full",
        "--show-leak-kinds=all",
        "--track-origins=yes",
        "--error-exitcode=100", # Valgrind returns 100 if leaks found
        sys.executable, PROGRAM
    ] + args

    log(f"Command: {' '.join(valgrind_cmd)}")
    
    # We capture stderr because valgrind writes there
    proc = subprocess.Popen(valgrind_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = proc.communicate()

    # Filter Python's internal noise. We are looking for "definitely lost" in the summary.
    # Note: Python always has "still reachable" memory. We care about "definitely lost".
    
    leak_error = False
    for line in stderr.splitlines():
        if "definitely lost:" in line:
            parts = line.split()
            # Format usually: ==123==    definitely lost: 1,024 bytes in 1 blocks
            try:
                # Find the number after "lost:"
                idx = parts.index("lost:")
                bytes_lost = parts[idx+1].replace(',', '')
                if int(bytes_lost) > 0:
                    leak_error = True
            except:
                pass

    if leak_error:
        log("MEMORY LEAK DETECTED! [FAIL]", RED)
        # Print only the relevant part of valgrind output
        print("--- Valgrind Summary ---")
        start_printing = False
        for line in stderr.splitlines():
            if "HEAP SUMMARY" in line:
                start_printing = True
            if start_printing:
                print(line)
    else:
        log("No 'definitely lost' memory detected. [PASS]", GREEN)
        log("(Note: 'Still reachable' blocks are normal in Python C extensions)", YELLOW)


# ================= MAIN TESTER LOGIC =================

def main():
    log(r"""
 __      __ HUUUUGE  _______ ______  ______ _______ ______ _____  
 \ \    / /          |__   __|  ____|/ ____|__   __|  ____|  __ \ 
  \ \  / / __ _ _ __    | |  | |__  | (___    | |  | |__  | |__) |
   \ \/ / / _` | '__|   | |  |  __|  \___ \   | |  |  __| |  _  / 
    \  / | (_| | |      | |  | |____ ____) |  | |  | |____| | \ \ 
     \/   \__,_|_|      |_|  |______|_____/   |_|  |______|_|  \_\
    """, YELLOW)

    compile_extension()
    create_dummy_files()

    passed = 0
    total = 0

    log("\n--- 1. INPUT VALIDATION TESTS (LOGIC) ---", CYAN)
    
    # 1. Invalid K (String)
    total+=1; passed += run_test_case("K is string", ["not_int", "10", "0.01", "dummy_1.csv", "dummy_2.csv"], expected_msg="Incorrect number of clusters!", expected_ret_code=1)

    # 2. Invalid K (Negative)
    total+=1; passed += run_test_case("K is negative", ["-5", "10", "0.01", "dummy_1.csv", "dummy_2.csv"], expected_msg="Incorrect number of clusters!", expected_ret_code=1)
    
    # 3. Invalid K (1) - Logic says > 1
    total+=1; passed += run_test_case("K is 1", ["1", "10", "0.01", "dummy_1.csv", "dummy_2.csv"], expected_msg="Incorrect number of clusters!", expected_ret_code=1)

    # 4. K >= N (Assumption: dummy files have 3 points. K=3 is edge, K=4 is error)
    total+=1; passed += run_test_case("K >= N", ["4", "10", "0.01", "dummy_1.csv", "dummy_2.csv"], expected_msg="Incorrect number of clusters!", expected_ret_code=1)

    # 5. Invalid Iter (String)
    total+=1; passed += run_test_case("Iter is string", ["2", "iter", "0.01", "dummy_1.csv", "dummy_2.csv"], expected_msg="Incorrect maximum iteration!", expected_ret_code=1)

    # 6. Invalid Iter (Negative)
    total+=1; passed += run_test_case("Iter is negative", ["2", "-10", "0.01", "dummy_1.csv", "dummy_2.csv"], expected_msg="Incorrect maximum iteration!", expected_ret_code=1)

    # 7. Invalid Iter (> 800 per PDF)
    total+=1; passed += run_test_case("Iter > 800", ["2", "801", "0.01", "dummy_1.csv", "dummy_2.csv"], expected_msg="Incorrect maximum iteration!", expected_ret_code=1)

    # 8. Invalid Eps (String)
    total+=1; passed += run_test_case("Eps is string", ["2", "100", "not_eps", "dummy_1.csv", "dummy_2.csv"], expected_msg="Incorrect epsilon!", expected_ret_code=1)

    # 9. Invalid Eps (Negative)
    total+=1; passed += run_test_case("Eps is negative", ["2", "100", "-0.01", "dummy_1.csv", "dummy_2.csv"], expected_msg="Incorrect epsilon!", expected_ret_code=1)

    # 10. Default Iteration Logic (Pass 5 arguments)
    # Just checking it doesn't crash and returns 0 code. dummy inputs are small enough to converge.
    total+=1; passed += run_test_case("Default Iter (5 args)", ["2", "0.01", "dummy_1.csv", "dummy_2.csv"], expected_ret_code=0)

    log("\n--- 2. FUNCTIONAL TESTS (FULL DATASETS) ---", CYAN)
    
    # We rely on the tests folder existing
    if not os.path.isdir(TEST_DIR):
        log(f"Warning: '{TEST_DIR}' directory not found. Skipping functional tests.", YELLOW)
    else:
        # TEST 1
        args1 = ["3", "100", "0.01", f"{TEST_DIR}/input_1_db_1.txt", f"{TEST_DIR}/input_1_db_2.txt"]
        total+=1; passed += run_test_case("Test 1 (K=3)", args1, validation_file=f"{TEST_DIR}/output_1.txt")

        # TEST 2
        args2 = ["7", "300", "0.01", f"{TEST_DIR}/input_2_db_1.txt", f"{TEST_DIR}/input_2_db_2.txt"]
        total+=1; passed += run_test_case("Test 2 (K=7)", args2, validation_file=f"{TEST_DIR}/output_2.txt")

        # TEST 3
        args3 = ["15", "300", "0.01", f"{TEST_DIR}/input_3_db_1.txt", f"{TEST_DIR}/input_3_db_2.txt"]
        total+=1; passed += run_test_case("Test 3 (K=15)", args3, validation_file=f"{TEST_DIR}/output_3.txt")


    log("\n--- 3. MEMORY CHECK (VALGRIND) ---", CYAN)
    # Run Valgrind on a small valid case (Test 1 inputs)
    # We use Test 1 inputs because they are valid and invoke the C module.
    if os.path.isdir(TEST_DIR):
         run_valgrind_check(["3", "100", "0.01", f"{TEST_DIR}/input_1_db_1.txt", f"{TEST_DIR}/input_1_db_2.txt"])
    else:
         # Use dummy files if tests dir is missing
         run_valgrind_check(["2", "100", "0.01", "dummy_1.csv", "dummy_2.csv"])

    # Cleanup
    remove_dummy_files()

    log("\n========================================")
    if passed == total:
         log(f"SUMMARY: {passed}/{total} TESTS PASSED. EXCELLENT JOB!", GREEN)
    else:
         log(f"SUMMARY: {passed}/{total} TESTS PASSED.", YELLOW)
         log("Please fix the [FAIL] cases above.", RED)

if __name__ == "__main__":
    main()