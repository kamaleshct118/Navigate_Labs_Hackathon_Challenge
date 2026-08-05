import { ShieldAlert, Mail, Phone } from 'lucide-react';

interface EscalationBannerProps {
  contact: string | null;
}

export function EscalationBanner({ contact }: EscalationBannerProps) {
  const email = contact || 'compliance-officer@enterprise.com';
  return (
    <div className="mt-4 animate-fade-in overflow-hidden rounded-xl border border-signal-red/25 bg-signal-red/5">
      <div className="flex items-start gap-3 p-4">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-signal-red/15">
          <ShieldAlert className="h-5 w-5 text-signal-red" strokeWidth={2} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-[13px] font-semibold text-red-300">High-Risk Legal Escalation</h3>
            <span className="rounded-full bg-signal-red/15 px-1.5 py-0.5 text-[9px] font-mono uppercase tracking-wide text-red-300">
              Action Required
            </span>
          </div>
          <p className="mt-1 text-xs leading-relaxed text-red-200/70">
            This query involves matters requiring human legal review. The AI assistant cannot
            provide guidance on this topic. Please escalate to the compliance team.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <a
              href={`mailto:${email}?subject=Compliance%20Escalation`}
              className="flex items-center gap-1.5 rounded-lg border border-signal-red/25 bg-signal-red/10 px-3 py-1.5 text-xs font-medium text-red-200 transition-colors hover:bg-signal-red/20"
            >
              <Mail className="h-3.5 w-3.5" />
              {email}
            </a>
            <div className="flex items-center gap-1.5 rounded-lg border border-white/8 bg-ink-800 px-3 py-1.5 text-xs font-medium text-slate-300">
              <Phone className="h-3.5 w-3.5 text-signal-amber" />
              +1 (800) 555-0199
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
