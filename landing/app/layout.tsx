import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PingCRM — Personal Networking CRM | AI-Powered, Open Source & Self-Hostable",
  description:
    "PingCRM is a personal networking CRM that syncs Gmail, Telegram, Twitter, and LinkedIn. AI-powered follow-ups, relationship scoring, and weekly digests — open source and self-hostable.",
  openGraph: {
    title: "PingCRM — Personal Networking CRM | AI-Powered & Open Source",
    description:
      "Personal networking CRM that syncs your conversations across Gmail, Telegram, Twitter, and LinkedIn. AI writes your follow-ups. Open source, self-hostable.",
    type: "website",
    url: "https://pingcrm.xyz",
    siteName: "PingCRM",
  },
  twitter: {
    card: "summary_large_image",
    title: "PingCRM — Personal Networking CRM | AI-Powered & Open Source",
    description:
      "Sync Gmail, Telegram, Twitter, and LinkedIn. AI-powered follow-ups and relationship scoring. Open source, self-hostable.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="antialiased min-h-screen">{children}</body>
    </html>
  );
}
