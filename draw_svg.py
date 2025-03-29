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

def create_svg(width, height, board_str, level_name=""):
    """Create an SVG representation of the level."""
    # Calculate cell size and padding
    cell_size = 30
    padding = 25
    svg_width = width * cell_size + 2 * padding
    svg_height = height * cell_size + 2 * padding + 20  # Extra space for title
    
    # SVG header
    svg = f'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    svg += f'<svg width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}" xmlns="http://www.w3.org/2000/svg">\n'
    svg += f'  <rect width="100%" height="100%" fill="white"/>\n'
    svg += f'  <g transform="translate({padding}, {padding})">\n'
    
    # Grid lines
    svg += f'    <!-- Grid lines -->\n'
    svg += f'    <g stroke="#ccc" stroke-width="1">\n'
    
    # Horizontal grid lines
    svg += f'      <!-- Horizontal grid lines -->\n'
    for i in range(height + 1):
        y = i * cell_size
        svg += f'      <line x1="0" y1="{y}" x2="{width * cell_size}" y2="{y}" />\n'
    
    # Vertical grid lines
    svg += f'      <!-- Vertical grid lines -->\n'
    for i in range(width + 1):
        x = i * cell_size
        svg += f'      <line x1="{x}" y1="0" x2="{x}" y2="{height * cell_size}" />\n'
    
    svg += f'    </g>\n'
    
    # Cells
    svg += f'    <!-- Cells -->\n'
    for y in range(height):
        for x in range(width):
            idx = y * width + x
            cell = board_str[idx]
            
            if cell == 'X':  # Wall
                svg += f'    <rect x="{x * cell_size}" y="{y * cell_size}" width="{cell_size}" height="{cell_size}" fill="#333" />\n'
            elif cell == 's':  # Start
                svg += f'    <rect x="{x * cell_size}" y="{y * cell_size}" width="{cell_size}" height="{cell_size}" fill="#4CAF50" />\n'
                svg += f'    <text x="{x * cell_size + cell_size/2}" y="{y * cell_size + cell_size/2 + 5}" text-anchor="middle" font-family="Arial" font-size="14" fill="white">S</text>\n'
    
    svg += f'  </g>\n'
    
    # Title
    if level_name:
        svg += f'  <text x="{svg_width/2}" y="{svg_height - 10}" text-anchor="middle" font-family="Arial" font-size="12">Level {level_name} ({width}x{height})</text>\n'
    
    svg += f'</svg>'
    
    return svg

def main():
    parser = argparse.ArgumentParser(description='Create an SVG image of a Coil level.')
    parser.add_argument('level_file', help='Path to the level file')
    parser.add_argument('--output', '-o', help='Output SVG file (default: level_{num}.svg)')
    args = parser.parse_args()
    
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
        
        # Get level name from file name
        level_name = Path(args.level_file).name
        
        # Create SVG
        svg_content = create_svg(width, height, board_str, level_name)
        
        # Write to file
        output_file = args.output if args.output else f"level_{level_name}.svg"
        with open(output_file, 'w') as f:
            f.write(svg_content)
        
        print(f"SVG created: {output_file}")
        
    except Exception as e:
        print(f"Error creating SVG: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())