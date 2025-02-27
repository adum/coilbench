#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned char u1;
typedef   signed int  s4;
typedef unsigned int  u4;

int main(int const argc, char** const argv)
{
	if (argc != 3)
	{
		fprintf(stderr,
			"%s <board filename> <solution filename>\n"
			"file formats:\n"
			"  board:    x=<x>&y=<y>&board=<board>\n"
			"  solution: x=<x>&y=<y>&path=<path>\n"
			"            x=<x>&y=<y>&qpath=<qpath>\n",
			argv[0]);
		return EXIT_FAILURE;
	}

	// Read board.
	FILE* const f = fopen(argv[1], "r");
	if (!f)
	{
		fprintf(stderr, "failed to open board\n");
		return EXIT_FAILURE;
	}

	u4 board_h;
	u4 board_w;
	if (fscanf(f, "x=%u&y=%u&board=", &board_w, &board_h) != 2)
	{
		fprintf(stderr, "could not parse board size\n");
		return EXIT_FAILURE;
	}

	// Add a blocked border.
	u4        n = 0;
	u4  const h = board_h + 2;
	u4  const w = board_w + 2;

	u1* const b = calloc(h * w, sizeof(*b));
	if (!b)
	{
		fprintf(stderr, "out of memory\n");
		return EXIT_FAILURE;
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
		}
	}
	fclose(f);

	// Check solution.
	FILE* const g = fopen(argv[2], "r");
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
		return EXIT_FAILURE;
	}

	u4 y = start_y + 1;
	u4 x = start_x + 1;

	u1* i = &b[y * w + x];
	if (!*i)
	{
		fprintf(stderr, "start position is blocked\n");
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
		return EXIT_FAILURE;
	}

	return EXIT_SUCCESS;
}
