import sys

def read_lines(path):
    """Read a file exactly as the assignment requires."""
    with open(path, "rb") as file:
        data = file.read()

    lines = data.split(b"\n")

    # A final newline does not create an extra line.
    if lines and lines[-1] == b"":
        lines.pop()

    return lines


def myers_diff(a, b):
    """Find a minimum insert/delete diff using linear-space Myers."""
    a = list(a)
    b = list(b)

    def solve(a_start, a_end, b_start, b_end):
        """Solve one smaller part of the two sequences."""
        n = a_end - a_start
        m = b_end - b_start

        if n == 0:
            return [("insert", b[j]) for j in range(b_start, b_end)]
        if m == 0:
            return [("delete", a[i]) for i in range(a_start, a_end)]

        # Small one-line cases avoid unnecessary recursion.
        if n == 1:
            try:
                match = b.index(a[a_start], b_start, b_end)
            except ValueError:
                return [("delete", a[a_start])] + [
                    ("insert", b[j]) for j in range(b_start, b_end)
                ]

            return (
                [("insert", b[j]) for j in range(b_start, match)]
                + [("equal", a[a_start])]
                + [("insert", b[j]) for j in range(match + 1, b_end)]
            )

        if m == 1:
            try:
                match = a.index(b[b_start], a_start, a_end)
            except ValueError:
                return [
                    ("delete", a[i]) for i in range(a_start, a_end)
                ] + [("insert", b[b_start])]

            return (
                [("delete", a[i]) for i in range(a_start, match)]
                + [("equal", b[b_start])]
                + [("delete", a[i]) for i in range(match + 1, a_end)]
            )

        # Remove a common prefix. It needs no edits.
        prefix = 0
        while (
            a_start + prefix < a_end
            and b_start + prefix < b_end
            and a[a_start + prefix] == b[b_start + prefix]
        ):
            prefix += 1

        if prefix:
            return (
                [("equal", a[a_start + i]) for i in range(prefix)]
                + solve(a_start + prefix, a_end, b_start + prefix, b_end)
            )

        # Remove a common suffix for the same reason.
        suffix = 0
        while (
            a_end - suffix > a_start
            and b_end - suffix > b_start
            and a[a_end - suffix - 1] == b[b_end - suffix - 1]
        ):
            suffix += 1

        if suffix:
            return (
                solve(a_start, a_end - suffix, b_start, b_end - suffix)
                + [
                    ("equal", a[a_end - suffix + i])
                    for i in range(suffix)
                ]
            )

        # Find the middle snake with Myers' forward and backward searches.
        max_d = (n + m + 1) // 2
        delta = n - m
        odd_delta = delta % 2 != 0

        # Only O(n + m) integers are kept here. This is the important
        # memory improvement over storing V for every d.
        forward = {1: 0}
        backward = {1: 0}

        for d in range(max_d + 1):
            # Search from the beginning.
            for k in range(-d, d + 1, 2):
                if k == -d or (
                    k != d and forward.get(k - 1, -1) < forward.get(k + 1, -1)
                ):
                    x = forward.get(k + 1, 0)
                else:
                    x = forward.get(k - 1, 0) + 1

                y = x - k

                while x < n and y < m and a[a_start + x] == b[b_start + y]:
                    x += 1
                    y += 1

                forward[k] = x

                if odd_delta:
                    other_k = delta - k
                    if other_k in backward and x + backward[other_k] >= n:
                        split_x = x
                        split_y = y
                        return (
                            solve(
                                a_start,
                                a_start + split_x,
                                b_start,
                                b_start + split_y,
                            )
                            + solve(
                                a_start + split_x,
                                a_end,
                                b_start + split_y,
                                b_end,
                            )
                        )

            # Search from the end.
            for k in range(-d, d + 1, 2):
                if k == -d or (
                    k != d and backward.get(k - 1, -1) < backward.get(k + 1, -1)
                ):
                    x = backward.get(k + 1, 0)
                else:
                    x = backward.get(k - 1, 0) + 1

                y = x - k

                while x < n and y < m and a[a_end - x - 1] == b[b_end - y - 1]:
                    x += 1
                    y += 1

                backward[k] = x

                if not odd_delta:
                    other_k = delta - k
                    if other_k in forward and x + forward[other_k] >= n:
                        split_x = forward[other_k]
                        split_y = split_x - other_k
                        return (
                            solve(
                                a_start,
                                a_start + split_x,
                                b_start,
                                b_start + split_y,
                            )
                            + solve(
                                a_start + split_x,
                                a_end,
                                b_start + split_y,
                                b_end,
                            )
                        )

        raise RuntimeError("Myers search could not find a split")

    return delete_first(solve(0, len(a), 0, len(b)))

