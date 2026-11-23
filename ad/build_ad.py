#!/usr/bin/env python3
"""Render the make.fun TikTok ad: five 9:16 slides, then the press pack's referral end card.

The creative, decided in the agent session that wrote this file:
  hook   "an AI agent just earned $100" - money already made by software, so the viewer's
         own agent is next. The number is the bounty's own first place.
  what   make.fun is where AI agents enter paid bounties.
  how    a bounty is posted, an agent builds it, the best one gets paid.
  money  real bounties, real USDC, paid to the agent's wallet.
  cta    bring your agent.
  end    the referral end card from make.fun's press pack, the entrant's code typed in.

Press files are fetched, never vendored: the brand badge overlay, the referral end card
video, the ghost illustration. Every position, pixel size and the code's box come from
https://make.fun/press/manifest.json (edition 2026-11-21), read at run time.

Usage:
    python3 ad/build_ad.py --code ab12cd34 --out ad.mp4
The frames land next to the output as frame-N.png so they can be looked at.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FPS = 30

# palette.txt, Night mode: the canvas, the inks, and the one accent.
BASE = (17, 20, 27)
SURFACE = (23, 27, 36)
HAIRLINE = (35, 41, 54)
INK = (224, 229, 239)
SECONDARY = (191, 199, 220)
MAGENTA = (196, 28, 131)
MAGENTA_INK = (255, 136, 196)

# TikTok in-feed + Reels safe box, from the manifest: keep every word inside it.
SAFE = (120, 269, 840, 979)
X0 = 132
XMAX = 948

HERE = Path(__file__).resolve().parent
WORK = HERE.parent  # the repository
# The press pack and the brand fonts stay outside the repository: set these to yours.
PRESS = Path(os.environ.get("MAKE_FUN_PRESS") or WORK.parent / "press")
FONTS = Path(os.environ.get("AD_FONTS") or WORK.parent / "fonts")

SLIDES = [3.4, 3.4, 3.6, 3.0, 3.1]  # seconds; their sum is where the end card starts
CARD_TAIL = 2.5  # the card's own length, 60 fps, from the manifest


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    files = {
        "bold": "Inter-Bold.ttf",
        "regular": "Inter-Regular.ttf",
        "mono": "JetBrainsMono-Bold.ttf",
    }
    return ImageFont.truetype(str(FONTS / files[name]), size)


def fit(text: str, name: str, size: int, max_width: float = XMAX - X0) -> ImageFont.FreeTypeFont:
    """The largest size at or under `size` at which `text` fits the measure."""
    while size > 8:
        f = font(name, size)
        if f.getlength(text) <= max_width:
            return f
        size -= 2
    return font(name, size)


def tracked(draw: ImageDraw.ImageDraw, xy, text, f, fill, tracking=6):
    """Draw a run of text with letter-spacing (PIL has none)."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill)
        x += f.getlength(ch) + tracking
    return x - tracking


def background() -> Image.Image:
    """Night canvas, a magenta bloom at the top right, and quiet hairlines."""
    im = Image.new("RGB", (W, H), BASE)
    bloom = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(bloom)
    bd.ellipse([560, -520, 1560, 460], fill=115)
    bd.ellipse([-560, 1320, 380, 2140], fill=60)
    bloom = bloom.filter(ImageFilter.GaussianBlur(300))
    im = Image.composite(Image.new("RGB", (W, H), MAGENTA), im, bloom.point(lambda v: int(v * 0.42)))
    lines = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lines)
    for y in range(240, H, 160):
        ld.line([(0, y), (W, y)], fill=HAIRLINE + (255,))
    return Image.alpha_composite(im.convert("RGBA"), lines).convert("RGB")


def kicker(d: ImageDraw.ImageDraw, text: str, y: int) -> int:
    """The magenta label and the rule under all of it; returns the y just under them."""
    f = font("mono", 36)
    end = tracked(d, (X0, y), text, f, MAGENTA_INK, tracking=8)
    d.rectangle([X0, y + 58, end, y + 62], fill=MAGENTA)
    return y + 62


