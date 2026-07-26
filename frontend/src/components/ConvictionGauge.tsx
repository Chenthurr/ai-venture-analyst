"use client";

/**
 * The "Conviction Gauge" -- this app's signature element. A semi-circle
 * dial in the style of an analyst instrument rather than a generic
 * progress ring. The needle position communicates overall investment
 * conviction at a glance; the arc segments (weak / building / strong)
 * give it meaning beyond a bare number.
 */
export function ConvictionGauge({ score }: { score: number }) {
  const clamped = Math.max(0, Math.min(100, score));
  const angle = -90 + (clamped / 100) * 180; // -90deg (0) to +90deg (100)

  const radius = 90;
  const cx = 100;
  const cy = 100;

  const polarToCartesian = (angleDeg: number) => {
    const rad = ((angleDeg - 180) * Math.PI) / 180;
    return {
      x: cx + radius * Math.cos(rad),
      y: cy + radius * Math.sin(rad),
    };
  };

  const arcPath = (startAngle: number, endAngle: number) => {
    const start = polarToCartesian(startAngle);
    const end = polarToCartesian(endAngle);
    const largeArc = endAngle - startAngle > 180 ? 1 : 0;
    return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArc} 1 ${end.x} ${end.y}`;
  };

  const needleTip = polarToCartesian(angle + 180);

  const label =
    clamped >= 75 ? "High Conviction" : clamped >= 50 ? "Building Conviction" : clamped >= 25 ? "Early Signal" : "Weak Signal";

  return (
    <div className="flex flex-col items-center">
      <svg width="200" height="120" viewBox="0 0 200 110">
        <path d={arcPath(0, 60)} stroke="#C1554A" strokeWidth="10" fill="none" strokeLinecap="round" opacity="0.55" />
        <path d={arcPath(60, 120)} stroke="#C9A24B" strokeWidth="10" fill="none" strokeLinecap="round" opacity="0.65" />
        <path d={arcPath(120, 180)} stroke="#4F9D69" strokeWidth="10" fill="none" strokeLinecap="round" opacity="0.55" />

        <line
          x1={cx}
          y1={cy}
          x2={needleTip.x}
          y2={needleTip.y}
          stroke="#E8EAED"
          strokeWidth="2"
          strokeLinecap="round"
        />
        <circle cx={cx} cy={cy} r="4" fill="#E8EAED" />
      </svg>
      <div className="font-mono text-4xl text-paper tabular-nums -mt-2">{Math.round(clamped)}</div>
      <div className="text-xs uppercase tracking-wider text-gold mt-1">{label}</div>
    </div>
  );
}
