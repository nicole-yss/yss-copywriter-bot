"use client";

import { CopyOutputCard } from "./copy-output-card";

interface AttachedFile {
  name: string;
  type: string;
  size: number;
  data: string;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  files?: AttachedFile[];
}

interface MessageBubbleProps {
  message: ChatMessage;
  contentType?: string;
  platform?: string;
  userMessage?: string;
}

function fileIcon(type: string): string {
  if (type.startsWith("image/")) return "\u{1F5BC}";
  if (type === "application/pdf") return "\u{1F4C4}";
  return "\u{1F4DD}";
}

export function MessageBubble({ message, contentType, platform, userMessage }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const text = message.content;

  if (!text && !message.files?.length) return null;

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-white text-[#071d2b] shadow-lg shadow-white/10"
            : "gradient-card text-white"
        }`}
      >
        {/* File attachment chips for user messages */}
        {isUser && message.files && message.files.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-2">
            {message.files.map((file, i) => (
              <span
                key={`${file.name}-${i}`}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-yss-navy/20 text-xs"
              >
                {fileIcon(file.type)} {file.name}
              </span>
            ))}
          </div>
        )}

        {isUser ? (
          <p className="whitespace-pre-wrap text-sm font-medium">{text}</p>
        ) : (
          <CopyOutputCard
            content={text}
            contentType={contentType}
            platform={platform}
            userMessage={userMessage}
          />
        )}
      </div>
    </div>
  );
}
