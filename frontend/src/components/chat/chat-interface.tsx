"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { MessageBubble } from "./message-bubble";
import { ContentTypeSelector } from "./content-type-selector";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  files?: AttachedFile[];
}

interface AttachedFile {
  name: string;
  type: string;
  size: number;
  data: string; // base64
}

const ACCEPTED_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/gif",
  "application/pdf",
  "text/plain",
  "text/markdown",
  "text/csv",
];

const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20MB

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

function fileIcon(type: string): string {
  if (type.startsWith("image/")) return "\u{1F5BC}";
  if (type === "application/pdf") return "\u{1F4C4}";
  return "\u{1F4DD}";
}

export function ChatInterface() {
  const [contentType, setContentType] = useState("caption");
  const [platform, setPlatform] = useState("instagram");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [files, setFiles] = useState<AttachedFile[]>([]);
  const [status, setStatus] = useState<"ready" | "submitted" | "streaming">("ready");
  const [dragOver, setDragOver] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isLoading = status === "submitted" || status === "streaming";

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, status]);

  const readFileAsBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        const base64 = result.split(",")[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const addFiles = useCallback(async (fileList: FileList | File[]) => {
    const newFiles: AttachedFile[] = [];
    for (const file of Array.from(fileList)) {
      if (!ACCEPTED_TYPES.includes(file.type) && !file.name.endsWith(".md") && !file.name.endsWith(".txt") && !file.name.endsWith(".csv")) {
        continue;
      }
      if (file.size > MAX_FILE_SIZE) continue;
      const data = await readFileAsBase64(file);
      newFiles.push({ name: file.name, type: file.type || "text/plain", size: file.size, data });
    }
    setFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSend = async () => {
    const text = input.trim();
    if ((!text && files.length === 0) || isLoading) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: text || "(attached files)",
      files: files.length > 0 ? [...files] : undefined,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    const sentFiles = [...files];
    setFiles([]);
    setStatus("submitted");

    try {
      const allMessages = [...messages, userMessage];
      const apiMessages = allMessages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: apiMessages,
          contentType,
          platform,
          files: sentFiles.map((f) => ({
            name: f.name,
            type: f.type,
            data: f.data,
          })),
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Request failed: ${response.status}`);
      }

      setStatus("streaming");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      const assistantId = crypto.randomUUID();
      let assistantContent = "";

      setMessages((prev) => [
        ...prev,
        { id: assistantId, role: "assistant", content: "" },
      ]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        assistantContent += decoder.decode(value, { stream: true });
        const currentContent = assistantContent;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: currentContent } : m
          )
        );
      }
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "Sorry, something went wrong. Please try again.",
        },
      ]);
    } finally {
      setStatus("ready");
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files);
    }
  };

  return (
    <div className="flex flex-col h-full relative">
      {/* Subtle accent glow at top */}
      <div className="absolute top-0 left-0 right-0 h-40 gradient-accent-glow pointer-events-none" />

      {/* Header */}
      <div className="relative z-10 flex items-center justify-between px-6 py-4 border-b border-white/[0.06] backdrop-blur-sm bg-white/[0.02]">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold tracking-tight text-white">
            YSS Content Copywriter
          </h1>
          <span className="text-[10px] font-medium px-2.5 py-0.5 rounded-full bg-gradient-to-r from-yss-accent/25 to-yss-accent/10 text-yss-accent border border-yss-accent/20">
            AI
          </span>
        </div>
        <ContentTypeSelector
          contentType={contentType}
          onContentTypeChange={setContentType}
          platform={platform}
          onPlatformChange={setPlatform}
        />
      </div>

      {/* Messages */}
      <div
        className={`flex-1 overflow-y-auto px-6 py-4 space-y-4 chat-scroll transition-colors ${
          dragOver ? "bg-yss-accent/5 ring-2 ring-inset ring-yss-accent/30 rounded-lg" : ""
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="max-w-lg space-y-5">
              <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-yss-accent/20 to-yss-accent/5 border border-yss-accent/15 mb-2">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-yss-accent">
                  <path d="M12 20h9" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M16.376 3.622a1 1 0 0 1 3.002 3.002L7.368 18.635a2 2 0 0 1-.855.506l-2.872.838a.5.5 0 0 1-.62-.62l.838-2.872a2 2 0 0 1 .506-.855z" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-white">
                What content do you need?
              </h2>
              <p className="text-white/50 text-sm leading-relaxed max-w-sm mx-auto">
                Describe what you want and I&apos;ll generate on-brand copy for
                YourSalonSupport. Select a content type and platform above, then
                tell me about your post idea.
              </p>
              <p className="text-white/30 text-xs">
                You can also attach photos, PDFs, or text files for reference.
              </p>
              <div className="grid grid-cols-2 gap-2.5 pt-4">
                {[
                  "Write a caption about salon growth tips",
                  "Create a carousel about client retention",
                  "Draft an EDM for our new package launch",
                  "Script a reel about booking systems",
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => setInput(suggestion)}
                    className="text-left text-xs p-3.5 rounded-xl border border-white/[0.06] hover:border-yss-accent/25 hover:bg-white/[0.03] transition-all duration-200 text-white/40 hover:text-white/70"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
        {messages.map((message, idx) => {
          // Find the preceding user message for assistant messages (for feedback context)
          let precedingUserMsg: string | undefined;
          if (message.role === "assistant") {
            for (let j = idx - 1; j >= 0; j--) {
              if (messages[j].role === "user") {
                precedingUserMsg = messages[j].content;
                break;
              }
            }
          }
          return (
            <MessageBubble
              key={message.id}
              message={message}
              contentType={contentType}
              platform={platform}
              userMessage={precedingUserMsg}
            />
          );
        })}
        {isLoading &&
          messages.length > 0 &&
          messages[messages.length - 1].role === "user" && (
            <div className="flex justify-start">
              <div className="gradient-card rounded-2xl px-5 py-4 max-w-[280px]">
                <div className="flex items-center gap-3 mb-2">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 rounded-full bg-yss-accent thinking-dot" />
                    <span className="w-2 h-2 rounded-full bg-yss-accent thinking-dot" />
                    <span className="w-2 h-2 rounded-full bg-yss-accent thinking-dot" />
                  </div>
                  <span className="text-xs text-white/50">
                    {status === "submitted" ? "Researching..." : "Writing..."}
                  </span>
                </div>
                <div className="w-full h-1 bg-white/[0.06] rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-yss-accent/40 to-yss-accent/80 rounded-full thinking-bar" />
                </div>
              </div>
            </div>
          )}
        <div ref={messagesEndRef} />
      </div>

      {/* File previews */}
      {files.length > 0 && (
        <div className="px-6 pt-3 flex flex-wrap gap-2">
          {files.map((file, i) => (
            <div
              key={`${file.name}-${i}`}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-xs text-white"
            >
              <span>{fileIcon(file.type)}</span>
              <span className="max-w-[120px] truncate">{file.name}</span>
              <span className="text-white/40">{formatFileSize(file.size)}</span>
              <button
                onClick={() => removeFile(i)}
                className="text-white/40 hover:text-red-400 ml-1 transition-colors"
              >
                x
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="relative px-6 py-4 border-t border-white/[0.06] bg-white/[0.02] backdrop-blur-sm">
        <div className="flex gap-3">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".jpg,.jpeg,.png,.webp,.gif,.pdf,.txt,.md,.csv"
            className="hidden"
            onChange={(e) => {
              if (e.target.files) addFiles(e.target.files);
              e.target.value = "";
            }}
          />
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className="text-white/40 hover:text-yss-accent hover:bg-white/[0.04] self-end h-[44px] w-[44px] transition-colors"
            title="Attach files (images, PDFs, text)"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
            </svg>
          </Button>
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={files.length > 0 ? "Describe what to do with the attached files..." : "Describe the content you need..."}
            className="flex-1 min-h-[44px] max-h-[120px] resize-none bg-white/[0.04] border-white/[0.08] text-white placeholder:text-white/30 focus:border-yss-accent/30 focus:ring-yss-accent/10 transition-colors rounded-xl"
            rows={1}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
          />
          <Button
            type="button"
            onClick={handleSend}
            disabled={isLoading || (!input.trim() && files.length === 0)}
            className="gradient-button text-yss-navy font-semibold px-6 self-end rounded-xl shadow-lg shadow-yss-accent/10 hover:shadow-yss-accent/20 transition-all disabled:opacity-40 disabled:shadow-none"
          >
            {isLoading ? "..." : "Send"}
          </Button>
        </div>
      </div>
    </div>
  );
}
