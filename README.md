# YTP Deluxe Generator — Legacy Complete Update (Assets, Effects, Beta Key)

A retro-friendly YouTube Poop (YTP) generator targeted at older Windows (XP / Vista / 7) and legacy Python (2.7 recommended; Python 3.4–3.7 workable). This release collects the full feature set, improved asset-folder scanning, per-effect toggles with probability and level, legacy-mode presets (2009 / 2012), a quick low-res Preview 2, and an Auto-Generate batch gated by a simple legacy beta key.

This project expects a working ffmpeg.exe (and optionally ffplay.exe) in PATH or in the project folder. It intentionally uses simple sequential ffmpeg calls and fallbacks (mpeg4 / libmp3lame) so it will run on older static FFmpeg builds.

Key features
- Effects implemented or scaffolded:
  - Random Sound overlay (audio)
  - Reverse clip (video + audio)
  - Speed up / Slow down (setpts + atempo with chain support)
  - Chorus (approx via aecho)
  - Vibrato / Pitch bend (asetrate + atempo approximation)
  - Stutter loop
  - Earrape Mode (large gain)
  - Auto-Tune Chaos (placeholder — external autotune tool required)
  - Dance & Squidward mode (video transforms)
  - Invert colors
  - Rainbow / Meme overlay (user-provided or auto-picked from assets/)
  - Mirror Mode
  - Sus Effect (random pitch/tempo)
  - Explosion Spam (repetitive overlays)
  - Frame Shuffle (simple sample implementation)
  - Meme Injection (image/audio mix)
  - Sentence Mixing / Random clip shuffle / Random cuts
- Per-effect toggles, probability (0.0–1.0), and a level/value field
- Asset discovery and auto-pick from structured assets/ subfolders:
  - assets/sounds/, assets/images/, assets/errors/, assets/adverts/, assets/overlays_videos/, assets/dance_sounds/
- Legacy-mode presets: 2009 Mode (web-era look) and 2012 Mode (meme-era look)
- Preview (play output with ffplay) and Preview 2 (fast low-res sample with heavy effect)
- Auto-Generate batch (requires legacy beta key in beta_key.txt or entered in GUI)
- Small run_legacy.bat for one-click launching on old Windows

Quick start
1. Put ffmpeg.exe (and optionally ffplay.exe) in the project folder or on PATH.
2. Put Python 2.7 (best for XP) or Python 3.4–3.7 on the machine.
3. Create the assets folder with recommended subfolders (see assets/README.txt).
4. Create a file `beta_key.txt` with a legacy key such as `OLD-MY-KEY-2009` to enable Auto-Generate.
5. Run:
   python main.py
6. Use the GUI to:
   - Pick input and output.
   - Toggle effects, click "Configure Effects" to set per-effect probability and level.
   - Use Preview 2 to check heavy effects quickly.
   - Use Auto-Generate to create many randomized YTPs (beta key required).

Compatibility notes and tips
- Test on short clips (5–15 seconds) first.
- Use `-preset ultrafast` or `-preset veryfast` for faster encodes on weak CPUs.
- If libx264/aac aren't available in your ffmpeg build, the engine attempts fallback to mpeg4/libmp3lame.
- Some filters may be missing from extremely old ffmpeg builds; fallback options or removing that effect helps.
- The Auto-Tune feature is a placeholder. To integrate autotune, point the engine at an external autotune binary/tool and add command-line invocation.

Files provided
- main.py — Tkinter GUI with effect controls and asset browsing
- engine.py — effect implementations and FFmpeg command orchestration
- utils.py — helpers (ffmpeg detection, temp files, beta-key validator, asset listing)
- assets/README.txt — how to structure assets/ and recommended filenames
- run_legacy.bat — small convenience script to run the GUI on older Windows

If you want, I can create:
- a ZIP with a tiny public-domain assets pack for testing,
- a pure-batch non-GUI script that runs a safe legacy-only pipeline,
- or add a tiny offline key-generator that emits keys your engine will accept.

```
