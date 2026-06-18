---
name: subtitle-checker
description: "检查并修正语音转录字幕文件(SRT格式)：修复ASR错字、强制每行≤10汉字、智能分段重分配时间轴、繁转简。适用于任何中文演讲/教学类字幕。"
version: 1.0.0
author: mr-money
license: MIT
metadata:
  hermes:
    tags: [subtitle, srt, asr, chinese, nlp, media]
    related_skills: []
---

# 字幕检查与修正 Skill

## Overview

中文SRT字幕检查与修正工具，专为语音识别(ASR)生成的中文演讲/教学类字幕设计。支持错字修正、智能长行拆分、繁转简、时间轴重分配。

提供 Python 和 Node.js 两个版本，零外部依赖。

## When to Use

- 用户提供了 ASR 生成的中文 SRT 字幕文件需要修正
- 需要修正错字、控制每行长度、保证时间轴对齐
- 繁体中文内容需要转简体
- 批量处理多个字幕文件

## 安装方式

### 方式一：Hermes Agent 技能安装

```bash
hermes skill install github:mr-money/subtitle-checker
```

### 方式二：手动克隆

```bash
git clone git@github.com:mr-money/subtitle-checker.git ~/.hermes/skills/media/subtitle-checker
```

### 方式三：直接使用脚本

无需安装技能，直接下载 `scripts/subtitle_fixer.py` 即可使用。

## 快速开始

### Python CLI

```bash
# 基本用法（输出到同目录 _fixed.srt）
python scripts/subtitle_fixer.py input.srt

# 指定错字修正词典 + 详细输出
python scripts/subtitle_fixer.py input.srt --corrections fixes.json --max-chars 10 --verbose

# 指定输出路径
python scripts/subtitle_fixer.py input.srt -o output_fixed.srt
```

### Node.js API

```javascript
const { processFile } = require('./scripts/subtitle_fixer');

const result = processFile(
  'input.srt',                    // 输入文件
  { '严实出高徒': '严师出高徒' }, // 错字修正词典
  10,                             // 每行最大汉字数
  'output_fixed.srt'              // 输出文件
);

console.log(`原始: ${result.stats.orig} → 输出: ${result.stats.out}`);
console.log(`修正: ${result.stats.fix} | 拆分: ${result.stats.split}`);
```

## 核心规则

1. 识别并修改ASR错字
2. 每行字幕长度**不能超过10个汉字**（10允许，11不允许）
3. 超长时根据语境智能分段，平分所属时间段
4. 每条字幕只有一行，不允许出现2行
5. 分段后必须语义通顺
6. **未修改部分的时间轴必须和原内容对齐**
7. 繁体中文→简体中文
8. **绝不修改正确的白话文部分**（字幕要和音频一一对应）

## 批量处理流程（Hermes Agent 推荐）

当用户提供多个文件夹（如 `{日期}-{序号}/` 每个含 `index.m4a` + `index.txt`）时：

### 第一步：全部读取，建立全局理解

```python
# 用 read_file 一次性读取所有 index.txt
# 不要边读边改——先理解每个文件的内容主题
```

- 理解演讲者风格、常见用词、专业术语
- 标记明显的ASR错误模式（同音替换、专有名词误识、古文引用错误）

### 第二步：评估ASR可行性

```bash
ls -lh /path/to/*/index.m4a
# m4a → wav 体积膨胀 ~10x；base64 再膨胀 ~33%
# 5MB m4a → wav ~50MB → base64 ~67MB → 远超 10MB 限制
```

- **单个 m4a > 1MB** → wav base64 大概率超 10MB → ASR不可用
- 超限时：跳过ASR校验，进入手动修正流程

### 第三步：构建修正词典

逐文件构建 `corrections` 字典。**key 必须是原文中的精确子串**。

```python
corrections = {
    "严实出高徒": "严师出高徒",     # 同音替换
    "运心去领悟": "用心去领悟",     # 方言口音
    "非礼物事": "非礼勿视",        # 古文引用
    "南淮锦先生": "南怀瑾先生",    # 专有名词
}
```

