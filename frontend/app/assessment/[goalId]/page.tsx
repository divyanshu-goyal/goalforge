"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import {
  Assessment,
  AssessmentResult,
  createAssessment,
  submitAssessment,
} from "../../../lib/api/assessments";

function label(value: string) {
  return value.replaceAll("_", " ");
}

function classification(score: number) {
  if (score < 60) return "Weak";
  if (score < 85) return "Developing";
  return "Strong";
}

export default function AssessmentPage() {
  const params = useParams<{ goalId: string }>();
  const searchParams = useSearchParams();
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!params.goalId) return;
    setIsLoading(true);
    setAssessment(null);
    setResult(null);
    setAnswers({});
    setCurrent(0);
    setError("");
    createAssessment(params.goalId, {
      experience_level: searchParams.get("experience_level") ?? undefined,
      learning_style: searchParams.get("learning_style") ?? undefined,
      resource_preference: searchParams.get("resource_preference") ?? undefined,
      difficulty: searchParams.get("difficulty") ?? undefined,
    })
      .then(setAssessment)
      .catch((requestError: Error) => setError(requestError.message))
      .finally(() => setIsLoading(false));
  }, [params.goalId, searchParams]);

  function chooseAnswer(answer: string) {
    if (!assessment) return;
    setAnswers((existing) => ({ ...existing, [assessment.questions[current].id]: answer }));
    setError("");
  }

  async function finishAssessment() {
    if (!assessment) return;
    const unanswered = assessment.questions.find((question) => !answers[question.id]);
    if (unanswered) {
      setError("Please answer every question before submitting.");
      setCurrent(assessment.questions.findIndex((question) => question.id === unanswered.id));
      return;
    }

    setIsSubmitting(true);
    setError("");
    try {
      setResult(await submitAssessment(
        assessment.assessment_id,
        assessment.questions.map((question) => ({ question_id: question.id, answer: answers[question.id] })),
      ));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The assessment could not be submitted.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (result) {
    return (
      <main className="min-h-screen bg-slate-950 px-6 py-12 text-slate-100">
        <section className="mx-auto max-w-3xl">
          <Link href="/" className="text-sm font-semibold text-cyan-300 hover:text-cyan-200">GoalForge AI</Link>
          <div className="mt-12 rounded-3xl border border-slate-800 bg-slate-900 p-8 shadow-2xl sm:p-12">
            <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cyan-300">Assessment complete</p>
            <h1 className="mt-4 text-3xl font-bold sm:text-4xl">Your skill results</h1>
            <div className="mt-8 rounded-2xl bg-slate-950 p-6">
              <p className="text-sm text-slate-400">Overall score</p>
              <p className="mt-2 text-4xl font-bold text-cyan-300">{result.overall_score}%</p>
              <p className="mt-1 text-slate-300">{result.total_correct} of {result.total_questions} correct · {classification(result.overall_score)}</p>
            </div>
            <div className="mt-8 space-y-5">
              {result.skill_results.map((skill) => (
                <div key={skill.skill_id}>
                  <div className="flex items-center justify-between gap-4 text-sm">
                    <span className="font-semibold capitalize">{label(skill.skill_id)}</span>
                    <span className="text-slate-400">{skill.score}% · {skill.classification}</span>
                  </div>
                  <div className="mt-2 h-2 rounded-full bg-slate-800">
                    <div className="h-2 rounded-full bg-cyan-300" style={{ width: `${skill.score}%` }} />
                  </div>
                  <p className="mt-2 text-xs text-slate-500">{skill.correct} of {skill.questions_attempted} correct</p>
                </div>
              ))}
            </div>
            <Link href={`/roadmap/${params.goalId}?assessment_id=${result.assessment_id}`} className="mt-10 inline-flex rounded-full bg-cyan-300 px-6 py-3 font-semibold text-slate-950 hover:bg-cyan-200">Build My Roadmap</Link>
            <Link href="/" className="mt-10 inline-flex rounded-full border border-slate-700 px-5 py-3 font-semibold text-slate-300 hover:border-slate-500">Return home</Link>
          </div>
        </section>
      </main>
    );
  }

  if (error && !assessment) {
    return <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-center text-rose-300"><p>{error}</p></main>;
  }

  if (isLoading || !assessment) {
    return <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-slate-300"><p>Loading assessment...</p></main>;
  }

  const question = assessment.questions[current];
  const isLastQuestion = current === assessment.questions.length - 1;

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-12 text-slate-100">
      <section className="mx-auto max-w-3xl">
        <Link href="/" className="text-sm font-semibold text-cyan-300 hover:text-cyan-200">GoalForge AI</Link>
        <div className="mt-12 flex items-end justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cyan-300">Skill assessment</p>
            <h1 className="mt-3 text-3xl font-bold sm:text-4xl">Show what you know.</h1>
          </div>
          <p className="shrink-0 text-sm text-slate-400">Question {current + 1} of {assessment.questions.length}</p>
        </div>
        <div className="mt-6 h-1 rounded-full bg-slate-800"><div className="h-1 rounded-full bg-cyan-300 transition-all" style={{ width: `${((current + 1) / assessment.questions.length) * 100}%` }} /></div>
        <div className="mt-10 rounded-3xl border border-slate-800 bg-slate-900 p-8 sm:p-12">
          <p className="text-sm capitalize text-slate-400">{label(question.skill_id)} · {question.difficulty}</p>
          <h2 className="mt-5 text-2xl font-semibold leading-tight">{question.question}</h2>
          <div className="mt-8 space-y-3">
            {question.options.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => chooseAnswer(option)}
                className={`w-full rounded-2xl border px-5 py-4 text-left transition ${answers[question.id] === option ? "border-cyan-300 bg-cyan-300/10 text-cyan-100" : "border-slate-700 bg-slate-950 text-slate-300 hover:border-slate-500"}`}
              >
                {option}
              </button>
            ))}
          </div>
          {error && <p role="alert" className="mt-6 text-sm font-medium text-rose-300">{error}</p>}
          <div className="mt-10 flex justify-between gap-4">
            <button type="button" onClick={() => { setError(""); setCurrent((value) => Math.max(0, value - 1)); }} disabled={current === 0} className="rounded-full border border-slate-700 px-5 py-3 font-semibold text-slate-300 hover:border-slate-500 disabled:invisible">Back</button>
            {isLastQuestion ? (
              <button type="button" onClick={finishAssessment} disabled={isSubmitting} className="rounded-full bg-cyan-300 px-6 py-3 font-semibold text-slate-950 hover:bg-cyan-200 disabled:opacity-60">{isSubmitting ? "Submitting..." : "Submit Assessment"}</button>
            ) : (
              <button type="button" onClick={() => setCurrent((value) => value + 1)} className="rounded-full bg-cyan-300 px-6 py-3 font-semibold text-slate-950 hover:bg-cyan-200">Next</button>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
