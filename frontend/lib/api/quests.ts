import { API_URL } from "./config";

export type Quest = {
  id: string;
  goal_id: string;
  roadmap_skill_id: string;
  quest_type: "learning" | "practice" | "challenge" | "recovery" | "emergency";
  title: string;
  description: string;
  resource_ids: string[];
  difficulty: "casual" | "standard" | "hunter" | "monarch";
  estimated_minutes: number;
  status: "locked" | "available" | "active" | "completed" | "expired";
  due_date: string;
  prerequisites: string[];
  completed_at: string | null;
};

export type QuestResource = {
  id: string;
  title: string;
  url: string;
  resource_type: string;
  difficulty: string;
  estimated_time: number;
  access_type: string;
  provider: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail ?? "The quest request failed.");
  }
  return response.json() as Promise<T>;
}

export async function getDailyQuests(goalId: string, assessmentId?: string) {
  const query = assessmentId ? `?goal_id=${encodeURIComponent(goalId)}&assessment_id=${encodeURIComponent(assessmentId)}` : `?goal_id=${encodeURIComponent(goalId)}`;
  return request<{ goal_id: string; date: string; quests: Quest[] }>(`/api/quests/daily${query}`);
}

export function startQuest(questId: string) {
  return request<Quest>(`/api/quests/${questId}/start`, { method: "POST" });
}

export function completeQuest(questId: string) {
  return request<Quest>(`/api/quests/${questId}/complete`, { method: "POST" });
}

export function getResource(resourceId: string) {
  return request<QuestResource>(`/api/resources/${resourceId}`);
}
