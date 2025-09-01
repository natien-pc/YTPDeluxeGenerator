from __future__ import print_function, unicode_literals
import os
import random
import re
import shutil
import tempfile
from utils import find_ffmpeg, temp_filename_for, run_command, rm_f, read_beta_key_from_file, is_valid_beta_key, find_assets_dir, list_asset_files

class YTPEngine(object):
    def __init__(self, ffmpeg_path=None, ffplay_path=None, work_dir=None):
        ffmpeg, ffplay = find_ffmpeg()
        self.ffmpeg = ffmpeg_path or ffmpeg
        self.ffplay = ffplay_path or ffplay
        if not self.ffmpeg:
            raise EnvironmentError("ffmpeg not found. Place ffmpeg.exe on PATH or next to script.")
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
                return int(h)*3600 + int(mm)*60 + float(ss)
        except Exception:
            pass
        return 0.0

    # Public API
    def generate(self, input_video, output_path, options):
        cur = input_video

        if options.get('sentence_mix', {}).get('enabled'):
            cur = self._sentence_mix(cur, options.get('sentence_mix', {}))

        if options.get('mode_2009'):
            cur = self._mode_2009(cur, options)
        if options.get('mode_2012'):
            cur = self._mode_2012(cur, options)

        # iterate effects in a stable order
        order = ['reverse','speed','stutter','earrape','chorus','vibrato','sus','invert','mirror','dance','rainbow','explosion','frame_shuffle','meme','random_sound']
        for eff in order:
            cfg = options.get(eff, {})
            if not cfg:
                continue
            enabled = cfg.get('enabled', False)
            prob = float(cfg.get('prob', 1.0)) if 'prob' in cfg else 1.0
            if enabled and random.random() <= prob:
                # dispatch
                try:
                    if eff == 'reverse':
                        cur = self._reverse(cur)
                    elif eff == 'speed':
                        cur = self._change_speed(cur, cfg.get('level', 1.0))
                    elif eff == 'stutter':
                        cur = self._stutter(cur, cfg.get('level', 2))
                    elif eff == 'earrape':
                        cur = self._earrape(cur, cfg.get('level', 16.0))
                    elif eff == 'chorus':
                        cur = self._chorus(cur, cfg.get('level', 0.6))
                    elif eff == 'vibrato':
                        cur = self._vibrato(cur, cfg.get('level', 1.03))
                    elif eff == 'sus':
                        cur = self._sus_effect(cur, cfg.get('level', 1.1))
                    elif eff == 'invert':
                        cur = self._invert_colors(cur)
                    elif eff == 'mirror':
                        cur = self._mirror(cur)
                    elif eff == 'dance':
                        cur = self._dance_mode(cur)
                    elif eff == 'rainbow':
                        asset = cfg.get('asset') or self._pick_asset(['.png','.gif','.jpg'])
                        if asset:
                            cur = self._overlay_image(cur, asset, x=cfg.get('x',0), y=cfg.get('y',0), opacity=cfg.get('opacity',0.9))
                    elif eff == 'explosion':
                        asset = cfg.get('asset') or self._pick_asset(['.png','.gif','.jpg'])
                        if asset:
                            cur = self._explosion_spam(cur, asset, count=cfg.get('count',4))
                    elif eff == 'frame_shuffle':
                        cur = self._frame_shuffle(cur, cfg.get('level',8))
                    elif eff == 'meme':
                        img = cfg.get('image') or self._pick_asset(['.png','.jpg','.gif'])
                        if img:
                            cur = self._overlay_image(cur, img, x='(main_w-overlay_w)/2', y='(main_h-overlay_h)-10')
                    elif eff == 'random_sound':
                        audio = cfg.get('asset') or self._pick_asset(['.wav','.mp3','.ogg','.aac'])
                        if audio:
                            cur = self._add_random_sound(cur, audio, cfg.get('count',3))
                except Exception as e:
                    print("Effect", eff, "failed:", e)

        # final encode with fallback
        out = output_path
        final_cmd = [self.ffmpeg, '-y', '-i', cur, '-c:v', 'libx264', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '192k', out]
        if not run_command(final_cmd):
            final_cmd2 = [self.ffmpeg, '-y', '-i', cur, '-c:v', 'mpeg4', '-qscale:v', '5', '-c:a', 'libmp3lame', '-b:a', '192k', out]
            run_command(final_cmd2)
        return out

    # Auto generate
    def auto_generate(self, input_video, out_dir, base_options, count=3, beta_key=None):
        b = beta_key or read_beta_key_from_file()
        if not b or not is_valid_beta_key(b):
            raise EnvironmentError("Auto-generate requires valid legacy beta key.")
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        outs = []
        for i in range(1, int(count)+1):
            opts = self._randomize_options(base_options)
            o = os.path.join(out_dir, 'ytp_auto_%03d.mp4' % i)
            print("Auto-gen:", o)
            self.generate(input_video, o, opts)
            outs.append(o)
        return outs

    def preview(self, output_file):
        if self.ffplay:
            run_command([self.ffplay, '-autoexit', output_file])
        else:
            print("ffplay not found. Open file manually:", output_file)

    def preview2(self, input_path, seconds=6):
        tmp = temp_filename_for('.mp4')
        try:
            vf = "scale=480:-2,format=yuv420p,eq=contrast=1.05:brightness=0.01:saturation=1.2"
            cmd = [self.ffmpeg, '-y', '-t', str(seconds), '-i', input_path, '-vf', vf, '-c:v', 'libx264', '-preset', 'ultrafast', tmp]
            if not run_command(cmd):
                cmd2 = [self.ffmpeg, '-y', '-t', str(seconds), '-i', input_path, '-vf', vf, '-c:v', 'mpeg4', '-qscale:v', '6', tmp]
                run_command(cmd2)
            self.preview(tmp)
        finally:
            rm_f(tmp)

    # ---------------- Effect implementations ----------------
    def _sentence_mix(self, input_path, cfg):
        dur = self._probe_duration(input_path) or 6.0
        parts = int(cfg.get('parts', 6))
        piece_len = min(1.5, max(0.15, dur / max(1, parts*2.0)))
        clips = []
        for i in range(parts):
            start = random.uniform(0, max(0.0, dur - piece_len))
            out = temp_filename_for('.mp4')
            cmd = [self.ffmpeg, '-y', '-ss', str(start), '-t', str(piece_len), '-i', input_path, '-c', 'copy', out]
            run_command(cmd)
            clips.append(out)
        concat = temp_filename_for('.txt')
        try:
            with open(concat, 'w') as f:
                for c in clips:
                    f.write("file '%s'\n" % c.replace("'", "'\\''"))
            out_all = temp_filename_for('.mp4')
            cmd = [self.ffmpeg, '-y', '-f', 'concat', '-safe', '0', '-i', concat, '-c', 'copy', out_all]
            run_command(cmd)
        finally:
            for c in clips:
                rm_f(c)
            rm_f(concat)
        return out_all

    def _reverse(self, input_path):
        out = temp_filename_for('.mp4')
        cmd = [self.ffmpeg, '-y', '-i', input_path, '-vf', 'reverse', '-af', 'areverse', out]
        if not run_command(cmd):
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
        rem = f
        while rem > 2.0:
            parts.append('atempo=2.0'); rem /= 2.0
        while rem < 0.5:
            parts.append('atempo=0.5'); rem /= 0.5
        parts.append('atempo=%s' % rem)
        return ','.join(parts)

    def _change_speed(self, input_path, factor):
        out = temp_filename_for('.mp4')
        try:
            f = float(factor)
            if f <= 0: f = 1.0
        except Exception:
            f = 1.0
        setpts = 'setpts=%s*PTS' % (1.0/f)
        atempo = self._build_atempo_chain(f)
        cmd = [self.ffmpeg, '-y', '-i', input_path, '-vf', setpts, '-af', atempo, out]
        run_command(cmd)
        return out

    def _stutter(self, input_path, level=2):
        dur = self._probe_duration(input_path) or 3.0
        seg_len = max(0.05, min(0.6, 0.1 * float(level)))
        start = random.uniform(0, max(0.0, dur - seg_len))
        seg = temp_filename_for('.mp4')
        cmd = [self.ffmpeg, '-y', '-ss', str(start), '-t', str(seg_len), '-i', input_path, '-c', 'copy', seg]
        run_command(cmd)
        loops = 2 + int(level)
        listf = temp_filename_for('.txt')
        try:
            with open(listf, 'w') as f:
                for i in range(loops):
                    f.write("file '%s'\n" % seg.replace("'", "'\\''"))
            out = temp_filename_for('.mp4')
            cmd = [self.ffmpeg, '-y', '-f', 'concat', '-safe', '0', '-i', listf, '-c', 'copy', out]
            run_command(cmd)
        finally:
            rm_f(listf); rm_f(seg)
        return out

    def _earrape(self, input_path, gain=20.0):
        out = temp_filename_for('.mp4')
        try:
            g = float(gain)
        except Exception:
            g = 20.0
        cmd = [self.ffmpeg, '-y', '-i', input_path, '-af', 'volume=%sdB' % g, out]
        run_command(cmd)
        return out

    def _chorus(self, input_path, level=0.6):
        out = temp_filename_for('.mp4')
        try:
            lev = float(level)
        except Exception:
            lev = 0.6
        d1 = int(30 + 400*lev); d2 = int(90 + 500*lev)
        decay1 = 0.4 + 0.3*lev; decay2 = 0.2 + 0.25*lev
        aecho = "aecho=0.8:0.9:%d|%d:%.2f|%.2f" % (d1,d2,decay1,decay2)
        cmd = [self.ffmpeg, '-y', '-i', input_path, '-af', aecho, out]
        run_command(cmd)
        return out

    def _vibrato(self, input_path, level=1.03):
        out = temp_filename_for('.mp4')
        try:
            lev = float(level); 
            if lev <= 0: lev = 1.03
        except Exception:
            lev = 1.03
        asetrate = 'asetrate=44100*%f' % lev
        atempo = self._build_atempo_chain(1.0/lev)
        af = "%s,%s" % (asetrate, atempo)
        cmd = [self.ffmpeg, '-y', '-i', input_path, '-af', af, '-c:v', 'copy', out]
        run_command(cmd)
        return out

    def _sus_effect(self, input_path, level=1.1):
        cur = input_path
        for i in range(2):
            factor = 0.85 + random.random() * (level + 0.3)
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
        # "Squidward" mode could be morph-like; we approximate with transpose + scale jitter
        cmd = [self.ffmpeg, '-y', '-i', input_path, '-vf', 'transpose=1,scale=iw*0.95:ih*0.95', out]
        if not run_command(cmd):
            cmd2 = [self.ffmpeg, '-y', '-i', input_path, '-vf', 'scale=iw*0.95:ih*0.95', out]
            run_command(cmd2)
        return out

    def _overlay_image(self, input_path, image_path, x=0, y=0, opacity=1.0):
        out = temp_filename_for('.mp4')
        try:
            if float(opacity) >= 0.99:
                cmd = [self.ffmpeg, '-y', '-i', input_path, '-i', image_path, '-filter_complex', 'overlay=%s:%s' % (x,y), out]
            else:
                cmd = [self.ffmpeg, '-y', '-i', input_path, '-i', image_path,
                       '-filter_complex', "[1]format=rgba,colorchannelmixer=aa=%f[ol];[0][ol]overlay=%s:%s" % (opacity, x, y), out]
            run_command(cmd)
        except Exception:
            cmd2 = [self.ffmpeg, '-y', '-i', input_path, '-i', image_path, '-filter_complex', 'overlay=0:0', out]
            run_command(cmd2)
        return out

    def _explosion_spam(self, input_path, overlay_path, count=4):
        current = input_path
        dur = self._probe_duration(input_path) or 5.0
        for i in range(int(count)):
            t = random.uniform(0, max(0.0, dur-0.6))
            x = random.randint(0, 200); y = random.randint(0, 200)
            out = temp_filename_for('.mp4')
            cmd = [self.ffmpeg, '-y', '-i', current, '-i', overlay_path,
                   '-filter_complex', "overlay=%d:%d:enable='between(t,%.3f,%.3f)'" % (x,y,t,min(t+0.6,dur)),
                   '-c:v', 'libx264', '-preset', 'veryfast', '-c:a', 'copy', out]
            if not run_command(cmd):
                cmd2 = [self.ffmpeg, '-y', '-i', current, '-i', overlay_path,
                        '-filter_complex', "overlay=%d:%d:enable='between(t,%.3f,%.3f)'" % (x,y,t,min(t+0.6,dur)),
                        '-c:v', 'mpeg4', '-qscale:v', '6', '-c:a', 'copy', out]
                run_command(cmd2)
            current = out
        return current

    def _frame_shuffle(self, input_path, level=8):
        tmpdir = tempfile.mkdtemp(prefix='frames_')
        try:
            pattern = os.path.join(tmpdir, 'frame_%05d.png')
            if not run_command([self.ffmpeg, '-y', '-i', input_path, pattern]):
                return input_path
            frames = sorted([os.path.join(tmpdir,f) for f in os.listdir(tmpdir) if f.startswith('frame_')])
            if not frames:
                return input_path
            num = min(len(frames), int(level))
            idx = list(range(len(frames))); random.shuffle(idx); sel = idx[:num]
            for i,j in enumerate(sel):
                a = frames[i]; b = frames[j]
                try:
                    tmpname = a + '.swap'; os.rename(a, tmpname); os.rename(b, a); os.rename(tmpname, b)
                except Exception:
                    pass
            out = temp_filename_for('.mp4')
            cmd = [self.ffmpeg, '-y', '-framerate', '25', '-i', os.path.join(tmpdir, 'frame_%05d.png'),
                   '-i', input_path, '-map', '0:v', '-map', '1:a?', '-c:v', 'libx264', '-preset', 'veryfast', '-c:a', 'copy', out]
            if not run_command(cmd):
                cmd2 = [self.ffmpeg, '-y', '-framerate', '25', '-i', os.path.join(tmpdir, 'frame_%05d.png'),
                        '-i', input_path, '-map', '0:v', '-map', '1:a?', '-c:v', 'mpeg4', '-qscale:v', '6', '-c:a', 'copy', out]
                run_command(cmd2)
            return out
        finally:
            try: shutil.rmtree(tmpdir)
            except Exception: pass

    def _add_random_sound(self, input_path, audio_asset, count=3):
        if not audio_asset:
            return input_path
        cur = input_path
        dur = self._probe_duration(input_path) or 6.0
        for i in range(int(count)):
            t = random.uniform(0, max(0.0, dur-0.5))
            out = temp_filename_for('.mp4')
            cmd = [self.ffmpeg, '-y', '-i', cur, '-itsoffset', str(t), '-i', audio_asset,
                   '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2', '-c:v', 'copy', '-c:a', 'aac', out]
            if not run_command(cmd):
                cmd2 = [self.ffmpeg, '-y', '-i', cur, '-itsoffset', str(t), '-i', audio_asset,
                        '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2', '-c:v', 'copy', '-c:a', 'libmp3lame', out]
                run_command(cmd2)
            cur = out
        return cur

    # Auto-Tune placeholder (no real auto-tune included)
    def _auto_tune_placeholder(self, input_audio_path, params=None):
        # This is a placeholder: add integration with an external autotune binary or VST host here.
        print("Auto-Tune Chaos requested but not implemented. Provide autotune tool and call it here.")
        return input_audio_path

    def _mode_2009(self, input_path, options):
        out = temp_filename_for('.mp4')
        overlay = options.get('assets', {}).get('2009_ad') or self._pick_asset(['.png','.jpg','.gif'])
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
                if 'level' in opts[k] and isinstance(opts[k]['level'], (int,float)):
                    jitter = 0.7 + random.random()*0.8
                    opts[k]['level'] = opts[k]['level'] * jitter
        if random.random() < 0.3:
            opts['mode_2009'] = True
        if random.random() < 0.2:
            opts['mode_2012'] = True
        return opts