import { useMemo } from "react";

const LEVELS = [
  { min: 0, max: 0, cls: "hm-0" },
  { min: 1, max: 3, cls: "hm-1" },
  { min: 4, max: 8, cls: "hm-2" },
  { min: 9, max: 15, cls: "hm-3" },
  { min: 16, max: Infinity, cls: "hm-4" },
];

function levelClass(count) {
  return LEVELS.find((l) => count >= l.min && count <= l.max)?.cls ?? "hm-0";
}

function buildGrid(data) {
  const map = {};
  data.forEach(({ date, count }) => { map[date] = count; });

  const today = new Date();
  const start = new Date(today);
  start.setFullYear(start.getFullYear() - 1);
  start.setDate(start.getDate() - start.getDay());

  const weeks = [];
  let week = [];
  const cur = new Date(start);

  while (cur <= today) {
    const iso = cur.toISOString().slice(0, 10);
    week.push({ date: iso, count: map[iso] ?? 0 });
    if (week.length === 7) { weeks.push(week); week = []; }
    cur.setDate(cur.getDate() + 1);
  }
  if (week.length) weeks.push(week);
  return weeks;
}

const MONTH_LABELS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

export default function HeatmapCalendar({ data = [] }) {
  const weeks = useMemo(() => buildGrid(data), [data]);

  const monthMarkers = useMemo(() => {
    const markers = [];
    weeks.forEach((week, wi) => {
      const first = week[0];
      if (first) {
        const d = new Date(first.date);
        if (d.getDate() <= 7) markers.push({ wi, label: MONTH_LABELS[d.getMonth()] });
      }
    });
    return markers;
  }, [weeks]);

  return (
    <div className="heatmap-wrap">
      <div className="heatmap-months">
        {monthMarkers.map((m) => (
          <span key={`${m.wi}-${m.label}`} style={{ gridColumn: m.wi + 1 }}>{m.label}</span>
        ))}
      </div>
      <div className="heatmap-grid" style={{ gridTemplateColumns: `repeat(${weeks.length}, 12px)` }}>
        {weeks.map((week, wi) =>
          week.map((cell) => (
            <div
              key={cell.date}
              className={`heatmap-cell ${levelClass(cell.count)}`}
              title={`${cell.date}: ${cell.count} events`}
            />
          ))
        )}
      </div>
      <div className="heatmap-legend">
        <span>Less</span>
        {["hm-0","hm-1","hm-2","hm-3","hm-4"].map((c) => (
          <div key={c} className={`heatmap-cell ${c}`} />
        ))}
        <span>More</span>
      </div>
    </div>
  );
}
