#!/usr/bin/env python3
"""Myers diff assignment solution.

Part A: minimal line diff of two files.
Part B: the same diff plus minimal changed-character ranges for paired lines.

The core sequence diff is the same Myers O(ND) furthest-reaching-diagonal
approach used in the deployed DiffLab backend, generalized to arbitrary
sequences.
"""
from __future__ import annotations

import sys
from typing import Any, Iterable, Sequence


# ---------------------------------------------------------------------------
# Myers core — kept structurally close to the deployed DiffLab implementation
# ---------------------------------------------------------------------------

def myers_operations(a: Iterable[Any], b: Iterable[Any]) -> list[tuple[str, Any]]:
    """Return a minimal edit script transforming sequence a into b.

    Each operation is ('equal', item), ('delete', item), or ('insert', item).
    """
    a, b = list(a), list(b)
    n, m = len(a), len(b)

    if not n:
        return [("insert", item) for item in b]
    if not m:
        return [("delete", item) for item in a]

    v = {1: 0}
    trace: list[dict[int, int]] = []
    end_d = 0
    found = False

    for d in range(n + m + 1):
        trace.append(v.copy())
        for k in range(-d, d + 1, 2):
            if k == -d or (k != d and v.get(k - 1, -1) < v.get(k + 1, -1)):
                x = v.get(k + 1, 0)
            else:
                x = v.get(k - 1, 0) + 1

            y = x - k
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1

            v[k] = x
            if x >= n and y >= m:
                end_d = d
                found = True
                break
        if found:
            break

    x, y = n, m
    reversed_ops: list[tuple[str, Any]] = []

    for d in range(end_d, -1, -1):
        previous_v = trace[d]
        k = x - y

        if d == 0:
            while x > 0 and y > 0:
                reversed_ops.append(("equal", a[x - 1]))
                x -= 1
                y -= 1
            while x > 0:
                reversed_ops.append(("delete", a[x - 1]))
                x -= 1
            while y > 0:
                reversed_ops.append(("insert", b[y - 1]))
                y -= 1
            break

        if k == -d or (k != d and previous_v.get(k - 1, -1) < previous_v.get(k + 1, -1)):
            prev_k = k + 1
        else:
            prev_k = k - 1

        prev_x = previous_v.get(prev_k, 0)
        prev_y = prev_x - prev_k

        while x > prev_x and y > prev_y:
            reversed_ops.append(("equal", a[x - 1]))
            x -= 1
            y -= 1

        if x == prev_x:
            if y > 0:
                reversed_ops.append(("insert", b[y - 1]))
                y -= 1
        else:
            if x > 0:
                reversed_ops.append(("delete", a[x - 1]))
                x -= 1

    reversed_ops.reverse()
    return reversed_ops


def normalize_change_order(ops: Sequence[tuple[str, Any]]) -> list[tuple[str, Any]]:
    """Enforce the assignment's delete-before-insert rule in each change block."""
    result: list[tuple[str, Any]] = []
    i = 0
    while i < len(ops):
        if ops[i][0] == "equal":
            result.append(ops[i])
            i += 1
            continue

        deletes: list[tuple[str, Any]] = []
        inserts: list[tuple[str, Any]] = []
        while i < len(ops) and ops[i][0] != "equal":
            if ops[i][0] == "delete":
                deletes.append(ops[i])
            else:
                inserts.append(ops[i])
            i += 1
        result.extend(deletes)
        result.extend(inserts)
    return result


def diff_sequence(a: Sequence[Any], b: Sequence[Any]) -> list[tuple[str, Any]]:
    return normalize_change_order(myers_operations(a, b))


# ---------------------------------------------------------------------------
# File handling required by the assignment
# ---------------------------------------------------------------------------

def read_raw_lines(path: str) -> list[bytes]:
    """Read raw bytes, split only on LF, preserve CR, and drop final empty part."""
    with open(path, "rb") as f:
        data = f.read()
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    return lines


def render_part_a(a: Sequence[bytes], b: Sequence[bytes]) -> bytes:
    """Render the minimal line diff exactly as required by Part A."""
    ops = diff_sequence(a, b)
    out = bytearray()
    for kind, line in ops:
        prefix = {"equal": b" ", "delete": b"-", "insert": b"+"}[kind]
        out.extend(prefix)
        out.extend(line)
        out.extend(b"\n")
    return bytes(out)


# ---------------------------------------------------------------------------
# Part B — Myers again at Unicode-code-point granularity
# ---------------------------------------------------------------------------

def changed_ranges(old: str, new: str) -> tuple[str, str]:
    """Return minimal changed ranges for old/new Unicode strings."""
    ops = diff_sequence(list(old), list(new))
    old_ranges: list[tuple[int, int]] = []
    new_ranges: list[tuple[int, int]] = []
    old_pos = 0
    new_pos = 0

    for kind, item in ops:
        if kind == "equal":
            old_pos += 1
            new_pos += 1
        elif kind == "delete":
            old_ranges.append((old_pos, old_pos + 1))
            old_pos += 1
        else:
            new_ranges.append((new_pos, new_pos + 1))
            new_pos += 1

    def merge(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
        if not ranges:
            return []
        merged = [ranges[0]]
        for start, end in ranges[1:]:
            prev_start, prev_end = merged[-1]
            if start <= prev_end:
                merged[-1] = (prev_start, max(prev_end, end))
            else:
                merged.append((start, end))
        return merged

    def format_ranges(ranges: list[tuple[int, int]]) -> str:
        return ",".join(f"{start}-{end}" for start, end in merge(ranges)) or "."

    return format_ranges(old_ranges), format_ranges(new_ranges)


def render_highlight(a: Sequence[bytes], b: Sequence[bytes]) -> bytes:
    """Render Part A plus ? lines after each paired inserted line."""
    ops = diff_sequence(a, b)
    out = bytearray()
    i = 0

    while i < len(ops):
        kind, line = ops[i]

        if kind == "equal":
            out.extend(b" ")
            out.extend(line)
            out.extend(b"\n")
            i += 1
            continue

        deletes: list[bytes] = []
        inserts: list[bytes] = []

        while i < len(ops) and ops[i][0] != "equal":
            if ops[i][0] == "delete":
                deletes.append(ops[i][1])
            else:
                inserts.append(ops[i][1])
            i += 1

        for old_line in deletes:
            out.extend(b"-")
            out.extend(old_line)
            out.extend(b"\n")

        pairs = min(len(deletes), len(inserts))
        for idx, new_line in enumerate(inserts):
            out.extend(b"+")
            out.extend(new_line)
            out.extend(b"\n")

            if idx < pairs:
                try:
                    old_text = deletes[idx].decode("utf-8")
                    new_text = new_line.decode("utf-8")
                except UnicodeDecodeError:
                    raise ValueError("highlight input must be valid UTF-8")
                old_ranges, new_ranges = changed_ranges(old_text, new_text)
                out.extend(f"? {old_ranges} | {new_ranges}\n".encode("utf-8"))

    return bytes(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if len(args) != 3 or args[0] not in {"lines", "highlight"}:
        print("usage: main.py lines A B | main.py highlight A B", file=sys.stderr)
        return 2

    command, path_a, path_b = args

    try:
        a = read_raw_lines(path_a)
        b = read_raw_lines(path_b)
        if command == "lines":
            output = render_part_a(a, b)
        else:
            output = render_highlight(a, b)
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"cpsdiff: {exc}", file=sys.stderr)
        return 2

    sys.stdout.buffer.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
