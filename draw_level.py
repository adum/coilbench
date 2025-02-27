#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path

def parse_level(level_str):
    """Parse a level string into width, height, and board."""
    parts = level_str.split('&')
    width = int(parts[0].split('=')[1])
    height = int(parts[1].split('=')[1])
    board_str = parts[2].split('=')[1]
    
    return width, height, board_str

def draw_level(width, height, board_str):
    """Draw the level as a 2D grid."""
    # Create a 2D grid from the board string
    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            idx = y * width + x
            cell = board_str[idx]
            row.append(cell)
        grid.append(row)
    
    # Draw the grid with borders
    print("+" + "-" * (width * 2 - 1) + "+")
    
    for row in grid:
        print("|", end="")
        for i, cell in enumerate(row):
            if cell == 'X':
                print("█", end="")
            else:
                print(".", end="")
            
            # Add separator between cells, except for the last cell
            if i < len(row) - 1:
                print(" ", end="")
        print("|")
    
    print("+" + "-" * (width * 2 - 1) + "+")

def main():
    parser = argparse.ArgumentParser(description='Draw a Coil level as a 2D grid.')
    parser.add_argument('level_file', help='Path to the level file')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    args = parser.parse_args()
    
    # Redirect output to file if specified
    if args.output:
        sys.stdout = open(args.output, 'w')
    
    # Read the level file
    try:
        with open(args.level_file, 'r') as f:
            level_str = f.read().strip()
    except FileNotFoundError:
        print(f"Error: Level file '{args.level_file}' not found.")
        return 1
    except Exception as e:
        print(f"Error reading level file: {str(e)}")
        return 1
    
    try:
        # Parse the level
        width, height, board_str = parse_level(level_str)
        
        # Print level information
        print(f"Level: {Path(args.level_file).name}")
        print(f"Dimensions: {width}x{height}")
        print(f"Board string: {board_str}")
        print()
        
        # Draw the level
        draw_level(width, height, board_str)
        
    except Exception as e:
        print(f"Error parsing or drawing level: {str(e)}")
        return 1
    finally:
        # Close the output file if we opened one
        if args.output and sys.stdout != sys.__stdout__:
            sys.stdout.close()
            sys.stdout = sys.__stdout__
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
