export type GapAnalysisItem = {
  skill_id: string;
  skill_name: string;
  mastery: number | null;
  classification: "skip" | "review" | "learn" | "locked";
  reason: string;
  blocked_by: string[];
};

export type RoadmapNode = {
  order: number;
  skill_id: string;
  skill_name: string;
  mastery: number | null;
  classification: "skip" | "review" | "learn" | "locked";
  status: "locked" | "available" | "in_progress" | "completed" | "skipped";
  estimated_effort: string | null;
  prerequisites: string[];
  reason: string;
  resources: Array<{
    id: string;
    title: string;
    description: string;
    url: string;
    resource_type: string;
    skill_ids: string[];
    difficulty: string;
    estimated_time: number;
    learning_styles: string[];
    access_type: string;
    provider: string;
  }>;
  boss_battle_status: "locked" | "unavailable" | "available" | "completed";
};

export type PersonalizationResult = {
  goal_id: string;
  assessment_id: string;
  summary: {
    skills_to_skip: number;
    skills_to_review: number;
    skills_to_learn: number;
    skills_locked: number;
  };
  gap_analysis: GapAnalysisItem[];
  roadmap: RoadmapNode[];
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function analyzePersonalization(goalId: string, assessmentId: string) {
  const response = await fetch(`${API_URL}/api/personalization/analyze`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ goal_id: goalId, assessment_id: assessmentId }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail ?? "We could not generate your personalized roadmap.");
  }

  return response.json() as Promise<PersonalizationResult>;
}