def slide_hook() -> Image.Image:
    im = background()
    d = ImageDraw.Draw(im)
    y = kicker(d, "NOT A HUMAN", 528)
    y += 54
    f1 = fit("an AI agent", "bold", 104)
    d.text((X0, y), "an AI agent", font=f1, fill=INK)
    y += int(f1.size * 1.16)
    d.text((X0, y), "just earned", font=f1, fill=INK)
    y += int(f1.size * 1.10) + 26
    f3 = fit("$100", "bold", 210)
    d.text((X0, y), "$100", font=f3, fill=MAGENTA_INK)
    y += int(f3.size * 0.92) + 36
    d.text((X0, y), "by shipping code for a bounty", font=font("regular", 46), fill=SECONDARY)
    assert y + 46 < SAFE[1] + SAFE[3], "content runs past the safe box"
    return im


def slide_what() -> Image.Image:
    im = background()
    d = ImageDraw.Draw(im)
    lockup = Image.open(PRESS / "lockup-on-dark-2400.png").convert("RGBA")
    lw = 660
    lockup = lockup.resize((lw, round(lockup.height * lw / lockup.width)), Image.LANCZOS)
    im.paste(lockup, (X0 - 6, 528), lockup)
    y = 528 + lockup.height + 92
    f = fit("where AI agents", "bold", 96)
    d.text((X0, y), "where AI agents", font=f, fill=INK)
    y += int(f.size * 1.16)
    f2 = fit("compete in bounties", "bold", 96)
    d.text((X0, y), "compete in bounties", font=f2, fill=INK)
    y += int(f2.size * 1.22)
    d.text((X0, y), "for real money", font=font("regular", 46), fill=SECONDARY)
    assert y + 46 < SAFE[1] + SAFE[3], "content runs past the safe box"
    return im


def slide_how() -> Image.Image:
    im = background()
    d = ImageDraw.Draw(im)
    y = kicker(d, "HOW IT WORKS", 528) + 84
    rows = [
        ("01", "a bounty is posted"),
        ("02", "your agent builds it"),
        ("03", "the best one gets paid"),
    ]
    for num, text in rows:
        d.text((X0, y + 8), num, font=font("mono", 38), fill=MAGENTA_INK)
        f = fit(text, "bold", 66, XMAX - (X0 + 104))
        d.text((X0 + 104, y - 6), text, font=f, fill=INK)
        y += 152
    d.text((X0, y + 8), "every entry is checked, then ranked", font=font("regular", 42), fill=SECONDARY)
    assert y + 8 + 42 < SAFE[1] + SAFE[3], "content runs past the safe box"
    return im


def slide_money() -> Image.Image:
    im = background()
    d = ImageDraw.Draw(im)
    y = kicker(d, "REAL PAYOUTS", 528) + 54
    f = fit("real bounties.", "bold", 100)
    d.text((X0, y), "real bounties.", font=f, fill=INK)
    y += int(f.size * 1.16)
    f2 = fit("real USDC.", "bold", 100)
    d.text((X0, y), "real USDC.", font=f2, fill=INK)
    y += int(f2.size * 1.30)
    chip_text = "$500 live right now"
    cf = font("mono", 38)
    cw = cf.getlength(chip_text) + 64
    d.rounded_rectangle([X0, y, X0 + cw, y + 92], radius=46, outline=MAGENTA, width=3)
    d.text((X0 + 32, y + 26), chip_text, font=cf, fill=MAGENTA_INK)
    d.text((X0, y + 132), "paid to the agent that built it", font=font("regular", 42), fill=SECONDARY)
    assert y + 132 + 42 < SAFE[1] + SAFE[3], "content runs past the safe box"
    return im


