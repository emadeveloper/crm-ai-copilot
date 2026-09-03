type BandStyle = { text: string; fill: string; grad: string; border: string };

// Literal class strings so Tailwind's scanner keeps them.
const BANDS: Record<string, BandStyle> = {
  hot: {
    text: "text-band-hot",
    fill: "bg-band-hot",
    grad: "bg-[linear-gradient(90deg,var(--color-accent-dim),var(--color-accent))]",
    border: "border-band-hot/35",
  },
  warm: {
    text: "text-band-warm",
    fill: "bg-band-warm",
    grad: "bg-[linear-gradient(90deg,#c88a2e,#ffb454)]",
    border: "border-band-warm/35",
  },
  cold: {
    text: "text-band-cold",
    fill: "bg-band-cold",
    grad: "bg-[linear-gradient(90deg,#3d6fab,#5aa2f5)]",
    border: "border-band-cold/35",
  },
};

type Props = {
  value: number;
  band: string;
  size?: "sm" | "lg";
  "data-testid"?: string;
};

const FALLBACK_BAND: BandStyle = {
  text: "text-band-hot",
  fill: "bg-band-hot",
  grad: "bg-[linear-gradient(90deg,var(--color-accent-dim),var(--color-accent))]",
  border: "border-band-hot/35",
};

export function ScoreMeter({ value, band, size = "lg", "data-testid": testId }: Props) {
  const b = BANDS[band] ?? FALLBACK_BAND;
  const pct = Math.max(0, Math.min(100, value));
  const fillId = testId ? `${testId}-fill` : undefined;

  if (size === "sm") {
    return (
      <div
        role="meter"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`score ${value} of 100, ${band}`}
        data-testid={testId}
        className="flex items-center gap-2"
      >
        <span className="font-mono text-[13px] tabular-nums">{value}</span>
        <div className="h-1 flex-1 overflow-hidden rounded-full bg-line">
          <div
            data-testid={fillId}
            className={`h-full ${b.fill}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className={`font-mono text-[9px] uppercase tracking-[0.08em] ${b.text}`}>
          {band}
        </span>
      </div>
    );
  }

  return (
    <div
      role="meter"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`score ${value} of 100, ${band}`}
      data-testid={testId}
      className="flex flex-col gap-2"
    >
      <div className="flex items-end gap-1.5">
        <span className="font-mono text-[40px] font-medium leading-none tabular-nums">
          {value}
        </span>
        <span className="pb-1 font-mono text-[13px] text-dim">/100</span>
        <span
          className={`ml-auto self-center rounded-[2px] border px-2 py-[3px] font-mono text-[10px] uppercase tracking-[0.1em] ${b.text} ${b.border}`}
        >
          {band}
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-line">
        <div
          data-testid={fillId}
          className={`h-full ${b.grad}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
