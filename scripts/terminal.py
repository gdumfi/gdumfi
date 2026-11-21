# Renders assets/terminal.gif: a static retro-terminal session (no network, no API).
#
# Run from the repo root:
#   pip install -r scripts/requirements.txt
#   python scripts/terminal.py
#
# Requires ffmpeg on PATH (or `pip install imageio-ffmpeg`, used as a fallback).
# gifos reads its config from ~/.config/gifos, so the script points HOME at a
# temp dir holding scripts/gifos_settings.toml and scripts/ansi_escape_colors.toml
# (the "mono" gray-only scheme). Frames are rendered in that temp dir and removed.
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "assets" / "terminal.gif"

if not shutil.which("ffmpeg"):
    try:
        import imageio_ffmpeg
    except ImportError:
        sys.exit("ffmpeg not found: install it or `pip install imageio-ffmpeg`")
    bindir = tempfile.mkdtemp(prefix="ffbin_")
    os.symlink(imageio_ffmpeg.get_ffmpeg_exe(), os.path.join(bindir, "ffmpeg"))
    os.environ["PATH"] = bindir + os.pathsep + os.environ["PATH"]

work = Path(tempfile.mkdtemp(prefix="gifos_"))
cfg = work / "home" / ".config" / "gifos"
cfg.mkdir(parents=True)
for name in ("gifos_settings.toml", "ansi_escape_colors.toml"):
    shutil.copy(HERE / name, cfg / name)
os.environ["HOME"] = str(work / "home")
os.chdir(work)  # gifos writes ./frames and ./output.gif relative to cwd

import gifos  # noqa: E402  (must be imported after HOME/cwd are set)

PROMPT = "\x1b[1;97mgdumfi@github\x1b[0m:\x1b[0;37m~\x1b[0m$ "
W = 720
t = gifos.Terminal(W, 480, 14, 12)
t.set_prompt(PROMPT)
t.set_fps(15)

row = 1


def out(lines):
    """Print output lines below the current row."""
    global row
    if isinstance(lines, str):
        lines = [lines]
    for ln in lines:
        t.gen_text(ln, row, count=2)
        row += 1


def command(cmd, result, pause=12):
    global row
    t.gen_prompt(row, count=6)
    t.gen_typing_text(cmd, row, contin=True, speed=1)
    t.clone_frame(6)
    row += 1
    out(result)
    t.clone_frame(pause)


try:
    # 1. BIOS-style boot
    out("GDUMFI BIOS v2.6  (C) 2026")
    for kb in (4096, 16384):
        out(f"Memory test: {kb:>5}K OK")
    out("Storage check: OK")
    out("Booting...")
    t.clone_frame(15)
    t.clear_frame()
    row = 1

    # 2-7. Session
    command("whoami", "full-stack developer \u00b7 infosec student")
    command("cat about.txt", [
        "- 5th-year information security student",
        "- security research: static & taint analysis, symbolic execution",
        "  (KLEE) of smart contracts",
        "- secure CI: secret scanning, SCA, container scanning, CodeQL,",
        "  pinned actions",
        "- spec -> production: CI/CD, monitoring, tested restores",
        "- commercial VPN service under NDA",
    ], pause=30)
    command("ls stack/", [
        "security:      gitleaks osv-scanner trivy codeql klee taint-analysis",
        "               symbolic-execution",
        "languages:     typescript go python rust c++ c# dart solidity bash",
        "backend:       node.js nestjs next.js fastify fastapi prisma grpc openapi",
        "frontend&apps: react vue.js vite tailwind-css flutter telegram-mini-apps",
        "data:          postgresql redis meilisearch sqlite duckdb polars",
        "devops:        docker nginx github-actions linux caddy yandex-cloud",
        "observability: prometheus grafana sentry opentelemetry",
    ], pause=45)
    command("echo $YEAR_2026", "~4,000 commits \u00b7 6,000+ tests", pause=15)

    # 8. Final prompt, blinking cursor
    t.gen_prompt(row, count=60)
    t.gen_gif()
    OUT.parent.mkdir(exist_ok=True)
    shutil.move(str(work / "output.gif"), OUT)
    print(f"Wrote {OUT}")
finally:
    os.chdir(HERE)
    shutil.rmtree(work, ignore_errors=True)
