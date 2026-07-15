"use client";
import { useState, useRef, useEffect } from "react";
import { Send, Bot, Copy, ThumbsUp, ThumbsDown, ChevronDown, ChevronUp, Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from "recharts";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Monotonic message id generator — kept at module scope so it stays out of the
// component render path (calling Date.now() during render is flagged as impure).
let msgSeq = 0;
const nextMsgId = () => `msg-${++msgSeq}`;

const CHART_COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#06b6d4", "#8b5cf6"];

const SUGGESTED = [
  "What is the revenue trend?",
  "Which experiments should we ship?",
  "What are the top customer complaints?",
  "Show me anomalies detected",
  "What is the conversion funnel drop-off?",
  "Which user segment has highest spend?",
  "What are the root cause hypotheses?",
  "Give me the full decision recommendation",
];

interface ChartData {
  type: "bar" | "line" | "pie";
  title: string;
  data: { name: string; value: number; anomaly?: boolean }[];
}

interface Decision {
  action?: string;
  confidence?: number;
  rationale?: string;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  charts?: ChartData[];
  thinking?: string[];
  decision?: Decision;
  usedRemoteLLM?: boolean;
  timestamp: Date;
}

const DECISION_STYLE: Record<string, string> = {
  LAUNCH: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  ITERATE: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  ROLLBACK: "bg-red-500/15 text-red-400 border-red-500/30",
  INVESTIGATE: "bg-sky-500/15 text-sky-400 border-sky-500/30",
};

function DecisionBadge({ decision, live }: { decision: Decision; live?: boolean }) {
  const action = (decision.action ?? "").toUpperCase();
  if (!action) return null;
  return (
    <div className="flex items-center gap-2 mb-2">
      <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-full border ${DECISION_STYLE[action] ?? "bg-zinc-800 text-zinc-300 border-zinc-700"}`}>
        Decision: {action}
      </span>
      {decision.confidence != null && (
        <span className="text-[11px] text-zinc-500">Confidence {Math.round((decision.confidence ?? 0) * 100)}%</span>
      )}
      <span className={`text-[10px] px-1.5 py-0.5 rounded ${live ? "bg-indigo-500/15 text-indigo-400" : "bg-zinc-800 text-zinc-500"}`}>
        {live ? "🧠 LLM-synthesized" : "grounded fallback"}
      </span>
    </div>
  );
}

function InlineChart({ chart }: { chart: ChartData }) {
  return (
    <div className="mt-3 rounded-lg border border-zinc-700 bg-zinc-800/60 p-3">
      <p className="text-xs font-medium text-zinc-400 mb-2">{chart.title}</p>
      <ResponsiveContainer width="100%" height={160}>
        {chart.type === "pie" ? (
          <PieChart>
            <Pie data={chart.data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={60} innerRadius={35} isAnimationActive={false}>
              {chart.data.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
            </Pie>
            <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", fontSize: 11 }} />
          </PieChart>
        ) : chart.type === "line" ? (
          <LineChart data={chart.data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 9, fill: "#71717a" }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
            <YAxis tick={{ fontSize: 9, fill: "#71717a" }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", fontSize: 11 }} />
            <Line type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={2} dot={false} isAnimationActive={false} />
          </LineChart>
        ) : (
          <BarChart data={chart.data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 9, fill: "#71717a" }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 9, fill: "#71717a" }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", fontSize: 11 }} />
            <Bar dataKey="value" radius={[3, 3, 0, 0]} isAnimationActive={false}>
              {chart.data.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
            </Bar>
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}

function ThinkingSteps({ steps }: { steps: string[] }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mb-2">
      <button onClick={() => setOpen(o => !o)} className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-400 transition-colors">
        <Sparkles className="w-3 h-3 text-indigo-500" />
        Thinking steps
        {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>
      {open && (
        <div className="mt-2 pl-4 border-l border-zinc-800 space-y-1">
          {steps.map((s, i) => (
            <p key={i} className="text-xs text-zinc-600">{i + 1}. {s}</p>
          ))}
        </div>
      )}
    </div>
  );
}

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(msg.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (msg.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-lg bg-indigo-600/20 border border-indigo-500/20 rounded-2xl rounded-tr-sm px-4 py-3">
          <p className="text-sm text-zinc-200">{msg.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3">
      <div className="w-7 h-7 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center shrink-0 mt-1">
        <Bot className="w-3.5 h-3.5 text-indigo-400" />
      </div>
      <div className="flex-1 min-w-0">
        {msg.thinking && msg.thinking.length > 0 && <ThinkingSteps steps={msg.thinking} />}
        {msg.decision && <DecisionBadge decision={msg.decision} live={msg.usedRemoteLLM} />}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl rounded-tl-sm px-4 py-3">
          <div className="prose prose-invert prose-sm max-w-none text-zinc-300
            [&_h1]:text-zinc-100 [&_h1]:text-base [&_h1]:font-bold [&_h1]:mb-3
            [&_h2]:text-zinc-200 [&_h2]:text-sm [&_h2]:font-semibold [&_h2]:mt-4 [&_h2]:mb-2
            [&_h3]:text-zinc-300 [&_h3]:text-xs [&_h3]:font-semibold
            [&_table]:text-xs [&_th]:bg-zinc-800 [&_th]:px-3 [&_th]:py-1.5 [&_th]:text-zinc-400
            [&_td]:px-3 [&_td]:py-1.5 [&_td]:border-b [&_td]:border-zinc-800
            [&_code]:bg-zinc-800 [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-indigo-300
            [&_pre]:bg-zinc-800 [&_pre]:rounded-lg [&_pre]:p-3
            [&_blockquote]:border-l-2 [&_blockquote]:border-indigo-500 [&_blockquote]:pl-3 [&_blockquote]:text-zinc-400
            [&_strong]:text-zinc-200 [&_a]:text-indigo-400">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
          </div>
          {msg.charts && msg.charts.map((chart, i) => <InlineChart key={i} chart={chart} />)}
        </div>
        <div className="flex items-center gap-2 mt-1.5 ml-1">
          <button onClick={copy} className="text-[10px] text-zinc-600 hover:text-zinc-400 flex items-center gap-1 transition-colors">
            <Copy className="w-3 h-3" />{copied ? "Copied" : "Copy"}
          </button>
          <button className="text-[10px] text-zinc-600 hover:text-emerald-400 flex items-center gap-1 ml-2 transition-colors">
            <ThumbsUp className="w-3 h-3" />
          </button>
          <button className="text-[10px] text-zinc-600 hover:text-red-400 flex items-center gap-1 transition-colors">
            <ThumbsDown className="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>
  );
}

export function AIChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "0",
      role: "assistant",
      content: "Hi! Ask me anything about your product — revenue, experiments, reviews, anomalies, segments, or decisions. I'll analyse the real data and respond with evidence.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: nextMsgId(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };
    setMessages(m => [...m, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text }),
      });

      if (!res.ok) throw new Error(`API error ${res.status}`);
      const data = await res.json();

      const aiMsg: ChatMessage = {
        id: nextMsgId(),
        role: "assistant",
        content: data.answer,
        charts: data.charts ?? [],
        thinking: data.thinking ?? [],
        decision: data.decision ?? undefined,
        usedRemoteLLM: data.used_remote_llm ?? false,
        timestamp: new Date(),
      };
      setMessages(m => [...m, aiMsg]);
    } catch (err) {
      const errMsg: ChatMessage = {
        id: nextMsgId(),
        role: "assistant",
        content: `❌ Could not reach the API. Make sure the backend is running on \`http://localhost:8000\`.\n\nError: ${err}`,
        timestamp: new Date(),
      };
      setMessages(m => [...m, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 min-h-0 overflow-y-auto space-y-5 pb-4">
        {messages.map(msg => <MessageBubble key={msg.id} msg={msg} />)}
        {loading && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center shrink-0">
              <Bot className="w-3.5 h-3.5 text-indigo-400" />
            </div>
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2">
              <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
              <span className="text-xs text-zinc-500">Analysing your data...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggested questions */}
      <div className="flex flex-wrap gap-2 py-3 border-t border-zinc-800">
        {SUGGESTED.map(q => (
          <button
            key={q}
            onClick={() => send(q)}
            className="text-xs bg-zinc-900 border border-zinc-800 hover:border-indigo-500/40 hover:text-indigo-400 text-zinc-500 px-3 py-1.5 rounded-full transition-all"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="flex gap-3 pt-3">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && !e.shiftKey && send(input)}
          placeholder="Ask about revenue, experiments, reviews, anomalies..."
          className="flex-1 bg-zinc-900 border border-zinc-800 focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20 rounded-xl px-4 py-2.5 text-sm text-zinc-200 placeholder:text-zinc-600 outline-none transition-all"
        />
        <Button variant="primary" size="md" onClick={() => send(input)} disabled={!input.trim() || loading}>
          <Send className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
