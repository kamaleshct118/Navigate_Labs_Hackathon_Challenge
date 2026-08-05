import { ShieldCheck, FileText, Scale, GitCompare, Lock, Globe2 } from 'lucide-react';

const QUICK_PROMPTS = [
  { icon: FileText, label: 'Annual PTO allowance & holiday schedule', query: 'What is the annual PTO allowance and holiday schedule?' },
  { icon: Scale, label: 'Remote work policy across branches', query: 'What is the remote work policy?' },
  { icon: GitCompare, label: 'Compare US-NY vs EU-London leave policies', query: 'Compare the leave policies between US-NY and EU-London branches' },
  { icon: Lock, label: 'Data retention & privacy obligations', query: 'What are the data retention and privacy obligations?' },
];

const STATS = [
  { label: 'Policy Docs', value: '1,240' },
  { label: 'Jurisdictions', value: '14' },
  { label: 'Avg Response', value: '1.2s' },
  { label: 'Accuracy', value: '99.4%' },
];

export function WelcomeScreen({ onPickPrompt }: { onPickPrompt: (q: string) => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-6 py-8">
      <div className="w-full max-w-[640px]">
        {/* Hero */}
        <div className="mb-8 animate-fade-in text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl border border-brand-500/20 bg-brand-500/12">
            <ShieldCheck className="h-6 w-6 text-brand-400" strokeWidth={1.8} />
          </div>
          <h2 className="text-lg font-semibold tracking-tight text-slate-100 sm:text-xl">
            Enterprise Compliance AI Assistant
          </h2>
          <p className="mx-auto mt-2 max-w-sm text-sm leading-relaxed text-slate-400">
            Ask about HR policies, regional regulations, and compliance standards — backed by
            verified, versioned citations.
          </p>
        </div>

        {/* Stats */}
        <div className="mb-8 grid grid-cols-4 gap-2">
          {STATS.map((s, i) => (
            <div
              key={s.label}
              style={{ animationDelay: `${i * 40}ms` }}
              className="animate-fade-in rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-3 text-center"
            >
              <p className="text-base font-semibold leading-none text-slate-100">{s.value}</p>
              <p className="mt-1.5 text-[10px] font-medium uppercase tracking-wide text-slate-500">
                {s.label}
              </p>
            </div>
          ))}
        </div>

        {/* Quick prompts */}
        <div>
          <p className="mb-2.5 flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-wider text-slate-500">
            <Globe2 className="h-3 w-3" />
            Suggested prompts
          </p>
          <div className="grid gap-2 sm:grid-cols-2">
            {QUICK_PROMPTS.map((p, i) => (
              <button
                key={p.label}
                onClick={() => onPickPrompt(p.query)}
                style={{ animationDelay: `${i * 40}ms` }}
                className="group flex animate-fade-in items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3 text-left transition-colors hover:border-brand-500/30 hover:bg-slate-800/80"
              >
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-brand-500/10 transition-colors group-hover:bg-brand-500/18">
                  <p.icon className="h-3.5 w-3.5 text-brand-400" strokeWidth={1.8} />
                </div>
                <span className="text-xs leading-snug text-slate-300">{p.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
