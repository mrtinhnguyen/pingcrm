import type { Metadata } from "next";
import { DM_Sans, Plus_Jakarta_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { QueryProvider } from "@/lib/query-provider";
import { ThemeProvider } from "@/components/theme-provider";
import { Nav } from "@/components/nav";
import { ErrorReporter } from "@/components/error-reporter";

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-body",
});

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-display",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
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
        className={`${dmSans.variable} ${jakarta.variable} ${jetbrainsMono.variable} font-body bg-stone-50 text-stone-900 dark:bg-stone-950 dark:text-stone-50`}
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
