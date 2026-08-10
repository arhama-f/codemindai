import { ImageResponse } from "next/og";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          justifyContent: "center",
          gap: 28,
          padding: 96,
          backgroundColor: "#0a0d12",
        }}
      >
        <svg width={72} height={72} viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="#6d6af1" />
          <line x1="10" y1="21" x2="16" y2="11" stroke="#f8f9fb" strokeOpacity="0.55" strokeWidth="1.4" />
          <line x1="16" y1="11" x2="22" y2="21" stroke="#f8f9fb" strokeOpacity="0.55" strokeWidth="1.4" />
          <line x1="10" y1="21" x2="22" y2="21" stroke="#f8f9fb" strokeOpacity="0.35" strokeWidth="1.4" />
          <circle cx="16" cy="11" r="2.6" fill="#f8f9fb" />
          <circle cx="10" cy="21" r="2.2" fill="#f8f9fb" fillOpacity="0.85" />
          <circle cx="22" cy="21" r="2.2" fill="#f8f9fb" fillOpacity="0.85" />
        </svg>
        <div style={{ display: "flex", fontSize: 56, fontWeight: 600, color: "#e8ecf1" }}>
          CodeMind AI
        </div>
        <div style={{ display: "flex", fontSize: 30, color: "#8a95a3", maxWidth: 820 }}>
          An AI staff engineer that actually reads your code
        </div>
      </div>
    ),
    { ...size },
  );
}
