"""
Number stats: read numbers from stdin and report sum and average.

Usage:
    echo "1 2 3 4 5" | python solution.py
    python solution.py  (then type numbers, one per line; Ctrl+D to finish)
"""

import sys


def parse_numbers(lines: list[str]) -> list[float]:
    """Parse numeric values from lines; skip non-numeric."""
    numbers = []
    for line in lines:
        for part in line.strip().split():
            try:
                numbers.append(float(part))
            except ValueError:
                pass
    return numbers


def main() -> None:
    lines = sys.stdin.readlines()
    numbers = parse_numbers(lines)
    if not numbers:
        print("No numbers provided.", file=sys.stderr)
        sys.exit(1)
    total = sum(numbers)
    count = len(numbers)
    average = total / count
    print(f"Count: {count}")
    print(f"Sum: {total}")
    print(f"Average: {average}")


if __name__ == "__main__":
    main()
