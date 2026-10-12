"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { BossBattleAttempt, BossBattleResult, getBossBattle, submitBossBattle } from "../../../lib/api/bossBattles";

export default function BossBattlePage() {
  const params = useParams<{ attemptId: string }>();
  const searchParams = useSearchParams();
  const assessmentId = searchParams.get("assessment_id");
  const [attempt, setAttempt] = useState<BossBattleAttempt | null>(null);
  const [result, setResult] = useState<BossBattleResult | null>(null);
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!params.attemptId) return;
    getBossBattle(params.attemptId)
      .then(setAttempt)
      .catch((requestError: Error) => setError(requestError.message));
  }, [params.attemptId]);

  async function submit() {
    if (!attempt) return;
    const missing = attempt.questions.find((question) => !answers[question.id]);
    if (missing) {
      setError("Answer every Boss Battle question before submitting.");
      setCurrent(attempt.questions.findIndex((question) => question.id === missing.id));
      return;
    }
    setIsSubmitting(true);
    setError("");
    try {
      setResult(await submitBossBattle(attempt.attempt_id, attempt.questions.map((question) => ({ question_id: question.id, answer: answers[question.id] }))));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Boss Battle submission failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (error) return <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-center text-rose-300"><p>{error}</p></main>;
  if (result) return (
    <main className="min-h-screen bg-slate-950 px-6 py-12 text-slate-100">
      <section className="mx-auto max-w-3xl rounded-3xl border border-cyan-300/30 bg-slate-900 p-8 sm:p-12">
        <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cyan-300">Boss Battle result</p>
        <h1 className="mt-4 text-4xl font-bold">{result.passed ? "Battle passed" : "Battle failed"}</h1>
        <p className="mt-4 text-5xl font-bold text-cyan-300">{result.score}%</p>
        <p className="mt-2 text-slate-300">{result.questions_correct} / {result.questions_correct + result.questions_incorrect} correct</p>
        <dl className="mt-8 grid gap-4 sm:grid-cols-2">
          <div><dt className="text-slate-500">Mastery</dt><dd className="mt-1">{result.mastery_before}% → {result.mastery_after}%</dd></div>
          <div><dt className="text-slate-500">XP awarded</dt><dd className="mt-1">+{result.xp_awarded} XP</dd></div>
          <div><dt className="text-slate-500">Rank</dt><dd className="mt-1">{result.rank_before} → {result.rank_after}</dd></div>
          <div><dt className="text-slate-500">Next</dt><dd className="mt-1">{result.next_action}</dd></div>
        </dl>
        {result.weak_areas.length > 0 && <div className="mt-8 border-t border-slate-800 pt-6"><p className="font-semibold">Review these areas</p><ul className="mt-3 list-disc space-y-2 pl-5 text-slate-400">{result.weak_areas.map((area) => <li key={area}>{area}</li>)}</ul></div>}
        {assessmentId ? (
          <Link href={`/roadmap/${result.goal_id}?assessment_id=${encodeURIComponent(assessmentId)}`} className="mt-10 inline-flex rounded-full bg-cyan-300 px-6 py-3 font-semibold text-slate-950">Return to roadmap</Link>
        ) : (
          <div className="mt-10 border-t border-slate-800 pt-6">
            <p className="text-sm text-amber-300">Your assessment context is unavailable, so this result cannot reopen the roadmap.</p>
            <Link href="/" className="mt-4 inline-flex rounded-full border border-slate-700 px-5 py-3 font-semibold text-slate-300">Return home</Link>
          </div>
        )}
      </section>
    </main>
  );
  if (!attempt) return <main className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-300"><p>Loading Boss Battle...</p></main>;

  const question = attempt.questions[current];
  return (
    <main className="min-h-screen bg-slate-950 px-6 py-12 text-slate-100">
      <section className="mx-auto max-w-3xl">
        <p className="text-sm font-semibold uppercase tracking-[0.25em] text-rose-300">Boss Battle · {question.skill_id.replaceAll("_", " ")}</p>
        <div className="mt-4 flex items-end justify-between gap-4"><h1 className="text-3xl font-bold">Mastery validation</h1><p className="text-sm text-slate-400">Question {current + 1} of {attempt.questions.length}</p></div>
        <div className="mt-6 h-1 rounded-full bg-slate-800"><div className="h-1 rounded-full bg-rose-300" style={{ width: `${((current + 1) / attempt.questions.length) * 100}%` }} /></div>
        <div className="mt-10 rounded-3xl border border-rose-300/30 bg-slate-900 p-8 sm:p-12"><p className="text-sm capitalize text-slate-400">{question.question_type} · {question.difficulty}</p><h2 className="mt-5 whitespace-pre-wrap text-2xl font-semibold">{question.question}</h2><div className="mt-8 space-y-3">{question.options.map((option) => <button key={option} type="button" disabled={isSubmitting} onClick={() => { setAnswers((old) => ({ ...old, [question.id]: option })); setError(""); }} className={`w-full rounded-2xl border px-5 py-4 text-left disabled:opacity-60 ${answers[question.id] === option ? "border-rose-300 bg-rose-300/10" : "border-slate-700 bg-slate-950 hover:border-slate-500"}`}>{option}</button>)}</div>{error && <p role="alert" className="mt-6 text-rose-300">{error}</p>}<div className="mt-10 flex justify-between"><button type="button" disabled={current === 0 || isSubmitting} onClick={() => setCurrent((value) => value - 1)} className="rounded-full border border-slate-700 px-5 py-3 disabled:invisible">Back</button>{current === attempt.questions.length - 1 ? <button type="button" onClick={submit} disabled={isSubmitting} className="rounded-full bg-rose-300 px-6 py-3 font-semibold text-slate-950 disabled:opacity-60">{isSubmitting ? "Submitting..." : "Submit Boss Battle"}</button> : <button type="button" onClick={() => setCurrent((value) => value + 1)} disabled={isSubmitting} className="rounded-full bg-rose-300 px-6 py-3 font-semibold text-slate-950 disabled:opacity-60">Next</button>}</div></div>
      </section>
    </main>
  );
}
