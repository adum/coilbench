Testing results for various llms, informally added.

The estimate column is a very rough projection of how long this solver would take on a level that's 2000 by 2000. The capital M stands for millennia. Solving level 63 represents about 0.14% of the final board area. And the problem is generally exponential in difficulty with respects to board area.

Calling a model "iter" means repeatedly iterating on the solution inside Claude Code, OpenAI codex, or cline, having the model write code, test, repeat, as many times as it wants to. The score value is the highest tested score during this process, even if there are regressions later.

Calling with "-p" means doing the non interactive mode with Claude Code.

| Date        | Model         | Timeout  | Score    | Estimate for 2000 | Percent of goal | Tokens |
| --------    | --------      | -------- | -------- | -------- |  -------- |  -------- |
| Feb 27 2025 | (brute force) | 600       | 47       | 104 M |  |  |
| Feb 27 2025 | 01 pro 1shot  | 60       | 0        |  |  |  |
| Feb 27 2025 | 03 mini 1shot | 600       | 63        | 658 M |  |  |
| Feb 27 2025 | Sonnet 3.7 1shot | 600       |  63       | 696 M |  |  |
| Feb 28 2025 | Grok 3.7 1shot | 600       |  47       | 108 M |  |  |
| Feb 28 2025 | 03 mini iter | 600       |    47     |  |  |  |
| Feb 28 2025 | Sonnet 3.7 iter | 600       | 14        | 121 M |  |  |
| May 29 2025 | Opus 4 -p | 600       | 64        | | 0.014% |  |
| August 8 2025 | Gpt 5 iter | 600       | 47        | | 0.00855% |   33300081 |
