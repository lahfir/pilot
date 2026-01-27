"""
Brand banner rendering for the terminal UI.

This module renders the PILOT wordmark optimized for dark terminal backgrounds.
It includes an optional glitch-style intro animation that resolves into the
final crisp wordmark.
"""

from __future__ import annotations

import random
import time
from typing import List, Sequence

from rich.console import Console, Group
from rich.live import Live
from rich.text import Text

from ..state import VerbosityLevel
from ..theme import THEME


_NOISE_CHARS = "░▒▓█╳╱╲─═·*+"


def get_wordmark_lines() -> List[str]:
    """
    Return the PILOT wordmark lines.

    The LOT portion forms a front-view aircraft silhouette:
    - L: left wing root and fuselage strut
    - O: cockpit with two window eyes (front view)
    - T: right wing root and fuselage strut

    Returns:
        A list of strings representing the banner wordmark.
    """
    banner = [
        "██████╗ ██╗██╗         ██████████████╗  ████████╗",
        "██╔══██╗██║██║       ██╔════════════╗██ ╚══██╔══╝",
        "██████╔╝██║██║     ██╔╝              ╚██╗  ██║   ",
        "██╔═══╝ ██║██║     ██║  ████╗  ████╗  ██║  ██║   ",
        "██║     ██║███████╗██║  ████║  ████║  ██║  ██║   ",
        "╚═╝     ╚═╝╚══════╝╚═╝  ╚═══╝  ╚═══╝  ╚═╝  ╚═╝   ",
    ]
    return banner


def _center_lines(lines: Sequence[str], width: int) -> List[str]:
    """
    Center lines to the current terminal width.

    Args:
        lines: Lines to center
        width: Terminal width

    Returns:
        Centered lines
    """
    art_width = max((len(line) for line in lines), default=0)
    padding = max(0, (width - art_width) // 2)
    pad_str = " " * padding
    return [pad_str + line for line in lines]


def _style_wordmark_lines(lines: Sequence[str], width: int) -> List[Text]:
    """
    Convert wordmark lines into Rich Text with flat, high-contrast colors.

    Args:
        lines: Wordmark lines
        width: Terminal width

    Returns:
        Styled Rich Text lines
    """
    base = THEME.get("header", "#ffffff")
    cockpit = THEME.get("output", "#00ccff")
    eye = THEME.get("header", "#ffffff")

    centered = _center_lines(lines, width)
    styled: List[Text] = []

    cockpit_frame_chars = set("╭╮╰╯│├┤")
    for line in centered:
        t = Text()
        for ch in line:
            if ch == "◉":
                t.append(ch, style=f"bold {eye}")
            elif ch in cockpit_frame_chars:
                t.append(ch, style=f"bold {cockpit}")
            else:
                t.append(ch, style=f"bold {base}" if ch.strip() else base)
        styled.append(t)
    return styled


def _glitch_frame(
    final_lines: Sequence[str],
    corruption: float,
    rng: random.Random,
) -> List[str]:
    """
    Create a glitched variant of the final lines.

    Args:
        final_lines: Target final lines
        corruption: Value in [0, 1], where 1 is maximum corruption
        rng: Random generator

    Returns:
        A list of glitched lines.
    """
    if corruption <= 0:
        return list(final_lines)

    lines: List[str] = []
    jitter = 0
    if corruption >= 0.55:
        jitter = rng.choice([-2, -1, 0, 1, 2])
    elif corruption >= 0.25:
        jitter = rng.choice([-1, 0, 1])

    replace_p = min(0.55, 0.10 + (corruption * 0.45))
    space_p = min(0.30, corruption * 0.25)

    for line in final_lines:
        out_chars: List[str] = []
        for ch in line:
            if ch == " ":
                if rng.random() < space_p:
                    out_chars.append(rng.choice(_NOISE_CHARS))
                else:
                    out_chars.append(" ")
                continue
            if rng.random() < replace_p:
                out_chars.append(rng.choice(_NOISE_CHARS))
            else:
                out_chars.append(ch)
        out = "".join(out_chars)
        if jitter < 0:
            out = out[(-jitter):] + (" " * (-jitter))
        elif jitter > 0:
            out = (" " * jitter) + out[: max(0, len(out) - jitter)]
        lines.append(out)
    return lines


def _build_banner_renderable(
    wordmark_lines: Sequence[str],
    width: int,
    tagline: str,
) -> Group:
    """
    Build a single renderable containing the wordmark and tagline.

    Args:
        wordmark_lines: Wordmark lines
        width: Terminal width
        tagline: Tagline text

    Returns:
        A Group renderable suitable for Live updates.
    """
    c_dim = THEME["hud_dim"]
    styled_lines = _style_wordmark_lines(wordmark_lines, width)
    tag_pad = max(0, (width - len(tagline)) // 2)
    tag = Text.from_markup(f"{' ' * tag_pad}[{c_dim}]{tagline}[/]")
    return Group(*styled_lines, Text(""), tag)


def print_banner(
    console: Console,
    verbosity: VerbosityLevel = VerbosityLevel.NORMAL,
    *,
    animate: bool = True,
) -> None:
    """
    Print the PILOT banner.

    Args:
        console: Rich console
        verbosity: Output verbosity level
        animate: If True, show glitch intro animation
    """
    if verbosity == VerbosityLevel.QUIET:
        return

    wordmark = get_wordmark_lines()
    width = console.width

    c_border = THEME["border"]
    console.print()
    console.print(Text.from_markup(f"[{c_border}]{'━' * width}[/]"))

    tagline = "AUTONOMOUS DESKTOP & WEB CONTROL"

    if not animate:
        renderable = _build_banner_renderable(wordmark, width, tagline)
        console.print(renderable)
        console.print()
        console.print(Text.from_markup(f"[{c_border}]{'━' * width}[/]"))
        return

    rng = random.Random(1337)
    frames = 14
    frame_time = 0.055

    with Live(
        _build_banner_renderable(_glitch_frame(wordmark, 1.0, rng), width, tagline),
        console=console,
        refresh_per_second=24,
        transient=False,
    ) as live:
        for i in range(frames):
            t = i / max(1, frames - 1)
            corruption = max(0.0, 1.0 - (t * t))
            glitched = _glitch_frame(wordmark, corruption, rng)
            live.update(_build_banner_renderable(glitched, width, tagline))
            time.sleep(frame_time)

    console.print()
    console.print(Text.from_markup(f"[{c_border}]{'━' * width}[/]"))
