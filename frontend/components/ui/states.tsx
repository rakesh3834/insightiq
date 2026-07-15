"use client";
import { AlertCircle, RefreshCw, Inbox } from "lucide-react";
import { Button } from "./button";

export function ErrorState({ message, onRetry }: { message?: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-4 text-center">
      <div className="p-3 rounded-full bg-red-500/10 border border-red-500/20">
        <AlertCircle className="w-6 h-6 text-red-400" />
      </div>
      <div>
        <p className="text-sm font-medium text-zinc-200">Something went wrong</p>
        <p className="text-xs text-zinc-500 mt-1">{message ?? "Failed to load data from the API."}</p>
      </div>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          <RefreshCw className="w-3.5 h-3.5" /> Retry
        </Button>
      )}
    </div>
  );
}

export function EmptyState({ message = "No data available." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
      <div className="p-3 rounded-full bg-zinc-800 border border-zinc-700">
        <Inbox className="w-6 h-6 text-zinc-500" />
      </div>
      <p className="text-sm text-zinc-500">{message}</p>
    </div>
  );
}
