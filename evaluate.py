#!/usr/bin/env python3
import argparse
import math
import os
import shlex
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

DEFAULT_PUBLIC_LEVELS_DIR = Path("levels_public")
DEFAULT_RESULTS_PATH = Path("test.md")
TEST_HEADER = [
    "| Date | Model/Solver | Timeout | Highest Passed | Mode | Command |",
    "| --- | --- | --- | --- | --- | --- |",
]


@dataclass
class EvaluationSummary:
    highest_passed: int
    total_levels: int
    elapsed_seconds: float
    stop_reason: str
    estimate_output: str | None = None


def time_to_human_readable(seconds):
    """Convert seconds to a human-readable time format."""
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    if seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f} minutes"
    if seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.2f} hours"
    if seconds < 31536000:
        days = seconds / 86400
        return f"{days:.2f} days"
    if seconds < 315360000:  # 10 years
        years = seconds / 31536000
        return f"{years:.2f} years"
    if seconds < 31536000000:  # 1000 years
        centuries = seconds / 315360000
        return f"{centuries:.2f} centuries"
    millennia = seconds / 3153600000
    return f"{millennia:.2f} millennia"


def estimate_solving_times(level_data):
    """Estimate solving times for larger levels based on collected data."""
    try:
        import numpy as np
        from scipy.optimize import curve_fit
    except Exception as exc:
        raise RuntimeError("numpy and scipy are required for --estimate") from exc

    if len(level_data) < 3:
        return "Not enough data to make predictions. Need at least 3 levels."

    # Extract data
    sizes = np.array([level[0] * level[1] for level in level_data])  # Total cells (width * height)
    times = np.array([level[2] for level in level_data])  # Solving times

    # Check if all times are very similar
    if np.max(times) - np.min(times) < 0.1:
        print("Warning: All solving times are very similar. Using calibrated theoretical complexity for estimation.")

        # Calibrate the model based on the observed data.
        avg_time = np.mean(times)
        avg_size = np.mean(sizes)
        coefficient = avg_time / (np.power(avg_size, 2.5) / 1000)

        def theoretical_func(n):
            return coefficient * np.power(n, 2.5) / 1000

        sizes_to_predict = [n * n for n in [100, 200, 300, 400, 500, 750, 1000, 1500, 2000]]
        predictions = []
        for size in sizes_to_predict:
            n = int(math.sqrt(size))
            predicted_time = theoretical_func(size)
            human_time = time_to_human_readable(predicted_time)
            predictions.append(f"{n}x{n}: {human_time}")

        result = "Using theoretical complexity model to predict solving times for square levels:\n"
        result += "\n".join(predictions)
        return result

    # Exponential model: y = a * exp(b * x)
    def exp_func(x, a, b):
        return a * np.exp(b * x)

    # Polynomial model: y = a * x^b
    def poly_func(x, a, b):
        return a * np.power(x, b)

    # Linear model: y = a * x + b
    def linear_func(x, a, b):
        return a * x + b

    models = []
    try:
        popt_exp, _ = curve_fit(exp_func, sizes, times, maxfev=10000)
        exp_residuals = np.sum((times - exp_func(sizes, *popt_exp)) ** 2)
        models.append(("Exponential", popt_exp, exp_func, exp_residuals))
    except Exception:
        pass

    try:
        popt_poly, _ = curve_fit(poly_func, sizes, times, maxfev=10000)
        poly_residuals = np.sum((times - poly_func(sizes, *popt_poly)) ** 2)
        models.append(("Polynomial", popt_poly, poly_func, poly_residuals))
    except Exception:
        pass

    try:
        popt_linear, _ = curve_fit(linear_func, sizes, times, maxfev=10000)
        linear_residuals = np.sum((times - linear_func(sizes, *popt_linear)) ** 2)
        models.append(("Linear", popt_linear, linear_func, linear_residuals))
    except Exception:
        pass

    if not models:
        return "Could not fit any model to the data."

    avg_time = np.mean(times)
    avg_size = np.mean(sizes)
    coefficient = avg_time / (np.power(avg_size, 2.5) / 1000)

    def theoretical_func(n):
        return coefficient * np.power(n, 2.5) / 1000

    models.append(("Theoretical", None, theoretical_func, float("inf")))

    sizes_to_predict = [n * n for n in [100, 200, 300, 400, 500, 750, 1000, 1500, 2000]]
    all_predictions = {}
    reasonable_models = []

    for model_name, params, func, _ in models:
        predictions = []
        is_reasonable = True

        for size in sizes_to_predict:
            n = int(math.sqrt(size))

            if model_name == "Theoretical":
                predicted_time = func(size)
            else:
                try:
                    if model_name == "Exponential" and size > 200:
                        is_reasonable = False
                        break

                    with np.errstate(all="ignore"):
                        predicted_time = func(size, *params)

                    if (
                        np.isinf(predicted_time)
                        or np.isnan(predicted_time)
                        or predicted_time < 0
                        or predicted_time > 31536000000000
                    ):
                        is_reasonable = False
                        break
                except (OverflowError, FloatingPointError, ValueError, RuntimeWarning):
                    is_reasonable = False
                    break

            human_time = time_to_human_readable(predicted_time)
            predictions.append(f"{n}x{n}: {human_time}")

        if is_reasonable:
            all_predictions[model_name] = predictions
            reasonable_models.append(model_name)

    result = "Note: These estimates have significant variance due to the nature of the puzzle-solving algorithm.\n"
    result += "Different levels of the same size can take vastly different times to solve depending on their structure.\n"
    result += "The following estimates should be considered rough approximations and likely optimistic.\n\n"

    if not reasonable_models:
        result += "No models produced reasonable predictions. Using theoretical model only:\n"
        result += "\n".join(all_predictions["Theoretical"])
    else:
        sorted_models = ["Theoretical"] + [m for m in reasonable_models if m != "Theoretical"]
        for model_name in sorted_models:
            if model_name in all_predictions:
                result += f"\nUsing {model_name} model to predict solving times for square levels:\n"
                result += "\n".join(all_predictions[model_name])

    return result


