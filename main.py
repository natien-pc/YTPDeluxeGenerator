from __future__ import print_function, unicode_literals
import os
import sys
import json
import traceback
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog
except Exception:
    import Tkinter as tk
    import tkFileDialog as filedialog
    import tkMessageBox as messagebox
    import tkSimpleDialog as simpledialog

from engine import YTPEngine
from utils import read_beta_key_from_file, is_valid_beta_key, find_assets_dir

DEFAULT_CONFIG = {
    "reverse": {"enabled": False, "prob": 1.0},
    "speed": {"enabled": False, "prob": 1.0, "level": 1.2},
    "stutter": {"enabled": False, "prob": 0.8, "level": 2},
    "earrape": {"enabled": False, "prob": 0.5, "level": 12.0},
    "chorus": {"enabled": False, "prob": 0.6, "level": 0.6},
    "vibrato": {"enabled": False, "prob": 0.6, "level": 1.03},
    "sus": {"enabled": False, "prob": 0.5, "level": 1.1},
    "invert": {"enabled": False, "prob": 0.5},
    "mirror": {"enabled": False, "prob": 0.5},
    "dance": {"enabled": False, "prob": 0.4},
    "rainbow": {"enabled": False, "prob": 0.6, "asset": "", "opacity": 0.9},
    "explosion": {"enabled": False, "prob": 0.5, "asset": "", "count": 4},
    "frame_shuffle": {"enabled": False, "prob": 0.3, "level": 8},
    "meme": {"enabled": False, "prob": 0.5, "image": ""},
    "random_sound": {"enabled": False, "prob": 0.7, "asset": "", "count": 3},
    "sentence_mix": {"enabled": False, "parts": 6},
}

