"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, UserPlus, Trash2, Shield, ShieldOff, Loader2, Link2, KeyRound, Copy, Check } from "lucide-react";

interface User {
  id: string;
  email: string;
  role: string;
  fullName: string | null;
  createdAt: string;
  lastSignIn: string | null;
  emailConfirmed: boolean;
}

export default function AdminPage() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteName, setInviteName] = useState("");
  const [invitePassword, setInvitePassword] = useState("");
  const [inviteAsAdmin, setInviteAsAdmin] = useState(false);
  const [inviteMode, setInviteMode] = useState<"invite" | "password">("invite");
  const [inviting, setInviting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [createdResult, setCreatedResult] = useState<{
    email: string;
    inviteUrl?: string;
    password?: string;
  } | null>(null);
  const [copied, setCopied] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  const fetchUsers = useCallback(async () => {
    try {
      const res = await fetch("/api/admin/users");
      if (res.status === 403) {
        router.push("/");
        return;
      }
      const data = await res.json();
      if (data.users) setUsers(data.users);
    } catch {
      setError("Failed to load users");
    } finally {
      setLoadingUsers(false);
    }
  }, [router]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setInviting(true);

    try {
      const res = await fetch("/api/admin/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: inviteEmail,
          fullName: inviteName || undefined,
          isAdmin: inviteAsAdmin,
          mode: inviteMode,
          password: inviteMode === "password" ? invitePassword || undefined : undefined,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Failed to add user");
        return;
      }

      if (inviteMode === "invite") {
        setCreatedResult({ email: inviteEmail, inviteUrl: data.inviteUrl });
        setSuccess(`Invite link generated for ${inviteEmail}`);
      } else {
        setCreatedResult({ email: inviteEmail, password: data.tempPassword });
        setSuccess(`Account created for ${inviteEmail}`);
      }
      setCopied(false);
      setInviteEmail("");
      setInviteName("");
      setInvitePassword("");
      setInviteAsAdmin(false);
      fetchUsers();
    } catch {
      setError("Failed to add user");
    } finally {
      setInviting(false);
    }
  };

  const handleDelete = async (id: string, email: string) => {
    if (!confirm(`Remove ${email} from the team? This cannot be undone.`)) return;
    setDeletingId(id);
    setError("");

    try {
      const res = await fetch(`/api/admin/users/${id}`, { method: "DELETE" });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Failed to remove user");
        return;
      }
      setUsers((prev) => prev.filter((u) => u.id !== id));
      setSuccess(`${email} has been removed`);
    } catch {
      setError("Failed to remove user");
    } finally {
      setDeletingId(null);
    }
  };

  const handleToggleRole = async (id: string, currentRole: string) => {
    const newRole = currentRole === "admin" ? "member" : "admin";
    setTogglingId(id);
    setError("");

    try {
      const res = await fetch(`/api/admin/users/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: newRole }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Failed to update role");
        return;
      }
      setUsers((prev) =>
        prev.map((u) => (u.id === id ? { ...u, role: newRole } : u))
      );
    } catch {
      setError("Failed to update role");
    } finally {
      setTogglingId(null);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "Never";
    return new Date(dateStr).toLocaleDateString("en-AU", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  };

  return (
    <div className="min-h-screen bg-[#040e16]">
      {/* Header */}
      <div className="border-b border-white/[0.06] bg-white/[0.02] backdrop-blur-sm">
        <div className="max-w-3xl mx-auto px-6 py-4 flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push("/")}
            className="text-white/50 hover:text-yss-accent hover:bg-white/[0.04] h-8 w-8 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <h1 className="text-lg font-semibold text-white">Admin Settings</h1>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-8 space-y-10">
        {/* Feedback messages */}
        {error && (
          <div className="text-red-400 text-sm bg-red-400/10 border border-red-400/20 rounded-xl px-4 py-2.5">
            {error}
          </div>
        )}
        {success && (
          <div className="text-green-400 text-sm bg-green-400/10 border border-green-400/20 rounded-xl px-4 py-2.5">
            {success}
          </div>
        )}

        {/* Add User */}
        <section className="space-y-4">
          <div>
            <h2 className="text-base font-semibold text-white">Add Team Member</h2>
            <p className="text-sm text-white/40 mt-1">
              Add someone to the team via invite link or by creating credentials directly.
            </p>
          </div>

          {/* Result card */}
          {createdResult && (
            <div className="bg-green-400/10 border border-green-400/20 rounded-xl px-4 py-3 space-y-3">
              {createdResult.inviteUrl ? (
                <>
                  <p className="text-sm font-medium text-green-400">Invite link generated for {createdResult.email}</p>
                  <div className="bg-black/20 rounded-lg px-3 py-2 text-sm text-white/80 break-all font-mono leading-relaxed">
                    {createdResult.inviteUrl}
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(createdResult.inviteUrl!);
                        setCopied(true);
                        setTimeout(() => setCopied(false), 2000);
                      }}
                      className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-yss-accent/20 text-yss-accent hover:bg-yss-accent/30 transition-colors"
                    >
                      {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                      {copied ? "Copied" : "Copy link"}
                    </button>
                    <p className="text-xs text-white/30">Share this link with the user. They&apos;ll set their own password.</p>
                  </div>
                </>
              ) : (
                <>
                  <p className="text-sm font-medium text-green-400">Account created — share these credentials:</p>
                  <div className="bg-black/20 rounded-lg px-3 py-2 font-mono text-sm text-white/80 space-y-1">
                    <p>Email: <span className="text-white">{createdResult.email}</span></p>
                    <p>Password: <span className="text-white">{createdResult.password}</span></p>
                  </div>
                  <p className="text-xs text-white/30">The user can change their password from their profile after signing in.</p>
                </>
              )}
              <button
                onClick={() => setCreatedResult(null)}
                className="text-xs text-white/40 hover:text-white/60 transition-colors"
              >
                Dismiss
              </button>
            </div>
          )}

          {/* Mode toggle */}
          <div className="flex gap-1 p-1 rounded-xl bg-white/[0.04] border border-white/[0.06] w-fit">
            <button
              type="button"
              onClick={() => setInviteMode("invite")}
              className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-colors ${
                inviteMode === "invite"
                  ? "bg-yss-accent/15 text-yss-accent"
                  : "text-white/40 hover:text-white/60"
              }`}
            >
              <Link2 className="h-3 w-3" />
              Invite link
            </button>
            <button
              type="button"
              onClick={() => setInviteMode("password")}
              className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-colors ${
                inviteMode === "password"
                  ? "bg-yss-accent/15 text-yss-accent"
                  : "text-white/40 hover:text-white/60"
              }`}
            >
              <KeyRound className="h-3 w-3" />
              Set password
            </button>
          </div>

          <form onSubmit={handleInvite} className="space-y-3">
            <div className="flex flex-col sm:flex-row gap-3">
              <Input
                type="email"
                placeholder="Email address"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                required
                className="flex-1 bg-white/[0.04] border-white/[0.08] text-white placeholder:text-white/30 focus:border-yss-accent/30 focus:ring-yss-accent/10 rounded-xl h-11"
              />
              <Input
                type="text"
                placeholder="Name (optional)"
                value={inviteName}
                onChange={(e) => setInviteName(e.target.value)}
                className="sm:w-44 bg-white/[0.04] border-white/[0.08] text-white placeholder:text-white/30 focus:border-yss-accent/30 focus:ring-yss-accent/10 rounded-xl h-11"
              />
            </div>
            <div className="flex flex-col sm:flex-row gap-3">
              {inviteMode === "password" && (
                <Input
                  type="text"
                  placeholder="Password (auto-generated if empty)"
                  value={invitePassword}
                  onChange={(e) => setInvitePassword(e.target.value)}
                  className="flex-1 bg-white/[0.04] border-white/[0.08] text-white placeholder:text-white/30 focus:border-yss-accent/30 focus:ring-yss-accent/10 rounded-xl h-11"
                />
              )}
              <label className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/[0.04] border border-white/[0.08] cursor-pointer hover:bg-white/[0.06] transition-colors whitespace-nowrap">
                <input
                  type="checkbox"
                  checked={inviteAsAdmin}
                  onChange={(e) => setInviteAsAdmin(e.target.checked)}
                  className="rounded border-white/20 bg-white/10 text-yss-accent focus:ring-yss-accent/20"
                />
                <span className="text-sm text-white/60">Admin</span>
              </label>
              <Button
                type="submit"
                disabled={inviting}
                className="gradient-button text-[#040e16] font-semibold rounded-xl h-11 px-5 shadow-lg shadow-yss-accent/10 hover:shadow-yss-accent/20 transition-all disabled:opacity-40 whitespace-nowrap"
              >
                {inviting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <UserPlus className="h-4 w-4 mr-2" />
                    {inviteMode === "invite" ? "Generate Link" : "Create"}
                  </>
                )}
              </Button>
            </div>
          </form>
        </section>

        {/* Divider */}
        <div className="border-t border-white/[0.06]" />

        {/* Team Members */}
        <section className="space-y-4">
          <div>
            <h2 className="text-base font-semibold text-white">Team Members</h2>
            <p className="text-sm text-white/40 mt-1">
              {users.length} {users.length === 1 ? "member" : "members"} on the team.
            </p>
          </div>

          {loadingUsers ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-5 w-5 animate-spin text-white/30" />
            </div>
          ) : (
            <div className="space-y-2">
              {users.map((u) => (
                <div
                  key={u.id}
                  className="flex items-center justify-between px-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.05] transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-yss-accent/25 to-yss-accent/10 border border-yss-accent/15 flex items-center justify-center text-sm font-semibold text-yss-accent shrink-0">
                      {(u.fullName || u.email || "?")[0].toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-white truncate">
                          {u.fullName || u.email}
                        </span>
                        <Badge
                          variant={u.role === "admin" ? "default" : "secondary"}
                          className={
                            u.role === "admin"
                              ? "bg-yss-accent/15 text-yss-accent border-yss-accent/20 text-[10px] px-1.5 py-0"
                              : "bg-white/[0.06] text-white/40 border-white/[0.08] text-[10px] px-1.5 py-0"
                          }
                        >
                          {u.role}
                        </Badge>
                        {!u.emailConfirmed && (
                          <Badge className="bg-amber-500/15 text-amber-400 border-amber-500/20 text-[10px] px-1.5 py-0">
                            pending
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-3 text-xs text-white/30 mt-0.5">
                        {u.fullName && <span className="truncate">{u.email}</span>}
                        <span>Joined {formatDate(u.createdAt)}</span>
                        {u.lastSignIn && <span>Last seen {formatDate(u.lastSignIn)}</span>}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0 ml-3">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleToggleRole(u.id, u.role)}
                      disabled={togglingId === u.id}
                      className="text-white/30 hover:text-yss-accent hover:bg-white/[0.04] h-8 w-8 transition-colors"
                      title={u.role === "admin" ? "Remove admin access" : "Grant admin access"}
                    >
                      {togglingId === u.id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : u.role === "admin" ? (
                        <ShieldOff className="h-3.5 w-3.5" />
                      ) : (
                        <Shield className="h-3.5 w-3.5" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(u.id, u.email || "")}
                      disabled={deletingId === u.id}
                      className="text-white/30 hover:text-red-400 hover:bg-white/[0.04] h-8 w-8 transition-colors"
                      title="Remove user"
                    >
                      {deletingId === u.id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Trash2 className="h-3.5 w-3.5" />
                      )}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Divider */}
        <div className="border-t border-white/[0.06]" />

        {/* App Info */}
        <section className="space-y-4">
          <div>
            <h2 className="text-base font-semibold text-white">Application</h2>
            <p className="text-sm text-white/40 mt-1">
              System information and service status.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <InfoCard label="Brand" value="YourSalonSupport" sub="@yoursalonsupport" />
            <InfoCard label="AI Model" value="Claude (Anthropic)" sub="Content generation" />
            <InfoCard label="Embeddings" value="Voyage AI 3.5" sub="RAG & brand context" />
            <InfoCard label="Database" value="Supabase" sub="PostgreSQL + pgvector" />
          </div>
        </section>

        {/* Divider */}
        <div className="border-t border-white/[0.06]" />

        {/* Content Defaults */}
        <section className="space-y-4 pb-8">
          <div>
            <h2 className="text-base font-semibold text-white">Content Defaults</h2>
            <p className="text-sm text-white/40 mt-1">
              Default settings for new chat sessions.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <InfoCard label="Default Content Type" value="Caption" sub="Changeable per session" />
            <InfoCard label="Default Platform" value="Instagram" sub="Changeable per session" />
            <InfoCard
              label="Available Types"
              value="4 types"
              sub="Caption, Carousel, EDM, Reel Script"
            />
            <InfoCard
              label="Available Platforms"
              value="3 platforms"
              sub="Instagram, TikTok, YouTube"
            />
          </div>
        </section>
      </div>
    </div>
  );
}

function InfoCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub: string;
}) {
  return (
    <div className="px-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
      <p className="text-[10px] uppercase tracking-wider text-white/30 mb-1">{label}</p>
      <p className="text-sm font-medium text-white">{value}</p>
      <p className="text-xs text-white/40 mt-0.5">{sub}</p>
    </div>
  );
}
