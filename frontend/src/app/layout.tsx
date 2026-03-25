import type { Metadata } from "next";
import { Inter, Be_Vietnam_Pro, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { QueryProvider } from "@/lib/query-provider";
import { ThemeProvider } from "@/components/theme-provider";
import { Nav } from "@/components/nav";
import { ErrorReporter } from "@/components/error-reporter";

// Inter - Font hiện đại, hỗ trợ tiếng Việt tốt
const inter = Inter({
  subsets: ["latin", "vietnamese"],
  variable: "--font-body",
  display: "swap",
});

// Be Vietnam Pro - Font chuyên dụng cho tiếng Việt
const beVietnamPro = Be_Vietnam_Pro({
  subsets: ["latin", "vietnamese"],
  variable: "--font-display",
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "RealCRM - Quản lý Quan hệ Doanh nghiệp",
  description: "Trợ lý kết nối mạng lưới được hỗ trợ bởi AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem("pingcrm-theme");var d=t==="dark"||(t!=="light"&&matchMedia("(prefers-color-scheme:dark)").matches);if(d)document.documentElement.classList.add("dark")}catch(e){}})()`,
          }}
        />
      </head>
      <body
        className={`${inter.variable} ${beVietnamPro.variable} ${jetbrainsMono.variable} font-body bg-stone-50 text-stone-900 dark:bg-stone-950 dark:text-stone-50`}
        suppressHydrationWarning
      >
        <ThemeProvider>
          <QueryProvider>
            <ErrorReporter />
            <Nav />
            {children}
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
