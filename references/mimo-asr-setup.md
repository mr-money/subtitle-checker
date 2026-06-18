# MiMo-V2.5-ASR 语音识别配置

## 概述
小米提供专用ASR模型 `mimo-v2.5-asr`，支持中英双语、方言、噪声环境、专业术语识别。

## 配置方式
Hermes STT使用 `command` 类型provider调用外部脚本：

**脚本位置**: `/opt/data/scripts/mimo_asr.py`

**config.yaml 配置**:
```yaml
stt:
  provider: mimo
  providers:
    mimo:
      type: command
      command: "python3 /opt/data/scripts/mimo_asr.py {input_path} {output_path} {language}"
      language: zh
      timeout: 300
```

## API详情
- **端点**: `https://api.xiaomimimo.com/v1/chat/completions`
- **模型**: `mimo-v2.5-asr`
- **格式**: wav、mp3（其他格式自动ffmpeg转换）
- **编码**: base64，上限10MB
- **环境变量**: `XIAOMI_API_KEY`（在 `.env` 中配置）

## 占位符说明
| 占位符 | 说明 |
|--------|------|
| `{input_path}` | 音频文件绝对路径 |
| `{output_path}` | 输出转录文本路径 |
| `{language}` | 语言代码（zh/en/auto） |

## 与字幕检查流程配合
1. 用 mimo-asr 转录音频 → 生成初始SRT
2. 用 subtitle-checker 修正错字、拆分长行
3. 输出最终字幕文件

## 注意事项
- m4a等非wav/mp3格式会自动用ffmpeg转换
- API key从 `~/.hermes/.env` 读取
- 转录结果直接写入 `{output_path}`，同时输出到stdout
