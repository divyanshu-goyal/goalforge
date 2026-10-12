"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { completeQuest, getDailyQuests, getResource, Quest, QuestResource, startQuest } from "../../../lib/api/quests";
import { getGamificationProfile, GamificationProfile } from "../../../lib/api/gamification";

function format(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function goalName(goalId: string) {
  return format(goalId.replace("learn_", "").replaceAll("_", " "));
}

export default function QuestsPage() {
  const params = useParams<{ goalId: string }>();
  const searchParams = useSearchParams();
  const assessmentId = searchParams.get("assessment_id") ?? undefined;
  const [quests, setQuests] = useState<Quest[]>([]);
  const [dailyDate, setDailyDate] = useState("");
  const [selected, setSelected] = useState<Quest | null>(null);
  const [resources, setResources] = useState<QuestResource[]>([]);
  const [error, setError] = useState("");
  const [profile, setProfile] = useState<GamificationProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [updatingQuest, setUpdatingQuest] = useState<"start" | "complete" | null>(null);

  useEffect(() => {
    if (!params.goalId) return;
    setIsLoading(true);
    setError("");
    getDailyQuests(params.goalId, assessmentId)
      .then((response) => {
        setDailyDate(response.date);
        setQuests(response.quests);
        setSelected(response.quests[0] ?? null);
      })
      .catch((requestError: Error) => setError(requestError.message))
      .finally(() => setIsLoading(false));
    getGamificationProfile()
      .then(setProfile)
      .catch((requestError: Error) => setError(requestError.message));
  }, [assessmentId, params.goalId]);

  useEffect(() => {
    if (!selected || selected.resource_ids.length === 0) {
      setResources([]);
      return;
    }
    Promise.all(selected.resource_ids.map(getResource))
      .then(setResources)
      .catch(() => setResources([]));
  }, [selected]);

  async function updateQuest(action: "start" | "complete") {
    if (!selected) return;
    setError("");
    setUpdatingQuest(action);
    try {
      const updated = action === "start" ? await startQuest(selected.id) : await completeQuest(selected.id);
      setQuests((current) => current.map((quest) => quest.id === updated.id ? updated : quest));
      setSelected(updated);
      if (action === "complete") setProfile(await getGamificationProfile());
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The quest could not be updated.");
    } finally {
      setUpdatingQuest(null);
    }
  }

  function displayDate(value: string) {
    const [year, month, day] = value.split("-");
    return value ? `${Number(month)}/${Number(day)}/${year}` : "";
  }

  if (error) {
    return <main className="flex min-h-screen flex-col items-center justify-center gap-5 bg-slate-950 px-6 text-center text-rose-300"><p>{error}</p><button type="button" onClick={() => window.location.reload()} className="rounded-full border border-slate-700 px-5 py-3 font-semibold text-slate-300">Retry</button></main>;
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-12 text-slate-100">
      <section className="mx-auto max-w-4xl">
        <Link href="/" className="text-sm font-semibold text-cyan-300 hover:text-cyan-200">GoalForge AI</Link>
        <div className="mt-12">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cyan-300">{goalName(params.goalId)}{dailyDate ? ` · ${displayDate(dailyDate)}` : ""}</p>
          <h1 className="mt-3 text-3xl font-bold sm:text-4xl">Today&apos;s Quests</h1>
          <p className="mt-2 text-slate-400">Turn your roadmap into a few focused actions.</p>
        </div>

        {profile && (
          <section className="mt-8 rounded-3xl border border-slate-800 bg-slate-900 p-6 sm:p-8">
            <div className="flex flex-wrap items-end justify-between gap-5">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">Progress</p>
                <p className="mt-2 text-3xl font-bold">Level {profile.level}</p>
                <p className="mt-1 text-slate-400">{profile.total_xp} XP · next level at {profile.xp_for_next_level} XP</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-orange-300">{profile.current_streak} day streak</p>
                <p className="mt-1 text-slate-400">Shield: {profile.streak_shields} · Rank: {profile.current_rank}</p>
              </div>
            </div>
            <div className="mt-5 h-2 rounded-full bg-slate-800"><div className="h-2 rounded-full bg-cyan-300" style={{ width: `${Math.min(100, (profile.xp_progress / Math.max(1, profile.xp_for_next_level - (profile.level === 1 ? 0 : 50 * profile.level ** 2))) * 100)}%` }} /></div>
            <div className="mt-4 flex flex-wrap gap-3 text-sm text-slate-400">
              <span>XP buff: +{profile.active_xp_multiplier - 100}%</span>
              <span>{profile.active_buff}</span>
              {profile.eligible_rank !== profile.current_rank && <span>Eligible for rank {profile.eligible_rank}, promotion pending.</span>}
            </div>
            <div className="mt-6 border-t border-slate-800 pt-5">
              <p className="font-semibold">Achievements</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {profile.achievements.filter((achievement) => !achievement.hidden).map((achievement) => <span key={achievement.achievement_id} className={`rounded-full border px-3 py-1 text-xs ${achievement.unlocked ? "border-emerald-300/50 text-emerald-300" : "border-slate-700 text-slate-500"}`}>{achievement.unlocked ? "✓" : "○"} {achievement.name}</span>)}
              </div>
            </div>
          </section>
        )}

        {isLoading ? (
          <div className="mt-10 rounded-3xl border border-slate-800 bg-slate-900 p-8 text-slate-300">Loading today&apos;s quests...</div>
        ) : quests.length === 0 ? (
          <div className="mt-10 rounded-3xl border border-slate-800 bg-slate-900 p-8 text-slate-300">No available quests are required right now.</div>
        ) : (
          <div className="mt-10 grid gap-6 lg:grid-cols-[1fr_1.1fr]">
            <div className="space-y-3">
              {quests.map((quest, index) => (
                <button key={quest.id} type="button" onClick={() => setSelected(quest)} className={`w-full rounded-2xl border p-5 text-left transition ${selected?.id === quest.id ? "border-cyan-300 bg-cyan-300/10" : "border-slate-800 bg-slate-900 hover:border-slate-600"}`}>
                  <div className="flex items-start gap-4">
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-800 text-sm font-semibold">{index + 1}</span>
                    <div className="min-w-0">
                      <h2 className="font-semibold">{quest.title}</h2>
                      <p className="mt-2 text-sm uppercase tracking-wide text-slate-400">{format(quest.quest_type)} · {quest.estimated_minutes} min</p>
                      <p className="mt-2 text-xs capitalize text-slate-500">{format(quest.status)}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            {selected && (
              <article className="rounded-3xl border border-slate-800 bg-slate-900 p-7">
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">{format(selected.quest_type)} quest</p>
                <h2 className="mt-3 text-2xl font-bold">{selected.title}</h2>
                <p className="mt-5 leading-7 text-slate-300">{selected.description}</p>
                <dl className="mt-7 grid grid-cols-2 gap-4 text-sm">
                  <div><dt className="text-slate-500">Skill</dt><dd className="mt-1 capitalize">{selected.roadmap_skill_id.replaceAll("_", " ")}</dd></div>
                  <div><dt className="text-slate-500">Difficulty</dt><dd className="mt-1 capitalize">{selected.difficulty}</dd></div>
                  <div><dt className="text-slate-500">Estimated time</dt><dd className="mt-1">{selected.estimated_minutes} minutes</dd></div>
                  <div><dt className="text-slate-500">Status</dt><dd className="mt-1 capitalize">{selected.status}</dd></div>
                </dl>
                {resources.length > 0 && (
                  <div className="mt-8 border-t border-slate-800 pt-6">
                    <h3 className="font-semibold">Resources</h3>
                    <div className="mt-3 space-y-2">
                      {resources.map((resource) => <a key={resource.id} href={resource.url} target="_blank" rel="noreferrer" className="block rounded-xl border border-slate-800 bg-slate-950 p-4 hover:border-cyan-300/60"><p className="font-medium">{resource.title}</p><p className="mt-1 text-xs text-slate-500">{resource.provider} · {resource.access_type} · {resource.estimated_time}h</p></a>)}
                    </div>
                  </div>
                )}
                <div className="mt-8">
                  {selected.status === "available" && <button type="button" onClick={() => updateQuest("start")} disabled={updatingQuest !== null} className="rounded-full bg-cyan-300 px-6 py-3 font-semibold text-slate-950 hover:bg-cyan-200 disabled:opacity-60">{updatingQuest === "start" ? "Starting..." : "Start Quest"}</button>}
                  {selected.status === "active" && <button type="button" onClick={() => updateQuest("complete")} disabled={updatingQuest !== null} className="rounded-full bg-emerald-300 px-6 py-3 font-semibold text-slate-950 hover:bg-emerald-200 disabled:opacity-60">{updatingQuest === "complete" ? "Completing..." : "Complete Quest"}</button>}
                  {selected.status === "completed" && <p className="font-semibold text-emerald-300">Quest completed</p>}
                </div>
              </article>
            )}
          </div>
        )}
      </section>
    </main>
  );
}