def read_level(level_path: Path):
    """Read a level file and return its contents and dimensions."""
    content = level_path.read_text(encoding="utf-8").strip()

    parts = content.split("&")
    width = int(parts[0].split("=")[1])
    height = int(parts[1].split("=")[1])
    return content, width, height


def validate_solution(level_path: Path, solution: str, debug=False):
    """Validate a solution using the check.c program."""
    fd, solution_path_str = tempfile.mkstemp(prefix="temp_solution_", suffix=".txt")
    solution_path = Path(solution_path_str)
    os.close(fd)

    try:
        solution_path.write_text(solution, encoding="utf-8")
        cmd = ["./coil_check/check"]
        if debug:
            cmd.append("-d")
        cmd.extend([str(level_path), str(solution_path)])

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.returncode == 0, result.stderr if result.returncode != 0 else ""
    except Exception as exc:
        return False, str(exc)
    finally:
        if solution_path.exists():
            solution_path.unlink()


def _level_number(path: Path) -> int | None:
    return int(path.name) if path.name.isdigit() else None


def collect_level_files(level_dirs: Iterable[Path], start: int, end: int | None) -> list[tuple[int, Path]]:
    selected: dict[int, Path] = {}
    for level_dir in level_dirs:
        if not level_dir.exists() or not level_dir.is_dir():
            continue

        for path in level_dir.iterdir():
            if not path.is_file():
                continue

            level_num = _level_number(path)
            if level_num is None:
                continue
            if level_num < start:
                continue
            if end is not None and level_num > end:
                continue

            if level_num in selected:
                raise ValueError(f"Duplicate level number {level_num} found: {selected[level_num]} and {path}")
            selected[level_num] = path

    return sorted(selected.items(), key=lambda item: item[0])


def _ensure_test_header(results_path: Path) -> None:
    if not results_path.exists() or results_path.stat().st_size == 0:
        results_path.write_text("\n".join(TEST_HEADER) + "\n", encoding="utf-8")
        return

    lines = results_path.read_text(encoding="utf-8").splitlines()
    if TEST_HEADER[0] in lines:
        return

    with results_path.open("a", encoding="utf-8") as handle:
        if lines and lines[-1].strip():
            handle.write("\n")
        handle.write("\n".join(TEST_HEADER) + "\n")


def _escape_table_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def append_test_result_row(
    *,
    results_path: Path,
    solver: str,
    timeout: float,
    highest_passed: int,
    mode: str,
    command: str,
) -> None:
    _ensure_test_header(results_path)
    row = [
        datetime.now().strftime("%Y-%m-%d"),
        solver,
        f"{timeout:g}s",
        str(highest_passed),
        mode,
        command,
    ]
    escaped = [_escape_table_cell(value) for value in row]
    with results_path.open("a", encoding="utf-8") as handle:
        handle.write("| " + " | ".join(escaped) + " |\n")


