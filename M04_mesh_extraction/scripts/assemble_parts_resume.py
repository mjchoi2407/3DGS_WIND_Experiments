#!/usr/bin/env python3
"""Resume assembling HTTP range-download parts into one binary file."""

from __future__ import annotations

import argparse
import os
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("partdir", type=Path)
    parser.add_argument("expected_bytes", type=int)
    parser.add_argument("--chunk-mib", type=int, default=128)
    parser.add_argument("--verify-existing", action="store_true")
    return parser.parse_args()


def read_part0_size(partdir: Path) -> int:
    ranges = partdir / "ranges.tsv"
    with ranges.open("r", encoding="utf-8") as handle:
        first = handle.readline().split()
    if len(first) != 3 or first[0] != "001":
        raise RuntimeError(f"Cannot infer part_000 size from {ranges}")
    return int(first[1])


def compare_existing(output: Path, part: Path, start: int, length: int, chunk: int) -> None:
    if length <= 0:
        return
    checked = 0
    with output.open("rb") as out_handle, part.open("rb") as part_handle:
        out_handle.seek(start)
        while checked < length:
            want = min(chunk, length - checked)
            out_data = out_handle.read(want)
            part_data = part_handle.read(want)
            if out_data != part_data:
                raise RuntimeError(
                    f"Existing bytes differ for {part.name} at output offset "
                    f"{start + checked}"
                )
            checked += want
            print(f"checked {part.name}: {checked}/{length} bytes", flush=True)
    print(f"verified existing {part.name}: {length} bytes", flush=True)


def write_all(fd: int, data: bytes, offset: int) -> None:
    view = memoryview(data)
    written = 0
    while written < len(view):
        count = os.pwrite(fd, view[written:], offset + written)
        if count <= 0:
            raise RuntimeError(f"Short pwrite at output offset {offset + written}")
        written += count


def append_part(output: Path, part: Path, start: int, offset: int, chunk: int) -> int:
    size = part.stat().st_size
    written = offset
    fd = os.open(output, os.O_RDWR)
    try:
        with part.open("rb") as part_handle:
            part_handle.seek(written)
            while written < size:
                count = min(chunk, size - written)
                data = part_handle.read(count)
                if len(data) != count:
                    raise RuntimeError(f"Short read from {part}: {len(data)} != {count}")

                out_offset = start + written
                write_all(fd, data, out_offset)

                actual = output.stat().st_size
                expected = out_offset + count
                if actual != expected:
                    raise RuntimeError(
                        f"Unexpected output size after {part.name}: {actual} != {expected}"
                    )

                written += count
                pct = written * 100.0 / size
                total = actual * 100.0 / (start + size)
                print(
                    f"wrote {part.name}: {written}/{size} bytes "
                    f"({pct:5.1f}% of part); output={actual}; "
                    f"part_end_progress={total:5.1f}%",
                    flush=True,
                )
    finally:
        os.close(fd)
    return start + size


def main() -> int:
    args = parse_args()
    output = args.output
    partdir = args.partdir
    chunk = args.chunk_mib * 1024 * 1024

    part_paths = sorted(partdir.glob("part_[0-9][0-9][0-9]"))
    if not part_paths:
        raise RuntimeError(f"No part files found in {partdir}")

    part0 = partdir / "part_000"
    if part0.exists():
        start_offset = 0
        append_parts = part_paths
    else:
        start_offset = read_part0_size(partdir)
        if not output.exists() or output.stat().st_size < start_offset:
            raise RuntimeError(
                "part_000 is missing, and output does not contain the saved "
                f"prefix of {start_offset} bytes"
            )
        append_parts = [p for p in part_paths if p.name != "part_000"]

    total_parts = start_offset + sum(p.stat().st_size for p in append_parts)
    if total_parts != args.expected_bytes:
        raise RuntimeError(f"Part sizes sum to {total_parts}, expected {args.expected_bytes}")

    current_size = output.stat().st_size if output.exists() else 0
    if current_size > args.expected_bytes:
        raise RuntimeError(f"Output is too large: {current_size} > {args.expected_bytes}")
    if current_size < start_offset:
        raise RuntimeError(f"Output is shorter than fixed prefix: {current_size} < {start_offset}")

    print(f"resume output={output}", flush=True)
    print(
        f"current={current_size}, expected={args.expected_bytes}, prefix={start_offset}",
        flush=True,
    )

    start = start_offset
    for part in append_parts:
        part_size = part.stat().st_size
        part_end = start + part_size

        if current_size >= part_end:
            if args.verify_existing:
                compare_existing(output, part, start, part_size, chunk)
            print(f"skip complete {part.name}", flush=True)
            start = part_end
            continue

        if current_size > start:
            offset = current_size - start
            if args.verify_existing:
                compare_existing(output, part, start, offset, chunk)
            print(f"resume {part.name} from byte {offset}", flush=True)
        else:
            offset = 0
            print(f"append {part.name}", flush=True)

        current_size = append_part(output, part, start, offset, chunk)
        start = part_end

    final_size = output.stat().st_size
    if final_size != args.expected_bytes:
        raise RuntimeError(f"Final output size is {final_size}, expected {args.expected_bytes}")
    print(f"assembled complete: {output} ({final_size} bytes)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
