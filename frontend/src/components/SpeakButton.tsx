import { Volume2, Square } from 'lucide-react';

interface SpeakButtonProps {
  messageId: string;
  text: string;
  speakingId: string | null;
  onSpeak: (id: string, text: string) => void;
  supported: boolean;
}

export function SpeakButton({ messageId, text, speakingId, onSpeak, supported }: SpeakButtonProps) {
  if (!supported) return null;
  const isSpeaking = speakingId === messageId;
  return (
    <button
      onClick={() => onSpeak(messageId, text)}
      className="flex h-6 w-6 items-center justify-center rounded-md text-slate-500 transition-colors hover:bg-white/5 hover:text-brand-300"
      aria-label={isSpeaking ? 'Stop narration' : 'Read response aloud'}
      title={isSpeaking ? 'Stop narration' : 'Read aloud'}
    >
      {isSpeaking ? <Square className="h-3 w-3 fill-current" /> : <Volume2 className="h-3.5 w-3.5" />}
    </button>
  );
}
