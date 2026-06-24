#!/usr/bin/env python3
"""
字幕检查与修正工具 v2 - 修复版
用法: python subtitle_fixer.py <input_srt> [--max-chars 10] [--corrections corrections.json] [--output output.txt]

输入: SRT格式字幕文件
输出: 修正后的SRT文件（默认同目录 <原名>_fixed.txt）
"""

import re
import sys
import json
import os
import argparse

# ===== 数据目录 =====
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

def _load_json_list(filename):
    """从data目录加载JSON数组文件，过滤掉以_开头的注释项"""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [x for x in data if not x.startswith('_')]

def _load_json_dict(filename):
    """从data目录加载JSON对象文件，过滤掉以_开头的key"""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith('_')}


# ===== 基础工具 =====

def count_chinese(text):
    """统计汉字数量（不含标点、英文、数字）"""
    return sum(1 for c in text if '\u4e00' <= c <= '\u9fff')


def time_to_ms(t):
    """SRT时间字符串 → 毫秒"""
    h, m, rest = t.split(':')
    s, ms = rest.split(',')
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)


def ms_to_time(ms):
    """毫秒 → SRT时间字符串"""
    if ms < 0:
        ms = 0
    h = ms // 3600000; ms %= 3600000
    m = ms // 60000; ms %= 60000
    s = ms // 1000; ms %= 1000
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


# ===== SRT解析 =====

