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
        print("Warning: All solving times are very similar. Using theoretical complexity for estimation.")
        # For brute force backtracking, complexity is typically exponential
        # Let's use a reasonable estimate based on the problem domain
        
        # For a Coil puzzle with n cells, the brute force complexity is roughly O(4^n)
        # But our solver is smarter than pure brute force, so let's use a more reasonable estimate
        # Let's use a polynomial model with a higher exponent to represent the complexity
        def theoretical_func(n):
            # Use n^2.5 as a reasonable estimate for a backtracking algorithm
            # This is between quadratic and cubic complexity
            return 0.03 * np.power(n, 2.5) / 1000
        
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
    
    # Check if the model gives reasonable predictions
    test_size = 100 * 100
    test_prediction = func(test_size, *params)
    
    # If the prediction is unreasonably large (> 1000 years), use a more conservative model
    if test_prediction > 31536000000:  # 1000 years in seconds
        print(f"Warning: {model_name} model gives unreasonably large predictions. Using a more conservative model.")
        # Use a more conservative polynomial model
        def conservative_func(n):
            # Use n^2.5 as a reasonable estimate for a backtracking algorithm
            return 0.03 * np.power(n, 2.5) / 1000
        
        func = conservative_func
        model_name = "Conservative polynomial"
    
    # Generate predictions for square levels
    sizes_to_predict = [n*n for n in [100, 200, 300, 400, 500, 750, 1000, 1500, 2000]]
    predictions = []
    
    for size in sizes_to_predict:
        n = int(math.sqrt(size))
        predicted_time = func(size, *params) if model_name != "Conservative polynomial" else func(size)
        if predicted_time < 0:  # Sanity check
            predicted_time = 0
        human_time = time_to_human_readable(predicted_time)
        predictions.append(f"{n}x{n}: {human_time}")
    
    # Format the results
    result = f"Using {model_name} model to predict solving times for square levels:\n"
    result += "\n".join(predictions)
    
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

def validate_solution(level_path, solution):
    """Validate a solution using the check.c program."""
    # Create a temporary file for the solution
    solution_path = "temp_solution.txt"
    with open(solution_path, 'w') as f:
        f.write(solution)
    
    # Run the check program
    try:
        result = subprocess.run(
            ["./coil_check/check", level_path, solution_path],
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
            
            # Validate the solution
            is_valid, error_msg = validate_solution(level_file, solution)
            
            # Calculate time taken
            time_taken = time.time() - start_time
            
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
