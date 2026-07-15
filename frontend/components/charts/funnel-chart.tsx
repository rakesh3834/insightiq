"use client";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface TooltipProps {
  active?: boolean;
  payload?: { value: number }[];
  label?: string;
}

const CustomTooltip = ({ active, payload, label }: TooltipProps) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-xs shadow-xl">
      <p className="text-zinc-400 mb-1">{label}</p>
      <p className="text-indigo-400 font-semibold">{Number(payload[0].value).toLocaleString()} users</p>
    </div>
  );
};

export function FunnelChart({ data }: { data: { step: string; users: string }[] }) {
  const formatted = data.map(d => ({ step: d.step, users: Number(d.users) }));
  const max = Math.max(...formatted.map(d => d.users));
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={formatted} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={true} vertical={false} />
        <XAxis dataKey="step" tick={{ fontSize: 10, fill: "#71717a" }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fontSize: 10, fill: "#71717a" }} axisLine={false} tickLine={false} />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="users" radius={[4, 4, 0, 0]} isAnimationActive={false}>
          {formatted.map((entry, i) => (
            <Cell key={i} fill={`rgba(99,102,241,${0.4 + 0.6 * (entry.users / max)})`} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
