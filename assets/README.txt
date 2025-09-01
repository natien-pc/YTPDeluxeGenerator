Assets folder structure (recommended) for YTP Deluxe Generator — Legacy

Create the following subfolders inside the project assets/ folder:

assets/
  sounds/            <- old system sounds, beeps, error sounds (wav/mp3/ogg)
  dance_sounds/      <- short dance or meme sounds (wav/mp3)
  images/            <- generic images, PNG/JPG/GIF used for overlays
  errors/            <- OS error dialog screenshots / images
  adverts/           <- old overlay adverts / banners (PNG/JPG)
  overlays_videos/   <- short overlay videos / animated GIF converted to short mp4

Suggested filenames:
  sounds/os_beep.wav
  sounds/os_error.wav
  dance_sounds/dance_loop.wav
  images/meme_overlay.png
  errors/error_winxp.png
  adverts/advert_2009.png
  overlays_videos/overlay_loop_2009.mp4

Usage:
- If GUI asset fields are empty, engine will auto-pick appropriate items from these folders.
- Keep assets small (< a few MB) to reduce processing time on legacy PCs.
- Do not include copyrighted OS images in public repos.
