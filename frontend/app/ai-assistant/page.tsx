"use client";
import { Shell } from "@/components/layout/shell";
import { AIChat } from "@/components/ai/chat";
import { Bot, Zap } from "lucide-react";

export default function AIAssistantPage() {
  return (
    <Shell>
      <div className="flex flex-col h-[calc(100vh-8rem)]">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-9 h-9 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center">
            <Bot className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-zinc-100">AI Assistant</h1>
            <p className="text-xs text-zinc-500">Evidence-grounded answers from your real product data</p>
          </div>
          <div className="ml-auto flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-full">
            <Zap className="w-3 h-3" /> Connected to live data
          </div>
        </div>
        <div className="flex-1 min-h-0 rounded-xl border border-zinc-800 bg-zinc-900/40 p-5 flex flex-col">
          <AIChat />
        </div>
      </div>
    </Shell>
  );
}
