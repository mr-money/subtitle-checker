# MiMo-V2.5-ASR API 参考

## 概述

小米 MiMo-V2.5-ASR 是专用语音识别模型，支持中英双语、方言、噪声环境，自动标点。

- 模型ID: `mimo-v2.5-asr`
- API地址: `https://api.xiaomimimo.com/v1`
- 兼容 OpenAI SDK
- 支持流式/非流式调用

## 支持的音频格式

| 格式 | MIME类型 | 备注 |
|------|----------|------|
| wav | `audio/wav` | 推荐 |
| mp3 | `audio/mpeg` 或 `audio/mp3` | |

- 需转为 Base64 编码
- Base64后大小上限 10MB
- m4a 格式不直接支持，需先转换: `ffmpeg -i input.m4a output.wav`

## 语言参数

`asr_options.language`:
- `auto` — 自动检测（默认）
- `zh` — 中文
- `en` — 英文

## 调用示例

### Python (OpenAI SDK)

```python
import base64
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_MIMO_API_KEY",
    base_url="https://api.xiaomimimo.com/v1"
)

with open("audio.wav", "rb") as f:
    audio_base64 = base64.b64encode(f.read()).decode("utf-8")

completion = client.chat.completions.create(
    model="mimo-v2.5-asr",
    messages=[{
        "role": "user",
        "content": [{
            "type": "input_audio",
            "input_audio": {
                "data": f"data:audio/wav;base64,{audio_base64}"
            }
        }]
    }],
    extra_body={"asr_options": {"language": "zh"}}
)

# 提取文本
result_text = completion.choices[0].message.content
print(result_text)
```

### m4a 转 wav 后调用

```python
import subprocess, base64
from openai import OpenAI

# 1. 转换格式
subprocess.run(["ffmpeg", "-i", "input.m4a", "-ar", "16000", "-ac", "1", "output.wav"], check=True)

# 2. 读取并base64编码
with open("output.wav", "rb") as f:
    audio_base64 = base64.b64encode(f.read()).decode("utf-8")

# 3. 调用ASR
client = OpenAI(api_key="KEY", base_url="https://api.xiaomimimo.com/v1")
completion = client.chat.completions.create(
    model="mimo-v2.5-asr",
    messages=[{"role": "user", "content": [
        {"type": "input_audio", "input_audio": {"data": f"data:audio/wav;base64,{audio_base64}"}}
    ]}],
    extra_body={"asr_options": {"language": "zh"}}
)
print(completion.choices[0].message.content)
```

## 核心能力

- 中英双语识别 + 自动语种检测
- 方言支持：粤语、吴语、闽南语、四川话等
- 复杂场景：噪声、远场拾音、多人重叠对话
- 专业内容：古诗词、专业术语、人名地名
- 自动标点

## 与字幕检查流程集成

1. 用户提供 m4a 音频文件
2. ffmpeg 转换为 wav（16kHz单声道）
3. mimo-v2.5-asr 转录为文本
4. 按SRT格式构建字幕文件
5. 用 subtitle-checker 流程检查修正错字、拆分长行

## 参考链接

- 官方文档: https://mimo.mi.com/docs/zh-CN/quick-start/usage-guide/multimodal-understanding/Speech-Recognition
- 计费: https://mimo.mi.com/#/docs/pricing
