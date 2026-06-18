#!/usr/bin/env python3
"""
音频切片 ASR 转录工具
将大音频文件切成小段，逐段调用 mimo-v2.5-asr，拼接完整转录结果。

用法:
    python audio_split_asr.py input.m4a [--segment-seconds 30] [--output transcript.txt]

依赖: ffmpeg, openai (pip install openai)
环境变量: XIAOMI_API_KEY, XIAOMI_BASE_URL (从 ~/.hermes/.env 或 /opt/data/.env 读取)
"""

import argparse
import base64
import glob
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time


def load_env():
    """从 .env 文件加载环境变量"""
    env_paths = [
        os.path.expanduser("~/.hermes/.env"),
        "/opt/data/.env",
    ]
    for path in env_paths:
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        if k and v:
                            os.environ.setdefault(k.strip(), v.strip())


def get_audio_duration(input_path):
    """获取音频时长（秒）"""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", input_path],
        capture_output=True, text=True
    )
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])


def split_audio(input_path, segment_seconds, output_dir):
    """将音频切成多段 wav 文件，返回文件列表"""
    duration = get_audio_duration(input_path)
    num_segments = math.ceil(duration / segment_seconds)
    print(f"音频时长: {duration:.1f}s, 切成 {num_segments} 段 (每段 {segment_seconds}s)")

    segments = []
    for i in range(num_segments):
        start = i * segment_seconds
        output_path = os.path.join(output_dir, f"segment_{i:03d}.wav")
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", input_path,
                "-ss", str(start),
                "-t", str(segment_seconds),
                "-ar", "16000",  # 16kHz 采样率
                "-ac", "1",      # 单声道
                "-acodec", "pcm_s16le",
                output_path,
            ],
            capture_output=True, check=True
        )
        size_kb = os.path.getsize(output_path) / 1024
        segments.append((output_path, start, min(start + segment_seconds, duration)))
        print(f"  段 {i+1}/{num_segments}: {start:.0f}s-{min(start+segment_seconds, duration):.0f}s ({size_kb:.0f}KB)")

    return segments


def transcribe_segment(wav_path, api_key, base_url, language="zh"):
    """调用 mimo-v2.5-asr 转录单个音频段"""
    from openai import OpenAI

    with open(wav_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    b64_size_mb = len(audio_b64) / 1024 / 1024
    if b64_size_mb > 9.5:
        print(f"  ⚠️ base64 过大 ({b64_size_mb:.1f}MB)，跳过此段")
        return "[音频过长无法转录]"

    client = OpenAI(api_key=api_key, base_url=base_url)
    completion = client.chat.completions.create(
        model="mimo-v2.5-asr",
        messages=[{
            "role": "user",
            "content": [{
                "type": "input_audio",
                "input_audio": {
                    "data": f"data:audio/wav;base64,{audio_b64}"
                }
            }]
        }],
        extra_body={"asr_options": {"language": language}},
    )
    return completion.choices[0].message.content.strip()


def run_asr(input_path, segment_seconds=30, language="zh", output_path=None):
    """完整流程：切片 → 逐段 ASR → 拼接结果"""
    load_env()
    api_key = os.environ.get("XIAOMI_API_KEY", "")
    base_url = os.environ.get("XIAOMI_BASE_URL", "https://api.xiaomimimo.com/v1")

    if not api_key:
        print("❌ 未找到 XIAOMI_API_KEY，请在 /opt/data/.env 中配置")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. 切片
        segments = split_audio(input_path, segment_seconds, tmpdir)

        # 2. 逐段 ASR
        results = []
        for i, (wav_path, start_s, end_s) in enumerate(segments):
            print(f"  🎤 ASR 段 {i+1}/{len(segments)}...", end="", flush=True)
            t0 = time.time()
            text = transcribe_segment(wav_path, api_key, base_url, language)
            elapsed = time.time() - t0
            print(f" {elapsed:.1f}s | {len(text)}字")
            results.append({
                "segment": i + 1,
                "start": start_s,
                "end": end_s,
                "text": text,
            })

    # 3. 拼接
    full_text = "\n".join(r["text"] for r in results)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 转录结果已保存: {output_path}")

    print(f"\n=== 完整转录 ({len(full_text)}字) ===")
    print(full_text)

    return results, full_text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="音频切片 ASR 转录工具")
    parser.add_argument("input", help="输入音频文件路径 (m4a/wav/mp3)")
    parser.add_argument("--segment-seconds", type=int, default=30, help="每段时长秒数 (默认30)")
    parser.add_argument("--output", "-o", help="输出 JSON 文件路径")
    parser.add_argument("--language", default="zh", help="语言 (zh/en/auto)")
    args = parser.parse_args()

    run_asr(args.input, args.segment_seconds, args.language, args.output)
