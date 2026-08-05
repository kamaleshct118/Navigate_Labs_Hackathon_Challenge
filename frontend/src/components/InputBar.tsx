import { useEffect, useRef, useState } from 'react';
import { Send, Mic, Sparkles, Square } from 'lucide-react';

interface InputBarProps {
  onSend: (query: string) => void;
  onCancel?: () => void;
  disabled: boolean;
  branch: string;
}

const SUGGESTED_CHIPS = ['PTO allowance', 'Remote work', 'Code of conduct', 'Data retention'];

export function InputBar({ onSend, onCancel, disabled, branch }: InputBarProps) {
  const [value, setValue] = useState('');
  const [listening, setListening] = useState(false);
  const taRef = useRef<HTMLTextAreaElement | null>(null);
  const recognitionRef = useRef<any>(null);

  const autoResize = () => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  };

  useEffect(() => {
    autoResize();
  }, [value]);

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
  };

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const toggleVoice = () => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return;
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }
    const rec = new SR();
    rec.continuous = false;
    rec.interimResults = true;
    rec.lang = 'en-US';
    rec.onresult = (e: any) => {
      let transcript = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        transcript += e.results[i][0].transcript;
      }
      setValue(transcript);
    };
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    rec.start();
    recognitionRef.current = rec;
    setListening(true);
  };

  return (
    <div className="border-t border-slate-800/60 bg-ink-950/80 px-5 pb-5 pt-3 backdrop-blur-md">
      {/* Suggested chips row */}
      <div className="mx-auto mb-3 flex max-w-4xl flex-wrap items-center gap-1.5">
        <span className="mr-1 text-[10px] font-medium uppercase tracking-wider text-slate-500">Try:</span>
        {SUGGESTED_CHIPS.map((chip) => (
          <button
            key={chip}
            onClick={() => setValue(chip)}
            disabled={disabled}
            className="rounded-full border border-slate-800 bg-slate-900/60 px-3 py-1 text-[11px] text-slate-400 transition-colors hover:border-brand-500/30 hover:bg-brand-500/10 hover:text-brand-300 disabled:opacity-40"
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Input area */}
      <div className="mx-auto max-w-4xl">
        <div className="flex items-center gap-0 rounded-xl border border-slate-800/90 bg-slate-900/90 transition-colors focus-within:border-brand-500/30">
          {/* Branch badge — left of divider */}
          <div className="flex shrink-0 items-center self-stretch border-r border-slate-800/60 px-3">
            <span className="whitespace-nowrap rounded-md bg-brand-500/10 px-2 py-1 text-[10px] font-mono text-brand-300">
              {branch}
            </span>
          </div>
          {/* Textarea — grows freely */}
          <textarea
            ref={taRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKey}
            disabled={disabled}
            rows={1}
            placeholder="Ask about compliance policies, PTO, remote work…"
            className="flex-1 resize-none bg-transparent px-3 py-3 text-sm leading-6 text-slate-100 placeholder:text-slate-500 focus:outline-none disabled:opacity-50 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
            style={{ minHeight: '46px', maxHeight: '160px' }}
          />
          {/* Action buttons — right side */}
          <div className="flex shrink-0 items-center gap-1 self-stretch border-l border-slate-800/60 px-2">
            <button
              onClick={toggleVoice}
              disabled={disabled}
              className={`flex h-8 w-8 items-center justify-center rounded-lg transition-colors ${
                listening
                  ? 'bg-signal-red/15 text-signal-red'
                  : 'text-slate-500 hover:bg-white/5 hover:text-slate-300'
              }`}
              aria-label="Voice input"
              title={listening ? 'Stop listening' : 'Voice input'}
            >
              <Mic className="h-4 w-4" />
            </button>
            {disabled && onCancel ? (
              <button
                onClick={onCancel}
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-signal-red/20 text-signal-red transition-colors hover:bg-signal-red/30"
                title="Stop generating"
              >
                <Square className="h-3 w-3 fill-current" />
              </button>
            ) : (
              <button
                onClick={submit}
                disabled={disabled || !value.trim()}
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-500 text-white transition-colors hover:bg-brand-600 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <Send className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
        <p className="mt-2 flex items-center justify-center gap-1.5 text-center text-[10px] text-slate-600">
          <Sparkles className="h-2.5 w-2.5" />
          Compliance AI can make mistakes. Verify critical decisions with verified sources.
        </p>
      </div>
    </div>
  );
}
