"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { discoverGoal, GoalDiscoveryData, GoalProfile } from "../../lib/api/goals";

const assessmentTracks = [
  ["learn_python", "Learn Python"],
  ["learn_cpp", "Learn C++"],
  ["learn_web_development", "Learn Web Development"],
  ["learn_data_structures_algorithms", "Learn Data Structures & Algorithms"],
  ["learn_machine_learning", "Learn Machine Learning"],
] as const;

const initialForm: GoalDiscoveryData = {
  goal: "",
  objective: "",
  experience_level: "",
  weekly_hours: "",
  timeline: "",
  learning_style: "",
  difficulty: "",
  resource_preference: "",
  motivation: "",
  prior_knowledge: "",
};

const options = {
  objective: [
    ["job", "Job"],
    ["college", "College"],
    ["projects", "Projects"],
    ["freelancing", "Freelancing"],
    ["personal_interest", "Personal Interest"],
    ["other", "Other"],
  ],
  experience_level: [
    ["complete_beginner", "Complete Beginner"],
    ["beginner", "Beginner"],
    ["intermediate", "Intermediate"],
    ["advanced", "Advanced"],
  ],
  weekly_hours: [
    ["less_than_5", "Less than 5 hours"],
    ["5_to_10", "5–10 hours"],
    ["10_to_20", "10–20 hours"],
    ["20_plus", "20+ hours"],
  ],
  timeline: [
    ["1_month", "1 month"],
    ["3_months", "3 months"],
    ["6_months", "6 months"],
    ["1_year_plus", "1 year+"],
    ["no_fixed_deadline", "No fixed deadline"],
  ],
  learning_style: [
    ["videos", "Videos"],
    ["reading", "Reading"],
    ["projects", "Projects"],
    ["practice", "Practice"],
    ["mixed", "Mixed"],
  ],
  difficulty: [
    ["casual", "Casual"],
    ["standard", "Standard"],
    ["hunter", "Hunter"],
    ["monarch", "Monarch"],
  ],
  resource_preference: [
    ["free_only", "Free resources only"],
    ["free_and_paid", "Free + paid resources"],
  ],
} as const;

const labels: Record<keyof GoalDiscoveryData, string> = {
  goal: "Goal",
  objective: "Primary objective",
  experience_level: "Current experience",
  weekly_hours: "Weekly time commitment",
  timeline: "Target timeline",
  learning_style: "Learning style",
  difficulty: "Preferred difficulty",
  resource_preference: "Resource preference",
  motivation: "Motivation",
  prior_knowledge: "Prior knowledge",
};

function displayValue(value: string | number) {
  return String(value).replaceAll("_", " ");
}

