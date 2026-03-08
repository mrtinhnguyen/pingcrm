import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-stone-50 px-4">
      <div className="text-center max-w-2xl">
        <div className="flex items-center justify-center gap-3 mb-4">
          <span className="w-4 h-4 rounded-full bg-teal-500" />
          <h1 className="text-5xl font-display font-bold text-stone-900">Ping CRM</h1>
        </div>
        <p className="text-xl text-stone-600 mb-10">
          Your AI-powered networking assistant
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/contacts"
            className="inline-flex items-center px-6 py-3 rounded-lg bg-teal-600 text-white font-medium hover:bg-teal-700 transition-colors btn-press"
          >
            View Contacts
          </Link>
          <Link
            href="/dashboard"
            className="inline-flex items-center px-6 py-3 rounded-lg bg-white text-stone-800 font-medium border border-stone-300 hover:bg-stone-100 transition-colors btn-press"
          >
            Dashboard
          </Link>
        </div>
      </div>
    </main>
  );
}
