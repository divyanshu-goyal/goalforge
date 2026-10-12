import { API_URL } from "./config";

export type Achievement = {
  achievement_id: string;
  name: string;
  description: string;
  hidden: boolean;
  unlocked: boolean;
  unlocked_at: string | null;
};

export type GamificationProfile = {
  total_xp: number;
  current_xp: number;
  level: number;
  next_level: number;
  xp_for_next_level: number;
  xp_progress: number;
  current_streak: number;
  longest_streak: number;
  last_active_date: string | null;
  streak_shields: number;
  current_rank: string;
  eligible_rank: string;
  active_xp_multiplier: number;
  active_buff: string;
  achievements: Achievement[];
  recovery_required: boolean;
  roadmap_review_required: boolean;
  last_xp_awarded: number;
  last_xp_reason: string;
};

export async function getGamificationProfile() {
  const response = await fetch(`${API_URL}/api/gamification/profile`, { credentials: "include" });
  if (!response.ok) throw new Error("The gamification profile could not be loaded.");
  return response.json() as Promise<GamificationProfile>;
}
