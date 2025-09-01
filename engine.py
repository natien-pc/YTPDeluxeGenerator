from __future__ import print_function, unicode_literals
import os
import random
import shutil
import tempfile
import math
from utils import find_ffmpeg, temp_filename_for, run_command, rm_f, read_beta_key_from_file, is_valid_beta_key, find_assets_dir, list_asset_files

# Extended engine with legacy-friendly presets & auto-generation support.

class YTPEngine(object):
    def __init__(self, ffmpeg_path=None, ffplay_path=None, work_dir=None):
        ffmpeg, ffplay = find_ffmpeg()
        self.ffmpeg = ffmpeg_path or ffmpeg
        self.ffplay = ffplay_path or ffplay
        if not self.ffmpeg:
            raise EnvironmentError("ffmpeg executable not found. Place ffmpeg.exe on PATH or next to the script.")
        if not work_dir:
            work_dir = os.path.join(os.getcwd(), 'ytp_temp')
        self.work_dir = work_dir
        if not os.path.exists(self.work_dir):
            os.makedirs(self.work_dir)
        # load assets if present
        self.assets_dir = find_assets_dir()
        self.asset_index = list_asset_files(self.assets_dir) if self.assets_dir else {}

    def cleanup(self):
        rm_f(self.work_dir)

    def _next_tmp(self, ext):
        return temp_filename_for(ext)

    def _probe_duration(self, path):
        # Minimal probe using ffmpeg -i and parsing output
        cmd = [self.ffmpeg, '-i', path]
        try:
            import subprocess, re
            p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            out, err = p.communicate()
            text = (err or b'').decode('utf-8', errors='ignore') + (out or b'').decode('utf-8', errors='ignore')
            m = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', text)
            if m:
                h, mm, ss = m.groups()
                return int(h) * 3600 + int(mm) * 60 + float(ss)
        except Exception:
            pass
        return 0.0

    def generate(self, input_video, output_path, options):
        # options is a dict: includes new keys 'mode_2009', 'mode_2012', 'beta_key', 'auto' etc.
        working = os.path.abspath(self.work_dir)
        if not os.path.exists(working):
            os.makedirs(working)

        current = input_video

        # Optional automatic sentence mix / random cuts
        if options.get('sentence_mix', {}).get('enabled'):
            current = self._sentence_mix(current, options)

        # Apply legacy-era mode presets early if requested
        if options.get('mode_2009'):
            current = self._mode_2009(current, options)
        if options.get('mode_2012'):
            current = self._mode_2012(current, options)

        # Then existing individual effects (preserve previous logic)
        if options.get('reverse', {}).get('enabled') and random.random() <= options['reverse'].get('prob', 1.0):
            current = self._reverse(current)

        if options.get('speed', {}).get('enabled') and random.random() <= options['speed'].get('prob', 1.0):
            lvl = options['speed'].get('level', 1.0)
            current = self._change_speed(current, lvl)

        if options.get('stutter', {}).get('enabled') and random.random() <= options['stutter'].get('prob', 1.0):
            current = self._stutter(current, options['stutter'].get('level', 1))

        if options.get('earrape', {}).get('enabled') and random.random() <= options['earrape'].get('prob', 1.0):
            current = self._earrape(current, options['earrape'].get('level', 20.0))

        if options.get('chorus', {}).get('enabled') and random.random() <= options['chorus'].get('prob', 1.0):
            current = self._chorus(current, options['chorus'].get('level', 0.6))

        if options.get('vibrato', {}).get('enabled') and random.random() <= options['vibrato'].get('prob', 1.0):
            current = self._vibrato(current, options['vibrato'].get('level', 1.05))

        if options.get('invert', {}).get('enabled') and random.random() <= options['invert'].get('prob', 1.0):
            current = self._invert_colors(current)

        if options.get('mirror', {}).get('enabled') and random.random() <= options['mirror'].get('prob', 1.0):
            current = self._mirror(current)

        # Overlays using provided assets or assets directory
        if options.get('rainbow', {}).get('enabled') and random.random() <= options['rainbow'].get('prob', 1.0):
            overlay_path = options['rainbow'].get('asset') or self._pick_asset(['.png', '.gif', '.jpg'])
            if overlay_path:
                current = self._overlay_image(current, overlay_path, x=0, y=0, opacity=options['rainbow'].get('opacity', 0.8))

        if options.get('explosion', {}).get('enabled') and random.random() <= options['explosion'].get('prob', 1.0):
            overlay_path = options['explosion'].get('asset') or self._pick_asset(['.png', '.gif', '.jpg'])
            if overlay_path:
                current = self._explosion_spam(current, overlay_path, count=options['explosion'].get('count', 5))

        if options.get('frame_shuffle', {}).get('enabled') and random.random() <= options['frame_shuffle'].get('prob', 1.0):
            current = self._frame_shuffle(current, options['frame_shuffle'].get('level', 10))

        if options.get('meme', {}).get('enabled') and random.random() <= options['meme'].get('prob', 1.0):
            img = options['meme'].get('image') or self._pick_asset(['.png', '.jpg', '.gif'])
            if img:
                current = self._overlay_image(current, img, x='(main_w-overlay_w)/2', y='(main_h-overlay_h)-10')

        if options.get('random_sound', {}).get('enabled') and random.random() <= options['random_sound'].get('prob', 1.0):
            audio_asset = options['random_sound'].get('asset') or self._pick_asset(['.wav', '.mp3', '.ogg', '.aac'])
            if audio_asset:
                current = self._add_random_sound(current, audio_asset, options['random_sound'].get('count', 3))

        # Final encode: try libx264/aac, but for very old ffmpeg use mpeg4/mp3 fallback (uncomment if needed)
        final_cmd = [self.ffmpeg, '-y', '-i', current, '-c:v', 'libx264', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '192k', output_path]
        if not run_command(final_cmd):
            # Fallback for older ffmpeg builds without libx264/aac
            final_cmd2 = [self.ffmpeg, '-y', '-i', current, '-c:v', 'mpeg4', '-qscale:v', '5', '-c:a', 'libmp3lame', '-b:a', '192k', output_path]
            run_command(final_cmd2)
        return output_path

    # Auto-generate many YTPs (requires beta key)
    def auto_generate(self, input_video, out_dir, base_options, count=5, beta_key=None):
        # Validate beta key
        bkey = beta_key or read_beta_key_from_file()
        if not bkey or not is_valid_beta_key(bkey):
            raise EnvironmentError("Auto-generation requires a valid legacy beta key (place in beta_key.txt or pass in).")
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        generated = []
        for i in range(1, int(count) + 1):
            opts = self._randomize_options(base_options)
            out_path = os.path.join(out_dir, 'ytp_auto_%03d.mp4' % i)
            print("Auto-generate #%d -> %s" % (i, out_path))
            self.generate(input_video, out_path, opts)
            generated.append(out_path)
        return generated

    def preview(self, output_file):
        if self.ffplay:
            cmd = [self.ffplay, '-autoexit', output_file]
            run_command(cmd)
        else:
            print("ffplay not found. Open the file manually:", output_file)

    # Quick alternate preview that applies a low-res heavy-preview effect and plays it (Preview 2)
    def preview2(self, input_path, seconds=6):
        # Create a quick low-res preview with film-grain-ish effect and heavy compression for speed
        tmp = temp_filename_for('mp4')
        try:
            vf = "scale=480:-2,format=yuv420p,eq=contrast=1.1:brightness=0.02:saturation=1.2"
            af = "volume=1.0"
            cmd = [self.ffmpeg, '-y', '-t', str(seconds), '-i', input_path, '-vf', vf, '-af', af, '-c:v', 'libx264', '-preset', 'ultrafast', tmp]
            if not run_command(cmd):
                cmd2 = [self.ffmpeg, '-y', '-t', str(seconds), '-i', input_path, '-vf', vf, '-af', af, '-c:v', 'mpeg4', '-qscale:v', '5', tmp]
                run_command(cmd2)
            # play it
            self.preview(tmp)
        finally:
            rm_f(tmp)

    # ------------------ Implementations of new legacy presets ------------------
    def _mode_2009(self, input_path, options):
        # 2009 mode: emulate older web-era look: heavy compression artifacts, stronger saturation, watermark/ad overlay
        out = temp_filename_for('mp4')
        overlay = options.get('assets', {}).get('2009_ad') or self._pick_asset(['.png', '.jpg', '.gif'])
        # Use crop/scale + eq + noise
        vf = "scale=640:-2,eq=contrast=1.2:brightness=0.02:saturation=1.4,format=yuv420p"
        if overlay:
            fc = "[0][1]overlay=5:5"
            cmd = [self.ffmpeg, '-y', '-i', input_path, '-i', overlay, '-vf', vf + ',' + "overlay=5:5", '-c:v', 'libx264', '-preset', 'veryfast', '-c:a', 'copy', out]
        else:
            cmd = [self.ffmpeg, '-y', '-i', input_path, '-vf', vf, '-c:v', 'libx264', '-preset', 'veryfast', '-c:a', 'copy', out]
        if not run_command(cmd):
            # fallback to mpeg4
            cmd2 = [self.ffmpeg, '-y', '-i', input_path, '-vf', vf, '-c:v', 'mpeg4', '-qscale:v', '6', '-c:a', 'copy', out]
            run_command(cmd2)
        return out

    def _mode_2012(self, input_path, options):
        # 2012 mode: emulate early meme-era effects: stronger color crush, vignette-ish, slight shake
        out = temp_filename_for('mp4')
        # For older ffmpeg use simple filters: eq + curves-like via lut (simplified) + overlay if available
        vf = "scale=720:-2,eq=contrast=1.3:saturation=0.9,format=yuv420p"
        # Add a quick "shake" using transpose/jitter by alternating small crop offsets in a filter_complex is complex; keep simple
        cmd = [self.ffmpeg, '-y', '-i', input_path, '-vf', vf, '-c:v', 'libx264', '-preset', 'veryfast', '-c:a', 'copy', out]
        if not run_command(cmd):
            cmd2 = [self.ffmpeg, '-y', '-i', input_path, '-vf', vf, '-c:v', 'mpeg4', '-qscale:v', '6', '-c:a', 'copy', out]
            run_command(cmd2)
        return out

    # ------------------ Utility & existing effect methods (kept compatible) ------------------
    def _pick_asset(self, exts):
        if not self.asset_index:
            return None
        for e in exts:
            lst = self.asset_index.get(e)
            if lst:
                return random.choice(lst)
        # fallback try any
        for k, v in self.asset_index.items():
            if v:
                return random.choice(v)
        return None

    def _randomize_options(self, base):
        # Make a shallow copy and randomize a couple probabilities/levels for variety
        import copy
        opts = copy.deepcopy(base)
        # Random tweaks
        for k in opts:
            if isinstance(opts[k], dict):
                if 'prob' in opts[k]:
                    opts[k]['prob'] = max(0.0, min(1.0, random.random()))
                if 'level' in opts[k] and isinstance(opts[k]['level'], (int, float)):
                    jitter = 0.8 + random.random() * 0.8
                    opts[k]['level'] = opts[k]['level'] * jitter
        # Randomly enable a mode sometimes
        if random.random() < 0.3:
            opts['mode_2009'] = True
        if random.random() < 0.2:
            opts['mode_2012'] = True
        return opts

    # (Existing effect functions from the original project) ...
    # For brevity, the existing effect implementations (_sentence_mix, _reverse, _change_speed, _build_atempo_chain,
    # _stutter, _earrape, _chorus, _vibrato, _invert_colors, _mirror, _dance_mode, _overlay_image,
    # _explosion_spam, _frame_shuffle, _add_random_sound) are assumed present and compatible with the earlier engine.py.
    # If you want the full implementations re-included here, tell me and I'll paste them verbatim.