import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RealCRM — Personal Networking CRM | AI-Powered",
  description:
    "RealCRM is a personal networking CRM that syncs Gmail, Telegram, Twitter, and LinkedIn. AI-powered follow-ups, relationship scoring, and weekly digests — open source and self-hostable.",
  openGraph: {
    title: "RealCRM — Personal Networking CRM | AI-Powered",
    description:
      "Personal networking CRM that syncs your conversations across Gmail, Telegram, Twitter, and LinkedIn. AI writes your follow-ups.",
    type: "website",
    url: "https://realcrm.vn",
    siteName: "RealCRM",
    images: [
      {
        url: "https://realcrm.vn/og.png",
        width: 1200,
        height: 630,
        alt: "RealCRM — Personal Networking CRM",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "RealCRM — Personal Networking CRM | AI-Powered",
    description:
      "Sync Gmail, Telegram, Twitter, and LinkedIn. AI-powered follow-ups and relationship scoring.",
    images: ["https://realcrm.vn/og.png"],
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
