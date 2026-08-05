import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AuroraBackground } from '@/components/AuroraBackground';
import { Sidebar } from '@/components/Sidebar';
import { ChatHeader } from '@/components/ChatHeader';
import { MessageBubble } from '@/components/MessageBubble';
import { TypingIndicator } from '@/components/TypingIndicator';
import { InputBar } from '@/components/InputBar';
import { WelcomeScreen } from '@/components/WelcomeScreen';
import { useSpeech } from '@/hooks/useSpeech';
import { postChat, deleteSession } from '@/lib/api';
import type { Conversation, Message } from '@/types';

const STORAGE_KEY = 'ecai_sessions_v1';

interface PersistedState {
  conversations: Conversation[];
  messagesBySession: Record<string, Message[]>;
  activeSessionId: string;
  branch: string;
}

function genId(): string {
  return `emp_session_${Math.random().toString(36).slice(2, 10)}`;
}

function loadState(): PersistedState | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as PersistedState;
  } catch {
    return null;
  }
}

function titleFromQuery(q: string): string {
  const clean = q.replace(/[#*`]/g, '').trim();
  return clean.length > 42 ? clean.slice(0, 42) + '…' : clean || 'New conversation';
}

export default function App() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messagesBySession, setMessagesBySession] = useState<Record<string, Message[]>>({});
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [branch, setBranch] = useState<string>('Global');
  const [loading, setLoading] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const { supported: speechSupported, speakingId, speak } = useSpeech();

  // Hydrate from localStorage
  useEffect(() => {
    const persisted = loadState();
    if (persisted && persisted.activeSessionId) {
      setConversations(persisted.conversations || []);
      setMessagesBySession(persisted.messagesBySession || {});
      setActiveSessionId(persisted.activeSessionId);
      setBranch(persisted.branch || 'Global');
    } else {
      const id = genId();
      setActiveSessionId(id);
      setBranch('Global');
    }
  }, []);

  // Persist
  useEffect(() => {
    if (!activeSessionId) return;
    const state: PersistedState = { conversations, messagesBySession, activeSessionId, branch };
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      /* ignore quota */
    }
  }, [conversations, messagesBySession, activeSessionId, branch]);

  const activeMessages = useMemo(
    () => (activeSessionId ? messagesBySession[activeSessionId] || [] : []),
    [messagesBySession, activeSessionId],
  );

  // Auto-scroll
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  }, [activeMessages, loading]);

  const newChat = useCallback(() => {
    abortRef.current?.abort();
    setLoading(false);
    const id = genId();
    setActiveSessionId(id);
    setError(null);
  }, []);

  const selectConversation = useCallback((id: string) => {
    abortRef.current?.abort();
    setLoading(false);
    setActiveSessionId(id);
    setError(null);
  }, []);

  const deleteConversation = useCallback(
    (id: string) => {
      setConversations((prev) => prev.filter((c) => c.id !== id));
      setMessagesBySession((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      if (id === activeSessionId) {
        const id2 = genId();
        setActiveSessionId(id2);
      }
      deleteSession(id).catch(() => {});
    },
    [activeSessionId],
  );

  const clearMemory = useCallback(async () => {
    if (!activeSessionId || clearing) return;
    setClearing(true);
    try {
      await deleteSession(activeSessionId);
      setMessagesBySession((prev) => ({ ...prev, [activeSessionId]: [] }));
    } catch {
      setError('Could not clear session memory.');
    } finally {
      setClearing(false);
    }
  }, [activeSessionId, clearing]);

  const sendQuery = useCallback(
    async (query: string) => {
      if (!query.trim() || !activeSessionId || loading) return;
      setError(null);
      const userMsg: Message = {
        id: `${Date.now()}_u`,
        role: 'user',
        content: query,
        timestamp: Date.now(),
      };
      setMessagesBySession((prev) => ({
        ...prev,
        [activeSessionId]: [...(prev[activeSessionId] || []), userMsg],
      }));

      // Ensure conversation exists
      setConversations((prev) => {
        const exists = prev.find((c) => c.id === activeSessionId);
        if (exists) {
          return prev.map((c) =>
            c.id === activeSessionId
              ? { ...c, title: c.title === 'New conversation' ? titleFromQuery(query) : c.title, updatedAt: Date.now() }
              : c,
          );
        }
        return [
          { id: activeSessionId, title: titleFromQuery(query), branch, updatedAt: Date.now() },
          ...prev,
        ];
      });

      setLoading(true);
      const controller = new AbortController();
      abortRef.current = controller;

      const queryToSend =
        branch && branch !== 'Global' && !query.toLowerCase().includes(branch.toLowerCase())
          ? `${query} for ${branch}`
          : query;

      try {
        const res = await postChat({ query: queryToSend, session_id: activeSessionId }, controller.signal);
        const aiMsg: Message = {
          id: `${Date.now()}_a`,
          role: 'assistant',
          content: res.response,
          intent: res.intent,
          citations: res.citations,
          hasContradiction: res.has_contradiction,
          contradictionReason: res.contradiction_reason,
          requiresEscalation: res.requires_human_escalation,
          escalationContact: res.escalation_contact,
          timestamp: Date.now(),
        };
        setMessagesBySession((prev) => ({
          ...prev,
          [activeSessionId]: [...(prev[activeSessionId] || []), aiMsg],
        }));
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') return;
        const errMsg: Message = {
          id: `${Date.now()}_e`,
          role: 'assistant',
          content:
            'I could not reach the compliance service. Please verify the backend is running and try again.',
          timestamp: Date.now(),
        };
        setMessagesBySession((prev) => ({
          ...prev,
          [activeSessionId]: [...(prev[activeSessionId] || []), errMsg],
        }));
        setError(err instanceof Error ? err.message : 'Request failed');
      } finally {
        setLoading(false);
      }
    },
    [activeSessionId, loading, branch],
  );

  const handleBranchSelect = useCallback(
    (b: string) => {
      sendQuery(b);
    },
    [sendQuery],
  );

  return (
    <div className="relative flex h-screen w-screen overflow-hidden bg-ink-950 text-slate-100">
      <AuroraBackground />
      <Sidebar
        conversations={conversations}
        activeSessionId={activeSessionId}
        activeBranch={branch}
        onNewChat={newChat}
        onSelectConversation={selectConversation}
        onSelectBranch={setBranch}
        onDeleteConversation={deleteConversation}
      />
      <main className="relative z-10 flex min-w-0 flex-1 flex-col">
        <ChatHeader
          branch={branch}
          onClearMemory={clearMemory}
          clearing={clearing}
          hasMessages={activeMessages.length > 0}
        />
        <div ref={scrollRef} className="scroll-area min-h-0 flex-1 overflow-y-auto">
          {activeMessages.length === 0 ? (
            <WelcomeScreen onPickPrompt={sendQuery} />
          ) : (
            <div className="mx-auto max-w-3xl space-y-6 px-5 py-7">
              {activeMessages.map((m) => (
                <MessageBubble
                  key={m.id}
                  message={m}
                  speakingId={speakingId}
                  onSpeak={speak}
                  speechSupported={speechSupported}
                  onBranchSelect={handleBranchSelect}
                />
              ))}
              {loading && <TypingIndicator />}
            </div>
          )}
        </div>
        <InputBar onSend={sendQuery} disabled={loading} branch={branch} />
      </main>
    </div>
  );
}
