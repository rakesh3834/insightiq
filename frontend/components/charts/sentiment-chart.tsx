"use client";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { SENTIMENT_COLORS } from "@/constants";

export function SentimentChart({ data }: { data: { sentiment: string; count: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie data={data} dataKey="count" nameKey="sentiment" cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={3} isAnimationActive={false}>
          {data.map((entry, i) => (
            <Cell key={i} fill={SENTIMENT_COLORS[entry.sentiment] ?? "#6b7280"} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: "#a1a1aa" }}
        />
        <Legend iconType="circle" iconSize={8} formatter={(v) => <span style={{ color: "#a1a1aa", fontSize: 11 }}>{v}</span>} />
      </PieChart>
    </ResponsiveContainer>
  );
}
