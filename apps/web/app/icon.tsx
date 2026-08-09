import { ImageResponse } from "next/og";

export const size = { width: 32, height: 32 };
export const contentType = "image/png";

export default function Icon() {
  return new ImageResponse(
    (
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="32" height="32" rx="8" fill="#6d6af1" />
        <line x1="10" y1="21" x2="16" y2="11" stroke="#f8f9fb" strokeOpacity="0.55" strokeWidth="1.4" />
        <line x1="16" y1="11" x2="22" y2="21" stroke="#f8f9fb" strokeOpacity="0.55" strokeWidth="1.4" />
        <line x1="10" y1="21" x2="22" y2="21" stroke="#f8f9fb" strokeOpacity="0.35" strokeWidth="1.4" />
        <circle cx="16" cy="11" r="2.6" fill="#f8f9fb" />
        <circle cx="10" cy="21" r="2.2" fill="#f8f9fb" fillOpacity="0.85" />
        <circle cx="22" cy="21" r="2.2" fill="#f8f9fb" fillOpacity="0.85" />
      </svg>
    ),
    { ...size }
  );
}
