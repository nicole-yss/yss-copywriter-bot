import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

// Only allow redirects to these internal paths after auth
const ALLOWED_NEXT_PATHS = ["/", "/admin", "/auth/set-password", "/dashboard", "/reports"];

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const rawNext = searchParams.get("next") ?? "/";

  // Prevent open redirect: only allow known internal paths
  const next = ALLOWED_NEXT_PATHS.includes(rawNext) ? rawNext : "/";

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  return NextResponse.redirect(`${origin}/login?error=auth_callback_failed`);
}
