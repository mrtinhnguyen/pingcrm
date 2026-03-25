'use client'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html>
      <body>
        <div className="min-h-screen flex items-center justify-center bg-white dark:bg-stone-950">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-4 text-stone-900 dark:text-stone-100">Đã xảy ra lỗi!</h2>
            <button
              onClick={() => reset()}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Thử lại
            </button>
          </div>
        </div>
      </body>
    </html>
  )
}
