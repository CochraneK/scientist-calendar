// 单日人物分享海报（Canvas 2D 客户端生成，1080x1440 竖版 3:4）。
// 沿用主站暖纸质感与印刷体层级：不引入任何外部字体或第三方重依赖。

import type { ScientistSummary } from "../domain/calendar";

export type PosterInput = {
  scientist: ScientistSummary;
  quote?: { text: string; source: string };
  fact?: string;
  portraitUrl: string | null;
};

const TONE_COLORS: Record<string, { bg: string; accent: string }> = {
  blue: { bg: "#c9dae7", accent: "#42657d" },
  coral: { bg: "#f1b8a7", accent: "#a85240" },
  gold: { bg: "#f0d88d", accent: "#8c6918" },
  green: { bg: "#bed8b6", accent: "#3f6939" },
  violet: { bg: "#c9bee1", accent: "#5a4a7d" },
};

const PAPER = "#f7f1e7";
const CREAM = "#fdfaf4";
const INK = "#15263d";
const MUTED = "#5a6978";
const LINE = "#d6cdbd";

/**
 * 按视觉宽度对中英混排文本折行（纯函数，可直接做 Node 单测）。
 * measureWidth 由调用方传入（浏览器传 ctx.measureText(s).width，测试传近似宽度函数）。
 */
