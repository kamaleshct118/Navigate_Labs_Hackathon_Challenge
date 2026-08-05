import { useState } from 'react';
import { FileText, ChevronDown, ChevronUp } from 'lucide-react';

interface CitationCardsProps {
  citations: string[];
}

function parsePillLabel(cite: string): string {
  const clean = cite.replace(/^\[|\]$/g, '').trim();
  const parts = clean.split(' - ');
  if (parts.length > 0 && parts[0]) {
    return parts[0];
  }
  return clean.length > 20 ? clean.slice(0, 20) + '…' : clean;
}

export function CitationCards({ citations }: CitationCardsProps) {
  const [expanded, setExpanded] = useState(false);

  if (!citations || citations.length === 0) return null;

  // Group citations by pill label to prevent duplicate document badges
  const labelMap = new Map<string, string[]>();
  for (const cite of citations) {
    const label = parsePillLabel(cite);
    if (!labelMap.has(label)) {
      labelMap.set(label, []);
    }
    labelMap.get(label)!.push(cite);
  }

  const entries = Array.from(labelMap.entries());
  const visibleEntries = expanded ? entries : entries.slice(0, 2);
  const hiddenCount = entries.length - 2;

  return (
    <div className="mt-2.5 flex items-center justify-end gap-1 flex-wrap border-t border-slate-800/60 pt-2 text-right">
      <span className="mr-0.5 text-[8.5px] font-semibold tracking-wider text-slate-500 uppercase">
        Sources:
      </span>
      {visibleEntries.map(([label, fullCites], idx) => {
        const tooltip = fullCites.join('\n• ');
        return (
          <span
            key={idx}
            title={`• ${tooltip}`}
            className="inline-flex items-center gap-1 rounded-full border border-slate-800/90 bg-slate-950/90 px-1.5 py-0.5 font-mono text-[9px] text-slate-300 transition-all hover:border-brand-500/40 hover:bg-slate-900 hover:text-brand-300 cursor-help shadow-xs"
          >
            <FileText className="h-2 w-2 shrink-0 text-brand-400" />
            {label}
          </span>
        );
      })}

      {hiddenCount > 0 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="inline-flex items-center gap-0.5 rounded-full border border-brand-500/30 bg-brand-500/10 px-1.5 py-0.5 font-mono text-[9px] font-medium text-brand-300 transition-all hover:bg-brand-500/20 cursor-pointer"
          title={expanded ? "Show fewer sources" : `View ${hiddenCount} more source documents`}
        >
          {expanded ? (
            <>
              Show less <ChevronUp className="h-2.5 w-2.5" />
            </>
          ) : (
            <>
              +{hiddenCount} <ChevronDown className="h-2.5 w-2.5" />
            </>
          )}
        </button>
      )}
    </div>
  );
}
