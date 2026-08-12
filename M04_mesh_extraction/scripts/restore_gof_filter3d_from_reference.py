#!/usr/bin/env python3
"""viewer용 crop PLY에 GOF의 filter_3D 필드를 복원한다."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from plyfile import PlyData, PlyElement


XYZ_FIELDS = ("x", "y", "z")
FILTER_FIELD = "filter_3D"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "GOF 원본 PLY의 동일 XYZ Gaussian을 찾아 crop PLY에 filter_3D "
            "필드를 다시 붙인다."
        )
    )
    parser.add_argument("--input", required=True, type=Path, help="filter_3D가 없는 crop PLY")
    parser.add_argument("--reference", required=True, type=Path, help="filter_3D를 가진 원본 GOF PLY")
    parser.add_argument("--output", required=True, type=Path, help="복원된 GOF 호환 PLY 출력 경로")
    parser.add_argument(
        "--summary",
        type=Path,
        default=None,
        help="매칭 통계 JSON 출력 경로. 생략하면 output 옆에 .filter3d_summary.json을 쓴다.",
    )
    parser.add_argument(
        "--allow-existing-filter",
        action="store_true",
        help="input에 이미 filter_3D가 있어도 그대로 재출력한다.",
    )
    return parser.parse_args()


def require_fields(ply: PlyData, fields: tuple[str, ...], label: str) -> None:
    names = ply["vertex"].data.dtype.names or ()
    missing = [field for field in fields if field not in names]
    if missing:
        raise SystemExit(f"{label}에 필요한 필드가 없다: {', '.join(missing)}")


def xyz_array(vertex_data: np.ndarray) -> np.ndarray:
    xyz = np.stack([np.asarray(vertex_data[field], dtype=np.float32) for field in XYZ_FIELDS], axis=1)
    return np.ascontiguousarray(xyz)


def key_view(xyz: np.ndarray) -> np.ndarray:
    if xyz.dtype != np.float32 or xyz.ndim != 2 or xyz.shape[1] != 3:
        raise ValueError("XYZ 배열은 float32 Nx3 형태여야 한다.")
    return xyz.view(np.dtype((np.void, xyz.dtype.itemsize * xyz.shape[1]))).reshape(-1)


def match_filter_values(input_xyz: np.ndarray, reference_xyz: np.ndarray, reference_filter: np.ndarray) -> np.ndarray:
    input_keys = key_view(input_xyz)
    reference_keys = key_view(reference_xyz)
    order = np.argsort(reference_keys)
    sorted_keys = reference_keys[order]

    positions = np.searchsorted(sorted_keys, input_keys)
    in_bounds = positions < len(sorted_keys)
    matched = np.zeros(len(input_keys), dtype=bool)
    matched[in_bounds] = sorted_keys[positions[in_bounds]] == input_keys[in_bounds]

    if not np.all(matched):
        unmatched = int((~matched).sum())
        examples = input_xyz[~matched][:5].tolist()
        raise SystemExit(
            "원본 GOF PLY에서 crop 좌표를 모두 찾지 못했다. "
            f"unmatched={unmatched}, examples={examples}"
        )

    return reference_filter[order[positions]]


def append_filter_field(input_vertex: np.ndarray, filter_values: np.ndarray) -> np.ndarray:
    input_names = input_vertex.dtype.names or ()
    if FILTER_FIELD in input_names:
        output_dtype = input_vertex.dtype
        output = np.empty(input_vertex.shape, dtype=output_dtype)
        for name in input_names:
            output[name] = input_vertex[name]
        output[FILTER_FIELD] = filter_values
        return output

    output_dtype = list(input_vertex.dtype.descr) + [(FILTER_FIELD, "<f4")]
    output = np.empty(input_vertex.shape, dtype=output_dtype)
    for name in input_names:
        output[name] = input_vertex[name]
    output[FILTER_FIELD] = filter_values.astype(np.float32, copy=False)
    return output


def main() -> None:
    args = parse_args()
    summary_path = args.summary or args.output.with_suffix(".filter3d_summary.json")

    input_ply = PlyData.read(args.input)
    reference_ply = PlyData.read(args.reference)
    input_vertex = input_ply["vertex"].data
    reference_vertex = reference_ply["vertex"].data

    require_fields(input_ply, XYZ_FIELDS, "input PLY")
    require_fields(reference_ply, XYZ_FIELDS + (FILTER_FIELD,), "reference PLY")

    input_names = input_vertex.dtype.names or ()
    if FILTER_FIELD in input_names and not args.allow_existing_filter:
        raise SystemExit("input PLY에 이미 filter_3D가 있다. --allow-existing-filter를 사용해라.")

    input_xyz = xyz_array(input_vertex)
    reference_xyz = xyz_array(reference_vertex)
    reference_filter = np.asarray(reference_vertex[FILTER_FIELD], dtype=np.float32)
    filter_values = match_filter_values(input_xyz, reference_xyz, reference_filter)

    output_vertex = append_filter_field(input_vertex, filter_values)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    PlyData([PlyElement.describe(output_vertex, "vertex")], text=False).write(args.output)

    summary = {
        "input": str(args.input),
        "reference": str(args.reference),
        "output": str(args.output),
        "input_vertices": int(len(input_vertex)),
        "reference_vertices": int(len(reference_vertex)),
        "matched_vertices": int(len(input_vertex)),
        "input_property_count": int(len(input_names)),
        "output_property_count": int(len(output_vertex.dtype.names or ())),
        "restored_property": FILTER_FIELD,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("filter_3D 복원 완료")
    print(f"  input: {args.input}")
    print(f"  reference: {args.reference}")
    print(f"  output: {args.output}")
    print(f"  vertices: {len(input_vertex)}")
    print(f"  summary: {summary_path}")


if __name__ == "__main__":
    main()
