import { useEffect, useState } from 'react';
import { Plus, ShieldCheck, Activity, History, Trash2, ChevronDown, Menu } from 'lucide-react';
import type { Conversation } from '@/types';
import { useHealth, type HealthState } from '@/hooks/useHealth';

const BRANCHES = [
  { id: 'US-NY', label: 'US — New York', flag: '🗽' },
  { id: 'US-Austin', label: 'US — Austin', flag: '🤠' },
  { id: 'EU-London', label: 'EU — London', flag: '🇬🇧' },
  { id: 'Global', label: 'Global Standard', flag: '🌍' },
] as const;

interface SidebarProps {
  conversations: Conversation[];
  activeSessionId: string;
  activeBranch: string;
  onNewChat: () => void;
  onSelectConversation: (id: string) => void;
  onSelectBranch: (branch: string) => void;
  onDeleteConversation: (id: string) => void;
  isOpen: boolean;
  onToggleSidebar: () => void;
}

function HealthDot({ state }: { state: HealthState }) {
  const color =
    state === 'online'
      ? 'bg-signal-green'
      : state === 'offline'
        ? 'bg-signal-red'
        : 'bg-signal-amber';
  return <span className={`inline-flex h-2 w-2 rounded-full ${color}`} />;
}

function BranchSelector({
  activeBranch,
  onSelect,
}: {
  activeBranch: string;
  onSelect: (b: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const current = BRANCHES.find((b) => b.id === activeBranch) ?? BRANCHES[3];

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2 text-xs font-medium text-slate-200 transition-colors hover:bg-slate-800/80"
      >
        <span className="flex items-center gap-2">
          <span>{current.flag}</span>
          {current.label}
        </span>
        <ChevronDown className={`h-3.5 w-3.5 text-slate-400 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute z-20 mt-1 w-full animate-fade-in-soft rounded-lg border border-slate-800 bg-slate-900 p-1 shadow-xl shadow-black/40">
            {BRANCHES.map((b) => (
              <button
                key={b.id}
                onClick={() => {
                  onSelect(b.id);
                  setOpen(false);
                }}
                className={`flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-left text-xs transition-colors ${
                  b.id === activeBranch
                    ? 'bg-brand-500/15 text-brand-300'
                    : 'text-slate-300 hover:bg-white/5'
                }`}
              >
                <span>{b.flag}</span>
                {b.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export function Sidebar({
  conversations,
  activeSessionId,
  activeBranch,
  onNewChat,
  onSelectConversation,
  onSelectBranch,
  onDeleteConversation,
  isOpen,
  onToggleSidebar,
}: SidebarProps) {
  const { state: health } = useHealth();
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 30);
    return () => clearTimeout(t);
  }, []);

  return (
    <aside className={`relative z-20 flex h-full w-[260px] shrink-0 flex-col border-r border-slate-800/60 bg-ink-850/80 transition-all duration-300 ease-in-out ${isOpen ? 'ml-0 opacity-100' : '-ml-[260px] opacity-0 pointer-events-none'}`}>
      {/* Brand */}
      <div className="flex h-14 items-center gap-3 px-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-500/15 border border-brand-500/20">
          <ShieldCheck className="h-4 w-4 text-brand-400" strokeWidth={2} />
        </div>
        <div className="leading-tight flex-1 min-w-0">
          <h1 className="text-[13px] font-semibold text-slate-100 truncate">Enterprise Compliance</h1>
          <p className="text-[10px] font-mono text-slate-500">AI Assistant</p>
        </div>
        <button
          onClick={onToggleSidebar}
          className="flex shrink-0 items-center justify-center rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-white/5 hover:text-slate-200"
          aria-label="Close Sidebar"
        >
          <Menu className="h-4 w-4" />
        </button>
      </div>

      {/* New Chat */}
      <div className="px-4 pb-3">
        <button
          onClick={onNewChat}
          className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-800 bg-slate-900/80 px-4 py-2.5 text-[13px] font-medium text-slate-200 transition-colors hover:bg-slate-800 hover:border-slate-700"
        >
          <Plus className="h-4 w-4" strokeWidth={2.25} />
          New Chat
        </button>
      </div>

      {/* Branch scope */}
      <div className="px-4 pb-4">
        <p className="mb-1.5 text-[10px] font-medium uppercase tracking-wider text-slate-500">
          Branch Scope
        </p>
        <BranchSelector activeBranch={activeBranch} onSelect={onSelectBranch} />
      </div>

      {/* History */}
      <div className="flex min-h-0 flex-1 flex-col px-4 pb-2">
        <div className="mb-1.5 flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-wider text-slate-500">
          <History className="h-3 w-3" />
          Recent
        </div>
        <div className="scroll-area min-h-0 flex-1 overflow-y-auto pr-1">
          {conversations.length === 0 ? (
            <p className="px-2 py-4 text-[11px] text-slate-600">No conversations yet</p>
          ) : (
            <ul className="space-y-0.5">
              {conversations.map((c, i) => {
                const active = c.id === activeSessionId;
                return (
                  <li
                    key={c.id}
                    style={{
                      animation: mounted ? 'fade-in 0.3s ease-out both' : undefined,
                      animationDelay: `${Math.min(i, 8) * 40}ms`,
                    }}
                  >
                    <div
                      className={`group relative flex items-center rounded-lg pl-3 pr-1 py-2 text-xs transition-colors ${
                        active ? 'bg-brand-500/10 text-slate-100' : 'text-slate-400 hover:bg-white/5'
                      }`}
                    >
                      <button
                        onClick={() => onSelectConversation(c.id)}
                        className="min-w-0 flex-1 truncate text-left"
                      >
                        {c.title}
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteConversation(c.id);
                        }}
                        className="shrink-0 rounded p-1 text-slate-600 opacity-0 transition-opacity hover:text-signal-red group-hover:opacity-100"
                        aria-label="Delete conversation"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                      {active && (
                        <span className="absolute left-0 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-full bg-brand-400" />
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>

      {/* Health status */}
      <div className="border-t border-slate-800/60 p-4">
        <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2">
          <div className="flex items-center gap-2">
            <HealthDot state={health} />
            <span className="text-[11px] font-medium text-slate-300">
              {health === 'online' ? 'System Online' : health === 'offline' ? 'Offline' : 'Checking…'}
            </span>
          </div>
          <span className="flex items-center gap-1 text-[9px] font-mono text-slate-500">
            <Activity className="h-2.5 w-2.5" />
            health
          </span>
        </div>
      </div>
    </aside>
  );
}
