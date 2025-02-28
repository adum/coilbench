#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import argparse
import numpy as np
from pathlib import Path
from scipy.optimize import curve_fit
import math
#!/usr/bin/env python3

def time_to_human_readable(seconds):
    """Convert seconds to a human-readable time format."""
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f} minutes"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.2f} hours"
    elif seconds < 31536000:
        days = seconds / 86400
        return f"{days:.2f} days"
    elif seconds < 315360000:  # 10 years
        years = seconds / 31536000
        return f"{years:.2f} years"
    elif seconds < 31536000000:  # 1000 years
        centuries = seconds / 315360000
        return f"{centuries:.2f} centuries"
    else:
        millennia = seconds / 3153600000
        return f"{millennia:.2f} millennia"

def estimate_solving_times(level_data):
    """Estimate solving times for larger levels based on collected data."""
    if len(level_data) < 3:
        return "Not enough data to make predictions. Need at least 3 levels."
    
    # Extract data
    sizes = np.array([level[0] * level[1] for level in level_data])  # Total cells (width * height)
    times = np.array([level[2] for level in level_data])  # Solving times
    
    # Check if all times are very similar
    if np.max(times) - np.min(times) < 0.1:
        print("Warning: All solving times are very similar. Using calibrated theoretical complexity for estimation.")
        
        # Calculate a scaling factor based on the actual timing data
        # Use the average time and size to calibrate the model
        avg_time = np.mean(times)
        avg_size = np.mean(sizes)
        
        # For a Coil puzzle, we'll use a polynomial model with exponent 2.5
        # This is between quadratic and cubic complexity, which is reasonable for this type of puzzle
        # Calibrate the coefficient based on the actual timing data
        coefficient = avg_time / (np.power(avg_size, 2.5) / 1000)
        
        def theoretical_func(n):
            return coefficient * np.power(n, 2.5) / 1000
        
        # Generate predictions for square levels
        sizes_to_predict = [n*n for n in [100, 200, 300, 400, 500, 750, 1000, 1500, 2000]]
        predictions = []
        
        for size in sizes_to_predict:
            n = int(math.sqrt(size))
            predicted_time = theoretical_func(size)
            human_time = time_to_human_readable(predicted_time)
            predictions.append(f"{n}x{n}: {human_time}")
        
        # Format the results
        result = "Using theoretical complexity model to predict solving times for square levels:\n"
        result += "\n".join(predictions)
        
        return result
    
    # Try different curve fits and choose the best one
    
    # Exponential model: y = a * exp(b * x)
    def exp_func(x, a, b):
        return a * np.exp(b * x)
    
    # Polynomial model: y = a * x^b
    def poly_func(x, a, b):
        return a * np.power(x, b)
    
    # Linear model: y = a * x + b
    def linear_func(x, a, b):
        return a * x + b
    
    # Try to fit each model
    models = []
    try:
        # Fit exponential model
        popt_exp, _ = curve_fit(exp_func, sizes, times, maxfev=10000)
        exp_residuals = np.sum((times - exp_func(sizes, *popt_exp)) ** 2)
        models.append(("Exponential", popt_exp, exp_func, exp_residuals))
    except:
        pass
    
    try:
        # Fit polynomial model
        popt_poly, _ = curve_fit(poly_func, sizes, times, maxfev=10000)
        poly_residuals = np.sum((times - poly_func(sizes, *popt_poly)) ** 2)
        models.append(("Polynomial", popt_poly, poly_func, poly_residuals))
    except:
        pass
    
    try:
        # Fit linear model
        popt_linear, _ = curve_fit(linear_func, sizes, times, maxfev=10000)
        linear_residuals = np.sum((times - linear_func(sizes, *popt_linear)) ** 2)
        models.append(("Linear", popt_linear, linear_func, linear_residuals))
    except:
        pass
    
    if not models:
        return "Could not fit any model to the data."
    
    # Choose the model with the lowest residuals
    best_model = min(models, key=lambda x: x[3])
    model_name, params, func, _ = best_model
    
    # Add a calibrated theoretical model
    # Calculate a scaling factor based on the actual timing data
    # Use the average time and size to calibrate the model
    avg_time = np.mean(times)
    avg_size = np.mean(sizes)
    
    # For a Coil puzzle, we'll use a polynomial model with exponent 2.5
    # This is between quadratic and cubic complexity, which is reasonable for this type of puzzle
    # Calibrate the coefficient based on the actual timing data
    coefficient = avg_time / (np.power(avg_size, 2.5) / 1000)
    
    def theoretical_func(n):
        return coefficient * np.power(n, 2.5) / 1000
    
    models.append(("Theoretical", None, theoretical_func, float('inf')))  # Add to models with infinite residuals
    
    # Generate predictions for all models
    sizes_to_predict = [n*n for n in [100, 200, 300, 400, 500, 750, 1000, 1500, 2000]]
    all_predictions = {}
    
    # Track which models give reasonable predictions
    reasonable_models = []
    
    for model_name, params, func, _ in models:
        predictions = []
        is_reasonable = True
        
        for size in sizes_to_predict:
            n = int(math.sqrt(size))
            
            if model_name == "Theoretical":
                predicted_time = func(size)
            else:
                # Check if this model gives reasonable predictions for this size
                try:
                    # For exponential model, we need to be extra careful with large inputs
                    if model_name == "Exponential" and size > 200:
                        # For large sizes, exponential will likely overflow
                        is_reasonable = False
                        break
                    
                    # Suppress numpy warnings temporarily
                    with np.errstate(all='ignore'):
                        predicted_time = func(size, *params)
                    
                    if np.isinf(predicted_time) or np.isnan(predicted_time) or predicted_time < 0 or predicted_time > 31536000000000:  # > 1 million years
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
    
    # Format the results
    result = "Note: These estimates have significant variance due to the nature of the puzzle-solving algorithm.\n"
    result += "Different levels of the same size can take vastly different times to solve depending on their structure.\n"
    result += "The following estimates should be considered rough approximations and likely optimistic.\n\n"
    
    if not reasonable_models:
        result += "No models produced reasonable predictions. Using theoretical model only:\n"
        result += "\n".join(all_predictions["Theoretical"])
    else:
        # Sort models by complexity (theoretical first, then others)
        sorted_models = ["Theoretical"] + [m for m in reasonable_models if m != "Theoretical"]
        
        for model_name in sorted_models:
            if model_name in all_predictions:
                result += f"\nUsing {model_name} model to predict solving times for square levels:\n"
                result += "\n".join(all_predictions[model_name])
    
    return result

