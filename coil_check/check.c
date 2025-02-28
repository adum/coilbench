#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <getopt.h>

typedef unsigned char u1;
typedef   signed int  s4;
typedef unsigned int  u4;

// Global variables
bool debug_mode = false;
u4 board_w, board_h, w, h;
u1* board = NULL;

// Function to print the board state for debugging
void print_board_state(u1* b, u4 w, u4 h, u4 curr_x, u4 curr_y)
{
    fprintf(stderr, "\nBoard state (%ux%u):\n", w-2, h-2);
    fprintf(stderr, "Current position: (%u,%u)\n", curr_x-1, curr_y-1);
    
    // Print column numbers
    fprintf(stderr, "  ");
    for (u4 x = 1; x < w - 1; ++x)
    {
        fprintf(stderr, "%u ", x-1);
    }
    fprintf(stderr, "\n");
    
    for (u4 y = 1; y < h - 1; ++y)
    {
        // Print row number
        fprintf(stderr, "%u ", y-1);
        
        for (u4 x = 1; x < w - 1; ++x)
        {
            u1 cell = b[y * w + x];
            
            // Highlight current position
            if (x == curr_x && y == curr_y)
            {
                fprintf(stderr, "@ ");
            }
            else if (cell == 0)
            {
                // Cell is either a wall or has been visited
                // Check original board to distinguish
                if (board[y * w + x] == 0)
                {
                    fprintf(stderr, "X "); // Wall
                }
                else
                {
                    fprintf(stderr, "# "); // Visited
                }
            }
            else
            {
                fprintf(stderr, ". "); // Empty
            }
        }
        fprintf(stderr, "\n");
    }
    fprintf(stderr, "\n");
}

