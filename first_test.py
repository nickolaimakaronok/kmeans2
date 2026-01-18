import subprocess
import os
import sys
import math

# --- НАСТРОЙКИ ---
EXECUTABLE = "kmeans_pp.py"
TESTS_DIR = "tests"
TOLERANCE = 1e-4  # Допустимая погрешность при сравнении чисел

# Цвета для вывода
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
YELLOW = "\033[93m"

def print_status(message, status):
    if status == "PASS":
        print(f"{message:.<60} {GREEN}[PASS]{RESET}")
    elif status == "FAIL":
        print(f"{message:.<60} {RED}[FAIL]{RESET}")
    else:
        print(f"{message:.<60} {YELLOW}[WARN]{RESET}")

def is_float_equal(a, b):
    try:
        return abs(float(a) - float(b)) < TOLERANCE
    except ValueError:
        return False

def compare_outputs(generated_output, expected_file):
    """Сравнивает вывод программы с файлом эталона, учитывая числа float"""
    try:
        with open(expected_file, 'r') as f:
            expected_lines = f.read().strip().split('\n')
    except FileNotFoundError:
        return False, f"Missing expected file: {expected_file}"

    gen_lines = generated_output.strip().split('\n')

    # Убираем пустые строки
    gen_lines = [line for line in gen_lines if line.strip()]
    expected_lines = [line for line in expected_lines if line.strip()]

    if len(gen_lines) != len(expected_lines):
        return False, f"Line count mismatch: Got {len(gen_lines)}, Expected {len(expected_lines)}"

    for i, (gen_line, exp_line) in enumerate(zip(gen_lines, expected_lines)):
        gen_vals = gen_line.split(',')
        exp_vals = exp_line.split(',')

        if len(gen_vals) != len(exp_vals):
            return False, f"Column count mismatch at line {i+1}"

        for j, (g, e) in enumerate(zip(gen_vals, exp_vals)):
            if not is_float_equal(g, e):
                return False, f"Value mismatch at line {i+1}, col {j+1}: Got '{g}', Expected '{e}'"
    
    return True, "OK"

def run_test(args, expected_file=None, expect_failure=False):
    """Запускает программу и проверяет результат"""
    cmd = ["python3", EXECUTABLE] + args
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except subprocess.TimeoutExpired:
        print_status(f"Test {' '.join(args)}", "FAIL")
        print(f"{RED}Error: Timeout (Infinite loop?){RESET}")
        return

    # Если ожидаем ошибку (негативный тест)
    if expect_failure:
        if result.returncode != 0:
            print_status(f"Negative Test {' '.join(args)}", "PASS")
        else:
            print_status(f"Negative Test {' '.join(args)}", "FAIL")
            print(f"Expected error, but program finished successfully.")
        return

    # Если ожидаем успех
    if result.returncode != 0:
        print_status(f"Test {' '.join(args)}", "FAIL")
        print(f"{RED}Program crashed with exit code {result.returncode}{RESET}")
        print("Stderr:", result.stderr)
        return

    if expected_file:
        success, msg = compare_outputs(result.stdout, expected_file)
        if success:
            print_status(f"Test {expected_file}", "PASS")
        else:
            print_status(f"Test {expected_file}", "FAIL")
            print(f"{RED}Details: {msg}{RESET}")
            # print("Generated:\n", result.stdout) # Раскомментируй для отладки

def main():
    print(f"{YELLOW}=== Starting Comprehensive Tester ==={RESET}")

    # Проверка наличия файлов
    if not os.path.exists(EXECUTABLE):
        print(f"{RED}Error: {EXECUTABLE} not found!{RESET}")
        return

    # 1. ФУНКЦИОНАЛЬНЫЕ ТЕСТЫ (Сравнение с output_X.txt)
    print(f"\n{YELLOW}--- Functional Tests (Correctness) ---{RESET}")
    
    # Test 1
    run_test(
        ["3", "333", "0", f"{TESTS_DIR}/input_1_db_1.txt", f"{TESTS_DIR}/input_1_db_2.txt"], 
        expected_file=f"{TESTS_DIR}/output_1.txt"
    )

    # Test 2
    run_test(
        ["7", "300", "0", f"{TESTS_DIR}/input_2_db_1.txt", f"{TESTS_DIR}/input_2_db_2.txt"], 
        expected_file=f"{TESTS_DIR}/output_2.txt"
    )

    # Test 3
    run_test(
        ["15", "750", "0", f"{TESTS_DIR}/input_3_db_1.txt", f"{TESTS_DIR}/input_3_db_2.txt"], 
        expected_file=f"{TESTS_DIR}/output_3.txt"
    )

    # 2. НЕГАТИВНЫЕ ТЕСТЫ (Проверка ошибок)
    print(f"\n{YELLOW}--- Negative Tests (Error Handling) ---{RESET}")
    
    # K > N (должна быть ошибка)
    # Предполагаем, что в input_1 меньше 100 точек
    run_test(["100", "100", "0.01", f"{TESTS_DIR}/input_1_db_1.txt", f"{TESTS_DIR}/input_1_db_2.txt"], expect_failure=True)

    # K is string (не число)
    run_test(["not_a_number", "100", "0.01", f"{TESTS_DIR}/input_1.txt"], expect_failure=True)

    # Iter is string
    run_test(["3", "iter", "0.01", f"{TESTS_DIR}/input_1.txt"], expect_failure=True)

    # Negative K
    run_test(["-5", "100", "0.01", f"{TESTS_DIR}/input_1.txt"], expect_failure=True)

    # File not found
    run_test(["3", "100", "0.01", "ghost_file.txt", "ghost_2.txt"], expect_failure=True)

    # Missing arguments (мало аргументов)
    run_test(["3", "100"], expect_failure=True)

    print(f"\n{YELLOW}=== Testing Complete ==={RESET}")

if __name__ == "__main__":
    main()