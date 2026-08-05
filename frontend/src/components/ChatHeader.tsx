import { Trash2, RotateCcw, Brain } from 'lucide-react';

interface ChatHeaderProps {
  branch: string;
  onClearMemory: () => void;
  clearing: boolean;
  hasMessages: boolean;
}

export function ChatHeader({ branch, onClearMemory, clearing, hasMessages }: ChatHeaderProps) {
  return (
    <div className="flex h-14 items-center justify-between border-b border-slate-800/60 px-5">
      <div className="flex items-center gap-2.5">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-500/15">
          <Brain className="h-4 w-4 text-brand-400" />
        </div>
        <span className="text-sm font-semibold text-slate-100">Compliance Session</span>
        <span className="rounded-md border border-slate-800 bg-slate-900/60 px-2 py-0.5 text-[10px] font-medium text-slate-300">
          {branch}
        </span>
      </div>
      {hasMessages && (
        <button
          onClick={onClearMemory}
          disabled={clearing}
          className="flex items-center gap-1.5 rounded-lg border border-slate-800 px-2.5 py-1.5 text-xs font-medium text-slate-400 transition-colors hover:border-signal-red/30 hover:bg-signal-red/5 hover:text-signal-red disabled:opacity-50"
        >
          {clearing ? (
            <RotateCcw className="h-3.5 w-3.5 animate-spin-slow" />
          ) : (
            <Trash2 className="h-3.5 w-3.5" />
          )}
          Clear Memory
        </button>
      )}
    </div>
  );
}
