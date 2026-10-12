import { API_URL } from "./config";

export type AIInsight = {
  summary: string;
  insights: string[];
  recommended_skill_ids: string[];
  recommended_resource_ids: string[];
  recommended_quest_types: string[];
  explanations: string[];
  ai_available: boolean;
};

export type AIMentorResponse = {
  message: string;
  context_used: string[];
  ai_available: boolean;
};

async function request<T>(path: string, body: object): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const bodyJson = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(bodyJson?.detail ?? "The AI request failed.");
  }
  return response.json() as Promise<T>;
}

export function getAIInsights(goalId: string, assessmentId: string) {
  return request<AIInsight>(`/api/ai/personalize`, { goal_id: goalId, assessment_id: assessmentId });
}

export function askMentor(goalId: string, message: string) {
  return request<AIMentorResponse>(`/api/ai/mentor`, { goal_id: goalId, message });
}
