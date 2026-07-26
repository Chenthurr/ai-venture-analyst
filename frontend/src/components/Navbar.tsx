"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store";

export function Navbar({ title }: { title?: string }) {
  const router = useRouter();
  const logout = useAuthStore((s) => s.logout);

  return (
    <header className="border-b border-ink-border bg-ink/95 backdrop-blur sticky top-0 z-20">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/dashboard" className="flex items-baseline gap-2">
          <span className="font-display italic text-xl text-paper">AI Venture Analyst</span>
          <span className="font-mono text-[10px] text-gold tracking-widest uppercase">
            Investment Committee
          </span>
        </Link>
        <div className="flex items-center gap-4">
          {title && <span className="text-sm text-paper-muted hidden md:block">{title}</span>}
          <button
            onClick={() => {
              logout();
              router.push("/login");
            }}
            className="text-xs text-paper-faint hover:text-signal-negative"
          >
            Sign out
          </button>
        </div>
      </div>
    </header>
  );
}
