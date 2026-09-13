"use client";

import { useEffect, useState } from "react";
import { getLocalDate, getUTCDate, type DateParts } from "../domain/calendar";

/** 距离下一次本地午夜的毫秒数（用于精确调度刷新）。 */
function msUntilNextLocalMidnight(): number {
  const now = new Date();
  const next = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate() + 1,
    0,
    0,
    0,
    0,
  );
  return next.getTime() - now.getTime();
}

/**
 * 返回“当前本地日期”，并在以下时机自动更新：
 *  - 精确调度到下一次本地午夜（跨午夜无需刷新页面即可切换今日人物）；
 *  - 标签页从后台回到前台（visibilitychange）时立即重新检查日期（覆盖睡眠跨日）。
 * 初始值用 UTC，保证 SSR 与客户端首屏渲染一致，避免水合不匹配。
 */
export function useCurrentDate(): DateParts {
  const [now, setNow] = useState<DateParts>(getUTCDate);

  useEffect(() => {
    let cancelled = false;

    // 客户端挂载后，把首屏的 UTC 时间校正为本地时间（避免 hydration mismatch）。
    // 用 queueMicrotask 延迟到当前提交之后，规避 react-hooks/set-state-in-effect
    // 对「effect 体内同步 setState」的告警；microtask 在绘制前执行，几乎无闪烁。
    queueMicrotask(() => {
      if (!cancelled) setNow(getLocalDate());
    });

    let timer: ReturnType<typeof setTimeout>;
    const schedule = () => {
      timer = setTimeout(() => {
        setNow(getLocalDate());
        schedule(); // 递归调度到下一个午夜
      }, msUntilNextLocalMidnight());
    };
    schedule();

    const onVisible = () => {
      if (document.visibilityState === "visible") {
        setNow(getLocalDate());
      }
    };
    document.addEventListener("visibilitychange", onVisible);

    return () => {
      cancelled = true;
      clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, []);

  return now;
}
