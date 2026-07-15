"use client";
import { useState } from "react";
import { Shell } from "@/components/layout/shell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/providers/theme-provider";
import { Moon, Sun, Key, User, Bell, Check } from "lucide-react";

export default function SettingsPage() {
  const { theme, toggle } = useTheme();
  const [apiKey, setApiKey] = useState("sk-••••••••••••••••••••••••••••••••");
  const [saved, setSaved] = useState(false);

  const save = () => { setSaved(true); setTimeout(() => setSaved(false), 2000); };

  return (
    <Shell>
      <div className="space-y-6 max-w-2xl">
        <div>
          <h1 className="text-xl font-bold text-zinc-100">Settings</h1>
          <p className="text-sm text-zinc-500 mt-0.5">Manage your account and preferences</p>
        </div>

        {/* Theme */}
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Sun className="w-4 h-4 text-zinc-400" /> Appearance</CardTitle></CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-300">Theme</p>
                <p className="text-xs text-zinc-500 mt-0.5">Currently using {theme} mode</p>
              </div>
              <Button variant="outline" size="sm" onClick={toggle}>
                {theme === "dark" ? <><Sun className="w-3.5 h-3.5" /> Light mode</> : <><Moon className="w-3.5 h-3.5" /> Dark mode</>}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* API Key */}
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Key className="w-4 h-4 text-zinc-400" /> API Configuration</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-xs text-zinc-500 block mb-1.5">Backend API URL</label>
              <input defaultValue="http://localhost:8000" className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-300 outline-none focus:border-indigo-500/50" />
            </div>
            <div>
              <label className="text-xs text-zinc-500 block mb-1.5">Hugging Face Token</label>
              <input value={apiKey} onChange={e => setApiKey(e.target.value)} type="password"
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-300 outline-none focus:border-indigo-500/50" />
            </div>
            <Button variant="primary" size="sm" onClick={save}>
              {saved ? <><Check className="w-3.5 h-3.5" /> Saved</> : "Save Changes"}
            </Button>
          </CardContent>
        </Card>

        {/* Profile */}
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><User className="w-4 h-4 text-zinc-400" /> Profile</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-lg font-bold text-white">R</div>
              <div>
                <p className="text-sm font-medium text-zinc-200">Rakesh</p>
                <p className="text-xs text-zinc-500">Admin · InsightIQ</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-zinc-500 block mb-1.5">Name</label>
                <input defaultValue="Rakesh" className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-300 outline-none focus:border-indigo-500/50" />
              </div>
              <div>
                <label className="text-xs text-zinc-500 block mb-1.5">Role</label>
                <input defaultValue="Product Manager" className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-300 outline-none focus:border-indigo-500/50" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Bell className="w-4 h-4 text-zinc-400" /> Notifications</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {[
              { label: "Anomaly alerts", desc: "Get notified when anomalies are detected" },
              { label: "Experiment results", desc: "Notify when experiments reach significance" },
              { label: "Weekly digest", desc: "Weekly summary of key metrics" },
            ].map((item, i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-zinc-800 last:border-0">
                <div>
                  <p className="text-sm text-zinc-300">{item.label}</p>
                  <p className="text-xs text-zinc-500">{item.desc}</p>
                </div>
                <button className="w-10 h-5 bg-indigo-600 rounded-full relative transition-colors">
                  <span className="absolute right-0.5 top-0.5 w-4 h-4 bg-white rounded-full shadow" />
                </button>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </Shell>
  );
}
