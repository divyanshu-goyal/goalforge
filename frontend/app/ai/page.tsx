"use client";

import { useState } from "react";

import { askMentor, getAIInsights } from "../../lib/api/ai";

export default function AIPage() {
  const [goalId, setGoalId] = useState("learn_python");
  const [assessmentId, setAssessmentId] = useState("");
  const [insight, setInsight] = useState<string>("");
  const [mentorReply, setMentorReply] = useState<string>("");
  const [error, setError] = useState("");
  const [isLoadingInsights, setIsLoadingInsights] = useState(false);
  const [isLoadingMentor, setIsLoadingMentor] = useState(false);

  async function fetchInsights() {
    if (!goalId.trim() || !assessmentId.trim()) {
      setError("Enter a goal ID and a submitted assessment ID before requesting insights.");
      return;
    }
    setError("");
    setIsLoadingInsights(true);
    try {
      const result = await getAIInsights(goalId, assessmentId);
      setInsight(result.summary || "AI insights unavailable. Using deterministic recommendations.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "AI insights could not be loaded.");
    } finally {
      setIsLoadingInsights(false);
    }
  }

  async function fetchMentorReply() {
    if (!goalId.trim()) {
      setError("Enter a goal ID before asking the mentor.");
      return;
    }
    setError("");
    setIsLoadingMentor(true);
    try {
      const result = await askMentor(goalId, "Why am I stuck on my current skill?");
      setMentorReply(result.message);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The mentor could not respond.");
    } finally {
      setIsLoadingMentor(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-12 text-slate-100">
      <section className="mx-auto max-w-3xl rounded-3xl border border-slate-800 bg-slate-900 p-8">
        <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cyan-300">GoalForge AI</p>
        <h1 className="mt-4 text-3xl font-bold">AI mentor + personalization</h1>
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <input aria-label="Goal ID" value={goalId} onChange={(event) => setGoalId(event.target.value)} className="rounded-xl border border-slate-700 bg-slate-950 px-4 py-3" placeholder="learn_python" />
          <input aria-label="Assessment ID" value={assessmentId} onChange={(event) => setAssessmentId(event.target.value)} className="rounded-xl border border-slate-700 bg-slate-950 px-4 py-3" placeholder="assessment_id" />
        </div>
        <div className="mt-6 flex gap-3">
          <button type="button" onClick={fetchInsights} disabled={isLoadingInsights || isLoadingMentor} className="rounded-full bg-cyan-300 px-6 py-3 font-semibold text-slate-950 disabled:opacity-60">{isLoadingInsights ? "Loading insights..." : "Get Insights"}</button>
          <button type="button" onClick={fetchMentorReply} disabled={isLoadingInsights || isLoadingMentor} className="rounded-full border border-cyan-300/60 px-6 py-3 font-semibold text-cyan-300 disabled:opacity-60">{isLoadingMentor ? "Asking mentor..." : "Ask Mentor"}</button>
        </div>
        {error && <p className="mt-6 text-rose-300">{error}</p>}
        {insight && <div className="mt-8 rounded-2xl border border-slate-700 bg-slate-950 p-5"><p className="text-sm uppercase tracking-[0.2em] text-cyan-300">AI Insights</p><p className="mt-3 text-slate-200">{insight}</p></div>}
        {mentorReply && <div className="mt-8 rounded-2xl border border-cyan-300/30 bg-cyan-300/5 p-5"><p className="text-sm uppercase tracking-[0.2em] text-cyan-300">Mentor</p><p className="mt-3 text-slate-200">{mentorReply}</p></div>}
      </section>
    </main>
  );
}
