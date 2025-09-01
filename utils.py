from __future__ import print_function, unicode_literals
import os
import sys
import tempfile
import shutil
import random
import subprocess

# Compatibility helpers used by engine and GUI

def which(exe_name):
    paths = os.environ.get('PATH', '').split(os.pathsep)
    exts = ['']
    if os.name == 'nt':
        pathext = os.environ.get('PATHEXT', '.EXE;.BAT;.CMD')
        exts = pathext.split(';')
    for p in paths:
        candidate = os.path.join(p, exe_name)
        for e in exts:
            full = candidate + e
            if os.path.exists(full) and os.path.isfile(full):
                return full
    return None

def find_ffmpeg():
    ffmpeg = which('ffmpeg') or which('ffmpeg.exe')
    ffplay = which('ffplay') or which('ffplay.exe')
    return ffmpeg, ffplay

def safe_tempfile(suffix='', prefix='ytp_', dir=None):
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
    os.close(fd)
    return path

def temp_filename_for(ext):
    if not ext.startswith('.'):
        ext = '.' + ext
    return safe_tempfile(suffix=ext)

def rm_f(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    except Exception:
        pass

def run_command(cmd, shell=False):
    # Keep printing behavior simple for legacy consoles
    try:
        if isinstance(cmd, (list, tuple)):
            print("Running:", " ".join(cmd))
        else:
            print("Running:", cmd)
        p = subprocess.Popen(cmd, shell=shell)
        p.communicate()
        return p.returncode == 0
    except Exception as e:
        print("Command failed:", e)
        return False

# Beta key helpers (very simple legacy-style validator)
def read_beta_key_from_file(path='beta_key.txt'):
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                k = f.read().strip()
                return k
    except Exception:
        pass
    return None

def is_valid_beta_key(key):
    # Very permissive validator for legacy/beta keys:
    # - Accept any non-empty string starting with 'OLD-' for legacy convenience.
    # - You can replace this with a real validator if you have a server or a list of keys.
    try:
        if not key:
            return False
        key = key.strip()
        if key.upper().startswith('OLD-'):
            return True
        # legacy fallback: accept short keys of the form 'BETA2009' etc.
        if key.upper().startswith('BETA') or len(key) >= 8:
            return True
    except Exception:
        pass
    return False

def find_assets_dir(default='assets'):
    # Return assets dir if exists
    if os.path.isdir(default):
        return default
    return None

def list_asset_files(assets_dir):
    files = {}
    if not assets_dir:
        return files
    try:
        for fn in os.listdir(assets_dir):
            path = os.path.join(assets_dir, fn)
            if os.path.isfile(path):
                ext = os.path.splitext(fn)[1].lower()
                files.setdefault(ext, []).append(path)
    except Exception:
        pass
    return files