def delete_first(operations):
    """Put all deletions before insertions inside each change block."""
    result = []
    i = 0

    while i < len(operations):
        if operations[i][0] == "equal":
            result.append(operations[i])
            i += 1
            continue

        deletes = []
        inserts = []

        while i < len(operations) and operations[i][0] != "equal":
            operation, item = operations[i]

            if operation == "delete":
                deletes.append((operation, item))
            else:
                inserts.append((operation, item))

            i += 1

        result.extend(deletes)
        result.extend(inserts)

    return result


def print_lines_diff(a, b):
    """Print Part A."""
    operations = myers_diff(a, b)

    output = sys.stdout.buffer

    for operation, line in operations:
        if operation == "equal":
            prefix = b" "
        elif operation == "delete":
            prefix = b"-"
        else:
            prefix = b"+"

        output.write(prefix + line + b"\n")


def changed_ranges(old_line, new_line):
    """
    Find the minimum changed character ranges.

    The assignment defines positions using Unicode code points,
    so Python's list(str) is useful here.
    """
    old_text = old_line.decode("utf-8")
    new_text = new_line.decode("utf-8")

    operations = myers_diff(list(old_text), list(new_text))

    old_ranges = []
    new_ranges = []

    old_position = 0
    new_position = 0

    old_start = None
    new_start = None

    def finish_old():
        nonlocal old_start
        if old_start is not None:
            old_ranges.append((old_start, old_position))
            old_start = None

    def finish_new():
        nonlocal new_start
        if new_start is not None:
            new_ranges.append((new_start, new_position))
            new_start = None

    for operation, character in operations:
        if operation == "equal":
            finish_old()
            finish_new()
            old_position += 1
            new_position += 1

        elif operation == "delete":
            if old_start is None:
                old_start = old_position
            old_position += 1

        else:  # insert
            if new_start is None:
                new_start = new_position
            new_position += 1

    finish_old()
    finish_new()

    return format_ranges(old_ranges), format_ranges(new_ranges)


def format_ranges(ranges):
    """Convert [(start, end), ...] into the required string."""
    if not ranges:
        return "."

    # Merge touching ranges.
    merged = []

    for start, end in ranges:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return ",".join(f"{start}-{end}" for start, end in merged)


def print_highlight(a, b):
    """Print Part B: normal diff plus character ranges."""
    operations = myers_diff(a, b)

    i = 0
    output = sys.stdout.buffer

    while i < len(operations):

        if operations[i][0] == "equal":
            output.write(b" " + operations[i][1] + b"\n")
            i += 1
            continue

        # Collect one change block.
        deletes = []
        inserts = []

        while i < len(operations) and operations[i][0] != "equal":
            operation, line = operations[i]

            if operation == "delete":
                deletes.append(line)
            else:
                inserts.append(line)

            i += 1

        # Part A output: all deletions come first.
        for line in deletes:
            output.write(b"-" + line + b"\n")

        # Then print insertions. After each paired insertion,
        # print its character ranges immediately.
        pairs = min(len(deletes), len(inserts))

        for j, line in enumerate(inserts):
            output.write(b"+" + line + b"\n")

            if j < pairs:
                old_ranges, new_ranges = changed_ranges(
                    deletes[j], line
                )

                output.write(
                    f"? {old_ranges} | {new_ranges}\n".encode("utf-8")
                )


def main():
    if len(sys.argv) != 4:
        print(
            "Usage: python src/main.py lines A B", file=sys.stderr
        )
        print(
            "   or: python src/main.py highlight A B",
            file=sys.stderr
        )
        return 2

    mode = sys.argv[1]
    file_a = sys.argv[2]
    file_b = sys.argv[3]

    try:
        a = read_lines(file_a)
        b = read_lines(file_b)
    except (OSError, IOError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if mode == "lines":
        print_lines_diff(a, b)
        return 0

    if mode == "highlight":
        # Highlight files are guaranteed to be valid UTF-8.
        print_highlight(a, b)
        return 0

    print("error: mode must be 'lines' or 'highlight'", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
