"use client";

import { cn } from "@/lib/utils";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace("/api/v1", "") ??
  "http://localhost:8000";

interface ContactAvatarProps {
  avatarUrl: string | null | undefined;
  name: string;
  size?: "xs" | "sm" | "md" | "lg";
  className?: string;
}

const sizeClasses = {
  xs: "w-6 h-6 text-[10px]",
  sm: "w-8 h-8 text-xs",
  md: "w-10 h-10 text-sm",
  lg: "w-12 h-12 text-lg",
};

export function ContactAvatar({
  avatarUrl,
  name,
  size = "md",
  className,
}: ContactAvatarProps) {
  const words = (name || "?").trim().split(/\s+/);
  const initial = words.length >= 2
    ? (words[0][0] + words[words.length - 1][0]).toUpperCase()
    : (words[0]?.[0] || "?").toUpperCase();
  const classes = sizeClasses[size];

  if (avatarUrl) {
    return (
      <img
        src={`${API_BASE}${avatarUrl}`}
        alt={name}
        className={cn(
          classes,
          "rounded-full object-cover flex-shrink-0",
          className,
        )}
      />
    );
  }

  return (
    <div
      className={cn(
        classes,
        "rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-semibold flex-shrink-0",
        className,
      )}
    >
      {initial}
    </div>
  );
}
