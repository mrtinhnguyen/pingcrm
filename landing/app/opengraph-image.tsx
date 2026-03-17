import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "PingCRM — Personal Networking CRM";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          background: "linear-gradient(135deg, #070911 0%, #0d1117 50%, #070911 100%)",
          fontFamily: "monospace",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Grid background */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            backgroundImage:
              "linear-gradient(rgba(52,211,153,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(52,211,153,0.05) 1px, transparent 1px)",
            backgroundSize: "60px 60px",
            opacity: 0.6,
          }}
        />

        {/* Glow */}
        <div
          style={{
            position: "absolute",
            top: "-100px",
            left: "50%",
            transform: "translateX(-50%)",
            width: "800px",
            height: "500px",
            borderRadius: "50%",
            background: "radial-gradient(ellipse, rgba(52,211,153,0.12) 0%, transparent 70%)",
            display: "flex",
          }}
        />

        {/* Dot */}
        <div
          style={{
            width: "20px",
            height: "20px",
            borderRadius: "50%",
            background: "#34d399",
            boxShadow: "0 0 30px rgba(52,211,153,0.6), 0 0 60px rgba(52,211,153,0.3)",
            marginBottom: "32px",
            display: "flex",
          }}
        />

        {/* Title */}
        <div
          style={{
            fontSize: "72px",
            fontWeight: 700,
            color: "#e6edf3",
            letterSpacing: "-2px",
            display: "flex",
            alignItems: "center",
            gap: "0",
          }}
        >
          Ping
          <span style={{ color: "#34d399" }}>CRM</span>
        </div>

        {/* Subtitle */}
        <div
          style={{
            fontSize: "28px",
            color: "#8b949e",
            marginTop: "16px",
            display: "flex",
          }}
        >
          Personal Networking CRM
        </div>

        {/* Platform pills */}
        <div
          style={{
            display: "flex",
            gap: "12px",
            marginTop: "40px",
          }}
        >
          {["Gmail", "Telegram", "Twitter", "LinkedIn"].map((p) => (
            <div
              key={p}
              style={{
                padding: "8px 20px",
                borderRadius: "6px",
                fontSize: "16px",
                letterSpacing: "1px",
                background: "rgba(52,211,153,0.08)",
                border: "1px solid rgba(52,211,153,0.25)",
                color: "#34d399",
                display: "flex",
              }}
            >
              {p}
            </div>
          ))}
        </div>

        {/* Tagline */}
        <div
          style={{
            fontSize: "18px",
            color: "#6e7681",
            marginTop: "40px",
            display: "flex",
            gap: "8px",
          }}
        >
          AI-Powered &middot; Open Source &middot; Self-Hostable
        </div>
      </div>
    ),
    { ...size }
  );
}
