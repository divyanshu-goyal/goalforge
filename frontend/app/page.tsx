import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 py-16 text-slate-100">
      <section className="w-full max-w-2xl text-center">
        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.3em] text-cyan-300">
          GoalForge AI
        </p>
        <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
          Turn your programming goal into a path forward.
        </h1>
        <p className="mx-auto mt-6 max-w-xl text-lg leading-8 text-slate-300">
          A personalized learning platform that helps you discover what to learn next and keep making progress.
        </p>
        <Link
          href="/goal-setup"
          className="mt-10 rounded-full bg-cyan-300 px-6 py-3 font-semibold text-slate-950 transition hover:bg-cyan-200"
        >
          Start Learning
        </Link>
      </section>
    </main>
  );
}
