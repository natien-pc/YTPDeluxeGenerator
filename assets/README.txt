Assets folder structure and usage for YTP Deluxe Generator — Legacy

Create the following subfolders inside the project assets/ folder:

assets/
  sounds/            <- old system sounds, beeps, error sounds (wav/mp3/ogg)
  images/            <- generic images, PNG/JPG/GIF used for overlays or memes
  errors/            <- old OS error dialog screenshots / images
  adverts/           <- old overlay adverts / banners
  overlays_videos/   <- short overlay videos / animated GIF converted to short mp4

Suggested filenames (examples only):
  sounds/os_beep.wav
  sounds/os_error.wav
  images/meme_overlay.png
  errors/error_winxp.png
  adverts/advert_2009.png
  overlays_videos/overlay_loop_2009.mp4

Usage:
- If you leave GUI asset fields empty, the engine will automatically pick appropriate assets from the assets/ subfolders.
- Avoid very large assets; keep overlays small (under a few megabytes) to reduce processing time on legacy machines.

Do NOT include copyrighted OS files in public repositories.