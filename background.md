# Origin
This puzzle format was originally created by a mathematician by the name of Erich Friedman, manually constructing puzzles and intending people to solve it by hand.

# Computerization
In 2007, a computerized version was created for the site hacker.org (https://www.hacker.org/coil/) as a way to test the ability for people to write programs to solve it -- querying and submitting via API. To push the boundaries of the solving algorithms, large problem boards were created with a program, up to 2000x2000, much larger than can be solved with a naive brute force algorithm.

Over the years, over a thousand people have tried their hand at creating programs to solve this puzzle. Only 4 solvers have made it to the end.

# Why this could be a good benchmark for AI

A lot of existing coding benchmarks look at small discrete tasks, and a score is determined by how many the ai gets correct independently. However, a common real world case is a hard problem that requires iteration: you start with a basic approach, then trying new ideas, evaluating, integrating or rejecting, continuing to iterate until a satisfactory approach is developed. This benchmark provides a way to objectively measure such a task with a single score: the highest level you can solve.

- Single scale of difficulty: size of board, represented by the level number
- Optimizations are specific to the task and must be created, not known algorithms that can be integrated
- Decades of human testing have shown that there are at a minimum dozens of interesting optimization approaches that can be creatively applied in concert, not a single trick to discover

If we give a coding AI a prompt like "iterate on this challenge until you have fully solved the last level" are they able to do it? How far can they get?
