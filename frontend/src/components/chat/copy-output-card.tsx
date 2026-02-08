"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";

interface CopyOutputCardProps {
  content: string;
  contentType?: string;
  platform?: string;
  userMessage?: string;
  onFeedback?: (rating: "positive" | "negative", note?: string) => void;
}

export function CopyOutputCard({
  content,
  contentType,
  platform,
  userMessage,
  onFeedback,
}: CopyOutputCardProps) {
  const [copied, setCopied] = useState(false);
  const [feedbackState, setFeedbackState] = useState<"none" | "positive" | "negative" | "noting">("none");
  const [feedbackNote, setFeedbackNote] = useState("");
  const [feedbackSent, setFeedbackSent] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const submitFeedback = async (rating: "positive" | "negative", note?: string) => {
    try {
      await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contentType: contentType || "caption",
          platform: platform || "instagram",
          userMessage: userMessage || "",
          assistantMessage: content,
          rating,
          feedbackNote: note || null,
        }),
      });
      setFeedbackSent(true);
      onFeedback?.(rating, note);
    } catch (error) {
      console.error("Feedback error:", error);
    }
  };

  const handleThumbsUp = () => {
    if (feedbackSent) return;
    setFeedbackState("positive");
    submitFeedback("positive");
  };

  const handleThumbsDown = () => {
    if (feedbackSent) return;
    setFeedbackState("noting");
  };

  const handleNoteSubmit = () => {
    setFeedbackState("negative");
    submitFeedback("negative", feedbackNote || undefined);
  };

  const handleNoteSkip = () => {
    setFeedbackState("negative");
    submitFeedback("negative");
  };

  return (
    <div className="space-y-2">
      <div className="prose prose-invert prose-sm max-w-none leading-relaxed
        prose-headings:text-white prose-headings:font-semibold prose-headings:mt-4 prose-headings:mb-2
        prose-h1:text-lg prose-h1:border-b prose-h1:border-white/10 prose-h1:pb-2
        prose-h2:text-base
        prose-h3:text-sm prose-h3:text-yss-accent
        prose-p:text-white/90 prose-p:my-1.5
        prose-strong:text-yss-accent prose-strong:font-semibold
        prose-em:text-white/60 prose-em:italic
        prose-hr:border-white/10 prose-hr:my-3
        prose-ul:text-white/90 prose-ul:my-1
        prose-ol:text-white/90 prose-ol:my-1
        prose-li:my-0.5
        prose-code:text-yss-accent prose-code:bg-white/[0.06] prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs
        prose-pre:bg-white/[0.04] prose-pre:border prose-pre:border-white/[0.08] prose-pre:rounded-lg prose-pre:p-3
        prose-a:text-yss-accent prose-a:no-underline hover:prose-a:underline
      ">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
      </div>

      {content.length > 0 && (
        <div className="flex items-center justify-between pt-2 border-t border-white/[0.06]">
          {/* Feedback buttons */}
          <div className="flex items-center gap-1">
            {feedbackSent ? (
              <span className="text-[11px] text-white/30">
                {feedbackState === "positive" ? "Liked" : "Noted"} - thanks!
              </span>
            ) : feedbackState === "noting" ? (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={feedbackNote}
                  onChange={(e) => setFeedbackNote(e.target.value)}
                  placeholder="What could be better?"
                  className="text-xs bg-white/[0.04] border border-white/[0.08] rounded-lg px-2.5 py-1.5 text-white placeholder:text-white/30 w-[200px] focus:outline-none focus:border-yss-accent/30"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleNoteSubmit();
                  }}
                  autoFocus
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleNoteSubmit}
                  className="text-yss-accent hover:text-yss-accent hover:bg-white/[0.06] text-xs h-7 px-2"
                >
                  Send
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleNoteSkip}
                  className="text-white/30 hover:text-white/50 hover:bg-white/[0.06] text-xs h-7 px-2"
                >
                  Skip
                </Button>
              </div>
            ) : (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleThumbsUp}
                  className="text-white/30 hover:text-green-400 hover:bg-green-400/10 text-xs h-7 w-7 p-0 transition-colors"
                  title="Good output - more like this"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M7 10v12" />
                    <path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z" />
                  </svg>
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleThumbsDown}
                  className="text-white/30 hover:text-red-400 hover:bg-red-400/10 text-xs h-7 w-7 p-0 transition-colors"
                  title="Not great - I'll tell you why"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17 14V2" />
                    <path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z" />
                  </svg>
                </Button>
              </>
            )}
          </div>

          {/* Copy button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopy}
            className="text-white/40 hover:text-white hover:bg-white/[0.06] text-xs h-7 transition-colors"
          >
            {copied ? "Copied!" : "Copy"}
          </Button>
        </div>
      )}
    </div>
  );
}
