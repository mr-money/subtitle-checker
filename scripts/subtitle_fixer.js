const fs = require('fs');

// ===== 基础工具 =====
function countChinese(text) {
  let n = 0;
  for (const c of text) if (c.charCodeAt(0) >= 0x4e00 && c.charCodeAt(0) <= 0x9fff) n++;
  return n;
}

function timeToMs(t) {
  const [h, m, rest] = t.split(':');
  const [s, ms] = rest.split(',');
  return +h*3600000 + +m*60000 + +s*1000 + +ms;
}

function msToTime(ms) {
  if (ms < 0) ms = 0;
  const h = Math.floor(ms/3600000); ms %= 3600000;
  const m = Math.floor(ms/60000); ms %= 60000;
  const s = Math.floor(ms/1000); ms %= 1000;
  return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')},${String(ms).padStart(3,'0')}`;
}

// ===== SRT 解析 =====
function parseSrt(path) {
  const content = fs.readFileSync(path, 'utf-8');
  const blocks = content.trim().split(/\n\s*\n/);
  const entries = [];
  for (const block of blocks) {
    const lines = block.trim().split('\n');
    if (lines.length < 3) continue;
    const idx = parseInt(lines[0]);
    if (isNaN(idx)) continue;
    const tm = lines[1].match(/(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})/);
    if (!tm) continue;
    entries.push({
      idx, start: tm[1], end: tm[2],
      startMs: timeToMs(tm[1]), endMs: timeToMs(tm[2]),
      text: lines.slice(2).join('\n').trim()
    });
  }
  return entries;
}

// ===== 繁→简 =====
const T = '學書樂禮歲國問開關來車長門馬說讀認請誰對過還進選錢經練給華實義機結體響這從們個會樣現當業發備歷氣號畫話壞歡環換獲擊積極際繼堅減檢見將獎講腳階節僅緊盡競舉據覺軍類裏離聯靈領錄論難農盤憑齊騎啟簽牆親窮區權勸確讓熱軟殺聲勝濕識勢術數雙順隨損縮態嘆調鐵圖團穩務習戲嚇險鄉協寫謝興選壓養億陰應營優魚語園遠願雲戰鎮爭織職紙製質眾專裝準資總組產廠稱處創詞導斷隊兒豐婦趕個溝穀顧掛館慣護匯級價簡膠潔課況擴蘭藍糧療齡輪羅買賣貓滅謀歐噴騙飄鋪擾潤賽傘曬設審樹碩鬆討題託衛窩鮮縣獻尋訓搖憶銀隱郵漁雜災漲診燭鑽償蟲醜處';
const S = '学书乐礼岁国问关来车长门马说读认请谁对过还进选钱经练给华实义机体响这从们个会样现当业发备历气号画坏欢环换获击积极际继坚减检见将奖讲脚阶节仅紧尽竞举据觉军类里离联灵领录论难农盘凭齐骑启签墙亲穷区权劝确让热软杀声胜湿识势术数双顺随损缩态叹调铁图团稳务习戏吓险乡协写谢兴选压养亿阴应营优鱼语园远愿云战镇争织职纸制质众专装准资总组产厂称处创词导断队儿丰妇赶沟谷顾挂馆惯护汇级价简胶洁课况扩兰蓝粮疗龄轮罗买卖猫灭谋欧喷骗飘铺扰润赛伞晒审树硕松讨题托卫窝鲜县献寻训摇忆银隐邮渔杂灾涨诊烛钻偿虫丑处';
function tradToSimp(text) {
  let r = text;
  for (let i = 0; i < T.length; i++) r = r.replaceAll(T[i], S[i]);
  return r;
}

// ===== 错字修正 =====
function applyCorrections(text, corrections) {
  let r = text;
  for (const [wrong, right] of Object.entries(corrections).sort((a,b) => b[0].length - a[0].length))
    r = r.replaceAll(wrong, right);
  return r;
}

// ===== 不可拆词表（根据内容主题可扩展） =====
const DEFAULT_NO_SPLIT_WORDS = [
  '所以','因为','但是','而且','或者','然后','如果','就是','而是','不过',
  '因此','虽然','可是','并且','甚至','于是','能够','应该','已经','正在',
  '可以','不是','没有','什么','他们','我们','你们','自己','怎么','为什么',
  '小孩','孩子','先生','老师','父母','家长','大人','年轻人',
  '音乐','乐器','古琴','书法','围棋','象棋','军棋','武术',
  '诗词','诗歌','和尚','尚书','书经','夏令营',
  '人生','底气','格局','志向','兴趣','爱好','世界','宇宙',
  '六十','七十','八十','九十','一个','第一','第二','第三',
  '告诉','培养','教育','发现','认为','需要','开始','喜欢',
  '重要','代表','叫做','知道','看到','听到','感到','学到',
  '下来','起来','出来','过去','过来','上去','到了',
  '中华民族','礼仪之邦','严师出高徒','手无缚鸡之力',
  '取法乎上','取法乎中','诗词歌赋','宫商角徵羽',
  '礼乐射御书数','一砖一瓦','大道至简','剑胆琴心',
  '大气磅礴','一贫如洗','周游列国','千军万马',
  '但问耕耘','莫问收获','保家卫国','修身齐家',
  '低级趣味','人生下半场','兴趣爱好',
  '孔老夫子','曾国藩','太极文化',
  '告诉小孩','培养小孩','教育小孩',
  '知礼节','懂礼仪','驾马车',
  '胸怀天下','有王者之气','有自信','有信心',
  '人生观','世界观','方法论',
  '慧命','君子六艺','小孩子','老夫子','怎么样','差不多',
  '大多数人','很多人','无数人',
];

