#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from PIL import Image, ImageDraw


def parse_indices(value: str) -> list[int]:
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a GT/prediction contact sheet for GOF renders.")
    parser.add_argument("--render-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--indices", default="0,20,40,60,80,100,120,140")
    parser.add_argument("--scale-label", default="8")
    args = parser.parse_args()

    pred_dir = args.render_root / f"test_preds_{args.scale_label}"
    gt_dir = args.render_root / f"gt_{args.scale_label}"
    args.output_dir.mkdir(parents=True, exist_ok=True)

    indices = parse_indices(args.indices)
    thumb_w = 220
    thumb_h = 150
    label_h = 24
    pad = 8
    rows = len(indices)
    cols = 2

    sheet = Image.new(
        "RGB",
        (cols * thumb_w + (cols + 1) * pad, rows * (thumb_h + label_h) + (rows + 1) * pad),
        "white",
    )
    draw = ImageDraw.Draw(sheet)

    for row, idx in enumerate(indices):
        name = f"{idx:05d}.png"
        for col, kind in enumerate(("gt", "pred")):
            src = (gt_dir if kind == "gt" else pred_dir) / name
            if not src.exists():
                raise FileNotFoundError(src)
            dst = args.output_dir / f"{idx:05d}_{kind}.png"
            shutil.copy2(src, dst)

            img = Image.open(src).convert("RGB")
            img.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)

            x = pad + col * (thumb_w + pad)
            y = pad + row * (thumb_h + label_h + pad)
            draw.text((x, y), f"{name} {kind.upper()}", fill=(0, 0, 0))

            img_x = x + (thumb_w - img.width) // 2
            img_y = y + label_h + (thumb_h - img.height) // 2
            sheet.paste(img, (img_x, img_y))

    sheet.save(args.output_dir / "contact_sheet_gt_vs_pred.jpg", quality=92)


if __name__ == "__main__":
    main()