### 第四步：execute_code 批量处理

```python
import re, os

# [使用 scripts/subtitle_fixer.py 中的函数]

base = "/path/to/字幕检查"
all_corrections = {
    "folder1": c1, "folder2": c2, ...
}

total = {'orig': 0, 'out': 0, 'fix': 0, 'split': 0}
for folder in sorted(all_corrections.keys()):
    input_path = os.path.join(base, folder, "index.txt")
    output_path = os.path.join(base, folder, "index_fixed.txt")
    entries, changes, stats = process_file(
        input_path, all_corrections[folder], max_chars=10, output_path=output_path)
    for k in total: total[k] += stats[k]
    print(f"✅ {folder}: {stats['orig']}→{stats['out']}条 | 修正:{stats['fix']} | 拆分:{stats['split']}")
```

### 第五步：验证 + 报告

- 检查 `stats['fix']`——如果某文件修正数为 0，说明 key 不匹配，需要重新检查原文
- 输出汇总统计表
- 所有行 ≤10 汉字验证通过后完成

## 智能拆分算法

当一行字幕超过 `max_chars` 个汉字时：

1. **评分机制**选择最佳断点：
   - 标点后断 → 最优 (-50分)
   - 虚词"的了着"后断 → 优秀 (-30分)
   - 不可拆词之前断 → 好 (-20分)
   - 切断2字词 → 差 (+100分)
   - 切断多字词组 → 很差 (+150分)
   - 孤立片段(≤2字) → 差 (+60分)

2. **递归拆分**直到每段 ≤ max_chars

3. **时间轴**按字数比例分配，最后一段精确到原结束时间

## 错字修正词典

创建 JSON 文件，key 为 ASR 错误文本，value 为正确文本：

```json
{
  "严实出高徒": "严师出高徒",
  "运心去领悟": "用心去领悟",
  "非礼物事": "非礼勿视",
  "南淮锦": "南怀瑾",
  "九指离火运": "九紫离火运"
}
```

> ⚠️ **重要**：key 必须是SRT文件中的**精确子串**，否则不会匹配。

## 常见 ASR 错字模式

详见 `references/asr-error-patterns.md`，包含：
- 同音/近音替换（成语、古文、常用词）
- 专有名词误识（人名、文化术语）
- 口语化误识（动词/名词混淆）
- 判断原则（必须修正 vs 保持原样）

## 音频转录（可选）

如有原始音频且 <1MB，可用 mimo-v2.5-asr 转录后对比修正。
详见 `references/mimo-asr-api.md`。

## Common Pitfalls

### 1. 修正词典 key 必须精确匹配原文

**最常见的错误！** 构建 `corrections` 时，key 必须是 SRT 中的**精确子串**。

```python
# ❌ 错误：你以为原文是"浑色"，但实际是"组设就都是浑的"
"浑色": "红色"  # key不存在，修正数=0

# ✅ 正确：用原文中的精确子串
"组设就都是浑的": "主色调就都是红的"
```

**验证方法：** 处理完后检查 `stats['fix']`——如果某文件修正数为 0，立即重新检查原文。

### 2. 繁简转换时机

繁→简必须在应用修正词典**之前**。否则简体 key 匹配不到繁体原文。脚本已内置此顺序。

### 3. ASR API 10MB 限制

mimo-v2.5-asr base64 上限 10MB。m4a→wav 膨胀 ~10x，base64 再膨胀 ~33%。
- **>1MB 的 m4a → ASR 不可用**，走手动修正流程

### 4. 不可修改的内容

- 口语化表达（"你放心好了"）→ 保持原样
- 演讲者可能故意的说法 → 保持原样
- 不确定的修正 → 标记 `[?]` 或保持原样

## Verification Checklist

- [ ] 所有行 ≤ max_chars 汉字
- [ ] 修正数 > 0（否则 key 不匹配）
- [ ] 时间轴连续无重叠
- [ ] 不可拆词组未被切断
- [ ] 繁体已全部转简体