def parse_srt(filepath):
    """解析SRT文件，返回字幕条目列表"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    blocks = re.split(r'\n\s*\n', content.strip())
    entries = []
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        try:
            idx = int(lines[0].strip())
        except ValueError:
            continue
        tm = re.match(
            r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})',
            lines[1].strip()
        )
        if not tm:
            continue
        entries.append({
            'idx': idx,
            'start': tm.group(1), 'end': tm.group(2),
            'start_ms': time_to_ms(tm.group(1)),
            'end_ms': time_to_ms(tm.group(2)),
            'text': '\n'.join(lines[2:]).strip(),
        })
    return entries


# ===== 繁→简转换 =====

# 使用字典映射，更可靠（避免字符串长度不匹配导致错位）
_TRAD_TO_SIMP = {
    '學': '学', '書': '书', '樂': '乐', '禮': '礼', '歲': '岁',
    '國': '国', '問': '问', '開': '开', '關': '关', '來': '来',
    '車': '车', '長': '长', '門': '门', '馬': '马', '說': '说',
    '讀': '读', '認': '认', '請': '请', '誰': '谁', '對': '对',
    '過': '过', '還': '还', '進': '进', '選': '选', '錢': '钱',
    '經': '经', '練': '练', '給': '给', '華': '华', '實': '实',
    '義': '义', '機': '机', '結': '结', '體': '体', '響': '响',
    '這': '这', '從': '从', '們': '们', '個': '个', '會': '会',
    '樣': '样', '現': '现', '當': '当', '業': '业', '發': '发',
    '備': '备', '歷': '历', '氣': '气', '號': '号', '畫': '画',
    '話': '话', '壞': '坏', '歡': '欢', '環': '环', '換': '换',
    '獲': '获', '擊': '击', '積': '积', '極': '极', '際': '际',
    '繼': '继', '堅': '坚', '減': '减', '檢': '检', '見': '见',
    '將': '将', '獎': '奖', '講': '讲', '腳': '脚', '階': '阶',
    '節': '节', '僅': '仅', '緊': '紧', '盡': '尽', '競': '竞',
    '舉': '举', '據': '据', '覺': '觉', '軍': '军', '類': '类',
    '裏': '里', '離': '离', '聯': '联', '靈': '灵', '領': '领',
    '錄': '录', '論': '论', '難': '难', '農': '农', '盤': '盘',
    '憑': '凭', '齊': '齐', '騎': '骑', '啟': '启', '簽': '签',
    '牆': '墙', '親': '亲', '窮': '穷', '區': '区', '權': '权',
    '勸': '劝', '確': '确', '讓': '让', '熱': '热', '軟': '软',
    '殺': '杀', '聲': '声', '勝': '胜', '濕': '湿', '識': '识',
    '勢': '势', '術': '术', '數': '数', '雙': '双', '順': '顺',
    '隨': '随', '損': '损', '縮': '缩', '態': '态', '嘆': '叹',
    '調': '调', '鐵': '铁', '圖': '图', '團': '团', '穩': '稳',
    '務': '务', '習': '习', '戲': '戏', '嚇': '吓', '險': '险',
    '鄉': '乡', '協': '协', '寫': '写', '謝': '谢', '興': '兴',
    '壓': '压', '養': '养', '億': '亿', '陰': '阴', '應': '应',
    '營': '营', '優': '优', '魚': '鱼', '語': '语', '園': '园',
    '遠': '远', '願': '愿', '雲': '云', '戰': '战', '鎮': '镇',
    '爭': '争', '織': '织', '職': '职', '紙': '纸', '製': '制',
    '質': '质', '眾': '众', '專': '专', '裝': '装', '準': '准',
    '資': '资', '總': '总', '組': '组', '產': '产', '廠': '厂',
    '稱': '称', '處': '处', '創': '创', '詞': '词', '導': '导',
    '斷': '断', '隊': '队', '兒': '儿', '豐': '丰', '婦': '妇',
    '趕': '赶', '溝': '沟', '穀': '谷', '顧': '顾', '掛': '挂',
    '館': '馆', '慣': '惯', '護': '护', '匯': '汇', '級': '级',
    '價': '价', '簡': '简', '膠': '胶', '潔': '洁', '課': '课',
    '況': '况', '擴': '扩', '蘭': '兰', '藍': '蓝', '糧': '粮',
    '療': '疗', '齡': '龄', '輪': '轮', '羅': '罗', '買': '买',
    '賣': '卖', '貓': '猫', '滅': '灭', '謀': '谋', '歐': '欧',
    '噴': '喷', '騙': '骗', '飄': '飘', '鋪': '铺', '擾': '扰',
    '潤': '润', '賽': '赛', '傘': '伞', '曬': '晒', '設': '设',
    '審': '审', '樹': '树', '碩': '硕', '鬆': '松', '討': '讨',
    '題': '题', '託': '托', '衛': '卫', '窩': '窝', '鮮': '鲜',
    '縣': '县', '獻': '献', '尋': '寻', '訓': '训', '搖': '摇',
    '憶': '忆', '銀': '银', '隱': '隐', '郵': '邮', '漁': '渔',
    '雜': '杂', '災': '灾', '漲': '涨', '診': '诊', '燭': '烛',
    '鑽': '钻', '償': '偿', '蟲': '虫', '醜': '丑', '轉': '转',
    '為': '为', '於': '于', '與': '与', '藝': '艺', '億': '亿',
    '娛': '娱', '獄': '狱', '載': '载', '暫': '暂', '贊': '赞',
    '臟': '脏', '則': '则', '責': '责', '澤': '泽', '賊': '贼',
    '贈': '赠', '詐': '诈', '齋': '斋', '債': '债', '佔': '占',
    '帳': '账', '脹': '胀', '趙': '赵', '針': '针', '偵': '侦',
    '陣': '阵', '徵': '征', '證': '证', '執': '执', '種': '种',
    '週': '周', '軸': '轴', '驟': '骤', '磚': '砖', '賺': '赚',
    '莊': '庄', '壯': '壮', '狀': '状', '綜': '综', '縱': '纵',
}

def trad_to_simp(text):
    """繁体→简体"""
    result = text
    for trad, simp in _TRAD_TO_SIMP.items():
        result = result.replace(trad, simp)
    return result


# ===== 错字修正 =====

def apply_corrections(text, corrections):
    """应用错字修正字典，按key长度降序匹配"""
    for wrong, right in sorted(corrections.items(), key=lambda x: -len(x[0])):
        text = text.replace(wrong, right)
    return text


# ===== 智能拆分 v2 =====

# --- 2字不可拆词（相邻两字不可从中间断） ---
NO_SPLIT_2 = set(_load_json_list('no_split_2.json'))

# --- 多字不可断词组（整个词组不可被拆开，任何位置都不行） ---
NO_SPLIT_PHRASES = _load_json_list('no_split_phrases.json')

# 按长度降序排列（优先匹配长词）
NO_SPLIT_PHRASES_SORTED = sorted(NO_SPLIT_PHRASES, key=len, reverse=True)

# 可安全放在行尾的虚词
TAIL_SAFE = set('的了着过得地')


def would_break_phrase(text, pos):
    """
    检查在 position pos 处断开是否会切断任何不可断词组。
    遍历所有词组，检查是否有词组跨越 pos。
    返回 (True, phrase) 或 (False, None)
    """
    for phrase in NO_SPLIT_PHRASES_SORTED:
        plen = len(phrase)
        # 词组在 text 中的所有出现位置
        start = 0
        while True:
            idx = text.find(phrase, start)
            if idx == -1:
                break
            phrase_end = idx + plen
            # 如果断点在词组内部（不包括恰好在词组边界）
            if idx < pos < phrase_end:
                return True, phrase
            start = idx + 1
    return False, None


def would_break_2word(text, pos):
    """
    检查在 position pos 处断开是否会切断任何2字不可拆词。
    检查 pos-1|pos 和 pos|pos+1 两个边界。
    """
    if pos > 0 and pos < len(text):
        two = text[pos - 1] + text[pos]
        if two in NO_SPLIT_2:
            return True, two
    return False, None


def smart_split(text, max_chars=10):
    """智能拆分文本，每段不超过max_chars个汉字。递归处理。"""
    if count_chinese(text) <= max_chars:
        return [text]
    result = _do_split(text, max_chars)
    final = []
    for r in result:
        if count_chinese(r) > max_chars:
            final.extend(smart_split(r, max_chars))
        elif count_chinese(r) == 0:
            continue
        else:
            final.append(r)
    return final if final else [text]


def _do_split(text, max_chars):
    """单次拆分：评分机制选最佳断点"""
    cn_total = count_chinese(text)
    candidates = []
    ideal_left = cn_total / 2

    for i in range(1, len(text)):
        left_cn = count_chinese(text[:i])
        right_cn = count_chinese(text[i:])

        # 至少每边2个汉字
        if left_cn < 2 or right_cn < 2:
            continue
        if left_cn > max_chars or right_cn > max_chars:
            continue

        score = abs(left_cn - ideal_left) * 10
        prev = text[i - 1] if i > 0 else ''
        c = text[i]

        # === 优秀断点（大幅减分） ===
        # 标点后断 → 最佳
        if prev in '，。、；！？,;：:':
            score -= 50
        # "的了着"后断 → 好
        if prev in TAIL_SAFE:
            score -= 30
        # 2字词之前断（保护词完整性）→ 好
        two = text[i:i + 2] if i + 1 < len(text) else ''
        if two in NO_SPLIT_2:
            score -= 20

        # === 禁止断点（大幅加分） ===
        # 检查是否切断2字词
        breaks_2, word_2 = would_break_2word(text, i)
        if breaks_2:
            score += 100

        # 检查是否切断多字词组（这是v2的核心改进）
        breaks_phrase, phrase = would_break_phrase(text, i)
        if breaks_phrase:
            score += 150  # 比2字词惩罚更重

        # 左或右≤2汉字（孤立字）→ 差
        if left_cn <= 2:
            score += 60
        if right_cn <= 2:
            score += 60
        # 右以虚词开头且很短 → 差
        if c in TAIL_SAFE and right_cn <= 4:
            score += 40

        candidates.append((i, score))

    if not candidates:
        # 无合法候选，强制从中间断
        mid = len(text) // 2
        return [text[:mid], text[mid:]]

    best = min(candidates, key=lambda x: x[1])
    pos = best[0]
    return [text[:pos].strip(), text[pos:].strip()]


# ===== 主处理函数 =====

def process_file(input_path, corrections=None, max_chars=10, output_path=None):
    """
    处理SRT字幕文件。

    参数:
        input_path: 输入SRT文件路径
        corrections: 错字修正字典 {错误文本: 正确文本}
        max_chars: 每行最大汉字数（默认10）
        output_path: 输出文件路径（默认同目录 <原名>_fixed.txt）

    返回:
        (entries, changes, stats)
    """
    if corrections is None:
        corrections = {}
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_fixed{ext}"

    entries = parse_srt(input_path)
    changes = []
    new_entries = []
    stats = {'orig': len(entries), 'out': 0, 'fix': 0, 'split': 0}

    for e in entries:
        text = e['text']
        idx = e['idx']
        s_ms, e_ms = e['start_ms'], e['end_ms']

        # 1. 繁→简
        text = trad_to_simp(text)

        # 2. 错字修正
        t3 = apply_corrections(text, corrections)
        if t3 != text:
            stats['fix'] += 1
            changes.append(f"#{idx} 修正: '{text}' → '{t3}'")
        text = t3

        # 3. 长度检查+拆分
        cn = count_chinese(text)
        if cn > max_chars:
            splits = smart_split(text, max_chars)
            stats['split'] += 1
            total_cn = sum(count_chinese(s) for s in splits)
            dur = e_ms - s_ms
            cur = s_ms
            for i, st in enumerate(splits):
                sc = count_chinese(st)
                portion = sc / total_cn if total_cn > 0 else 1 / len(splits)
                seg_dur = int(dur * portion)
                seg_end = cur + seg_dur if i < len(splits) - 1 else e_ms
                new_entries.append({
                    'start_ms': cur, 'end_ms': seg_end, 'text': st.strip()
                })
                cur = seg_end
            changes.append(
                f"#{idx} 拆分({cn}字→{len(splits)}行): "
                f"{[s.strip() for s in splits]}"
            )
        else:
            new_entries.append({
                'start_ms': s_ms, 'end_ms': e_ms, 'text': text
            })

    # 重新编号
    for i, e in enumerate(new_entries, 1):
        e['idx'] = i
    stats['out'] = len(new_entries)

    # 写入文件
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            for e in new_entries:
                f.write(f"{e['idx']}\n")
                f.write(f"{ms_to_time(e['start_ms'])} --> {ms_to_time(e['end_ms'])}\n")
                f.write(f"{e['text']}\n\n")

    return new_entries, changes, stats


# ===== 验证工具 =====

def validate_output(entries, max_chars=10, no_break_phrases=None):
    """
    验证输出质量。返回问题列表。
    """
    issues = []

    # 检查每行字数
    for e in entries:
        cn = count_chinese(e['text'])
        if cn > max_chars:
            issues.append(f"#{e['idx']} 超限: '{e['text']}' ({cn}字)")

    # 检查相邻行是否断开了不可断词组
    if no_break_phrases:
        for i in range(len(entries) - 1):
            t1 = entries[i]['text']
            t2 = entries[i + 1]['text']
            for phrase in no_break_phrases:
                for sp in range(1, len(phrase)):
                    if t1.endswith(phrase[:sp]) and t2.startswith(phrase[sp:]):
                        issues.append(
                            f"#{entries[i]['idx']}+#{entries[i+1]['idx']} "
                            f"断词: '{t1}'|'{t2}' → [{phrase}]"
                        )
                        break

    return issues


# ===== CLI入口 =====

def main():
    parser = argparse.ArgumentParser(description='字幕检查与修正工具 v2')
    parser.add_argument('input', help='输入SRT文件路径')
    parser.add_argument('--max-chars', type=int, default=10,
                        help='每行最大汉字数（默认10）')
    parser.add_argument('--corrections',
                        help='错字修正JSON文件路径 {错误: 正确}')
    parser.add_argument('--output', '-o',
                        help='输出文件路径（默认同目录 _fixed.txt）')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='显示详细变更')
    args = parser.parse_args()

    corrections = {}
    if args.corrections and os.path.exists(args.corrections):
        with open(args.corrections, 'r', encoding='utf-8') as f:
            corrections = json.load(f)
    else:
        # 尝试加载默认词典
        default_corr_path = os.path.join(DATA_DIR, 'default_corrections.json')
        if os.path.exists(default_corr_path):
            corrections = _load_json_dict('default_corrections.json')
            print(f"使用默认词典: {default_corr_path} ({len(corrections)}条)")

    entries, changes, stats = process_file(
        args.input, corrections, args.max_chars, args.output
    )

    # 输出统计
    print(f"\n=== 字幕检查报告 ===")
    print(f"原始条目: {stats['orig']} → 输出条目: {stats['out']}")
    print(f"错字修正: {stats['fix']} 条")
    print(f"超长拆分: {stats['split']} 条")

    if args.verbose:
        print(f"\n--- 变更明细 ---")
        for c in changes:
            print(f"  {c}")

    # 验证
    issues = validate_output(entries, args.max_chars, NO_SPLIT_PHRASES)
    if issues:
        print(f"\n⚠️ 发现{len(issues)}个问题:")
        for iss in issues:
            print(f"  {iss}")
    else:
        print(f"\n✅ 全部行≤{args.max_chars}汉字，无断词问题")


if __name__ == '__main__':
    main()
