"use client";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { CHART_COLORS } from "@/constants";

export function ForecastChart({ data }: { data: { forecast_day: string; forecast_revenue: string }[] }) {
  const formatted = data.map(d => ({ day: d.forecast_day, revenue: Number(d.forecast_revenue) }));
  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={formatted} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={CHART_COLORS.cyan} stopOpacity={0.3} />
            <stop offset="95%" stopColor={CHART_COLORS.cyan} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
        <XAxis dataKey="day" tick={{ fontSize: 10, fill: "#71717a" }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fontSize: 10, fill: "#71717a" }} axisLine={false} tickLine={false} tickFormatter={v => `$${v.toFixed(0)}`} />
        <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", borderRadius: 8, fontSize: 12 }} />
        <Area type="monotone" dataKey="revenue" stroke={CHART_COLORS.cyan} strokeWidth={2} fill="url(#forecastGrad)" dot={false} strokeDasharray="5 3" isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