const TAIL_SAFE = new Set('的了着过得地');

// ===== 核心：检查断点是否会切开不可拆词 =====
function wouldBreakWord(text, pos, noSplitSet) {
  for (const w of noSplitSet) {
    const wl = w.length;
    for (let start = Math.max(0, pos - wl + 1); start < pos; start++) {
      const end = start + wl;
      if (end <= text.length && text.slice(start, end) === w) {
        if (start < pos && pos < end) return { word: w, penalty: 120 };
      }
    }
  }
  return null;
}

// ===== 智能拆分 =====
function smartSplit(text, maxChars, noSplitSet) {
  if (countChinese(text) <= maxChars) return [text];
  const result = doSplit(text, maxChars, noSplitSet);
  const final = [];
  for (const r of result) {
    if (countChinese(r) > maxChars) final.push(...smartSplit(r, maxChars, noSplitSet));
    else if (countChinese(r) === 0) continue;
    else final.push(r);
  }
  return final.length ? final : [text];
}

function doSplit(text, maxChars, noSplitSet) {
  const cnTotal = countChinese(text);
  const candidates = [];
  const idealLeft = cnTotal / 2;

  for (let i = 1; i < text.length; i++) {
    const leftCn = countChinese(text.slice(0, i));
    const rightCn = countChinese(text.slice(i));
    if (leftCn < 2 || rightCn < 2) continue;
    if (leftCn > maxChars || rightCn > maxChars) continue;

    let score = Math.abs(leftCn - idealLeft) * 10;
    const prev = text[i-1];
    const c = text[i];

    if ('，。、；！？,;：:'.includes(prev)) score -= 50;
    if (TAIL_SAFE.has(prev)) score -= 30;

    // 核心：检查是否会在不可拆词中间断开
    const broken = wouldBreakWord(text, i, noSplitSet);
    if (broken) score += broken.penalty;

    // 右侧以不可拆词开头 → 保护右侧
    for (const w of noSplitSet) {
      if (text.slice(i, i + w.length) === w) { score -= 25; break; }
    }
    // 左侧以不可拆词结尾 → 保护左侧
    for (const w of noSplitSet) {
      if (i >= w.length && text.slice(i - w.length, i) === w) { score -= 15; break; }
    }

    if (leftCn <= 2) score += 60;
    if (rightCn <= 2) score += 60;
    if (TAIL_SAFE.has(c) && rightCn <= 4) score += 40;

    candidates.push({ pos: i, score });
  }

  if (!candidates.length) {
    const mid = Math.floor(text.length / 2);
    return [text.slice(0, mid), text.slice(mid)];
  }

  candidates.sort((a, b) => a.score - b.score);
  const pos = candidates[0].pos;
  return [text.slice(0, pos).trim(), text.slice(pos).trim()];
}

// ===== 主处理函数 =====
function processFile(inputPath, corrections, maxChars, outputPath, extraWords) {
  const noSplitSet = new Set([...DEFAULT_NO_SPLIT_WORDS, ...(extraWords || [])]);
  const entries = parseSrt(inputPath);
  const changes = [];
  const newEntries = [];
  const stats = { orig: entries.length, out: 0, fix: 0, split: 0 };

  for (const e of entries) {
    let text = tradToSimp(e.text);
    const t3 = applyCorrections(text, corrections);
    if (t3 !== text) { stats.fix++; changes.push(`#${e.idx} 修正`); }
    text = t3;

    const cn = countChinese(text);
    if (cn > maxChars) {
      const splits = smartSplit(text, maxChars, noSplitSet);
      stats.split++;
      const totalCn = splits.reduce((s, t) => s + countChinese(t), 0);
      const dur = e.endMs - e.startMs;
      let cur = e.startMs;
      for (let i = 0; i < splits.length; i++) {
        const sc = countChinese(splits[i]);
        const segDur = Math.floor(dur * (totalCn > 0 ? sc / totalCn : 1 / splits.length));
        const segEnd = i < splits.length - 1 ? cur + segDur : e.endMs;
        newEntries.push({ startMs: cur, endMs: segEnd, text: splits[i].trim() });
        cur = segEnd;
      }
      changes.push(`#${e.idx} 拆分(${cn}字→${splits.length}行): [${splits.map(s=>s.trim()).join('|')}]`);
    } else {
      newEntries.push({ startMs: e.startMs, endMs: e.endMs, text });
    }
  }

  newEntries.forEach((e, i) => e.idx = i + 1);
  stats.out = newEntries.length;

  if (outputPath) {
    let out = '';
    for (const e of newEntries) out += `${e.idx}\n${msToTime(e.startMs)} --> ${msToTime(e.endMs)}\n${e.text}\n\n`;
    fs.writeFileSync(outputPath, out, 'utf-8');
  }
  return { entries: newEntries, changes, stats };
}

// ===== 验证工具 =====
function verifyNoBrokenPhrases(entries, phrases) {
  const broken = [];
  for (let i = 0; i < entries.length - 1; i++) {
    const t1 = entries[i].text, t2 = entries[i+1].text, combined = t1 + t2;
    for (const p of phrases) {
      if (combined.includes(p) && !t1.includes(p) && !t2.includes(p))
        broken.push({ idx1: entries[i].idx, idx2: entries[i+1].idx, t1, t2, phrase: p });
    }
  }
  return broken;
}

function verifyMaxChars(entries, maxChars) {
  return entries.filter(e => countChinese(e.text) > maxChars);
}

module.exports = {
  countChinese, timeToMs, msToTime, parseSrt, tradToSimp,
  applyCorrections, smartSplit, processFile,
  verifyNoBrokenPhrases, verifyMaxChars,
  DEFAULT_NO_SPLIT_WORDS
};
