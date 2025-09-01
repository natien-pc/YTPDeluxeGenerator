# YTP Deluxe Generator — Legacy Update (Assets, Beta Key, Auto YTP, 2009/2012 Modes)

This update extends the original "YTP Deluxe Generator (Legacy)" with legacy-friendly features and scaffolding so you can run on older Windows (XP / Vista / 7) and older Python (2.7 / 3.x). It adds:

- Beta key handling (simple legacy-style key file).
- Assets folder guidance for old OS sounds/images/error-message-style overlays and advert overlays.
- New "2009 mode" and "2012 mode" presets (old-era look & transforms).
- Preview 2: alternate preview mode that shows a fast low-res preview with extra effects.
- Automatic YTP generation: batch/generate many randomized outputs (requires beta key unlock).
- GUI updates: fields for beta key, assets, mode toggles, Auto Generate button and Preview 2 button.
- Updated config sample for the new fields.

Important: This repository does not ship copyrighted OS images or sounds. The assets directory contains guidance and placeholder names — put your own legacy OS sounds, error message images, old adverts, and other media into the assets folder.

Quick start
1. Put ffmpeg.exe (and ffplay.exe if you want preview) in the project directory or on PATH.
2. Put Python 2.7 (recommended for XP) or Python 3.x on your machine.
3. Place your legacy assets (PNG/JPG/GIF images and WAV/MP3 sounds) into the `assets/` folder (see assets/README.txt).
4. Create a file named `beta_key.txt` in the project directory containing your beta key (format: OLD-...).
   - Auto-generation is locked unless a valid key is present.
   - For testing you can use a key that starts with `OLD-` (the validator accepts keys that start with `OLD-`).
5. Run:
   - python main.py
6. Use the GUI: pick input video, choose output, set mode (2009/2012), toggle effects or click "Auto Generate" (if beta key valid). Use "Preview 2" to quickly inspect a low-res effect sample.

Notes for old systems
- Use small clips when testing.
- Use `-preset ultrafast` to reduce CPU load.
- If libx264 or aac is missing, the engine provides fallbacks in comments; edit engine.py if necessary.
- Preview uses ffplay; if unavailable, engine prints instructions to open the file manually.

Files updated in this release
- main.py — GUI with beta key, auto-generate and mode toggles, Preview 2.
- engine.py — new 2009/2012 modes, preview2, auto-generate, beta-check integration.
- utils.py — beta key helpers and asset helpers.
- config_sample_updated.json — example settings including new options.
- assets/README.txt — where to put your old OS sounds/images and naming guidance.

If you'd like, I can:
- Add an optional "legacy-mode" batch (.bat) that picks safe codecs for very old ffmpeg builds.
- Add a script that scans a folder of assets and validates compatibility (image formats, audio sample rates).
- Add a small installer or packaged ZIP optimized for XP-era machines.

What's next: I updated the code in this message so you can drop these files into your project folder and test immediately. Below are the updated files.
```
