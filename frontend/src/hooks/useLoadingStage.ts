import { useEffect, useState } from "react";

const STAGES = 4;

export function useLoadingStage(active: boolean) {
  const [stage, setStage] = useState(0);
  useEffect(() => {
    if (!active) return;
    setStage(0);
    const timers = [700, 1400, 2200].map((ms, i) => window.setTimeout(() => setStage(i + 1), ms));
    return () => timers.forEach(clearTimeout);
  }, [active]);
  return Math.min(stage, STAGES - 1);
}
