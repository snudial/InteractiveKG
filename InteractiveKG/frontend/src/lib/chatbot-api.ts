/**
 * Client for the guided-session (`/api/chatbot`) endpoints that drive the study
 * walkthrough: session lifecycle, scenario loading, and phase progression.
 *
 * Unlike {@link GraphAPI}, these methods return the payload directly and throw
 * {@link ApiError} on failure — every call site wraps them in try/catch.
 */

import { apiFetch } from '@/lib/api';
import type {
  ChatbotRequest,
  ChatbotResponse,
  ScenarioLoadRequest,
  ScenarioLoadResponse,
  SessionInfo,
  TestPhase,
} from '@/types/chatbot';

/** Response of POST /api/chatbot/create-session. */
export interface CreateSessionResponse {
  session_id: string;
  current_phase: TestPhase;
  success: boolean;
}

/**
 * Response of POST /api/chatbot/advance-phase.
 *
 * `current_phase` is only meaningful when `success` is true — the backend omits it
 * when the phase transition is rejected — so call sites must check `success` first.
 */
export interface AdvancePhaseResponse {
  success: boolean;
  current_phase: TestPhase;
  advance_button?: ChatbotResponse['advance_button'];
  data_source_selection_buttons?: ChatbotResponse['data_source_selection_buttons'];
  message?: string;
}

/** Response of POST /api/chatbot/progress. */
export interface ProgressResponse {
  session_id: string;
  current_phase: TestPhase;
  progress_percentage: number;
  phase_description: string;
  next_instructions: string;
  success: boolean;
  error?: string;
}

/** Actions accepted by the progress endpoint. */
export type ProgressAction = 'next_phase' | 'previous_phase' | 'reset' | 'complete_act';

function postJson<T>(path: string, payload: unknown, fallbackMessage: string): Promise<T> {
  return apiFetch<T>(
    path,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
    fallbackMessage,
  );
}

export const ChatbotAPI = {
  /** Start a new guided session and get its identifier. */
  createSession(): Promise<CreateSessionResponse> {
    return postJson<CreateSessionResponse>('/api/chatbot/create-session', {}, 'Failed to create session');
  },

  /** Send a user message (or a named action) and get the assistant's reply. */
  sendMessage(request: ChatbotRequest): Promise<ChatbotResponse> {
    return postJson<ChatbotResponse>('/api/chatbot/chat', request, 'Failed to send message');
  },

  /** Read the current phase, progress, and pending UI affordances for a session. */
  getSessionInfo(sessionId: string): Promise<SessionInfo> {
    return apiFetch<SessionInfo>(
      `/api/chatbot/session/${encodeURIComponent(sessionId)}`,
      undefined,
      'Failed to load session info',
    );
  },

  /** Load a scenario's dataset into the graph for this session. */
  loadScenario(request: ScenarioLoadRequest): Promise<ScenarioLoadResponse> {
    return postJson<ScenarioLoadResponse>(
      '/api/chatbot/load-scenario',
      request,
      'Failed to load scenario',
    );
  },

  /** Move the session to `targetPhase`, or to the next phase when it is omitted. */
  advancePhase(sessionId: string, targetPhase?: TestPhase | string): Promise<AdvancePhaseResponse> {
    return postJson<AdvancePhaseResponse>(
      '/api/chatbot/advance-phase',
      { session_id: sessionId, target_phase: targetPhase },
      'Failed to advance phase',
    );
  },

  /** Apply a progress action (advance, rewind, reset, or complete the current act). */
  updateProgress(
    sessionId: string,
    action: ProgressAction,
    phase?: TestPhase,
  ): Promise<ProgressResponse> {
    return postJson<ProgressResponse>(
      '/api/chatbot/progress',
      { session_id: sessionId, action, phase },
      'Failed to update progress',
    );
  },
};