export default function GoalSetup() {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState(initialForm);
  const [profile, setProfile] = useState<GoalProfile | null>(null);
  const [assessmentGoal, setAssessmentGoal] = useState("learn_python");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function updateField(field: keyof GoalDiscoveryData, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
    setError("");
  }

  function validateCurrentStep() {
    const fields = step === 1 ? ["goal"] : Object.keys(initialForm).filter((field) => field !== "goal");
    const missing = fields.find((field) => !form[field as keyof GoalDiscoveryData].trim());

    if (missing) {
      setError(`Please complete ${labels[missing as keyof GoalDiscoveryData].toLowerCase()}.`);
      return false;
    }

    return true;
  }

  function goNext() {
    if (validateCurrentStep()) setStep((current) => current + 1);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!validateCurrentStep()) return;

    setIsSubmitting(true);
    setError("");
    try {
      setProfile(await discoverGoal(form));
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : "Something went wrong.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (profile) {
    return (
      <main className="min-h-screen bg-slate-950 px-6 py-12 text-slate-100">
        <section className="mx-auto max-w-3xl">
          <Link href="/" className="text-sm font-semibold text-cyan-300 hover:text-cyan-200">GoalForge AI</Link>
          <div className="mt-12 rounded-3xl border border-slate-800 bg-slate-900 p-8 shadow-2xl sm:p-12">
            <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cyan-300">Your goal profile</p>
            <h1 className="mt-4 text-3xl font-bold sm:text-4xl">{profile.goal}</h1>
            <dl className="mt-8 grid gap-5 sm:grid-cols-2">
              {Object.entries(profile).map(([field, value]) => (
                <div key={field} className="border-t border-slate-800 pt-4">
                  <dt className="text-sm text-slate-400">{labels[field as keyof GoalDiscoveryData]}</dt>
                  <dd className="mt-1 capitalize text-slate-100">{displayValue(value)}</dd>
                </div>
              ))}
            </dl>
            <div className="mt-10 border-t border-slate-800 pt-8">
              <label className="text-sm font-medium text-slate-300">
                Choose an assessment track
                <select
                  value={assessmentGoal}
                  onChange={(event) => setAssessmentGoal(event.target.value)}
                  className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 outline-none focus:ring-2 focus:ring-cyan-300"
                >
                  {assessmentTracks.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
              </label>
              <Link
                href={`/assessment/${assessmentGoal}?experience_level=${encodeURIComponent(profile.experience_level)}&learning_style=${encodeURIComponent(profile.learning_style)}&resource_preference=${encodeURIComponent(profile.resource_preference)}&difficulty=${encodeURIComponent(profile.difficulty)}`}
                className="mt-6 inline-flex rounded-full bg-cyan-300 px-6 py-3 font-semibold text-slate-950 transition hover:bg-cyan-200"
              >
                Start Assessment
              </Link>
            </div>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-12 text-slate-100">
      <section className="mx-auto max-w-3xl">
        <Link href="/" className="text-sm font-semibold text-cyan-300 hover:text-cyan-200">GoalForge AI</Link>
        <div className="mt-12 flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cyan-300">Goal setup</p>
            <h1 className="mt-3 text-3xl font-bold sm:text-4xl">Shape your learning path.</h1>
          </div>
          <p className="shrink-0 text-sm font-medium text-slate-400">Step {step} of 3</p>
        </div>
        <div className="mt-6 h-1 rounded-full bg-slate-800">
          <div className="h-1 rounded-full bg-cyan-300 transition-all" style={{ width: `${(step / 3) * 100}%` }} />
        </div>

        <form onSubmit={handleSubmit} className="mt-10 rounded-3xl border border-slate-800 bg-slate-900 p-8 sm:p-12">
          {step === 1 && (
            <div>
              <h2 className="text-2xl font-semibold">What do you want to achieve?</h2>
              <p className="mt-2 text-slate-400">Describe the programming goal you want to work toward.</p>
              <textarea
                value={form.goal}
                onChange={(event) => updateField("goal", event.target.value)}
                placeholder="Become a Machine Learning Engineer"
                rows={4}
                className="mt-8 w-full resize-none rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 outline-none ring-cyan-300 placeholder:text-slate-600 focus:ring-2"
              />
            </div>
          )}

          {step === 2 && (
            <div>
              <h2 className="text-2xl font-semibold">Tell us how you learn best.</h2>
              <p className="mt-2 text-slate-400">These answers help us understand the shape of your goal.</p>
              <div className="mt-8 grid gap-6 sm:grid-cols-2">
                {(Object.keys(options) as Array<keyof typeof options>).map((field) => (
                  <label key={field} className="text-sm font-medium text-slate-300">
                    {labels[field]}
                    <select
                      value={form[field]}
                      onChange={(event) => updateField(field, event.target.value)}
                      className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 outline-none focus:ring-2 focus:ring-cyan-300"
                    >
                      <option value="">Select an option</option>
                      {options[field].map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                    </select>
                  </label>
                ))}
                <label className="text-sm font-medium text-slate-300">
                  Motivation
                  <textarea value={form.motivation} onChange={(event) => updateField("motivation", event.target.value)} rows={4} placeholder="Why do you want to achieve this goal?" className="mt-2 w-full resize-none rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 outline-none focus:ring-2 focus:ring-cyan-300" />
                </label>
                <label className="text-sm font-medium text-slate-300">
                  Prior knowledge
                  <textarea value={form.prior_knowledge} onChange={(event) => updateField("prior_knowledge", event.target.value)} rows={4} placeholder="What do you already know that may be relevant to this goal?" className="mt-2 w-full resize-none rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 outline-none focus:ring-2 focus:ring-cyan-300" />
                </label>
              </div>
            </div>
          )}

          {step === 3 && (
            <div>
              <h2 className="text-2xl font-semibold">Ready to forge your profile?</h2>
              <p className="mt-2 text-slate-400">Review your answers before creating your learning profile.</p>
              <dl className="mt-8 space-y-5">
                {Object.entries(form).map(([field, value]) => (
                  <div key={field} className="border-t border-slate-800 pt-4">
                    <dt className="text-sm text-slate-400">{labels[field as keyof GoalDiscoveryData]}</dt>
                    <dd className="mt-1 whitespace-pre-wrap text-slate-100">{value}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          {error && <p role="alert" className="mt-6 text-sm font-medium text-rose-300">{error}</p>}
          <div className="mt-10 flex flex-wrap justify-between gap-4">
            <button type="button" onClick={() => { setError(""); setStep((current) => Math.max(1, current - 1)); }} disabled={step === 1} className="rounded-full border border-slate-700 px-5 py-3 font-semibold text-slate-300 transition hover:border-slate-500 disabled:invisible">Back</button>
            {step < 3 ? (
              <button type="button" onClick={goNext} className="rounded-full bg-cyan-300 px-6 py-3 font-semibold text-slate-950 transition hover:bg-cyan-200">Next</button>
            ) : (
              <button type="submit" disabled={isSubmitting} className="rounded-full bg-cyan-300 px-6 py-3 font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-wait disabled:opacity-60">{isSubmitting ? "Creating profile..." : "Create My Learning Profile"}</button>
            )}
          </div>
        </form>
      </section>
    </main>
  );
}