import { useCallback, useEffect, useState } from 'react';

function stripMarkdown(text: string): string {
  return text
    .replace(/```[\s\S]*?```/g, ' code block. ')
    .replace(/`[^`]*`/g, '')
    .replace(/[#*_|>~]/g, '')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\n{3,}/g, '. ')
    .trim();
}

export function useSpeech() {
  const [supported] = useState(() => typeof window !== 'undefined' && 'speechSynthesis' in window);
  const [speakingId, setSpeakingId] = useState<string | null>(null);

  useEffect(() => {
    if (!supported) return;
    const onEnd = () => setSpeakingId(null);
    window.speechSynthesis.addEventListener('end', onEnd);
    window.speechSynthesis.addEventListener('pause', onEnd);
    return () => {
      window.speechSynthesis.removeEventListener('end', onEnd);
      window.speechSynthesis.removeEventListener('pause', onEnd);
    };
  }, [supported]);

  const speak = useCallback(
    (id: string, text: string) => {
      if (!supported) return;
      if (speakingId === id) {
        window.speechSynthesis.cancel();
        setSpeakingId(null);
        return;
      }
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(stripMarkdown(text));
      utterance.rate = 1;
      utterance.pitch = 1;
      utterance.onend = () => setSpeakingId(null);
      utterance.onerror = () => setSpeakingId(null);
      setSpeakingId(id);
      window.speechSynthesis.speak(utterance);
    },
    [supported, speakingId],
  );

  const stop = useCallback(() => {
    if (!supported) return;
    window.speechSynthesis.cancel();
    setSpeakingId(null);
  }, [supported]);

  return { supported, speakingId, speak, stop };
}
