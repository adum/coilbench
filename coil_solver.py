#!/usr/bin/env python3
import sys
import argparse
from collections import deque

# Direction vectors: Up, Right, Down, Left
DIRECTIONS = [(-1, 0), (0, 1), (1, 0), (0, -1)]
DIRECTION_CHARS = ['U', 'R', 'D', 'L']

def parse_level(level_str):
    """Parse a level string into width, height, and board."""
    parts = level_str.split('&')
    width = int(parts[0].split('=')[1])
    height = int(parts[1].split('=')[1])
    board_str = parts[2].split('=')[1]
    
    # Convert board string to 2D grid
    board = []
    for y in range(height):
        row = []
        for x in range(width):
            idx = y * width + x
            row.append(board_str[idx] == '.')  # True for empty, False for wall
        board.append(row)
    
    return width, height, board

def count_empty_cells(board):
    """Count the number of empty cells in the board."""
    return sum(sum(row) for row in board)

def is_valid_move(board, visited, y, x):
    """Check if a move to (y, x) is valid."""
    height, width = len(board), len(board[0])
    return (0 <= y < height and 0 <= x < width and 
            board[y][x] and not visited[y][x])

def move_until_blocked(board, visited, y, x, dy, dx):
    """Move in direction (dy, dx) until blocked, marking visited cells."""
    height, width = len(board), len(board[0])
    path = []
    
    while True:
        y += dy
        x += dx
        
        if not (0 <= y < height and 0 <= x < width) or not board[y][x] or visited[y][x]:
            # Hit a wall, edge, or visited cell - move back one step
            y -= dy
            x -= dx
            break
        
        visited[y][x] = True
        path.append((y, x))
    
    return y, x, path

def solve_board(board, start_y, start_x):
    """Solve the board using brute force search starting from (start_y, start_x)."""
    height, width = len(board), len(board[0])
    total_empty = count_empty_cells(board)
    
    # Check if starting position is valid
    if not board[start_y][start_x]:
        return None
    
    # Initialize visited grid
    visited = [[False for _ in range(width)] for _ in range(height)]
    visited[start_y][start_x] = True
    
    # Initialize path
    path_chars = []
    visited_count = 1  # Count the starting cell
    
    def backtrack(y, x):
        nonlocal visited_count
        
        # If all empty cells are visited, we've found a solution
        if visited_count == total_empty:
            return True
        
        # Try each direction
        for i, (dy, dx) in enumerate(DIRECTIONS):
            # Check if we can move in this direction
            ny, nx = y + dy, x + dx
            if is_valid_move(board, visited, ny, nx):
                # Move until blocked
                end_y, end_x, path_cells = move_until_blocked(board, visited, y, x, dy, dx)
                
                # Add to visited count and path
                visited_count += len(path_cells)
                path_chars.append(DIRECTION_CHARS[i])
                
                # Recursively try to solve from the new position
                if backtrack(end_y, end_x):
                    return True
                
                # Backtrack: remove from path and mark cells as unvisited
                path_chars.pop()
                for cy, cx in path_cells:
                    visited[cy][cx] = False
                visited_count -= len(path_cells)
        
        return False
    
    # Start the backtracking search
    if backtrack(start_y, start_x):
        return f"x={start_x}&y={start_y}&path={''.join(path_chars)}"
    else:
        return None

def solve_level(width, height, board):
    """Try all possible starting positions to solve the level."""
    for y in range(height):
        for x in range(width):
            if board[y][x]:  # If it's an empty cell
                solution = solve_board(board, y, x)
                if solution:
                    return solution
    
    return "No solution found"

def main():
    parser = argparse.ArgumentParser(description='Solve a Coil puzzle using brute force search.')
    parser.add_argument('level_file', nargs='?', help='Path to the level file (optional, reads from stdin if not provided)')
    args = parser.parse_args()
    
    # Read the level from file or stdin
    if args.level_file:
        with open(args.level_file, 'r') as f:
            level_str = f.read().strip()
    else:
        level_str = sys.stdin.read().strip()
    
    # Parse the level
    width, height, board = parse_level(level_str)
    
    # Solve the level
    solution = solve_level(width, height, board)
    
    # Print the solution
    print(solution)

if __name__ == "__main__":
    main()
