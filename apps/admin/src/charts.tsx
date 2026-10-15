"use client";

/**
 * Small single-series charts for the admin panel (dataviz method). One validated colour
 * (--color-chart, light and dark), thin columns with 4px rounded data-ends and a 2px gap,
 * hairline grid, a hover tooltip on every mark with a hit target wider than the mark, and a
 * table view of the same numbers so nothing depends on seeing the chart.
 */
import { cn } from "@diyneco/shared-ui";
import { useId, useState } from "react";

export interface Point {
  label: string; // axis label
  value: number;
  tooltip: string; // full text for the hover tooltip and the table
}

function niceMax(v: number): number {
  if (v <= 4) return 4;
  const pow = 10 ** Math.floor(Math.log10(v));
  for (const step of [1, 2, 2.5, 5, 10]) if (step * pow >= v) return step * pow;
  return 10 * pow;
}

function compact(n: number): string {
  return n >= 1000 ? `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}K` : String(n);
}

/** Columns over time (one series): the title says what is plotted, so there is no legend. */
export function ColumnChart({ title, points, height = 180 }: { title: string; points: Point[]; height?: number }) {
  const [hover, setHover] = useState<number | null>(null);
  const id = useId();
  const max = niceMax(Math.max(0, ...points.map((p) => p.value)));
  const ticks = [0, max / 2, max];
  const top = 8;
  const bottom = 22;
  const left = 32;
  const plotH = height - top - bottom;
  const width = 720;
  const slot = (width - left) / Math.max(points.length, 1);
  const bar = Math.max(2, Math.min(24, slot - 2)); // <= 24px, a 2px gap between neighbours
  const every = Math.ceil(points.length / 8); // at most ~8 axis labels
  const y = (v: number) => top + plotH - (v / max) * plotH;
  const shown = hover !== null ? points[hover] : null;

  return (
    <figure className="relative">
      <figcaption className="sr-only">{title}</figcaption>
      <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full" role="img" aria-labelledby={`${id}-t`} onMouseLeave={() => setHover(null)}>
        <title id={`${id}-t`}>{title}</title>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={left} x2={width} y1={y(t)} y2={y(t)} className="stroke-line" strokeWidth={1} />
            <text x={left - 6} y={y(t) + 4} textAnchor="end" className="fill-muted text-[11px] tabular-nums">
              {compact(t)}
            </text>
          </g>
        ))}
        {points.map((p, i) => {
          const x = left + i * slot + (slot - bar) / 2;
          const h = Math.max(0, y(0) - y(p.value));
          const r = Math.min(4, h, bar / 2);
          // Square at the baseline, rounded (4px) at the data end.
          const d =
            h <= 0
              ? ""
              : `M${x},${y(0)} V${y(p.value) + r} Q${x},${y(p.value)} ${x + r},${y(p.value)} H${x + bar - r} Q${x + bar},${y(p.value)} ${x + bar},${y(p.value) + r} V${y(0)} Z`;
          return (
            <g key={p.label + i}>
              {d ? <path d={d} className={cn("fill-chart transition-opacity", hover !== null && hover !== i && "opacity-40")} /> : null}
              {i % every === 0 ? (
                <text x={x + bar / 2} y={height - 6} textAnchor="middle" className="fill-muted text-[11px]">
                  {p.label}
                </text>
              ) : null}
              {/* Hit target: the whole slot, taller than the mark. */}
              <rect
                x={left + i * slot}
                y={top}
                width={slot}
                height={plotH}
                fill="transparent"
                onMouseEnter={() => setHover(i)}
                onFocus={() => setHover(i)}
                tabIndex={0}
                aria-label={p.tooltip}
              />
            </g>
          );
        })}
      </svg>
      {shown && hover !== null ? (
        <div
          className="pointer-events-none absolute top-0 -translate-x-1/2 rounded-md border border-line bg-surface px-2 py-1 text-xs text-ink shadow-md"
          style={{ left: `${((left + hover * slot + slot / 2) / width) * 100}%` }}
        >
          {shown.tooltip}
        </div>
      ) : null}
      <details className="mt-2 text-xs text-muted">
        <summary className="cursor-pointer">Show as a table</summary>
        <table className="mt-2 w-full text-left">
          <tbody>
            {points.map((p) => (
              <tr key={p.tooltip} className="border-t border-line">
                <td className="py-1 text-ink">{p.tooltip}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}

/** Horizontal bars for a funnel: value and share of the first step at each bar's tip. */
export function FunnelBars({ steps }: { steps: { label: string; value: number }[] }) {
  const first = steps[0]?.value ?? 0;
  const max = Math.max(1, ...steps.map((s) => s.value));
  return (
    <ol className="flex flex-col gap-2.5">
      {steps.map((s) => {
        const pct = first ? Math.round((s.value / first) * 100) : 0;
        return (
          <li key={s.label} className="grid grid-cols-[10rem_1fr] items-center gap-3 text-sm" title={`${s.label}: ${s.value} (${pct}%)`}>
            <span className="truncate text-ink">{s.label}</span>
            <span className="flex items-center gap-2">
              <span className="h-5 rounded-r-[4px] bg-chart" style={{ width: `${Math.max(s.value ? 2 : 0, (s.value / max) * 85)}%` }} />
              <span className="shrink-0 tabular-nums text-ink">
                {s.value}
                <span className="text-muted"> · {pct}%</span>
              </span>
            </span>
          </li>
        );
      })}
    </ol>
  );
}
