Coil is a pathfinding puzzle game, where the objective is to traverse a grid-based maze while ensuring every tile is visited exactly once. The player starts at a designated position and must navigate using four-directional movement (up, down, left, right).


1. Input Format
A game level consists of a rectangular grid of dimensions x×y (width × height). Each cell is either empty or a wall.

2. Objective
The goal of the game is to visit every non-wall cell.

3. Rules
You may pick any starting point that isn't a wall. Then you can move in any orthogonal direction: up, down, left, or right. When you start moving, you continue until you hit a wall, the edge of the board, or a previously visited square. At this point you pick a new direction, if you are not at a dead end. If every empty square has been visited, you win.

4. Format
The input format looks like this:
x=<x dimension>&y=<y dimension>&board=<series of characters representing the board>

The characters are a '.' for empty, and a 'X' for a wall. This starts in the upper left and progresses across the first row, then the second, etc.

An example of a 3x3 board:
x=3&y=3&board=X.......X

Which represents:
X . .
. . .
. . X

5. Solution format
Looks like:
x=<x>&y=<y>&path=<path>

x and y are the coordinates of the starting point.
Path is a series of characters between U for up, D for down, L for left, and R for right.

6. Example
For this board:
x=3&y=3&board=X.......X

There are multiple solutions, but one is to start at (1, 0), move right, then down, then left, then down, then right.

The solution would be then:
x=1&y=0&path=RDLDR
