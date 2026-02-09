import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { createAdminClient } from "@/lib/supabase/admin";

async function requireAdmin() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return { error: "Not authenticated" as const, status: 401 as const };
  }

  // Verify role server-side via admin API to prevent self-promotion
  const admin = createAdminClient();
  const { data: serverUser } = await admin.auth.admin.getUserById(user.id);
  if (serverUser?.user?.user_metadata?.role !== "admin") {
    return { error: "Admin access required" as const, status: 403 as const };
  }

  return { user, admin };
}

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const auth = await requireAdmin();
  if ("error" in auth) {
    return NextResponse.json({ error: auth.error }, { status: auth.status });
  }

  if (id === auth.user.id) {
    return NextResponse.json(
      { error: "You cannot delete your own account" },
      { status: 400 }
    );
  }

  const { error } = await auth.admin.auth.admin.deleteUser(id);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ success: true });
}

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const auth = await requireAdmin();
  if ("error" in auth) {
    return NextResponse.json({ error: auth.error }, { status: auth.status });
  }

  const body = await request.json();
  const { role } = body;

  if (!role || !["admin", "member"].includes(role)) {
    return NextResponse.json({ error: "Invalid role" }, { status: 400 });
  }

  const { error } = await auth.admin.auth.admin.updateUserById(id, {
    user_metadata: { role },
  });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ success: true });
}
