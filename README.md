```markdown
# YTP Deluxe Generator — Legacy Complete Update

This update packages a retro-friendly YouTube Poop (YTP) generator that targets old Windows (XP / Vista / 7) and older Python (2.7 recommended, Python 3.4–3.7 will also work). It aims to be compatible with older FFmpeg builds by using simple sequential commands, fallbacks, and small temporary files.

What's included in this update
- Full Tkinter GUI (main.py) with:
  - Per-effect toggles, probability and level fields (common options)
  - Beta-key support (legacy-style `beta_key.txt`)
  - Asset browsing and automatic asset discovery in `assets/` subfolders
  - Preview and Preview 2 (fast low-res preview)
  - Auto-generate batch feature (requires a valid beta key)
- Engine (engine.py) implementing all requested effects:
  - Random Sound overlay
  - Reverse (video + audio)
  - Speed up / Slow down (setpts + atempo with chain support)
  - Chorus (aecho approximation)
  - Vibrato / Pitch bend (asetrate + atempo approximation)
  - Stutter loop
  - Earrape (large gain)
  - Auto-tune placeholder (external tool integration)
  - Dance & Squidward mode (video transforms)
  - Invert colors
  - Rainbow overlay (user-provided PNG/GIF/JPG)
  - Mirror mode
  - Sus effect (random pitch/tempo)
  - Explosion spam (repeated overlays)
  - Frame shuffle (simple implementation via frames on disk)
  - Meme injection (image/audio)
  - Sentence mixing / random clip shuffle / random cuts
- Asset folder guidance and automatic picking:
  - assets/sounds/
  - assets/images/
  - assets/errors/
  - assets/adverts/
  - assets/overlays_videos/
- Fallbacks for older FFmpeg builds (mpeg4/libmp3lame) where libx264/aac are unavailable.
- A simple legacy batch file to run on old Windows (run_legacy.bat).

How to use (short)
1. Put ffmpeg.exe and ffplay.exe (optional) into the project folder or add them to PATH.
2. Place your assets (small PNGs, JPGs, GIFs, WAV/MP3, short MP4 overlays) into the corresponding assets/ subfolders.
3. Create a `beta_key.txt` with a legacy key like `OLD-MY-KEY-2009` to unlock Auto-Generate.
4. Run:
   - python main.py
5. Select input, choose effects and assets, then Generate. Use Preview 2 on short clips to check heavy effects quickly.

Notes & compatibility
- Designed to work with older FFmpeg by doing multiple sequential commands instead of complex filtergraphs.
- Avoid running on very long source files during testing — try 5–10 second clips first.
- Auto-tune is left as a placeholder; integrate an external autotune binary by adjusting engine._autotune_placeholder.

If you want I can:
- Produce a ready-to-run ZIP for Windows XP (with a small HowTo text and a sample assets pack of free-to-use images).
- Add a local key-generation tool to create signed keys that the engine will accept offline.

Now the key project files follow.
```