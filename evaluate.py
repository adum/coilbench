#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import argparse
from pathlib import Path

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
                timeout=60  # 60 second timeout
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
            print(f"TIMEOUT ({time_taken:.2f}s)")
            break
        except Exception as e:
            time_taken = time.time() - start_time
            print(f"ERROR ({time_taken:.2f}s): {str(e)}")
            break

if __name__ == "__main__":
    main()