def read_level(level_path):
    """Read a level file and return its contents and dimensions."""
    with open(level_path, 'r') as f:
        content = f.read().strip()
    
    # Parse dimensions
    parts = content.split('&')
    width = int(parts[0].split('=')[1])
    height = int(parts[1].split('=')[1])
    
    return content, width, height

def validate_solution(level_path, solution, debug=False):
    """Validate a solution using the check.c program."""
    # Create a temporary file for the solution
    solution_path = "temp_solution.txt"
    with open(solution_path, 'w') as f:
        f.write(solution)
    
    # Run the check program
    try:
        cmd = ["./coil_check/check"]
        if debug:
            cmd.append("-d")
        cmd.extend([level_path, solution_path])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        # Remove the temporary file
        os.remove(solution_path)
        
        # Return True if the check program exits with 0
        return result.returncode == 0, result.stderr if result.returncode != 0 else ""
    except Exception as e:
        # Remove the temporary file if it exists
        if os.path.exists(solution_path):
            os.remove(solution_path)
        return False, str(e)

def main():
    parser = argparse.ArgumentParser(description='Evaluate a Coil solving program.')
    parser.add_argument('solver', help='Path to the solver program')
    parser.add_argument('--start', type=int, default=1, help='Starting level number')
    parser.add_argument('--end', type=int, default=None, help='Ending level number')
    parser.add_argument('--timeout', type=float, default=60, 
                        help='Maximum time in seconds allowed for solving a level (default: 60)')
    parser.add_argument('--estimate', action='store_true',
                        help='Estimate solving times for larger levels after evaluation')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug mode for solution validation')
    args = parser.parse_args()
    
    # Get the solver program
    solver = args.solver
    
    # Get the levels directory
    levels_dir = Path("levels")
    
    # Get all level files
    level_files = sorted([f for f in levels_dir.iterdir() if f.is_file()], 
                         key=lambda x: int(x.name) if x.name.isdigit() else float('inf'))
    
    # Filter levels based on start and end arguments
    if args.end:
        level_files = [f for f in level_files if args.start <= int(f.name) <= args.end]
    else:
        level_files = [f for f in level_files if args.start <= int(f.name)]
    
    # Check if there are any levels to evaluate
    if not level_files:
        print(f"No levels found between {args.start} and {args.end or 'end'}")
        return
    
    # Collect data for estimation
    level_data = []
    
    # Evaluate each level
    for level_file in level_files:
        level_num = level_file.name
        level_content, width, height = read_level(level_file)
        
        print(f"Level {level_num} ({width}x{height}): ", end="", flush=True)
        
        # Measure time
        start_time = time.time()
        
        try:
            # Run the solver program
            process = subprocess.run(
                [solver],
                input=level_content,
                capture_output=True,
                text=True,
                timeout=args.timeout  # Use the timeout parameter
            )
            
            # Get the solution
            solution = process.stdout.strip()
            
            # Calculate time taken
            time_taken = time.time() - start_time
            
            # Check if the solver couldn't find a solution
            if solution == "No solution found":
                print(f"FAIL (No solution found) ({time_taken:.2f}s)")
                break
                
            # Validate the solution
            is_valid, error_msg = validate_solution(level_file, solution, args.debug)
            
            # Print result
            if is_valid:
                print(f"PASS ({time_taken:.2f}s)")
                # Add to level data for estimation
                level_data.append((width, height, time_taken))
            else:
                print(f"FAIL ({time_taken:.2f}s)")
                if error_msg:
                    print(f"  Error: {error_msg}")
                if process.stderr:
                    print(f"  Solver stderr: {process.stderr}")
                # Stop on first failure
                break
                
        except subprocess.TimeoutExpired:
            time_taken = time.time() - start_time
            print(f"TIMEOUT - Exceeded {args.timeout}s limit ({time_taken:.2f}s)")
            break
        except Exception as e:
            time_taken = time.time() - start_time
            print(f"ERROR ({time_taken:.2f}s): {str(e)}")
            break

    # Estimate solving times for larger levels if requested
    if args.estimate and level_data:
        try:
            print("\nEstimating solving times for larger levels...")
            estimation = estimate_solving_times(level_data)
            print(estimation)
        except Exception as e:
            print(f"\nError estimating solving times: {str(e)}")
            print("Make sure numpy and scipy are installed:")
            print("pip install numpy scipy")

if __name__ == "__main__":
    main()
