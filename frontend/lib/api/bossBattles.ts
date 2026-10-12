import { API_URL } from "./config";

export type BossBattleQuestion = {
  id: string;
  skill_id: string;
  question: string;
  question_type: "mcq" | "code_output" | "conceptual";
  options: string[];
  difficulty: "medium" | "hard" | "advanced";
};

export type BossBattleAttempt = {
  attempt_id: string;
  goal_id: string;
  skill_id: string;
  questions: BossBattleQuestion[];
  status: "available" | "in_progress" | "passed" | "failed";
  current_question: number;
  score: number | null;
  result: BossBattleResult | null;
};

export type BossBattleResult = {
  attempt_id: string;
  goal_id: string;
  skill_id: string;
  score: number;
  passed: boolean;
  questions_correct: number;
  questions_incorrect: number;
  mastery_before: number;
  mastery_after: number;
  xp_awarded: number;
  rank_before: string;
  rank_after: string;
  weak_areas: string[];
  next_action: string;
  goal_completed: boolean;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail ?? "The Boss Battle request failed.");
  }
  return response.json() as Promise<T>;
}

export function startBossBattle(goalId: string, skillId: string) {
  return request<BossBattleAttempt>("/api/boss-battles", {
    method: "POST",
    body: JSON.stringify({ goal_id: goalId, skill_id: skillId }),
  });
}

export function getBossBattle(attemptId: string) {
  return request<BossBattleAttempt>(`/api/boss-battles/${attemptId}`);
}

export function submitBossBattle(attemptId: string, answers: Array<{ question_id: string; answer: string }>) {
  return request<BossBattleResult>(`/api/boss-battles/${attemptId}/submit`, {
    method: "POST",
    body: JSON.stringify({ answers }),
  });
}
