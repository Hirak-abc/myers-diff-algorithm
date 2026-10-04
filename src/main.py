import sys


def read_file(path):
    """Read a file as raw bytes and return its lines (split on \\n only)."""
    with open(path, "rb") as f:
        data = f.read()

    if not data:
        return []

    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    return lines


def myers_diff(a, b):
    """Return a minimal diff using Myers' shortest-edit-path algorithm."""

    n = len(a)
    m = len(b)

    if n == 0:
        return [("+", x) for x in b]

    if m == 0:
        return [("-", x) for x in a]

    max_d = n + m
    offset = max_d + 1
    v = [0] * (2 * max_d + 3)
    trace = []

    for d in range(max_d + 1):

        trace.append(v[offset - d: offset + d + 1])

        for k in range(-d, d + 1, 2):

            if k == -d or (k != d and v[offset + k - 1] < v[offset + k + 1]):
                x = v[offset + k + 1]
            else:
                x = v[offset + k - 1] + 1

            y = x - k

            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1

            v[offset + k] = x

            if x >= n and y >= m:
                return reconstruct(trace, a, b, d)

    return []


def reconstruct(trace, a, b, d):
    """Reconstruct the edit script from Myers' trace."""

    x = len(a)
    y = len(b)
    result = []

    for current_d in range(d, 0, -1):

        v = trace[current_d]

        def get(k):
            return v[k + current_d]

        k = x - y

        if k == -current_d or (k != current_d and get(k - 1) < get(k + 1)):
            previous_k = k + 1
        else:
            previous_k = k - 1

        previous_x = get(previous_k)
        previous_y = previous_x - previous_k

        while x > previous_x and y > previous_y:
            result.append((" ", a[x - 1]))
            x -= 1
            y -= 1

        if x == previous_x:
            result.append(("+", b[y - 1]))
            y -= 1
        else:
            result.append(("-", a[x - 1]))
            x -= 1

    while x > 0 and y > 0:
        result.append((" ", a[x - 1]))
        x -= 1
        y -= 1

    while x > 0:
        result.append(("-", a[x - 1]))
        x -= 1

    while y > 0:
        result.append(("+", b[y - 1]))
        y -= 1

    result.reverse()
    return result


# ---------------------------------------------------------------------------
# Part A
# ---------------------------------------------------------------------------

def output_lines_diff(diff):
    out = sys.stdout.buffer

    for tag, line in diff:
        out.write(tag.encode("ascii"))
        out.write(line)
        out.write(b"\n")

    out.flush()


# ---------------------------------------------------------------------------
# Part B
# ---------------------------------------------------------------------------

def character_diff(old_line, new_line):
    old_text = old_line.decode("utf-8", errors="surrogateescape")
    new_text = new_line.decode("utf-8", errors="surrogateescape")
    return myers_diff(old_text, new_text)


def change_ranges(old_line, new_line):
    """(old_ranges, new_ranges): lists of (start, end), end exclusive,
    in character offsets, consecutive changes merged."""

    diff = character_diff(old_line, new_line)

    old_ranges = []
    new_ranges = []
    i = 0
    j = 0

    for tag, _ in diff:
        if tag == " ":
            i += 1
            j += 1
        elif tag == "-":
            if old_ranges and old_ranges[-1][1] == i:
                old_ranges[-1] = (old_ranges[-1][0], i + 1)
            else:
                old_ranges.append((i, i + 1))
            i += 1
        else:
            if new_ranges and new_ranges[-1][1] == j:
                new_ranges[-1] = (new_ranges[-1][0], j + 1)
            else:
                new_ranges.append((j, j + 1))
            j += 1

    return old_ranges, new_ranges


def format_ranges(ranges):
    if not ranges:
        return "."
    return ",".join("%d-%d" % r for r in ranges)


def output_highlight_diff(diff):
    out = sys.stdout.buffer

    i = 0

    while i < len(diff):

        tag, line = diff[i]

        if tag == " ":
            out.write(b" " + line + b"\n")
            i += 1
            continue

        deleted = []
        inserted = []

        while i < len(diff) and diff[i][0] == "-":
            deleted.append(diff[i][1])
            i += 1

        while i < len(diff) and diff[i][0] == "+":
            inserted.append(diff[i][1])
            i += 1

        pairs = min(len(deleted), len(inserted))

        for d in deleted:
            out.write(b"-" + d + b"\n")

        for j, ins in enumerate(inserted):
            out.write(b"+" + ins + b"\n")
            if j < pairs:
                old_r, new_r = change_ranges(deleted[j], ins)
                marker = "? %s | %s\n" % (format_ranges(old_r),
                                          format_ranges(new_r))
                out.write(marker.encode("ascii"))

    out.flush()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:

    if len(sys.argv) != 4:
        print("usage: main.py lines|highlight A_PATH B_PATH", file=sys.stderr)
        return 2

    command = sys.argv[1]

    if command not in ("lines", "highlight"):
        print("usage: main.py lines|highlight A_PATH B_PATH", file=sys.stderr)
        return 2

    try:
        a = read_file(sys.argv[2])
        b = read_file(sys.argv[3])
    except OSError:
        return 2

    diff = myers_diff(a, b)

    if command == "lines":
        output_lines_diff(diff)
    else:
        output_highlight_diff(diff)

    return 0


raise SystemExit(main())