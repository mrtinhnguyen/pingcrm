"use client";

import { formatDistanceToNow } from "date-fns";
import { Mail, MessageCircle, Twitter, FileText, Plus, Calendar, Linkedin } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const URL_RE = /(https?:\/\/[^\s<]+)/g;

function Linkify({ text, className }: { text: string; className?: string }) {
  const parts = text.split(URL_RE);
  return (
    <span>
      {parts.map((part, i) =>
        URL_RE.test(part) ? (
          <a
            key={i}
            href={part}
            target="_blank"
            rel="noopener noreferrer"
            className={cn("underline break-all", className)}
          >
            {part}
          </a>
        ) : (
          part
        )
      )}
    </span>
  );
}

export interface TimelineEntry {
  id: string;
  platform: "email" | "telegram" | "twitter" | "linkedin" | "manual" | "meeting";
  direction: "inbound" | "outbound" | "mutual";
  content_preview: string | null;
  occurred_at: string;
}

interface TimelineProps {
  interactions: TimelineEntry[];
  onAddNote?: (content: string) => void;
  contactName?: string;
  className?: string;
}

const platformIcons: Record<TimelineEntry["platform"], React.ReactNode> = {
  email: <Mail className="w-3.5 h-3.5" />,
  telegram: <MessageCircle className="w-3.5 h-3.5" />,
  twitter: <Twitter className="w-3.5 h-3.5" />,
  linkedin: <Linkedin className="w-3.5 h-3.5" />,
  manual: <FileText className="w-3.5 h-3.5" />,
  meeting: <Calendar className="w-3.5 h-3.5" />,
};

export function Timeline({ interactions, onAddNote, contactName, className }: TimelineProps) {
  const [noteText, setNoteText] = useState("");
  const [showNoteInput, setShowNoteInput] = useState(false);

  const handleSubmitNote = () => {
    if (!noteText.trim()) return;
    onAddNote?.(noteText.trim());
    setNoteText("");
    setShowNoteInput(false);
  };

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Interactions</h2>
        <button
          onClick={() => setShowNoteInput((v) => !v)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md bg-blue-600 text-white hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add note
        </button>
      </div>

      {showNoteInput && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 space-y-2">
          <textarea
            className="w-full text-sm border border-gray-300 rounded-md p-2 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
            rows={3}
            placeholder="Write a note..."
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
          />
          <div className="flex gap-2 justify-end">
            <button
              onClick={() => setShowNoteInput(false)}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmitNote}
              className="text-sm px-3 py-1 rounded-md bg-blue-600 text-white hover:bg-blue-700"
            >
              Save
            </button>
          </div>
        </div>
      )}

      {interactions.length === 0 ? (
        <p className="text-sm text-gray-400 py-6 text-center">
          No interactions yet. Add a note to get started.
        </p>
      ) : (
        <div className="space-y-3">
          {interactions.map((item) => {
            const isManual = item.platform === "manual";
            const isOutbound = item.direction === "outbound";
            const isMutual = item.direction === "mutual";
            const authorLabel = isOutbound
              ? "You"
              : isMutual
                ? "Both"
                : contactName || "Contact";

            if (isManual) {
              return (
                <div
                  key={item.id}
                  className="mx-auto max-w-[90%] border border-amber-200 bg-amber-50 rounded-lg px-4 py-3"
                >
                  <div className="flex items-center gap-1.5 mb-1 text-amber-500">
                    <FileText className="w-3.5 h-3.5" />
                    <span className="text-xs font-medium">Note</span>
                    <span className="text-xs">
                      &middot;{" "}
                      {formatDistanceToNow(new Date(item.occurred_at), {
                        addSuffix: true,
                      })}
                    </span>
                  </div>
                  {item.content_preview && (
                    <p className="text-sm text-amber-900 leading-relaxed">
                      <Linkify text={item.content_preview} className="text-amber-700 hover:text-amber-900" />
                    </p>
                  )}
                </div>
              );
            }

            return (
              <div
                key={item.id}
                className={cn(
                  "flex",
                  isOutbound ? "justify-end" : "justify-start"
                )}
              >
                <div
                  className={cn(
                    "max-w-[80%] rounded-2xl px-4 py-2.5",
                    isOutbound
                      ? "bg-blue-600 text-white rounded-br-md"
                      : "bg-gray-100 text-gray-900 rounded-bl-md"
                  )}
                >
                  <div className={cn(
                    "flex items-center gap-1.5 mb-1",
                    isOutbound ? "text-blue-100" : "text-gray-400"
                  )}>
                    <span className="flex-shrink-0">{platformIcons[item.platform]}</span>
                    <span className="text-xs font-medium">
                      {authorLabel}
                    </span>
                    <span className="text-xs">
                      &middot; {item.platform} &middot;{" "}
                      {formatDistanceToNow(new Date(item.occurred_at), {
                        addSuffix: true,
                      })}
                    </span>
                  </div>
                  {item.content_preview && (
                    <p className={cn(
                      "text-sm leading-relaxed",
                      isOutbound ? "text-white" : "text-gray-700"
                    )}>
                      <Linkify
                        text={item.content_preview}
                        className={isOutbound ? "text-blue-100 hover:text-white" : "text-blue-600 hover:text-blue-800"}
                      />
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
