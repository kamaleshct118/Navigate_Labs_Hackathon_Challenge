export type Intent = 'ANSWER_DIRECT' | 'CLARIFY' | 'ESCALATE';

export interface ChatRequest {
  query: string;
  session_id: string;
}

export interface ChatResponse {
  query: string;
  session_id: string;
  intent: Intent;
  response: string;
  citations: string[];
  has_contradiction: boolean;
  contradiction_reason: string | null;
  requires_human_escalation: boolean;
  escalation_contact: string | null;
}

export interface HealthResponse {
  status: string;
  service?: string;
  [key: string]: unknown;
}

export type Role = 'user' | 'assistant';

export interface Message {
  id: string;
  role: Role;
  content: string;
  intent?: Intent;
  citations?: string[];
  hasContradiction?: boolean;
  contradictionReason?: string | null;
  requiresEscalation?: boolean;
  escalationContact?: string | null;
  timestamp: number;
}

export interface Conversation {
  id: string;
  title: string;
  branch: string;
  updatedAt: number;
}