class App(object):
    def __init__(self, master):
        self.master = master
        master.title("YTP Deluxe Generator — Legacy")
        self.engine = None
        self.config = DEFAULT_CONFIG.copy()
        self.detected_key = read_beta_key_from_file()
        assets = find_assets_dir() or "(no assets folder)"

        row = 0
        tk.Label(master, text="Beta key:").grid(row=row, column=0, sticky='w')
        self.beta_entry = tk.Entry(master, width=40); self.beta_entry.grid(row=row, column=1, columnspan=2, sticky='w')
        if self.detected_key:
            self.beta_entry.insert(0, self.detected_key)
        tk.Label(master, text="Assets: %s" % assets).grid(row=row, column=3, columnspan=2, sticky='w')
        row += 1

        tk.Label(master, text="Input video:").grid(row=row, column=0, sticky='w')
        self.input_entry = tk.Entry(master, width=60); self.input_entry.grid(row=row, column=1, columnspan=3, sticky='w')
        tk.Button(master, text="Browse", command=self.browse_input).grid(row=row, column=4)
        row += 1

        tk.Label(master, text="Output file:").grid(row=row, column=0, sticky='w')
        self.output_entry = tk.Entry(master, width=60); self.output_entry.grid(row=row, column=1, columnspan=3, sticky='w')
        self.output_entry.insert(0, os.path.join(os.getcwd(), 'ytp_out.mp4'))
        tk.Button(master, text="Browse", command=self.browse_output).grid(row=row, column=4)
        row += 1

        tk.Label(master, text="Legacy Modes:").grid(row=row, column=0, sticky='w')
        self.mode2009_var = tk.IntVar(value=0); tk.Checkbutton(master, text="2009 Mode", variable=self.mode2009_var).grid(row=row, column=1, sticky='w')
        self.mode2012_var = tk.IntVar(value=0); tk.Checkbutton(master, text="2012 Mode", variable=self.mode2012_var).grid(row=row, column=2, sticky='w')
        tk.Button(master, text="Configure Effects", command=self.configure_effects).grid(row=row, column=3, sticky='w')
        row += 1

        effects_frame = tk.LabelFrame(master, text="Effects (quick enable)")
        effects_frame.grid(row=row, column=0, columnspan=5, sticky='we', padx=5, pady=5)
        self.effect_vars = {}
        col = 0
        for key in sorted(self.config.keys()):
            var = tk.IntVar(value=1 if self.config[key].get('enabled') else 0)
            cb = tk.Checkbutton(effects_frame, text=key.replace('_',' ').title(), variable=var)
            cb.grid(row=0, column=col, sticky='w', padx=2)
            self.effect_vars[key] = var
            col += 1
        row += 1

        assets_frame = tk.LabelFrame(master, text="Assets / Paths")
        assets_frame.grid(row=row, column=0, columnspan=5, sticky='we', padx=5, pady=5)
        tk.Label(assets_frame, text="Rainbow image:").grid(row=0, column=0, sticky='w')
        self.rainbow_entry = tk.Entry(assets_frame, width=40); self.rainbow_entry.grid(row=0, column=1)
        tk.Button(assets_frame, text="Browse", command=self.browse_rainbow).grid(row=0, column=2)
        tk.Label(assets_frame, text="Random sound:").grid(row=1, column=0, sticky='w')
        self.sound_entry = tk.Entry(assets_frame, width=40); self.sound_entry.grid(row=1, column=1)
        tk.Button(assets_frame, text="Browse", command=self.browse_sound).grid(row=1, column=2)
        tk.Label(assets_frame, text="Meme image:").grid(row=2, column=0, sticky='w')
        self.meme_entry = tk.Entry(assets_frame, width=40); self.meme_entry.grid(row=2, column=1)
        tk.Button(assets_frame, text="Browse", command=self.browse_meme).grid(row=2, column=2)
        row += 1

        tk.Button(master, text="Generate", command=self.generate).grid(row=row, column=1, pady=8)
        tk.Button(master, text="Preview", command=self.preview).grid(row=row, column=2, pady=8)
        tk.Button(master, text="Preview 2", command=self.preview2).grid(row=row, column=3, pady=8)
        tk.Button(master, text="Auto Generate", command=self.auto_generate).grid(row=row, column=4, pady=8)
        row += 1

        self.status = tk.StringVar(value="Ready"); tk.Label(master, textvariable=self.status).grid(row=row, column=0, columnspan=5, sticky='we')

    def browse_input(self):
        path = filedialog.askopenfilename(title="Select input video", filetypes=[("Video","*.mp4;*.avi;*.mkv;*.mov;*.wmv"),("All","*.*")])
        if path: self.input_entry.delete(0,'end'); self.input_entry.insert(0,path)

    def browse_output(self):
        path = filedialog.asksaveasfilename(title="Select output", defaultextension='.mp4', filetypes=[("MP4","*.mp4"),("All","*.*")])
        if path: self.output_entry.delete(0,'end'); self.output_entry.insert(0,path)

    def browse_rainbow(self):
        path = filedialog.askopenfilename(title="Select overlay image", filetypes=[("Images","*.png;*.gif;*.jpg"),("All","*.*")])
        if path: self.rainbow_entry.delete(0,'end'); self.rainbow_entry.insert(0,path)

    def browse_sound(self):
        path = filedialog.askopenfilename(title="Select audio", filetypes=[("Audio","*.mp3;*.wav;*.ogg;*.aac"),("All","*.*")])
        if path: self.sound_entry.delete(0,'end'); self.sound_entry.insert(0,path)

    def browse_meme(self):
        path = filedialog.askopenfilename(title="Select image", filetypes=[("Images","*.png;*.jpg;*.gif"),("All","*.*")])
        if path: self.meme_entry.delete(0,'end'); self.meme_entry.insert(0,path)

    def configure_effects(self):
        # simple dialog that lets user set prob and level for each effect
        win = tk.Toplevel(self.master)
        win.title("Configure Effects (probability 0.0-1.0, level numeric)")
        row = 0
        entries = {}
        for k in sorted(self.config.keys()):
            tk.Label(win, text=k).grid(row=row, column=0, sticky='w')
            prob = tk.StringVar(value=str(self.config[k].get('prob', 1.0)))
            lev = tk.StringVar(value=str(self.config[k].get('level', self.config[k].get('parts',''))))
            eprob = tk.Entry(win, width=6, textvariable=prob); eprob.grid(row=row, column=1)
            elevel = tk.Entry(win, width=8, textvariable=lev); elevel.grid(row=row, column=2)
            entries[k] = (prob, lev)
            row += 1
        def savecfg():
            for k,(p,l) in entries.items():
                try:
                    self.config[k]['prob'] = float(p.get())
                except Exception:
                    pass
                try:
                    # keep existing type
                    if 'level' in self.config[k]:
                        self.config[k]['level'] = float(l.get())
                    elif 'parts' in self.config[k]:
                        self.config[k]['parts'] = int(l.get())
                except Exception:
                    pass
                # update enabled state from quick checkboxes
                self.config[k]['enabled'] = bool(self.effect_vars[k].get())
            win.destroy()
        tk.Button(win, text="Save", command=savecfg).grid(row=row, column=0, columnspan=3)

    def _gather_options(self):
        opts = {}
        for k,v in self.config.items():
            opts[k] = v.copy()
            opts[k]['enabled'] = bool(self.effect_vars[k].get())
        opts['rainbow']['asset'] = self.rainbow_entry.get().strip()
        opts['meme']['image'] = self.meme_entry.get().strip()
        opts['random_sound']['asset'] = self.sound_entry.get().strip()
        opts['mode_2009'] = bool(self.mode2009_var.get())
        opts['mode_2012'] = bool(self.mode2012_var.get())
        opts['beta_key'] = self.beta_entry.get().strip()
        return opts

    def generate(self):
        inp = self.input_entry.get().strip(); out = self.output_entry.get().strip()
        if not inp or not os.path.exists(inp):
            messagebox.showerror("Error","Input not found"); return
        if not out:
            messagebox.showerror("Error","Choose output"); return
        try:
            opts = self._gather_options()
            if not self.engine:
                self.engine = YTPEngine()
            self.status.set("Generating..."); self.master.update()
            self.engine.generate(inp, out, opts)
            self.status.set("Generated: %s" % out)
            messagebox.showinfo("Done","Generated: %s" % out)
        except Exception as e:
            traceback.print_exc(); messagebox.showerror("Generation failed", str(e)); self.status.set("Error")

    def preview(self):
        out = self.output_entry.get().strip()
        if not out or not os.path.exists(out):
            messagebox.showerror("Error","Output not found"); return
        try:
            if not self.engine: self.engine = YTPEngine()
            self.engine.preview(out)
        except Exception as e:
            messagebox.showerror("Preview failed", str(e))

    def preview2(self):
        inp = self.input_entry.get().strip()
        if not inp or not os.path.exists(inp):
            messagebox.showerror("Error","Input not found"); return
        try:
            if not self.engine: self.engine = YTPEngine()
            self.engine.preview2(inp, seconds=6)
        except Exception as e:
            messagebox.showerror("Preview2 failed", str(e))

    def auto_generate(self):
        inp = self.input_entry.get().strip()
        if not inp or not os.path.exists(inp):
            messagebox.showerror("Error","Input not found"); return
        try:
            cnt = simpledialog.askinteger("Auto Generate", "How many YTPs to generate?", initialvalue=3, minvalue=1, maxvalue=50)
            if not cnt: return
        except Exception:
            cnt = 3
        out_dir = filedialog.askdirectory(title="Select output directory")
        if not out_dir: return
        try:
            opts = self._gather_options()
            if not self.engine: self.engine = YTPEngine()
            beta = opts.get('beta_key') or None
            self.status.set("Auto-generating..."); self.master.update()
            generated = self.engine.auto_generate(inp, out_dir, opts, count=cnt, beta_key=beta)
            messagebox.showinfo("Auto Generate", "Generated %d files" % len(generated))
            self.status.set("Auto-generated %d files" % len(generated))
        except Exception as e:
            traceback.print_exc(); messagebox.showerror("Auto Generate failed", str(e)); self.status.set("Error")

if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()