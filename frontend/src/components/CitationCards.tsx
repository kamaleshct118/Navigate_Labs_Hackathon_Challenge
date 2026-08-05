import { FileText, ShieldCheck } from 'lucide-react';

interface CitationCardsProps {
  citations: string[];
}

export function CitationCards({ citations }: CitationCardsProps) {
  if (!citations || citations.length === 0) return null;
  return (
    <div className="mt-4 border-t border-white/5 pt-3">
      <div className="mb-2 flex items-center gap-1.5">
        <ShieldCheck className="h-3 w-3 text-signal-green" />
        <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">
          Verified Sources
        </span>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {citations.map((cite, idx) => (
          <span
            key={idx}
            style={{ animationDelay: `${idx * 50}ms` }}
            className="flex animate-fade-in items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/60 px-2.5 py-1 font-mono text-[11px] text-slate-300 transition-colors hover:border-brand-500/20 hover:text-brand-300"
          >
            <FileText className="h-3 w-3 shrink-0 text-slate-500" />
            {cite}
          </span>
        ))}
      </div>
    </div>
  );
}
