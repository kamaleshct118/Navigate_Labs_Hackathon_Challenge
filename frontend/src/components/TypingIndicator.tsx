import { ShieldCheck } from 'lucide-react';

export function TypingIndicator() {
  return (
    <div className="flex animate-fade-in gap-3">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-brand-500/15 border border-brand-500/20">
        <ShieldCheck className="h-3.5 w-3.5 text-brand-400" strokeWidth={2} />
      </div>
      <div className="flex items-center gap-2.5 rounded-2xl rounded-tl-md border border-white/8 bg-ink-850/70 px-4 py-3.5">
        <div className="flex items-center gap-1">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="h-1.5 w-1.5 rounded-full bg-slate-400 animate-dot-pulse"
              style={{ animationDelay: `${i * 0.18}s` }}
            />
          ))}
        </div>
        <span className="text-xs text-slate-500">Analyzing compliance policies…</span>
      </div>
    </div>
  );
}
