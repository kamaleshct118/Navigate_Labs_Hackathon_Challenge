import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, ShieldCheck } from 'lucide-react';
import type { Message } from '@/types';
import { SpeakButton } from './SpeakButton';
import { CitationCards } from './CitationCards';
import { DisambiguationWidget } from './DisambiguationWidget';
import { EscalationBanner } from './EscalationBanner';

interface MessageBubbleProps {
  message: Message;
  speakingId: string | null;
  onSpeak: (id: string, text: string) => void;
  speechSupported: boolean;
  onBranchSelect: (branch: string) => void;
}

export function MessageBubble({
  message,
  speakingId,
  onSpeak,
  speechSupported,
  onBranchSelect,
}: MessageBubbleProps) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex animate-fade-in justify-end gap-3">
        <div className="max-w-[78%] rounded-2xl rounded-br-md bg-brand-600 px-4 py-2.5 text-sm leading-relaxed text-white">
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
        <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-brand-500/15 border border-brand-500/20">
          <User className="h-3.5 w-3.5 text-brand-300" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex animate-fade-in gap-3">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-brand-500/15 border border-brand-500/20">
        <ShieldCheck className="h-3.5 w-3.5 text-brand-400" strokeWidth={2} />
      </div>
      <div className="max-w-[82%] min-w-0 flex-1">
        <div className="rounded-2xl border border-brand-500/12 bg-slate-900/85 p-4 shadow-lg shadow-black/20 backdrop-blur-md">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400">Compliance AI</span>
            <SpeakButton
              messageId={message.id}
              text={message.content}
              speakingId={speakingId}
              onSpeak={onSpeak}
              supported={speechSupported}
            />
          </div>
          <div className="md-body text-slate-200">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>

          {message.requiresEscalation && (
            <EscalationBanner contact={message.escalationContact ?? null} />
          )}

          {!message.requiresEscalation &&
            (message.intent === 'CLARIFY' || message.hasContradiction) && (
              <DisambiguationWidget
                onSelect={onBranchSelect}
                reason={message.contradictionReason}
              />
            )}

          {message.citations && message.citations.length > 0 && (
            <CitationCards citations={message.citations} />
          )}
        </div>
      </div>
    </div>
  );
}
