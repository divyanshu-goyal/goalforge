export type GoalDiscoveryData = {
  goal: string;
  objective: string;
  experience_level: string;
  weekly_hours: string;
  timeline: string;
  learning_style: string;
  difficulty: string;
  resource_preference: string;
  motivation: string;
  prior_knowledge: string;
};

export type GoalProfile = Omit<GoalDiscoveryData, "weekly_hours"> & {
  weekly_hours: number;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function discoverGoal(data: GoalDiscoveryData): Promise<GoalProfile> {
  const response = await fetch(`${API_URL}/api/goals/discover`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error("We could not create your learning profile.");
  }

  return response.json() as Promise<GoalProfile>;
}