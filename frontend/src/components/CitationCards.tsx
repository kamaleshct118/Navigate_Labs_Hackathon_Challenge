import { FileText } from 'lucide-react';

interface CitationCardsProps {
  citations: string[];
}

function parsePillLabel(cite: string): string {
  const clean = cite.replace(/^\[|\]$/g, '').trim();
  const parts = clean.split(' - ');
  if (parts.length > 0 && parts[0]) {
    return parts[0];
  }
  return clean.length > 24 ? clean.slice(0, 24) + '…' : clean;
}

export function CitationCards({ citations }: CitationCardsProps) {
  if (!citations || citations.length === 0) return null;

  // Deduplicate pill labels while keeping full citation context
  const uniqueCitations = Array.from(new Set(citations));

  return (
    <div className="mt-3 flex items-center justify-end gap-1.5 flex-wrap border-t border-slate-800/60 pt-2 text-right">
      <span className="mr-0.5 text-[9px] font-semibold tracking-wider text-slate-500 uppercase">
        Sources:
      </span>
      {uniqueCitations.map((cite, idx) => {
        const pillLabel = parsePillLabel(cite);
        return (
          <span
            key={idx}
            title={cite}
            className="inline-flex items-center gap-1 rounded-full border border-slate-800 bg-slate-950/80 px-2 py-0.5 font-mono text-[10px] text-slate-300 transition-all hover:border-brand-500/40 hover:bg-slate-900 hover:text-brand-300 cursor-help shadow-xs"
          >
            <FileText className="h-2.5 w-2.5 shrink-0 text-brand-400" />
            {pillLabel}
          </span>
        );
      })}
    </div>
  );
}
