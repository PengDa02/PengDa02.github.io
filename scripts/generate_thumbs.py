#!/usr/bin/env python3
"""
Generate WebP thumbnails for Moments images.

Convention:
  Moments/2026-05-19/1.jpeg  ->  Moments/2026-05-19/1.thumb.webp

Skips images that already have a thumbnail unless --force is passed.

Usage:
  pip install Pillow
  python scripts/generate_thumbs.py
  python scripts/generate_thumbs.py --moments-dir Moments --size 300 --quality 82
  python scripts/generate_thumbs.py --force
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Missing dependency. Install with: pip install Pillow", file=sys.stderr)
    sys.exit(1)

THUMB_MARKER = ".thumb.webp"
IMAGE_EXTENSIONS = {".jpeg", ".jpg", ".png", ".webp", ".gif", ".bmp", ".tiff"}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def is_source_image(path: Path) -> bool:
    name = path.name.lower()
    if name.endswith(THUMB_MARKER):
        return False
    if path.stem.endswith(".thumb"):
        return False
    return path.suffix.lower() in IMAGE_EXTENSIONS


def thumb_path_for(original: Path) -> Path:
    return original.with_name(f"{original.stem}.thumb.webp")


def save_webp(image: Image.Image, dest: Path, quality: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        image.save(dest, "WEBP", quality=quality, method=6)
    else:
        image.convert("RGB").save(dest, "WEBP", quality=quality, method=6)


def generate_thumb(original: Path, thumb: Path, size: int, quality: int) -> None:
    with Image.open(original) as im:
        im.load()
        resized = im.copy()
        resized.thumbnail((size, size), Image.Resampling.LANCZOS)
        save_webp(resized, thumb, quality)


def iter_source_images(moments_dir: Path):
    for path in sorted(moments_dir.rglob("*")):
        if path.is_file() and is_source_image(path):
            yield path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate WebP thumbnails for Moments images.")
    parser.add_argument(
        "--moments-dir",
        type=Path,
        default=repo_root() / "Moments",
        help="Directory containing moment images (default: ./Moments)",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=300,
        help="Max width/height of thumbnail in pixels (default: 300)",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=82,
        help="WebP quality 1-100 (default: 82)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate thumbnails even if they already exist",
    )
    args = parser.parse_args()

    moments_dir = args.moments_dir.resolve()
    if not moments_dir.is_dir():
        print(f"Moments directory not found: {moments_dir}", file=sys.stderr)
        return 1

    created = 0
    skipped = 0
    failed = 0

    for original in iter_source_images(moments_dir):
        thumb = thumb_path_for(original)
        if thumb.exists() and not args.force:
            skipped += 1
            continue

        try:
            generate_thumb(original, thumb, args.size, args.quality)
            created += 1
            print(f"created: {thumb.relative_to(moments_dir.parent)}")
        except Exception as exc:  # noqa: BLE001 - report and continue batch
            failed += 1
            print(f"failed:  {original} ({exc})", file=sys.stderr)

    print(
        f"\nDone. created={created}, skipped={skipped}, failed={failed}, "
        f"size={args.size}px, quality={args.quality}"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
