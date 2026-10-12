"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { analyzePersonalization, PersonalizationResult } from "../../../lib/api/personalization";
import { startBossBattle } from "../../../lib/api/bossBattles";

function formatClassification(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function goalName(goalId: string) {
  const names: Record<string, string> = {
    learn_python: "Learn Python",
    learn_cpp: "Learn C++",
    learn_web_development: "Learn Web Development",
    learn_data_structures_algorithms: "Learn Data Structures & Algorithms",
    learn_machine_learning: "Learn Machine Learning",
  };
  return names[goalId] ?? formatClassification(goalId.replace("learn_", ""));
}

export default function RoadmapPage() {
  const params = useParams<{ goalId: string }>();
  const searchParams = useSearchParams();
  const assessmentId = searchParams.get("assessment_id");
  const [result, setResult] = useState<PersonalizationResult | null>(null);
  const [error, setError] = useState("");
  const [startingSkill, setStartingSkill] = useState<string | null>(null);

  async function startBattle(skillId: string) {
    setStartingSkill(skillId);
    try {
      const attempt = await startBossBattle(result?.goal_id ?? params.goalId, skillId);
      window.location.href = `/boss-battle/${attempt.attempt_id}?assessment_id=${encodeURIComponent(assessmentId ?? "")}`;
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Boss Battle could not be started.");
    } finally {
      setStartingSkill(null);
    }
  }

  useEffect(() => {
    if (!params.goalId || !assessmentId) {
      setError("A completed assessment is required to build this roadmap.");
      return;
    }
    analyzePersonalization(params.goalId, assessmentId)
      .then(setResult)
      .catch((requestError: Error) => setError(requestError.message));
  }, [assessmentId, params.goalId]);

  if (error) {
    return <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-center text-rose-300"><p>{error}</p></main>;
  }

  if (!result) {
    return <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-slate-300"><p>Building your personalized roadmap...</p></main>;
  }

  const summaryItems = [
    ["Skip", result.summary.skills_to_skip, "text-emerald-300"],
    ["Review", result.summary.skills_to_review, "text-amber-300"],
    ["Learn", result.summary.skills_to_learn, "text-cyan-300"],
    ["Locked", result.summary.skills_locked, "text-rose-300"],
  ];

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-12 text-slate-100">
      <section className="mx-auto max-w-4xl">
        <Link href="/" className="text-sm font-semibold text-cyan-300 hover:text-cyan-200">GoalForge AI</Link>
        <div className="mt-12">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cyan-300">Your goal</p>
          <p className="mt-3 text-xl font-semibold text-slate-200">{goalName(result.goal_id)}</p>
          <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Your personalized learning roadmap</h1>
          <Link href={`/quests/${result.goal_id}?assessment_id=${result.assessment_id}`} className="mt-6 inline-flex rounded-full bg-cyan-300 px-6 py-3 font-semibold text-slate-950 hover:bg-cyan-200">View Today&apos;s Quests</Link>
        </div>
        <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {summaryItems.map(([name, count, color]) => (
            <div key={name} className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
              <p className={`text-3xl font-bold ${color}`}>{count}</p>
              <p className="mt-1 text-sm text-slate-400">{name === "Locked" ? "Locked skills" : `Skills to ${String(name).toLowerCase()}`}</p>
            </div>
          ))}
        </div>
        <div className="mt-10 rounded-3xl border border-slate-800 bg-slate-900 p-8 sm:p-10">
          <h2 className="text-2xl font-semibold">Personalized Roadmap</h2>
          <p className="mt-2 text-slate-400">Ordered around your current mastery and prerequisite dependencies.</p>
          <div className="mt-8 space-y-4">
            {result.roadmap.map((node) => (
              <article key={node.skill_id} className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
                <div className="flex items-start gap-4">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-800 text-sm font-semibold text-slate-300">{node.order}</span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h3 className="font-semibold">{node.skill_name}</h3>
                      <span className="text-sm font-semibold uppercase tracking-wide text-slate-400">{formatClassification(node.classification)} · {formatClassification(node.status)}</span>
                    </div>
                    <p className="mt-2 text-sm text-slate-300">{node.mastery === null ? "Mastery: unknown" : `Mastery: ${node.mastery}%`}</p>
                    <p className="mt-2 text-sm leading-6 text-slate-400">{node.reason}</p>
                    <div className="mt-4 flex items-center gap-3 text-sm">
                      <span className="text-slate-500">Boss Battle: {formatClassification(node.boss_battle_status)}</span>
                      {node.boss_battle_status === "available" && <button type="button" onClick={() => startBattle(node.skill_id)} disabled={startingSkill === node.skill_id} className="rounded-full border border-rose-300/60 px-3 py-1 font-semibold text-rose-300 hover:bg-rose-300/10">{startingSkill === node.skill_id ? "Starting..." : "Start Battle"}</button>}
                    </div>
                    {node.resources.length > 0 && (
                      <div className="mt-5 border-t border-slate-800 pt-4">
                        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Recommended resources</p>
                        <div className="mt-3 grid gap-3 sm:grid-cols-2">
                          {node.resources.map((resource) => (
                            <a
                              key={resource.id}
                              href={resource.url}
                              target="_blank"
                              rel="noreferrer"
                              className="rounded-xl border border-slate-800 bg-slate-900 p-4 transition hover:border-cyan-300/60"
                            >
                              <p className="font-semibold text-slate-100">{resource.title}</p>
                              <p className="mt-2 text-xs capitalize text-slate-400">{resource.resource_type} · {resource.difficulty} · {resource.estimated_time}h</p>
                              <p className="mt-1 text-xs text-slate-500">{resource.provider} · {resource.access_type}</p>
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}