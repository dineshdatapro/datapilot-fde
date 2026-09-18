import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Visualization } from "../types";

const COLORS = ["#1f4d3a", "#8a6a3b", "#3d5a73", "#6b4f71", "#5c6b4a", "#7a4a3b"];

function formatTick(v: number, kind?: string) {
  if (kind === "currency") {
    if (Math.abs(v) >= 10_000_000) return `₹${(v / 10_000_000).toFixed(1)}Cr`;
    if (Math.abs(v) >= 100_000) return `₹${(v / 100_000).toFixed(1)}L`;
    return `₹${Math.round(v).toLocaleString("en-IN")}`;
  }
  return Number(v).toLocaleString("en-IN");
}

type Props = { viz: Visualization };

export function ChartView({ viz }: Props) {
  if (viz.type === "none" || viz.type === "kpi") return null;
  const data = viz.data.map((d) => ({
    ...d,
    name: String(d.name ?? ""),
    value: Number(d.value ?? 0),
  }));

  if (viz.type === "table") {
    const cols = viz.data.length ? Object.keys(viz.data[0]).slice(0, 8) : [];
    return (
      <div className="overflow-x-auto rounded-xl border border-line">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-mist text-stone-500">
            <tr>
              {cols.map((c) => (
                <th key={c} className="px-3 py-2 font-medium">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {viz.data.slice(0, 20).map((row, i) => (
              <tr key={i} className="border-t border-line">
                {cols.map((c) => (
                  <td key={c} className="px-3 py-2">
                    {String(row[c] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  const tooltip = (
    <Tooltip
      formatter={(value: number | string) => formatTick(Number(value), viz.value_format)}
      contentStyle={{ borderRadius: 12, borderColor: "#e4ddd2" }}
    />
  );

  return (
    <div>
      <h3 className="mb-3 font-display text-lg">{viz.title}</h3>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {viz.type === "line" ? (
            <LineChart data={data}>
              <CartesianGrid stroke="#efeae2" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={(v) => formatTick(v, viz.value_format)} tick={{ fontSize: 12 }} width={72} />
              {tooltip}
              <Line type="monotone" dataKey="value" stroke="#1f4d3a" strokeWidth={2} dot />
            </LineChart>
          ) : viz.type === "pie" ? (
            <PieChart>
              {tooltip}
              <Pie data={data} dataKey="value" nameKey="name" innerRadius={50} outerRadius={90}>
                {data.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          ) : (
            <BarChart data={data} layout={viz.type === "horizontal_bar" ? "vertical" : "horizontal"}>
              <CartesianGrid stroke="#efeae2" />
              {viz.type === "horizontal_bar" ? (
                <>
                  <XAxis type="number" tickFormatter={(v) => formatTick(v, viz.value_format)} tick={{ fontSize: 12 }} />
                  <YAxis type="category" dataKey="name" width={110} tick={{ fontSize: 12 }} />
                </>
              ) : (
                <>
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis tickFormatter={(v) => formatTick(v, viz.value_format)} tick={{ fontSize: 12 }} width={72} />
                </>
              )}
              {tooltip}
              <Bar dataKey="value" fill="#1f4d3a" radius={[4, 4, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
      {viz.type !== "pie" && (
        <ul className="mt-3 space-y-1 text-sm text-stone-600">
          {data.slice(0, 8).map((row) => (
            <li key={row.name} className="flex justify-between gap-4">
              <span>{row.name}</span>
              <span className="font-mono text-xs">{formatTick(row.value, viz.value_format)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
