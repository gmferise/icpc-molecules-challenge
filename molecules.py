import sys

ChainSet = tuple[str, str, str, str]
ChainConfig = tuple[int, int, int, int, int, int]
Molecule = tuple[ChainSet, ChainConfig]

"""
Format explanation

Examples:
ChainSet: ('AZAAAAAAAAWA', 'BWBBBBBBBXBB', 'CYCCCCCCCCXC', 'DZDDDDDDDYDD')
ChainConfig: (10, 1, 9, 10, 1, 9)

Rendered, this Molecule would look like:
Area: 56
. D . . . . . . . . B .
A Z A A A A A A A A W A
. D . . . . . . . . B .
. D . . . . . . . . B .
. D . . . . . . . . B .
. D . . . . . . . . B .
. D . . . . . . . . B .
. D . . . . . . . . B .
. D . . . . . . . . B .
C Y C C C C C C C C X C
. D . . . . . . . . B .
. D . . . . . . . . B .

The ChainConfig takes the format:
(A_end, B_start, B_end, C_start, C_end, D_start)
which is written in short as (Ae, Bs, Be, Cs, Ce, Ds)

Each number represents an index of its chain (string).
So Ae is an index on chain A. In this example, Ae is 10 so A[Ae] == 'W'

These indicies determine where the chains intersect, so if we loop through
the right values, we can generate all possible octothorpes (#).

You can use these indicies to check if the characters at the intersections
are equal, and calculate the inner area.
"""


__author__ = "Gavin Ferise"


def main():
    # Process CLI args
    if (
        len(sys.argv) < 2
        or (len(sys.argv) >= 2 and sys.argv[1][-4:] != '.txt')
        or (len(sys.argv) >= 3 and sys.argv[2][-4:] != '.txt')
    ):
        done('Usage: python molecules.py input.txt ?[expected-output.txt]', 1)
    else:
        input_file = sys.argv[1]
        tests_file = sys.argv[2] if len(sys.argv) >= 3 else None

    # Open and process input into groups of chains
    try:
        print(f'Analyzing "{input_file}"...')
        chain_sets = process_input_file(input_file)
    except FileNotFoundError:
        done('The input file does not exist.', 1)

    # Process chains to get outputs (maximum areas)
    results = process_chain_sets(chain_sets)
    print(results)

    # Check the results
    if tests_file:
        try:
            failed_tests = []
            with open(tests_file) as ans:
                lines = ans.read().split()
                for i, ln in enumerate(lines):
                    if ln != str(results[i]):
                        failed_tests.append((i, ln, results[i], chain_sets[i]))
        except FileNotFoundError:
            done(f'The output test file "{tests_file}" does not exist.', 1)

        if not failed_tests:
            done('The results matched the output file!')
        else:
            for num, a, g, chains in failed_tests:
                print(f'Failed Test {num}: Max area was {g}, expected {a}')
                print(f'Original chains were: {chains}')
                print('Here are the generated molecules:')
                molecules = generate_molecules(chains)
                for cs, cfg in molecules:
                    render = render_molecule(cs, cfg)
                    print(f'Chains: {cs}')
                    print(f'Config: {cfg}')
                    print(f'Area: {calc_config_area(cfg)}')
                    print(render)
                    input('...')


def process_input_file(filename: str) -> list[ChainSet]:
    """
    Read the contents of a file in the expected molecules format,
    outputting a 4-tuple of strings for every 4 strings in the file.
    """
    chains = []
    with open(filename, 'r') as file:
        text = file.read()
        Q = text.find('Q')
        if Q == -1:
            done('Invalid file format: Expected to find EOF "Q" line', 1)
        lines = text[0:Q].split()
        if len(lines) % 4 != 0:
            done('Invalid file format: Expected even groups of 4 chains', 1)
        while lines:
            chains.append(tuple(lines[0:4]))
            lines = lines[4:]
    return chains


def process_chain_sets(chain_sets: list[ChainSet]) -> list[int]:
    """
    Take a list of chain sets and find the maximum area of
    the optimal molecule made with those chain sets
    """
    results = []
    for chains in chain_sets:
        molecules = generate_molecules(chains)
        if not molecules:  # can't assemble the chains
            results.append(0)
        else:
            configs = [config for chains, config in molecules]
            best = max(configs, key=calc_config_area)
            results.append(calc_config_area(best))
    return results


def generate_molecules(chains: ChainSet) -> list[Molecule]:
    """
    Generate all possible Molecules from a ChainSet.
    Will re-order the ChainSet to check all rotations.
    """
    # Which chain belongs in which of the 4 spots? Get all the combos
    chain_combinations = [
        tuple(chains[i] for i in c)
        for c in combinations(range(4))
    ]
    all_configs = []
    for combo in chain_combinations:
        for config in generate_valid_configs(combo):
            all_configs.append((combo, config))
    return all_configs