def run_evaluation(
    *,
    solver: str,
    level_files: list[tuple[int, Path]],
    timeout: float,
    estimate: bool,
    debug: bool,
) -> EvaluationSummary:
    run_start = time.time()
    highest_passed = 0
    level_data = []
    stop_reason = "COMPLETE"

    for level_num, level_path in level_files:
        level_content, width, height = read_level(level_path)
        print(f"Level {level_num} ({width}x{height}): ", end="", flush=True)

        level_start = time.time()

        try:
            process = subprocess.run(
                [solver],
                input=level_content,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            solution = process.stdout.strip()
            time_taken = time.time() - level_start

            if solution == "No solution found":
                print(f"FAIL (No solution found) ({time_taken:.2f}s)")
                stop_reason = "FAIL"
                break

            is_valid, error_msg = validate_solution(level_path, solution, debug)
            if is_valid:
                print(f"PASS ({time_taken:.2f}s)")
                highest_passed = level_num
                level_data.append((width, height, time_taken))
            else:
                print(f"FAIL ({time_taken:.2f}s)")
                if error_msg:
                    print(f"  Error: {error_msg}")
                if process.stderr:
                    print(f"  Solver stderr: {process.stderr}")
                stop_reason = "FAIL"
                break

        except subprocess.TimeoutExpired:
            time_taken = time.time() - level_start
            print(f"TIMEOUT - Exceeded {timeout}s limit ({time_taken:.2f}s)")
            stop_reason = "TIMEOUT"
            break
        except Exception as exc:
            time_taken = time.time() - level_start
            print(f"ERROR ({time_taken:.2f}s): {exc}")
            stop_reason = "ERROR"
            break

    estimate_output = None
    if estimate and level_data:
        try:
            print("\nEstimating solving times for larger levels...")
            estimate_output = estimate_solving_times(level_data)
            print(estimate_output)
        except Exception as exc:
            print(f"\nError estimating solving times: {exc}")
            print("Make sure numpy and scipy are installed:")
            print("pip install numpy scipy")
            estimate_output = f"estimate-error: {exc}"

    return EvaluationSummary(
        highest_passed=highest_passed,
        total_levels=len(level_files),
        elapsed_seconds=time.time() - run_start,
        stop_reason=stop_reason,
        estimate_output=estimate_output,
    )


def build_argument_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("solver", help="Path to the solver program")
    parser.add_argument("--start", type=int, default=1, help="Starting level number")
    parser.add_argument("--end", type=int, default=None, help="Ending level number")
    parser.add_argument(
        "--timeout",
        type=float,
        default=60,
        help="Maximum time in seconds allowed for solving a level (default: 60)",
    )
    parser.add_argument(
        "--estimate",
        action="store_true",
        help="Estimate solving times for larger levels after evaluation",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug mode for solution validation",
    )
    return parser


def evaluate_and_log(
    *,
    solver: str,
    start: int,
    end: int | None,
    timeout: float,
    estimate: bool,
    debug: bool,
    level_dirs: Iterable[Path],
    mode: str,
    invocation_argv: list[str],
    results_path: Path = DEFAULT_RESULTS_PATH,
) -> int:
    try:
        level_files = collect_level_files(level_dirs, start=start, end=end)
    except ValueError as exc:
        print(exc)
        return 1

    if not level_files:
        print(f"No levels found between {start} and {end or 'end'}")
        return 1

    summary = run_evaluation(
        solver=solver,
        level_files=level_files,
        timeout=timeout,
        estimate=estimate,
        debug=debug,
    )
    append_test_result_row(
        results_path=results_path,
        solver=solver,
        timeout=timeout,
        highest_passed=summary.highest_passed,
        mode=mode,
        command=shlex.join(invocation_argv),
    )
    print(f"\nWrote run summary row to {results_path}")
    return 0


def main() -> int:
    parser = build_argument_parser("Evaluate a Coil solving program (odd public levels only).")
    args = parser.parse_args()
    return evaluate_and_log(
        solver=args.solver,
        start=args.start,
        end=args.end,
        timeout=args.timeout,
        estimate=args.estimate,
        debug=args.debug,
        level_dirs=[DEFAULT_PUBLIC_LEVELS_DIR],
        mode="dev-odd",
        invocation_argv=sys.argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
