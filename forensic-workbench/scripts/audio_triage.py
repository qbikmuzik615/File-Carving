#!/usr/bin/env python3
"""Forensic audio extractor: original SHA256, codec inspection, stream packet copy,
PCM float decode, optional mild DSP, spectrogram and JSON process log.
Inputs remain read-only. Outputs and logs are PRIVATE. Python stdlib + FFmpeg.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

def sha256(path, block=1024*1024):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(block),b""):
            h.update(chunk)
    return h.hexdigest()

def ffprobe(path):
    p=subprocess.run(["ffprobe","-v","error","-show_format","-show_streams",
                      "-of","json",str(path)],capture_output=True,text=True,check=True)
    return json.loads(p.stdout)

def dsp_lowpass(sample_rate):
    if sample_rate<800:
        raise ValueError("Unsupported sample rate")
    return min(12000,max(100,int(sample_rate*0.4)))

def call_ffmpeg(args, commands, outputs, *, input_file):
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-n","-i",str(input_file),*args]
    proc=subprocess.run(cmd,capture_output=True,text=True)
    commands.append({"argv":cmd,"returncode":proc.returncode,
                     "stderr_tail":proc.stderr[-1200:]})
    if proc.returncode:
        raise RuntimeError("FFmpeg failed: "+proc.stderr[-600:])
    dest=Path(args[-1])
    outputs.append({"name":dest.name,"size":dest.stat().st_size,"sha256":sha256(dest)})

def run(source, output, *, dsp=False, spectrogram=False, label="audio"):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise EnvironmentError("FFmpeg and FFprobe are required")
    src=Path(source).expanduser().resolve(strict=True)
    if not src.is_file():
        raise ValueError("Expected a regular source file")
    out=Path(output).expanduser().resolve()
    if out==src.parent or out in src.parents or out==src:
        raise ValueError("Output must be separate from the original file directory")
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("Use a new EMPTY analysis folder; no overwriting results")
    out.mkdir(parents=True,exist_ok=True)
    start_hash=sha256(src)
    info=ffprobe(src)
    audios=[x for x in info.get("streams",[]) if x.get("codec_type")=="audio"]
    if not audios:
        raise ValueError("No recognized audio track; cannot invent missing audio")
    a=audios[0]
    index=int(a["index"])
    rate=int(a.get("sample_rate") or 0)
    if rate<800:
        raise ValueError("Cannot establish audio sample rate")
    codec=a.get("codec_name","unknown")
    ext=".m4a" if codec=="aac" else ".mka"
    outputs=[];commands=[]
    streamcopy=out/(label+"_audiostream_copy"+ext)
    wav=out/(label+"_decoded_reference_f32.wav")
    call_ffmpeg(["-map",f"0:{index}","-vn","-c:a","copy",str(streamcopy)],
                commands,outputs,input_file=src)
    call_ffmpeg(["-map",f"0:{index}","-vn","-c:a","pcm_f32le",str(wav)],
                commands,outputs,input_file=src)
    if dsp:
        lp=dsp_lowpass(rate)
        af=f"highpass=f=70,lowpass=f={lp}"
        call_ffmpeg(["-map","0:a:0","-vn","-af",af,"-c:a","pcm_f32le",
                     str(out/(label+"_DSP_mild_f32.wav"))],commands,outputs,input_file=src)
        call_ffmpeg(["-map","0:a:0","-vn","-af",af+",afftdn=nr=6:nf=-55",
                     "-c:a","pcm_f32le",str(out/(label+"_DSP_afftdn6_f32.wav"))],
                    commands,outputs,input_file=src)
    if spectrogram:
        call_ffmpeg(["-map","0:a:0","-lavfi",
                     "showspectrumpic=s=1600x900:legend=1:scale=log:color=intensity",
                     "-frames:v","1",str(out/(label+"_source_spectrogram.png"))],
                    commands,outputs,input_file=src)
    end_hash=sha256(src)
    if start_hash!=end_hash:
        raise RuntimeError("Source hash changed; stop and investigate integrity")
    report={
        "tool":"audio_triage.py","classification":"PRIVATE SOURCE / DERIVATIVES",
        "processed_at_utc":datetime.now(timezone.utc).isoformat(),
        "source":{"path":str(src),"size":src.stat().st_size,"sha256":start_hash},
        "source_sha256_reverified":end_hash,
        "audio_track":{"index":index,"codec":codec,"sample_rate":rate,
                       "channels":a.get("channels"),"bit_rate":a.get("bit_rate")},
        "media_duration":info.get("format",{}).get("duration"),
        "ffmpeg_version":subprocess.check_output(
            ["ffmpeg","-version"],text=True).splitlines()[0],
        "commands":commands,"derivatives":outputs,
        "warning":"No restored phonemes are authenticated. Unchanged source preserved. "
                  "DSP may attenuate or distort speech. Human review required.",
    }
    (out/"audio_triage_private_report.json").write_text(
        json.dumps(report,indent=2)+"\n",encoding="utf8")
    return report

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source",help="Private authorized working copy of source recording")
    ap.add_argument("--output",required=True,help="NEW empty PRIVATE output directory")
    ap.add_argument("--label",default="audio",
                    help="Short nonsensitive derivative label")
    ap.add_argument("--dsp",action="store_true",help="Produce mild DSP comparison branches")
    ap.add_argument("--spectrogram",action="store_true")
    a=ap.parse_args()
    if not all(c.isalnum() or c in "_-" for c in a.label):
        ap.error("Label may only contain letters, digits, _ and -")
    r=run(a.source,a.output,dsp=a.dsp,spectrogram=a.spectrogram,label=a.label)
    print("SOURCE VERIFIED SHA-256:",r["source"]["sha256"])
    print("audio codec:",r["audio_track"]["codec"],"outputs:",len(r["derivatives"]))
    print("PRIVATE REPORT DIRECTORY:",Path(a.output).resolve())
    return 0

if __name__=="__main__":
    raise SystemExit(main())