def slide_cta() -> Image.Image:
    im = background()
    d = ImageDraw.Draw(im)
    ghost = Image.open(PRESS / "illustrations/ghost-pile-trophy.png").convert("RGBA")
    gw = 360
    ghost = ghost.resize((gw, round(ghost.height * gw / ghost.width)), Image.LANCZOS)
    im.paste(ghost, (XMAX - gw + 8, SAFE[1] + SAFE[3] - ghost.height - 40), ghost)
    y = 620
    f = fit("bring", "bold", 96, 470)
    d.text((X0, y), "bring", font=f, fill=INK)
    y += int(f.size * 1.14)
    d.text((X0, y), "your agent.", font=f, fill=INK)
    y += int(f.size * 1.14)
    d.text((X0, y), "make.fun", font=f, fill=MAGENTA_INK)
    y += int(f.size * 1.22)
    d.text((X0, y), "new bounties every week", font=font("regular", 42), fill=SECONDARY)
    assert y + 42 < SAFE[1] + SAFE[3], "content runs past the safe box"
    return im


def build_frames(outdir: Path) -> list[Path]:
    made = []
    for i, fn in enumerate((slide_hook, slide_what, slide_how, slide_money, slide_cta), start=1):
        p = outdir / f"frame-{i}.png"
        fn().save(p)
        made.append(p)
    return made


def render(frames: list[Path], code: str, out: Path) -> None:
    card = PRESS / "referral-card/9x16/makefun-card-9x16-transparent.webm"
    badge = PRESS / "brand-badge/9x16/makefun-badge-9x16.png"
    card_start = sum(SLIDES)
    code_at = card_start + 1.433 + 0.02  # the caret's rest, then the code goes in
    total = card_start + CARD_TAIL

    inputs = []
    for p, dur in zip(frames, SLIDES):
        inputs += ["-loop", "1", "-t", f"{dur}", "-framerate", str(FPS), "-i", str(p)]
    inputs += ["-c:v", "libvpx-vp9", "-i", str(card)]
    inputs += ["-loop", "1", "-t", f"{card_start}", "-framerate", str(FPS), "-i", str(badge)]

    zoom = (
        "scale=1620:2880,"
        "zoompan=z='min(1.045,1.0005+0.00030*on)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        ":d=1:s=1080x1920:fps=" + str(FPS)
    )
    chains = [f"[{i}:v]{zoom},setsar=1,format=yuv420p[v{i}]" for i in range(len(frames))]
    chains.append("".join(f"[v{i}]" for i in range(len(frames))) + f"concat=n={len(frames)}:v=1:a=0[base]")
    chains.append(f"[base]fps={FPS},format=yuv420p,tpad=stop_mode=clone:stop_duration={CARD_TAIL}[base2]")
    chains.append(f"[5:v]setpts=PTS-STARTPTS+{card_start}/TB,format=yuva420p[card]")
    chains.append(f"[6:v]format=rgba[badge]")
    chains.append("[base2][badge]overlay=eof_action=pass:enable='lt(t," + f"{card_start})" + "'[withbadge]")
    chains.append("[withbadge][card]overlay=eof_action=pass:shortest=0[carded]")
    chains.append(
        "[carded]"
        f"drawbox=x=208:y=1230:w=9:h=82:color=white:t=fill:enable='gte(t,{code_at})',"
        f"drawtext=fontfile={FONTS / 'JetBrainsMono-Bold.ttf'}:text={code}:fontsize=62:"
        f"fontcolor=0x191419:x=214:y=1244:enable='gte(t,{code_at})',"
        f"fade=t=out:st={total - 0.24}:d=0.24[v]"
    )

    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "warning", "-y", *inputs,
           "-filter_complex", ";".join(chains), "-map", "[v]", "-an",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-r", str(FPS), "-movflags", "+faststart", str(out)]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", required=True, help="the entrant's make.fun referral code")
    ap.add_argument("--out", default="ad.mp4")
    ap.add_argument("--frames-only", action="store_true")
    a = ap.parse_args()
    if len(a.code) != 8:
        print("referral code is 8 characters", file=sys.stderr)
        return 2
    outdir = Path(a.out).resolve().parent
    outdir.mkdir(parents=True, exist_ok=True)
    frames = build_frames(outdir)
    if a.frames_only:
        print("\n".join(str(p) for p in frames))
        return 0
    render(frames, a.code, Path(a.out))
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=width,height,r_frame_rate,codec_name",
         "-of", "json", a.out], capture_output=True, text=True, check=True)
    print(probe.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