def generate_valid_configs(chains: ChainSet) -> list[ChainConfig]:
    """
    Generate all valid ChainConfigs from an ordered ChainSet
    """
    A, B, C, D = chains
    # Generate valid octothorpes, but the intersections may not match
    return [                                          # Ex for len 12
        (Ae, Bs, Be, Cs, Ce, Ds)
        for Ae in range(3, len(A) - 1)                # [3,          10]
        for Bs in range(1, len(B) - 3)                # [1,           8]
        for Be in range(Bs + 2, len(B) - 1)           # [(3, 10),    10]
        for Cs in range(3, len(C) - 1)                # [3,          10]
        for Ce in range(max(1, Cs - Ae + 1), Cs - 2)  # [(1, 8), (1, 8)]
        for Ds in range(1 + (Be - Bs), len(D) - 1)    # [(3, 10),    10]
        if (  # Narrow down by checking intersections
            A[Ae] == B[Bs]
            and B[Be] == C[Cs]
            and C[Ce] == D[Ds]
            and D[Ds - (Be - Bs)] == A[Ae - (Cs - Ce)]
        )
    ]


def calc_config_area(config: ChainConfig) -> int:
    """
    Calculate the inner area of a given configuration
    """
    Ae, Bs, Be, Cs, Ce, Ds = config
    width = Cs - Ce
    height = Be - Bs
    return (width - 1) * (height - 1)


def render_molecule(chains: ChainSet, config: ChainConfig) -> str:
    """
    Render a Molecule into a string from the ChainSet and ChainConfig.
    """
    EMPTY = '.'
    CONFLICT = '*'
    A, B, C, D = chains
    Ae, Bs, Be, Cs, Ce, Ds = config

    cursor = [0, 0]
    grid = [['.']]

    def ensured_write(char):
        """
        Expand the grid so the character can be written,
        move the cursor to where it expected to go,
        and write the character, recording if it overlapped.
        """
        # Expand up
        if cursor[0] < 0:
            for _ in range(-cursor[0]):
                grid.insert(0, [EMPTY for _ in range(len(grid[0]))])
            cursor[0] = 0
        # Expand left
        if cursor[1] < 0:
            for _ in range(-cursor[1]):
                for row in grid:
                    row.insert(0, EMPTY)
            cursor[1] = 0
        # Expand down
        if cursor[0] >= len(grid):
            for _ in range(cursor[0] - len(grid) + 1):
                grid.append([EMPTY for _ in range(len(grid[0]))])
            cursor[0] = len(grid) - 1
        # Expand right
        if cursor[1] >= len(grid[0]):
            for _ in range(cursor[1] - len(grid[0]) + 1):
                for row in grid:
                    row.append(EMPTY)
            cursor[1] = len(grid[0]) - 1

        # Write to grid
        current = grid[cursor[0]][cursor[1]]
        if current == char or current == EMPTY:
            grid[cursor[0]][cursor[1]] = char
        else:
            grid[cursor[0]][cursor[1]] = CONFLICT

    for a in A:
        ensured_write(a)
        cursor[1] += 1

    cursor[0] -= Bs
    cursor[1] += Ae - len(A)
    for b in B:
        ensured_write(b)
        cursor[0] += 1

    cursor[0] += Be - len(B)
    cursor[1] -= Cs
    for c in C:
        ensured_write(c)
        cursor[1] += 1

    cursor[1] += Ce - len(C)
    cursor[0] -= Ds
    for d in D:
        ensured_write(d)
        cursor[0] += 1

    return '\n'.join(
        ' '.join(row) for row in grid
    )


def recursive_combogen(choices: list, acc=()) -> list:
    """
    Generate tuple combinations using recursion.
    End result will be deeply nested.
    """
    if len(choices) == 1:
        return acc + tuple(choices)
    else:
        return [recursive_combogen(
            [item for item in choices if item != c],
            acc + (c,)
        ) for c in choices]


def recursive_flatten(a_list: list) -> list:
    """
    Recursively flatten any list
    """
    flat = []
    for c in a_list:
        if type(c) == list:
            flat += recursive_flatten(c)
        else:
            flat.append(c)
    return flat


def combinations(choices: list) -> list:
    """
    Calculate the possible combinations from
    the given (unique) items.
    """
    return recursive_flatten(recursive_combogen(choices))


def done(message: str, code: int = 0):
    """
    Exit the CLI program with a message.
    """
    print(message)
    exit(code)


if __name__ == '__main__':
    main()
