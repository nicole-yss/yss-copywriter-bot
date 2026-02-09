import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { createAdminClient } from "@/lib/supabase/admin";

async function requireAdmin() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return { error: "Not authenticated", status: 401 };
  }

  if (user.user_metadata?.role !== "admin") {
    return { error: "Admin access required", status: 403 };
  }

  return { user };
}

export async function GET() {
  const auth = await requireAdmin();
  if ("error" in auth) {
    return NextResponse.json(
      { error: auth.error },
      { status: auth.status }
    );
  }

  const admin = createAdminClient();
  const { data, error } = await admin.auth.admin.listUsers();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  const users = data.users.map((u) => ({
    id: u.id,
    email: u.email,
    role: u.user_metadata?.role || "member",
    fullName: u.user_metadata?.full_name || null,
    createdAt: u.created_at,
    lastSignIn: u.last_sign_in_at,
    emailConfirmed: !!u.email_confirmed_at,
  }));

  return NextResponse.json({ users });
}

export async function POST(request: Request) {
  const auth = await requireAdmin();
  if ("error" in auth) {
    return NextResponse.json(
      { error: auth.error },
      { status: auth.status }
    );
  }

  const body = await request.json();
  const { email, fullName, isAdmin, mode, password } = body;

  if (!email) {
    return NextResponse.json({ error: "Email is required" }, { status: 400 });
  }

  const admin = createAdminClient();
  const role = isAdmin ? "admin" : "member";
  const metadata = { role, full_name: fullName || null };

  // Mode: "invite" generates a link, "password" creates with credentials
  if (mode === "password") {
    const tempPassword = password || `YSS-${crypto.randomUUID().slice(0, 8)}`;
    const { data, error } = await admin.auth.admin.createUser({
      email,
      password: tempPassword,
      email_confirm: true,
      user_metadata: metadata,
    });

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }

    return NextResponse.json({
      user: {
        id: data.user.id,
        email: data.user.email,
        role: data.user.user_metadata?.role || "member",
      },
      tempPassword,
    });
  }

  // Default: generate invite link (no email sent)
  const redirectTo = `${process.env.FRONTEND_URL || "http://localhost:3000"}/auth/callback?next=/auth/set-password`;

  const { data, error } = await admin.auth.admin.generateLink({
    type: "invite",
    email,
    options: {
      data: metadata,
      redirectTo,
    },
  });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 400 });
  }

  // Build the invite URL from the token data
  const {
    properties: { hashed_token, verification_type },
  } = data;

  const inviteUrl = `${process.env.NEXT_PUBLIC_SUPABASE_URL}/auth/v1/verify?token=${hashed_token}&type=${verification_type}&redirect_to=${encodeURIComponent(redirectTo)}`;

  return NextResponse.json({
    user: {
      id: data.user.id,
      email: data.user.email,
      role: data.user.user_metadata?.role || "member",
    },
    inviteUrl,
  });
}
