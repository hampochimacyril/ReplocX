"""Build a lightweight animated GIF from the checked-in demo scenes.

The repository intentionally avoids requiring ffmpeg or Pillow for this step.
macOS `sips` converts each checked-in scene to a small GIF frame, and this script
assembles those single-image GIFs into one looping animation.
"""

from __future__ import annotations

import pathlib
import struct
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCENES = [
    ROOT / "docs/demo/scenes/01-overview.png",
    ROOT / "docs/demo/scenes/02-zip-explorer.png",
    ROOT / "docs/demo/scenes/03-scenario-builder.png",
    ROOT / "docs/demo/scenes/04-candidate-ranking.png",
    ROOT / "docs/demo/scenes/05-allocation-comparison.png",
    ROOT / "docs/demo/scenes/06-methodology.png",
]
OUT = ROOT / "docs/demo/replocx-demo.gif"
WIDTH = 720
FRAME_DELAY_CS = 120


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="replocx-gif-") as tmp:
        frame_paths = []
        for index, source in enumerate(SCENES):
            frame = pathlib.Path(tmp) / f"frame-{index:02d}.gif"
            subprocess.run(
                [
                    "sips",
                    "-s",
                    "format",
                    "gif",
                    "--resampleWidth",
                    str(WIDTH),
                    str(source),
                    "--out",
                    str(frame),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
            )
            frame_paths.append(frame)

        frames = [parse_single_gif(path.read_bytes()) for path in frame_paths]
        OUT.write_bytes(build_animation(frames))
        print(f"Wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)")


def parse_single_gif(data: bytes) -> dict[str, object]:
    if data[:6] not in (b"GIF87a", b"GIF89a"):
        raise ValueError("Not a GIF file")

    width, height, packed, background, aspect = struct.unpack("<HHBBB", data[6:13])
    has_gct = packed & 0b1000_0000
    gct_size = 3 * (2 ** ((packed & 0b0000_0111) + 1)) if has_gct else 0
    cursor = 13 + gct_size
    global_color_table = data[13 : 13 + gct_size]

    while cursor < len(data):
        block_id = data[cursor]
        if block_id == 0x2C:
            descriptor_start = cursor
            image_packed = data[cursor + 9]
            cursor += 10
            if image_packed & 0b1000_0000:
                local_size = 3 * (2 ** ((image_packed & 0b0000_0111) + 1))
                cursor += local_size
            cursor += 1
            while True:
                block_size = data[cursor]
                cursor += 1
                if block_size == 0:
                    image_end = cursor
                    break
                cursor += block_size
            return {
                "width": width,
                "height": height,
                "packed": packed,
                "background": background,
                "aspect": aspect,
                "global_color_table": global_color_table,
                "image_block": data[descriptor_start:image_end],
            }
        if block_id == 0x21:
            cursor += 2
            while True:
                block_size = data[cursor]
                cursor += 1
                if block_size == 0:
                    break
                cursor += block_size
            continue
        if block_id == 0x3B:
            break
        raise ValueError(f"Unexpected GIF block 0x{block_id:02x}")

    raise ValueError("GIF did not contain an image block")


def build_animation(frames: list[dict[str, object]]) -> bytes:
    first = frames[0]
    header = bytearray()
    header += b"GIF89a"
    header += struct.pack(
        "<HHBBB",
        int(first["width"]),
        int(first["height"]),
        int(first["packed"]) | 0b1000_0000,
        int(first["background"]),
        int(first["aspect"]),
    )
    header += first["global_color_table"]  # type: ignore[operator]
    header += b"\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00"

    body = bytearray()
    for frame in frames:
        body += b"\x21\xf9\x04\x04"
        body += struct.pack("<H", FRAME_DELAY_CS)
        body += b"\x00\x00"
        body += frame["image_block"]  # type: ignore[operator]
    body += b"\x3b"
    return bytes(header + body)


if __name__ == "__main__":
    main()
