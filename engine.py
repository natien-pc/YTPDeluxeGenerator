from __future__ import print_function, unicode_literals
import os
import random
import tempfile
import shutil
import re
from utils import find_ffmpeg, temp_filename_for, run_command, rm_f, read_beta_key_from_file, is_valid_beta_key, find_assets_dir, list_asset_files

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
        self.assets_dir = find_assets_dir()
        self.asset_index = list_asset_files(self.assets_dir) if self.assets_dir else {}

    def cleanup(self):
        rm_f(self.work_dir)

    def _pick_asset(self, exts):
        if not self.asset_index:
            return None
        for e in exts:
            lst = self.asset_index.get(e)
            if lst:
                return random.choice(lst)
        # fallback first available
        for k, v in self.asset_index.items():
            if v:
                return random.choice(v)
        return None

    def _probe_duration(self, path):
        try:
            cmd = [self.ffmpeg, '-i', path]
            p = __import__('subprocess').Popen(cmd, stdout=__import__('subprocess').PIPE, stderr=__import__('subprocess').PIPE)
            out, err = p.communicate()
            text = (err or b'').decode('utf-8', errors='ignore') + (out or b'').decode('utf-8', errors='ignore')
            m = re.search(r'Duration:\s*(\d+):(\d+):(\d+\.\d+)', text)
            if m:
                h, mm, ss = m.groups()
                return int(h) * 3600 + int(mm) * 60 + float(ss)
        except Exception:
            pass
        return 0.0

    # ---------------- Public API ----------------
    def generate(self, input_video, output_path, options):
        current = input_video

        # Sentence mixing
        if options.get('sentence_mix', {}).get('enabled'):
            current = self._sentence_mix(current, options.get('sentence_mix', {}))

        # Legacy presets
        if options.get('mode_2009'):
            current = self._mode_2009(current, options)
        if options.get('mode_2012'):
            current = self._mode_2012(current, options)

        # Individual effects
        if options.get('reverse', {}).get('enabled') and random.random() <= options['reverse'].get('prob', 1.0):
            current = self._reverse(current)

        if options.get('speed', {}).get('enabled') and random.random() <= options['speed'].get('prob', 1.0):
            current = self._change_speed(current, options['speed'].get('level', 1.0))

        if options.get('stutter', {}).get('enabled') and random.random() <= options['stutter'].get('prob', 1.0):
            current = self._stutter(current, options['stutter'].get('level', 2))

        if options.get('earrape', {}).get('enabled') and random.random() <= options['earrape'].get('prob', 1.0):
            current = self._earrape(current, options['earrape'].get('level', 16.0))

        if options.get('chorus', {}).get('enabled') and random.random() <= options['chorus'].get('prob', 1.0):
            current = self._chorus(current, options['chorus'].get('level', 0.6))

        if options.get('vibrato', {}).get('enabled') and random.random() <= options['vibrato'].get('prob', 1.0):
            current = self._vibrato(current, options['vibrato'].get('level', 1.03))

        if options.get('sus', {}).get('enabled') and random.random() <= options['sus'].get('prob', 1.0):
            current = self._sus_effect(current, options['sus'].get('level', 1.1))

        if options.get('invert', {}).get('enabled') and random.random() <= options['invert'].get('prob', 1.0):
            current = self._invert_colors(current)

        if options.get('mirror', {}).get('enabled') and random.random() <= options['mirror'].get('prob', 1.0):
            current = self._mirror(current)

        if options.get('dance', {}).get('enabled') and random.random() <= options['dance'].get('prob', 1.0):
            current = self._dance_mode(current)

        if options.get('rainbow', {}).get('enabled') and random.random() <= options['rainbow'].get('prob', 1.0):
            overlay_path = options['rainbow'].get('asset') or self._pick_asset(['.png', '.gif', '.jpg'])
            if overlay_path:
                current = self._overlay_image(current, overlay_path, x=options['rainbow'].get('x', 0), y=options['rainbow'].get('y', 0), opacity=options['rainbow'].get('opacity', 0.9))

        if options.get('explosion', {}).get('enabled') and random.random() <= options['explosion'].get('prob', 1.0):
            overlay_path = options['explosion'].get('asset') or self._pick_asset(['.png', '.gif', '.jpg'])
            if overlay_path:
                current = self._explosion_spam(current, overlay_path, count=options['explosion'].get('count', 4))

        if options.get('frame_shuffle', {}).get('enabled') and random.random() <= options['frame_shuffle'].get('prob', 1.0):
            current = self._frame_shuffle(current, options['frame_shuffle'].get('level', 8))

        if options.get('meme', {}).get('enabled') and random.random() <= options['meme'].get('prob', 1.0):
            img = options['meme'].get('image') or self._pick_asset(['.png', '.jpg', '.gif'])
            if img:
                current = self._overlay_image(current, img, x='(main_w-overlay_w)/2', y='(main_h-overlay_h)-10')

        if options.get('random_sound', {}).get('enabled') and random.random() <= options['random_sound'].get('prob', 1.0):
            audio_asset = options['random_sound'].get('asset') or self._pick_asset(['.wav', '.mp3', '.ogg', '.aac'])
            if audio_asset:
                current = self._add_random_sound(current, audio_asset, options['random_sound'].get('count', 3))

        # final encode with fallback
        out = output_path
        final_cmd = [self.ffmpeg, '-y', '-i', current, '-c:v', 'libx264', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '192k', out]
        if not run_command(final_cmd):
            final_cmd2 = [self.ffmpeg, '-y', '-i', current, '-c:v', 'mpeg4', '-qscale:v', '5', '-c:a', 'libmp3lame', '-b:a', '192k', out]
            run_command(final_cmd2)
        return out

    # ---------------- Core effects (compatible with older ffmpeg builds) ----------------
    def _sentence_mix(self, input_path, cfg):
        duration = self._probe_duration(input_path) or 6.0
        parts = int(cfg.get('parts', 6))
        piece_len = min(1.5, max(0.15, duration / max(1, parts * 2.0)))
        clips = []
        for i in range(parts):
            start = random.uniform(0, max(0.0, duration - piece_len))
            out = temp_filename_for('.mp4')
            cmd = [self.ffmpeg, '-y', '-ss', str(start), '-t', str(piece_len), '-i', input_path, '-c', 'copy', out]
            run_command(cmd)
            clips.append(out)
        concat_txt = temp_filename_for('.txt')
        try:
            with open(concat_txt, 'w') as f:
                for c in clips:
                    f.write("file '%s'\n" % c.replace("'", "'\\''"))
            out_all = temp_filename_for('.mp4')
            cmd = [self.ffmpeg, '-y', '-f', 'concat', '-safe', '0', '-i', concat_txt, '-c', 'copy', out_all]
            run_command(cmd)
        finally:
            for c in clips:
                rm_f(c)
            rm_f(concat_txt)
        return out_all

    def _reverse(self, input_path):
        out = temp_filename_for('.mp4')
        cmd = [self.ffmpeg, '-y', '-i', input_path, '-vf', 'reverse', '-af', 'areverse', out]
        if not run_command(cmd):
            # fallback: try reversing audio separately and video separately (less likely needed)
            return input_path
        return out

    def _build_atempo_chain(self, factor):
        try:
            f = float(factor)
        except Exception:
            f = 1.0
        if f == 1.0:
            return 'anull'
        parts = []
        remaining = f
        # atempo supports 0.5..2.0; chain factors
        while remaining > 2.0:
            parts.append('atempo=2.0')
            remaining /= 2.0
        while remaining < 0.5:
            parts.append('atempo=0.5')
            remaining /= 0.5
        parts.append('atempo=%s' % (remaining,))
        return ','.join(parts)

    def _change_speed(self, input_path, factor):
        out = temp_filename_for('.mp4')
        try:
            f = float(factor)
            if f <= 0:
                f = 1.0
        except Exception:
            f = 1.0
        setpts = 'setpts=%s*PTS' % (1.0 / f)
        atempo = self._build_atempo_chain(f)
        cmd = [self.ffmpeg, '-y', '-i', input_path, '-vf', setpts, '-af', atempo, out]
        run_command(cmd)
        return out

    def _stutter(self, input_path, level=2):
        duration = self._probe_duration(input_path) or 3.0
        seg_len = max(0.05, min(0.6, 0.1 * float(level)))
        start = random.uniform(0, max(0.0, duration - seg_len))
        seg = temp_filename_for('.mp4')
        cmd = [self.ffmpeg, '-y', '-ss', str(start), '-t', str(seg_len), '-i', input_path, '-c', 'copy', seg]
        run_command(cmd)
        loops = 2 + int(level)
        list_txt = temp_filename_for('.txt')
        try:
            with open(list_txt, 'w') as f:
                for i in range(loops):
                    f.write("file '%s'\n" % seg.replace("'", "'\\''"))
            out = temp_filename_for('.mp4')
            cmd = [self.ffmpeg, '-y', '-f', 'concat', '-safe', '0', '-i', list_txt, '-c', 'copy', out]
            run_command(cmd)
        finally:
            rm_f(list_txt)
            rm_f(seg)
        return out

    def _earrape(self, input_path, gain=20.0):
        out = temp_filename_for('.mp4')
        try:
            g = float(gain)
        except Exception:
            g = 20.0
        cmd = [self.ffmpeg, '-y', '-i', input_path, '-af', 'volume=%sdB' % (g,), out]
        run_command(cmd)
        return out

    def _chorus(self, input_path, level=0.6):
        out = temp_filename_for('.mp4')
        try:
            lev = float(level)
        except Exception:
            lev = 0.6
        d1 = int(30 + 400 * lev)
        d2 = int(90 + 500 * lev)
        decay1 = 0.4 + 0.3 * lev
        decay2 = 0.2 + 0.25 * lev
        aecho = "aecho=0.8:0.9:%d|%d:%.2f|%.2f" % (d1, d2, decay1, decay2)
        cmd = [self.ffmpeg, '-y', '-i', input_path, '-af', aecho, out]
        run_command(cmd)
        return out

    def _vibrato(self, input_path, level=1.03):
        out = temp_filename_for('.mp4')
        try:
            lev = float(level)
            if lev <= 0:
                lev = 1.03
        except Exception:
            lev = 1.03
        # approximate vibrato by changing sample rate then restoring tempo
        asetrate = 'asetrate=44100*%f' % (lev,)
        atempo = self._build_atempo_chain(1.0 / lev)
        af = "%s,%s" % (asetrate, atempo)
        cmd = [self.ffmpeg, '-y', '-i', input_path, '-af', af, '-c:v', 'copy', out]
        run_command(cmd)
        return out

    def _sus_effect(self, input_path, level=1.1):
        # Random pitch/tempo shifts to create "sus" playful effect
        tries = 2
        cur = input_path
        for i in range(tries):
            factor = 0.8 + random.random() * (level + 0.2)
            cur = self._change_speed(cur, factor)
        return cur

    def _invert_colors(self, input_path):
        out = temp_filename_for('.mp4')
        cmd = [self.ffmpeg, '-y', '-i', input_path, '-vf', 'negate', out]
        if not run_command(cmd):
            cmd2 = [self.ffmpeg, '-y', '-i', input_path, '-vf', "lutrgb='r=255-val:g=255-val:b=255-val'", out]
            run_command(cmd2)
        return out

    def _mirror(self, input_path):
        out = temp_filename_for('.mp4')
        cmd = [self.ffmpeg, '-y', '-i', input_path, '-vf', 'hflip', out]
        if run_command(cmd):
            return out
        return input_path

    def _dance_mode(self, input_path):
        out = temp_filename_for('.mp4')
        # simple rotate/scale/jitter approximation using transpose and scale
        cmd = [self.ffmpeg, '-y', '-i', input_path, '-vf', 'transpose=2,scale=iw*0.95:ih*0.95', out]
        if not run_command(cmd):
            cmd2 = [self.ffmpeg, '-y', '-i', input_path, '-vf', 'scale=iw*0.95:ih*0.95', out]
            run_command(cmd2)
        return out

    def _overlay_image(self, input_path, image_path, x=0, y=0, opacity=1.0):
        out = temp_filename_for('.mp4')
        try:
            if float(opacity) >= 0.99:
                cmd = [self.ffmpeg, '-y', '-i', input_path, '-i', image_path, '-filter_complex', 'overlay=%s:%s' % (x, y), out]
            else:
                # attempt with colorchannelmixer or blend fallback
                cmd = [self.ffmpeg, '-y', '-i', input_path, '-i', image_path,
                       '-filter_complex', "[1]format=rgba,colorchannelmixer=aa=%f[ol];[0][ol]overlay=%s:%s" % (opacity, x, y), out]
            run_command(cmd)
        except Exception:
            # simple overlay fallback
            cmd2 = [self.ffmpeg, '-y', '-i', input_path, '-i', image_path, '-filter_complex', 'overlay=0:0', out]
            run_command(cmd2)
        return out

    def _explosion_spam(self, input_path, overlay_path, count=5):
        current = input_path
        duration = self._probe_duration(input_path) or 5.0
        for i in range(int(count)):
            t = random.uniform(0, max(0.0, duration - 0.6))
            x = random.randint(0, 200)
            y = random.randint(0, 200)
            out = temp_filename_for('.mp4')
            cmd = [self.ffmpeg, '-y', '-i', current, '-i', overlay_path,
                   '-filter_complex', "overlay=%d:%d:enable='between(t,%.3f,%.3f)'" % (x, y, t, min(t + 0.6, duration)),
                   '-c:v', 'libx264', '-preset', 'veryfast', '-c:a', 'copy', out]
            if not run_command(cmd):
                cmd2 = [self.ffmpeg, '-y', '-i', current, '-i', overlay_path,
                        '-filter_complex', "overlay=%d:%d:enable='between(t,%.3f,%.3f)'" % (x, y, t, min(t + 0.6, duration)),
                        '-c:v', 'mpeg4', '-qscale:v', '6', '-c:a', 'copy', out]
                run_command(cmd2)
            current = out
        return current

    def _frame_shuffle(self, input_path, level=8):
        tmp_dir = tempfile.mkdtemp(prefix='frames_')
        try:
            pattern = os.path.join(tmp_dir, 'frame_%05d.png')
            cmd = [self.ffmpeg, '-y', '-i', input_path, pattern]
            if not run_command(cmd):
                return input_path
            frames = sorted([os.path.join(tmp_dir, f) for f in os.listdir(tmp_dir) if f.startswith('frame_')])
            if not frames:
                return input_path
            num = min(len(frames), int(level))
            idx = list(range(len(frames)))
            random.shuffle(idx)
            selected = idx[:num]
            for i, j in enumerate(selected):
                a = frames[i]
                b = frames[j]
                try:
                    tmpname = a + '.swap'
                    os.rename(a, tmpname)
                    os.rename(b, a)
                    os.rename(tmpname, b)
                except Exception:
                    pass
            out = temp_filename_for('.mp4')
            cmd = [self.ffmpeg, '-y', '-framerate', '25', '-i', os.path.join(tmp_dir, 'frame_%05d.png'),
                   '-i', input_path, '-map', '0:v', '-map', '1:a?', '-c:v', 'libx264', '-preset', 'veryfast', '-c:a', 'copy', out]
            if not run_command(cmd):
                cmd2 = [self.ffmpeg, '-y', '-framerate', '25', '-i', os.path.join(tmp_dir, 'frame_%05d.png'),
                        '-i', input_path, '-map', '0:v', '-map', '1:a?', '-c:v', 'mpeg4', '-qscale:v', '6', '-c:a', 'copy', out]
                run_command(cmd2)
            return out
        finally:
            try:
                shutil.rmtree(tmp_dir)
            except Exception:
                pass

    def _add_random_sound(self, input_path, audio_asset, count=3):
        if not audio_asset:
            return input_path
        current = input_path
        duration = self._probe_duration(input_path) or 6.0
        for i in range(int(count)):
            t = random.uniform(0, max(0.0, duration - 0.5))
            out = temp_filename_for('.mp4')
            # use itsoffset to offset the second input
            cmd = [self.ffmpeg, '-y', '-i', current, '-itsoffset', str(t), '-i', audio_asset,
                   '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2', '-c:v', 'copy', '-c:a', 'aac', out]
            if not run_command(cmd):
                cmd2 = [self.ffmpeg, '-y', '-i', current, '-itsoffset', str(t), '-i', audio_asset,
                        '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2', '-c:v', 'copy', '-c:a', 'libmp3lame', out]
                run_command(cmd2)
            current = out
        return current

    # Auto-generate batch
    def auto_generate(self, input_video, out_dir, base_options, count=3, beta_key=None):
        bkey = beta_key or read_beta_key_from_file()
        if not bkey or not is_valid_beta_key(bkey):
            raise EnvironmentError("Auto-generate requires a valid legacy beta key in beta_key.txt or passed-in.")
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        generated = []
        for i in range(1, int(count) + 1):
            opts = self._randomize_options(base_options)
            out_path = os.path.join(out_dir, 'ytp_auto_%03d.mp4' % (i,))
            print("Auto-gen #%d -> %s" % (i, out_path))
            self.generate(input_video, out_path, opts)
            generated.append(out_path)
        return generated

    def preview(self, output_file):
        if self.ffplay:
            cmd = [self.ffplay, '-autoexit', output_file]
            run_command(cmd)
        else:
            print("ffplay not found. Open %s manually." % output_file)

    def preview2(self, input_path, seconds=6):
        tmp = temp_filename_for('.mp4')
        try:
            vf = "scale=480:-2,format=yuv420p,eq=contrast=1.05:brightness=0.01:saturation=1.2"
            af = "volume=1.0"
            cmd = [self.ffmpeg, '-y', '-t', str(seconds), '-i', input_path, '-vf', vf, '-af', af, '-c:v', 'libx264', '-preset', 'ultrafast', tmp]
            if not run_command(cmd):
                cmd2 = [self.ffmpeg, '-y', '-t', str(seconds), '-i', input_path, '-vf', vf, '-af', af, '-c:v', 'mpeg4', '-qscale:v', '6', tmp]
                run_command(cmd2)
            self.preview(tmp)
        finally:
            rm_f(tmp)

    # Legacy-mode presets
    def _mode_2009(self, input_path, options):
        out = temp_filename_for('.mp4')
        overlay = None
        try:
            overlay = options.get('assets', {}).get('2009_ad') or self._pick_asset(['.png', '.jpg', '.gif'])
        except Exception:
            overlay = self._pick_asset(['.png', '.jpg', '.gif'])
        vf = "scale=640:-2,eq=contrast=1.2:brightness=0.02:saturation=1.4,format=yuv420p"
        if overlay:
            cmd = [self.ffmpeg, '-y', '-i', input_path, '-i', overlay, '-filter_complex', vf + ",overlay=5:5", '-c:v', 'libx264', '-preset', 'veryfast', '-c:a', 'copy', out]
        else:
            cmd = [self.ffmpeg, '-y', '-i', input_path, '-vf', vf, '-c:v', 'libx264', '-preset', 'veryfast', '-c:a', 'copy', out]
        if not run_command(cmd):
            cmd2 = [self.ffmpeg, '-y', '-i', input_path, '-vf', vf, '-c:v', 'mpeg4', '-qscale:v', '6', '-c:a', 'copy', out]
            run_command(cmd2)
        return out

    def _mode_2012(self, input_path, options):
        out = temp_filename_for('.mp4')
        vf = "scale=720:-2,eq=contrast=1.3:saturation=0.9,format=yuv420p"
        cmd = [self.ffmpeg, '-y', '-i', input_path, '-vf', vf, '-c:v', 'libx264', '-preset', 'veryfast', '-c:a', 'copy', out]
        if not run_command(cmd):
            cmd2 = [self.ffmpeg, '-y', '-i', input_path, '-vf', vf, '-c:v', 'mpeg4', '-qscale:v', '6', '-c:a', 'copy', out]
            run_command(cmd2)
        return out

    def _randomize_options(self, base):
        import copy
        opts = copy.deepcopy(base)
        for k in opts:
            if isinstance(opts[k], dict):
                if 'prob' in opts[k]:
                    opts[k]['prob'] = max(0.0, min(1.0, random.random()))
                if 'level' in opts[k] and isinstance(opts[k]['level'], (int, float)):
                    jitter = 0.7 + random.random() * 0.8
                    opts[k]['level'] = opts[k]['level'] * jitter
        if random.random() < 0.3:
            opts['mode_2009'] = True
        if random.random() < 0.2:
            opts['mode_2012'] = True
        return opts