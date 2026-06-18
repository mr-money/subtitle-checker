# subtitle-checker

中文SRT字幕检查与修正工具 — 修复ASR错字、智能拆分长行、繁转简、时间轴重分配。

专为语音识别(ASR)生成的中文演讲/教学类字幕设计，同时也是一个 [Hermes Agent](https://hermes-agent.nousresearch.com) 技能。

## 功能特性

- 🔤 **ASR错字修正** — 通过自定义词典批量替换识别错误
- ✂️ **智能长行拆分** — 超过指定汉字数时自动分段，语义优先断句
- 🈵 **繁体→简体** — 自动转换繁体中文
- ⏱️ **时间轴重分配** — 拆分后按字数比例平分时间段，无缝衔接
- 🔍 **断词保护** — 内置不可拆词表，避免在成语/连词中间断开
- ✅ **输出验证** — 自动检查每行字数和断词问题

## 安装

### Hermes Agent 技能安装

```bash
# 方式一：直接克隆到技能目录
git clone git@github.com:mr-money/subtitle-checker.git ~/.hermes/skills/media/subtitle-checker

# 方式二：在 Hermes 会话中让 agent 安装
# "帮我安装 subtitle-checker 技能"
```

安装后在新会话中自动可用，触发词：字幕检查、字幕修正、SRT修正、字幕校对。

### 独立使用（无需 Hermes）

```bash
git clone git@github.com:mr-money/subtitle-checker.git
cd subtitle-checker
python scripts/subtitle_fixer.py input.srt --corrections fixes.json -v
```

## 快速开始

### Python CLI

```bash
# 基本用法
python scripts/subtitle_fixer.py input.srt

# 指定错字修正词典和最大字数
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

## 输入/输出格式

**输入**：标准SRT字幕文件

```
1
00:00:01,000 --> 00:00:03,500
这是一个字幕示例

2
00:00:03,500 --> 00:00:06,000
第二行字幕内容
```

**输出**：修正后的SRT文件（序号重新编排，时间轴连续）

```
1
00:00:01,000 --> 00:00:03,500
这是修正后的字幕

2
00:00:03,500 --> 00:00:04,750
超长行会被拆分

3
00:00:04,750 --> 00:00:06,000
按字数比例分配时间
```

## 错字修正词典

创建一个 JSON 文件，key 为 ASR 错误文本，value 为正确文本：

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

## 项目结构

```
subtitle-checker/
├── SKILL.md                        # Hermes Agent 技能定义
├── README.md                       # 本文档
├── scripts/
│   ├── subtitle_fixer.py           # Python 版（完整功能）
│   └── subtitle_fixer.js           # Node.js 版
├── references/
│   ├── mimo-asr-api.md             # MiMo ASR API 参考
│   ├── asr-error-patterns.md       # ASR常见错误模式库
│   └── asr-correction-patterns.md  # 错误修正模式指南
├── examples/
│   ├── sample_input.srt            # 示例输入
│   └── sample_fixes.json           # 示例修正词典
├── LICENSE                         # MIT
└── .gitignore
```

## 依赖

- **Python 版本**：无外部依赖，纯标准库（Python 3.6+）
- **Node.js 版本**：无外部依赖，纯标准库（Node.js 14+）

## 适用场景

- 语音识别(ASR)生成的中文SRT字幕
- 演讲、教学、访谈等口语类内容
- 需要修正错字、控制每行长度、保证时间轴对齐
- 繁体中文内容转简体

## License

MIT
