import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-stone-50 dark:bg-stone-950 px-4">
      <div className="text-center max-w-2xl">
        <div className="flex items-center justify-center gap-3 mb-4">
          <span className="w-4 h-4 rounded-full bg-teal-500" />
          <h1 className="text-5xl font-display font-bold text-stone-900 dark:text-stone-100">RealCRM</h1>
        </div>
        <p className="text-xl text-stone-600 dark:text-stone-300 mb-10">
          Trợ lý kết nối mạng lưới được hỗ trợ bởi AI
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/contacts"
            className="inline-flex items-center px-6 py-3 rounded-lg bg-teal-600 text-white font-medium hover:bg-teal-700 transition-colors btn-press"
          >
            Xem Danh bạ
          </Link>
          <Link
            href="/dashboard"
            className="inline-flex items-center px-6 py-3 rounded-lg bg-white dark:bg-stone-900 text-stone-800 dark:text-stone-100 font-medium border border-stone-300 dark:border-stone-700 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors btn-press"
          >
            Bảng điều khiển
          </Link>
        </div>
      </div>
    </main>
  );
}