export function wrapTextLines(
  text: string,
  maxWidth: number,
  measureWidth: (sample: string) => number,
  maxLines = 4,
): string[] {
  const cleaned = text.replace(/\s+/g, " ").trim();
  if (!cleaned || maxLines <= 0) return [];

  // 按“拉丁连续词 + 单个非拉丁字符”切 token，避免把英文单词从中间切断
  const tokens = cleaned.match(/[A-Za-z0-9]+(?:['’.-][A-Za-z0-9]+)*\s*|\s+|./g) ?? [];
  const lines: string[] = [];
  let current = "";
  let truncated = false;

  for (let i = 0; i < tokens.length; i += 1) {
    const token = tokens[i];
    const candidate = current ? current + token : token.trimStart();
    if (!current || measureWidth(candidate) <= maxWidth) {
      current = candidate;
      continue;
    }

    lines.push(current.trimEnd());
    if (lines.length >= maxLines) {
      truncated = true;
      current = "";
      break;
    }
    current = token.trimStart();
  }

  if (current.trim()) {
    if (lines.length < maxLines) {
      lines.push(current.trimEnd());
    } else {
      truncated = true;
    }
  }

  if (truncated && lines.length > 0) {
    let last = lines[lines.length - 1].replace(/[，、；：,\s]+$/u, "");
    while (last.length > 1 && measureWidth(`${last}…`) > maxWidth) {
      last = last.slice(0, -1);
    }
    lines[lines.length - 1] = `${last}…`;
  }

  return lines;
}

function loadImage(src: string): Promise<HTMLImageElement | null> {
  return new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => resolve(img);
    img.onerror = () => resolve(null);
    img.src = src;
  });
}

function drawRoundedRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

function drawCoverImage(
  ctx: CanvasRenderingContext2D,
  img: HTMLImageElement,
  x: number,
  y: number,
  w: number,
  h: number,
) {
  const imgRatio = img.naturalWidth / Math.max(1, img.naturalHeight);
  const boxRatio = w / h;
  let sx = 0;
  let sy = 0;
  let sw = img.naturalWidth;
  let sh = img.naturalHeight;

  if (imgRatio > boxRatio) {
    sw = img.naturalHeight * boxRatio;
    sx = (img.naturalWidth - sw) / 2;
  } else {
    sh = img.naturalWidth / boxRatio;
    // 肖像优先保留上半张人脸区域（偏移 22% 而非 50%）
    sy = (img.naturalHeight - sh) * 0.22;
  }
  ctx.drawImage(img, sx, sy, sw, sh, x, y, w, h);
}

export async function renderScientistPosterBlob(input: PosterInput): Promise<Blob> {
  const { scientist, quote, portraitUrl } = input;
  const W = 1080;
  const H = 1440;
  const canvas = document.createElement("canvas");
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("浏览器不支持 Canvas 2D 渲染");

  const tone = TONE_COLORS[scientist.color] ?? TONE_COLORS.blue;
  const serif = 'Georgia, "Noto Serif SC", "Songti SC", "STSong", serif';
  const sans = 'Arial, "PingFang SC", "Microsoft YaHei", sans-serif';

  // 1. 纸张底色与外框
  ctx.fillStyle = PAPER;
  ctx.fillRect(0, 0, W, H);

  ctx.fillStyle = tone.bg;
  ctx.fillRect(0, 0, W, 16);

  // 内页细线装帧框
  const pad = 56;
  ctx.strokeStyle = LINE;
  ctx.lineWidth = 2;
  ctx.strokeRect(pad, pad, W - pad * 2, H - pad * 2);

  // 2. 顶部眉栏
  const innerX = pad + 44;
  const innerW = W - (pad + 44) * 2;
  let cursorY = pad + 64;

  ctx.fillStyle = INK;
  ctx.font = `700 26px ${sans}`;
  ctx.textBaseline = "alphabetic";
  ctx.fillText("∴  科学家日历", innerX, cursorY);

  const dateLabel = `${String(scientist.month).padStart(2, "0")}.${String(scientist.day).padStart(2, "0")}  ·  ${scientist.field}`;
  ctx.font = `600 24px ${sans}`;
  ctx.fillStyle = tone.accent;
  const dateW = ctx.measureText(dateLabel).width;
  ctx.fillText(dateLabel, innerX + innerW - dateW, cursorY);

  cursorY += 24;
  ctx.strokeStyle = LINE;
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(innerX, cursorY);
  ctx.lineTo(innerX + innerW, cursorY);
  ctx.stroke();

  // 3. 肖像与姓名头图区
  cursorY += 42;
  const portraitW = 310;
  const portraitH = 380;
  const portraitX = innerX;
  const portraitY = cursorY;

  const loadedImg = portraitUrl ? await loadImage(portraitUrl) : null;

  ctx.save();
  drawRoundedRect(ctx, portraitX, portraitY, portraitW, portraitH, 8);
  ctx.fillStyle = tone.bg;
  ctx.fill();
  ctx.clip();

  if (loadedImg) {
    drawCoverImage(ctx, loadedImg, portraitX, portraitY, portraitW, portraitH);
  } else {
    // 装饰轨道 + 单字版画
    ctx.strokeStyle = "rgba(21, 38, 61, 0.16)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(portraitX + portraitW * 0.5, portraitY + portraitH * 0.48, 124, 0, Math.PI * 2);
    ctx.stroke();

    ctx.fillStyle = INK;
    ctx.font = `600 132px ${serif}`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(scientist.name.slice(0, 1), portraitX + portraitW / 2, portraitY + portraitH * 0.48);

    ctx.font = `500 20px ${sans}`;
    ctx.fillStyle = "rgba(21, 38, 61, 0.72)";
    ctx.fillText(scientist.field, portraitX + portraitW / 2, portraitY + portraitH - 38);
    ctx.textAlign = "left";
    ctx.textBaseline = "alphabetic";
  }
  ctx.restore();

  ctx.strokeStyle = "rgba(21, 38, 61, 0.18)";
  ctx.lineWidth = 1.5;
  drawRoundedRect(ctx, portraitX, portraitY, portraitW, portraitH, 8);
  ctx.stroke();

  // 右侧身份栏
  const infoX = portraitX + portraitW + 44;
  const infoW = innerX + innerW - infoX;
  let infoY = portraitY + 40;

  ctx.fillStyle = tone.accent;
  ctx.font = `600 22px ${sans}`;
  const relLines = wrapTextLines(`${scientist.relation} · ${scientist.years}`, infoW, (s) => ctx.measureText(s).width, 2);
  for (const ln of relLines) {
    ctx.fillText(ln, infoX, infoY);
    infoY += 32;
  }

  infoY += 20;
  ctx.fillStyle = INK;
  const nameSize = scientist.name.length > 7 ? 48 : 58;
  ctx.font = `600 ${nameSize}px ${serif}`;
  const nameLines = wrapTextLines(scientist.name, infoW, (s) => ctx.measureText(s).width, 2);
  for (const ln of nameLines) {
    ctx.fillText(ln, infoX, infoY);
    infoY += nameSize + 12;
  }

  infoY += 4;
  ctx.fillStyle = MUTED;
  ctx.font = `400 23px ${sans}`;
  const latinLines = wrapTextLines(`${scientist.latinName} · ${scientist.country}`, infoW, (s) => ctx.measureText(s).width, 2);
  for (const ln of latinLines) {
    ctx.fillText(ln, infoX, infoY);
    infoY += 32;
  }

  // 阅读线索卡片
  infoY += 18;
  ctx.font = `500 25px ${sans}`;
  const tagLines = wrapTextLines(scientist.tagline, infoW - 24, (s) => ctx.measureText(s).width, 3);
  const tagBarH = Math.max(44, tagLines.length * 36 + 10);
  ctx.fillStyle = tone.accent;
  ctx.fillRect(infoX, infoY - 22, 5, tagBarH);
  ctx.fillStyle = INK;
  let ty = infoY + 4;
  for (const ln of tagLines) {
    ctx.fillText(ln, infoX + 20, ty);
    ty += 36;
  }

  // 4. 名言区（如有）
  cursorY = portraitY + portraitH + 54;
  if (quote?.text) {
    ctx.fillStyle = CREAM;
    const quoteFont = `400 32px ${serif}`;
    ctx.font = quoteFont;
    const qLines = wrapTextLines(`“${quote.text}”`, innerW - 72, (s) => ctx.measureText(s).width, 4);
    const quoteBoxH = 68 + qLines.length * 48 + (quote.source ? 42 : 16);

    drawRoundedRect(ctx, innerX, cursorY, innerW, quoteBoxH, 10);
    ctx.fill();
    ctx.strokeStyle = LINE;
    ctx.lineWidth = 1.5;
    ctx.stroke();

    ctx.fillStyle = tone.accent;
    ctx.font = `600 19px ${sans}`;
    ctx.fillText("今日引语", innerX + 36, cursorY + 40);

    ctx.fillStyle = INK;
    ctx.font = quoteFont;
    let qy = cursorY + 92;
    for (const ln of qLines) {
      ctx.fillText(ln, innerX + 36, qy);
      qy += 48;
    }

    if (quote.source) {
      ctx.fillStyle = MUTED;
      ctx.font = `400 21px ${sans}`;
      const srcText = `— ${quote.source}`;
      const srcLines = wrapTextLines(srcText, innerW - 72, (s) => ctx.measureText(s).width, 1);
      ctx.fillText(srcLines[0] ?? srcText, innerX + 36, qy + 6);
    }

    cursorY += quoteBoxH + 34;
  }

  // 5. 核心贡献区
  ctx.font = `500 28px ${sans}`;
  const contribLines = wrapTextLines(scientist.contribution, innerW - 72, (s) => ctx.measureText(s).width, 3);
  const contribBoxH = 68 + contribLines.length * 42 + 20;

  ctx.fillStyle = CREAM;
  drawRoundedRect(ctx, innerX, cursorY, innerW, contribBoxH, 10);
  ctx.fill();
  ctx.strokeStyle = LINE;
  ctx.lineWidth = 1.5;
  ctx.stroke();

  ctx.fillStyle = tone.accent;
  ctx.font = `600 19px ${sans}`;
  ctx.fillText("核心贡献", innerX + 36, cursorY + 40);

  ctx.fillStyle = INK;
  ctx.font = `500 28px ${sans}`;
  let cy = cursorY + 86;
  for (const ln of contribLines) {
    ctx.fillText(ln, innerX + 36, cy);
    cy += 42;
  }

  // 6. 底部页脚（固定贴底）
  const footerLineY = H - pad - 96;
  ctx.strokeStyle = LINE;
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(innerX, footerLineY);
  ctx.lineTo(innerX + innerW, footerLineY);
  ctx.stroke();

  ctx.fillStyle = INK;
  ctx.font = `500 23px ${serif}`;
  ctx.fillText("每天遇见一个改变世界的念头", innerX, footerLineY + 46);

  ctx.fillStyle = MUTED;
  ctx.font = `400 20px ${sans}`;
  const siteTag = "cochranek.github.io/scientist-calendar";
  const siteW = ctx.measureText(siteTag).width;
  ctx.fillText(siteTag, innerX + innerW - siteW, footerLineY + 46);

  return new Promise<Blob>((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) resolve(blob);
      else reject(new Error("无法导出分享海报图片"));
    }, "image/png");
  });
}

export function posterFilename(scientist: ScientistSummary): string {
  const mm = String(scientist.month).padStart(2, "0");
  const dd = String(scientist.day).padStart(2, "0");
  const safeName = scientist.name.replace(/[\\/:*?"<>|]/g, "");
  return `科学家日历_${mm}${dd}_${safeName}.png`;
}