int main(int const argc, char** const argv)
{
    // Parse command line options
    int opt;
    while ((opt = getopt(argc, argv, "d")) != -1)
    {
        switch (opt)
        {
            case 'd':
                debug_mode = true;
                break;
            default:
                fprintf(stderr,
                    "Usage: %s [-d] <board filename> <solution filename>\n"
                    "Options:\n"
                    "  -d    Enable debug mode\n"
                    "File formats:\n"
                    "  board:    x=<x>&y=<y>&board=<board>\n"
                    "  solution: x=<x>&y=<y>&path=<path>\n"
                    "            x=<x>&y=<y>&qpath=<qpath>\n",
                    argv[0]);
                return EXIT_FAILURE;
        }
    }
    
    // Check if we have the required arguments
    if (optind + 2 > argc)
    {
        fprintf(stderr,
            "Usage: %s [-d] <board filename> <solution filename>\n"
            "Options:\n"
            "  -d    Enable debug mode\n"
            "File formats:\n"
            "  board:    x=<x>&y=<y>&board=<board>\n"
            "  solution: x=<x>&y=<y>&path=<path>\n"
            "            x=<x>&y=<y>&qpath=<qpath>\n",
            argv[0]);
        return EXIT_FAILURE;
    }

	// Read board.
	FILE* const f = fopen(argv[optind], "r");
	if (!f)
	{
		fprintf(stderr, "failed to open board\n");
		return EXIT_FAILURE;
	}

	if (fscanf(f, "x=%u&y=%u&board=", &board_w, &board_h) != 2)
	{
		fprintf(stderr, "could not parse board size\n");
		return EXIT_FAILURE;
	}

	// Add a blocked border.
	u4        n = 0;
	h = board_h + 2;
	w = board_w + 2;

	u1* const b = calloc(h * w, sizeof(*b));
	if (!b)
	{
		fprintf(stderr, "out of memory\n");
		return EXIT_FAILURE;
	}

	// Create a copy of the original board for debugging
	if (debug_mode)
	{
		board = calloc(h * w, sizeof(*board));
		if (!board)
		{
			fprintf(stderr, "out of memory for debug board\n");
			free(b);
			return EXIT_FAILURE;
		}
	}

	for (u4 y = 1; y != h - 1; ++y)
	{
		for (u4 x = 1; x != w - 1; ++x)
		{
			u1 c;
			switch (fgetc(f))
			{
				case 'X': c = 0;      break;
				case '.': c = 1; ++n; break;

				case EOF:
					if (ferror(f))
					{
						fprintf(stderr, "read error\n");
					}
					else
					{
						fprintf(stderr, "board too short\n");
					}
					return EXIT_FAILURE;

				default:
					fprintf(stderr, "invalid board char at %ux%u\n", y - 1, x - 1);
					return EXIT_FAILURE;
			}
			b[y * w + x] = c;
			if (debug_mode)
			{
				board[y * w + x] = c;
			}
		}
	}
	fclose(f);

	// Check solution.
	FILE* const g = fopen(argv[optind + 1], "r");
	if (!g)
	{
		fprintf(stderr, "failed to open solution\n");
		return EXIT_FAILURE;
	}

	u4   start_y;
	u4   start_x;
	char path[7];
	if (fscanf(g, "x=%u&y=%u&%6[^=]=", &start_x, &start_y, path) != 3)
	{
		fprintf(stderr, "could not parse start position\n");
		return EXIT_FAILURE;
	}

	bool compressed;
	if (strcmp(path, "path") == 0)
	{
		compressed = false;
	}
	else if (strcmp(path, "qpath") == 0)
	{
		compressed = true;
	}
	else
	{
		fprintf(stderr, "did not recognize path type\n");
		return EXIT_FAILURE;
	}

	if (start_y >= board_h || start_x >= board_w)
	{
		fprintf(stderr, "start position not on board\n");
		if (debug_mode)
		{
			fprintf(stderr, "Board dimensions: %ux%u\n", board_w, board_h);
			fprintf(stderr, "Start position: (%u,%u)\n", start_x, start_y);
		}
		free(b);
		if (debug_mode) free(board);
		return EXIT_FAILURE;
	}

	u4 y = start_y + 1;
	u4 x = start_x + 1;

	u1* i = &b[y * w + x];
	if (!*i)
	{
		fprintf(stderr, "start position is blocked\n");
		if (debug_mode)
		{
			print_board_state(b, w, h, x, y);
		}
		free(b);
		if (debug_mode) free(board);
		return EXIT_FAILURE;
	}

	n -= 1;
	*i = 0;

	s4 const delta[] = { -1, -(s4)w, 1, (s4)w };

	for (;;)
	{
		s4 d;
		switch (fgetc(g))
		{
			case 'L': d = delta[0]; break;
			case 'U': d = delta[1]; break;
			case 'R': d = delta[2]; break;
			case 'D': d = delta[3]; break;

			case EOF:
				if (ferror(g))
				{
					fprintf(stderr, "read error\n");
					return EXIT_FAILURE;
				}
				/* FALLTHROUGH */
			case '\r':
			case '\n':
				goto end_of_path;

			default:
				fprintf(stderr, "invalid char in path\n");
				return EXIT_FAILURE;
		}

		if (!i[d])
		{
			fprintf(stderr, "direction is blocked\n");
			if (debug_mode)
			{
				// Calculate current position
				u4 curr_x = (i - b) % w;
				u4 curr_y = (i - b) / w;
				char dir_char = ' ';
				if (d == delta[0]) dir_char = 'L';
				else if (d == delta[1]) dir_char = 'U';
				else if (d == delta[2]) dir_char = 'R';
				else if (d == delta[3]) dir_char = 'D';
				fprintf(stderr, "Attempted direction: %c\n", dir_char);
				print_board_state(b, w, h, curr_x, curr_y);
			}
			free(b);
			if (debug_mode) free(board);
			return EXIT_FAILURE;
		}

		for (;;)
		{
			do
			{
				n -= 1;
				i += d;
				*i = 0;
			}
			while (i[d]);

			if (!compressed) break;

			// Check if there is only one free direction.
			for (u4 dir = 0;; ++dir)
			{
				if (dir == 4) goto decision; // No free neighbours?
				d = delta[dir];
				if (!i[d]) continue;
				// Is the opposite direction free, too?
				if (dir < 2 && i[delta[dir + 2]]) goto decision;
				break;
			}
		}
decision:;
	}
end_of_path:
	fclose(g);

	if (n != 0)
	{
		fprintf(stderr, "path misses %u fields\n", n);
		if (debug_mode)
		{
			// Calculate current position
			u4 curr_x = (i - b) % w;
			u4 curr_y = (i - b) / w;
			print_board_state(b, w, h, curr_x, curr_y);
			fprintf(stderr, "Remaining unvisited cells: %u\n", n);
		}
		free(b);
		if (debug_mode) free(board);
		return EXIT_FAILURE;
	}

	free(b);
	if (debug_mode) free(board);
	return EXIT_SUCCESS;
}
