import { API_URL } from "./config";

export type AssessmentQuestion = {
  id: string;
  skill_id: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  question_type: "multiple_choice";
  question: string;
  options: string[];
};

export type Assessment = {
  assessment_id: string;
  goal_id: string;
  questions: AssessmentQuestion[];
};

export type AssessmentContext = {
  experience_level?: string;
  learning_style?: string;
  resource_preference?: string;
  difficulty?: string;
};

export type SkillResult = {
  skill_id: string;
  questions_attempted: number;
  correct: number;
  score: number;
  classification: "weak" | "developing" | "strong";
};

export type AssessmentResult = {
  assessment_id: string;
  total_questions: number;
  total_correct: number;
  overall_score: number;
  overall_classification: "weak" | "developing" | "strong";
  skill_results: SkillResult[];
  weak_skills: string[];
  strong_skills: string[];
  question_results: Array<{
    question_id: string;
    skill_id: string;
    correct: boolean;
    explanation: string;
  }>;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init?.headers },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail ?? "The assessment request failed.");
  }

  return response.json() as Promise<T>;
}

export function createAssessment(goalId: string, context: AssessmentContext = {}) {
  return request<Assessment>("/api/assessments", {
    method: "POST",
    body: JSON.stringify({ goal_id: goalId, user_context: context }),
  });
}

export function submitAssessment(assessmentId: string, answers: Array<{ question_id: string; answer: string }>) {
  return request<AssessmentResult>(`/api/assessments/${assessmentId}/submit`, {
    method: "POST",
    body: JSON.stringify({ answers }),
  });
}
