#!/usr/bin/env python3
"""Batch audio runner for VoiceOps 2026.

Official run command specification:
Takes a folder of customer audio files, runs the agent on each,
and saves replies (as text and audio) with the document chunks used.

Usage:
    python run.py --input-dir path/to/audio/ --output-dir path/to/output/
"""
import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

# Ensure app is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import settings
from app.agent.orchestrator import VoiceOpsAgent
from app.voice.gnani_client import VoiceClient
from app.voice.mock_speech import generate_mock_wav


def process_audio_file(audio_path: Path, output_dir: Path, agent: VoiceOpsAgent,
                       voice_client: VoiceClient, language_code: str = "en-IN") -> Dict[str, Any]:
    file_stem = audio_path.stem
    reply_audio_path = output_dir / f"{file_stem}_reply.wav"
    
    t0 = time.perf_counter()
    turn_res = voice_client.voice_turn(
        audio_path=audio_path,
        agent=agent,
        conversation_id=f"batch_{file_stem}",
        language_code=language_code,
        output_file=reply_audio_path
    )
    total_time = (time.perf_counter() - t0) * 1000
    
    result = {
        "file_name": audio_path.name,
        "language_code": language_code,
        "transcript": turn_res["heard"],
        "reply": turn_res["reply"],
        "reply_audio": str(reply_audio_path.name),
        "source_chunks": turn_res.get("source_chunks", []),
        "tool_calls": turn_res.get("tool_calls", []),
        "latencies_ms": turn_res.get("latencies", {}),
        "processed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    # Save individual JSON result
    json_path = output_dir / f"{file_stem}_result.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        
    return result


def run_batch(input_dir: str | Path, output_dir: str | Path,
              language_code: str = "en-IN", step_mode: int = 3) -> Dict[str, Any]:
    inp = Path(input_dir)
    out = Path(output_dir)
    inp.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    
    audio_files = sorted(list(inp.glob("*.wav")) + list(inp.glob("*.mp3")) + list(inp.glob("*.m4a")))
    
    if not audio_files:
        print(f"No audio files found in {inp}. Creating sample customer audio clips...")
        demo_1 = inp / "sample_customer_order_help.wav"
        demo_2 = inp / "sample_customer_return_query.wav"
        demo_1.write_bytes(generate_mock_wav(duration_sec=1.2, freq=350.0))
        demo_2.write_bytes(generate_mock_wav(duration_sec=1.5, freq=440.0))
        audio_files = [demo_1, demo_2]

    print(f"Loaded {len(audio_files)} audio file(s) from {inp}.")
    print(f"Output directory: {out}")
    print(f"Speech Language: {language_code}")
    print(f"Gnani API Status: {'LIVE' if bool(settings.GNANI_API_KEY) else 'OFFLINE / MOCK'}\n")

    agent = VoiceOpsAgent()
    voice_client = VoiceClient()
    
    results: List[Dict[str, Any]] = []
    
    for i, file_path in enumerate(audio_files, 1):
        print(f"[{i}/{len(audio_files)}] Processing: {file_path.name} ...")
        res = process_audio_file(file_path, out, agent, voice_client, language_code=language_code)
        print(f"  Heard: {res['transcript']}")
        print(f"  Reply: {res['reply'][:70]}...")
        print(f"  Chunks: {res['source_chunks']}")
        print(f"  Saved: {res['reply_audio']}\n")
        results.append(res)
        
    summary = {
        "run_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "input_directory": str(inp),
        "output_directory": str(out),
        "total_files_processed": len(results),
        "results": results
    }
    
    summary_path = out / "batch_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        
    print(f"Batch run complete! Summary written to {summary_path}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="VoiceOps 2026 Batch Audio Evaluation Runner")
    parser.add_argument("--input-dir", "-i", type=str, default="data/sample_audios",
                        help="Folder containing customer audio files (.wav, .mp3)")
    parser.add_argument("--output-dir", "-o", type=str, default="sample_outputs",
                        help="Folder to save text replies, audio responses, and retrieved chunks")
    parser.add_argument("--language", "-l", type=str, default="en-IN",
                        help="Language code (en-IN, hi-IN, etc.)")
    parser.add_argument("--step", "-s", type=int, default=3,
                        help="Agent step mode (1: Baseline, 2: RAG, 3: Full Agent)")
                        
    args = parser.parse_args()
    run_batch(args.input_dir, args.output_dir, language_code=args.language, step_mode=args.step)


if __name__ == "__main__":
    main()
