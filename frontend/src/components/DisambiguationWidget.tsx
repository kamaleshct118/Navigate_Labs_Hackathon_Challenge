import { MapPin } from 'lucide-react';

const BRANCH_OPTIONS = [
  { id: 'US-NY', label: 'US — New York', flag: '🗽' },
  { id: 'US-Austin', label: 'US — Austin', flag: '🤠' },
  { id: 'EU-London', label: 'EU — London', flag: '🇬🇧' },
  { id: 'Global', label: 'Global Standard', flag: '🌍' },
] as const;

interface DisambiguationWidgetProps {
  onSelect: (branchId: string) => void;
  reason?: string | null;
}

export function DisambiguationWidget({ onSelect, reason }: DisambiguationWidgetProps) {
  return (
    <div className="mt-4 animate-fade-in rounded-xl border border-signal-amber/20 bg-signal-amber/5 p-3.5">
      <div className="mb-2.5 flex items-center gap-2">
        <div className="flex h-6 w-6 items-center justify-center rounded-md bg-signal-amber/15">
          <MapPin className="h-3.5 w-3.5 text-signal-amber" />
        </div>
        <div>
          <p className="text-[13px] font-semibold text-amber-300">Disambiguation Required</p>
          {reason && <p className="text-[11px] text-amber-200/60">{reason}</p>}
        </div>
      </div>
      <p className="mb-2 text-[11px] font-medium text-slate-400">Select your office location</p>
      <div className="flex flex-wrap gap-1.5">
        {BRANCH_OPTIONS.map((b) => (
          <button
            key={b.id}
            onClick={() => onSelect(b.id)}
            className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/80 px-3 py-1.5 text-xs font-medium text-slate-200 transition-colors hover:border-brand-500/30 hover:bg-brand-500/10 hover:text-brand-200"
          >
            <span>{b.flag}</span>
            {b.label}
          </button>
        ))}
      </div>
    </div>
  );
}
