"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function SetPasswordPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    setLoading(true);

    const supabase = createClient();
    const { error } = await supabase.auth.updateUser({ password });

    if (error) {
      setError(error.message);
      setLoading(false);
      return;
    }

    router.push("/");
    router.refresh();
  };

  return (
    <div className="min-h-screen bg-[#040e16] flex items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-8">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-green-500/20 to-green-500/5 border border-green-500/15 mb-4">
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              className="text-green-400"
            >
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white">Set your password</h1>
          <p className="text-white/40 text-sm">
            You&apos;ve been invited to YSS Content Copywriter. Choose a password to get started.
          </p>
        </div>

        <form onSubmit={handleSetPassword} className="space-y-4">
          {error && (
            <div className="text-red-400 text-sm text-center bg-red-400/10 border border-red-400/20 rounded-xl px-4 py-2.5">
              {error}
            </div>
          )}

          <div className="space-y-3">
            <Input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoFocus
              className="bg-white/[0.04] border-white/[0.08] text-white placeholder:text-white/30 focus:border-yss-accent/30 focus:ring-yss-accent/10 rounded-xl h-11"
            />
            <Input
              type="password"
              placeholder="Confirm password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              className="bg-white/[0.04] border-white/[0.08] text-white placeholder:text-white/30 focus:border-yss-accent/30 focus:ring-yss-accent/10 rounded-xl h-11"
            />
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="w-full gradient-button text-[#040e16] font-semibold rounded-xl h-11 shadow-lg shadow-yss-accent/10 hover:shadow-yss-accent/20 transition-all disabled:opacity-40"
          >
            {loading ? "Setting password..." : "Get Started"}
          </Button>
        </form>
      </div>
    </div>
  );
}
