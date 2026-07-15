import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
      <div className="text-center space-y-4">
        <p className="text-8xl font-bold text-zinc-800">404</p>
        <p className="text-xl font-semibold text-zinc-300">Page not found</p>
        <p className="text-sm text-zinc-500">The page you&apos;re looking for doesn&apos;t exist.</p>
        <Link href="/dashboard" className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg transition-colors">
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
