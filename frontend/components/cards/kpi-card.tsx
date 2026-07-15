import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface KPICardProps {
  label: string;
  value: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  icon?: React.ReactNode;
  highlight?: boolean;
}

export function KPICard({ label, value, trend, trendValue, icon, highlight }: KPICardProps) {
  return (
    <div className={cn(
      "rounded-xl border p-5 space-y-3 transition-all hover:border-zinc-700",
      highlight
        ? "bg-indigo-600/10 border-indigo-500/30"
        : "bg-zinc-900/60 border-zinc-800"
    )}>
      <div className="flex items-center justify-between">
        <p className="text-xs text-zinc-500 font-medium">{label}</p>
        {icon && <div className="text-zinc-600">{icon}</div>}
      </div>
      <p className={cn("text-2xl font-bold tracking-tight", highlight ? "text-indigo-300" : "text-zinc-100")}>{value}</p>
      {trend && trendValue && (
        <div className={cn("flex items-center gap-1 text-xs font-medium",
          trend === "up" ? "text-emerald-400" : trend === "down" ? "text-red-400" : "text-zinc-500"
        )}>
          {trend === "up" ? <TrendingUp className="w-3 h-3" /> : trend === "down" ? <TrendingDown className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
          {trendValue}
        </div>
      )}
    </div>
  );
}
