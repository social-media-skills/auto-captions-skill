#!/usr/bin/env python3
"""Transcribe the example's NASA clips with faster-whisper (tiny) and check the words came through.

    python3 tests/whisper_check.py        # needs ffmpeg, Pillow and faster-whisper
"""
import json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "auto-captions-skill")
ex = os.path.join(SKILL, "examples", "iss-radio")
tmp = tempfile.mkdtemp(prefix="captions-whisper-")
shutil.copytree(os.path.join(ex, "clips"), os.path.join(tmp, "clips"))
job = json.load(open(os.path.join(ex, "captions.json"), encoding="utf-8"))
json.dump(job, open(os.path.join(tmp, "captions.json"), "w"))
r = subprocess.run([sys.executable, os.path.join(SKILL, "scripts", "transcribe.py"), os.path.join(tmp, "captions.json"),
                    "--engine", "local", "--model", "tiny"], capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout, r.stderr[-1500:])
if r.returncode != 0:
    sys.exit("transcription failed")
problems = []
for vid, must in (("intro", ["space", "station", "earth"]), ("speed", ["radio", "horizon", "speed", "sound"])):
    words = json.load(open(os.path.join(tmp, "work", vid, "transcript.json"), encoding="utf-8"))["words"]
    text = " ".join(w["w"] for w in words).lower()
    missing = [m for m in must if m not in text]
    times_ok = all(0 <= w["start"] <= w["end"] for w in words) and words[-1]["end"] < 20
    print(vid, len(words), "words:", text[:120])
    if missing or not times_ok or len(words) < 15:
        problems.append(f"{vid}: missing {missing}, {len(words)} words, times ok: {times_ok}")
r = subprocess.run([sys.executable, os.path.join(SKILL, "scripts", "fix.py"), os.path.join(tmp, "captions.json"), "--report"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
if r.returncode != 0 or "Traceback" in r.stderr:
    problems.append("fix.py --report failed: " + r.stderr[-500:])
shutil.rmtree(tmp, ignore_errors=True)
if problems:
    sys.exit("FAILED\n" + "\n".join(problems))
print("whisper check passed")
