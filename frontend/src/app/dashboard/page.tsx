"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";

interface GeneratedContent {
  id: string;
  body: string;
  content_type_id: number;
  platform_id: number;
  rating: number | null;
  is_favorite: boolean;
  created_at: string;
}

const CONTENT_TYPES: Record<number, string> = {
  1: "Caption",
  2: "Carousel",
  3: "EDM",
  4: "Reel Script",
};

const PLATFORMS: Record<number, string> = {
  1: "Instagram",
  2: "TikTok",
  3: "YouTube",
};

export default function DashboardPage() {
  const [content, setContent] = useState<GeneratedContent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
    fetch(`${backendUrl}/api/v1/content/generated?limit=50`)
      .then((res) => res.json())
      .then((data) => {
        setContent(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-yss-cream">Content Dashboard</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Browse and manage your generated content
            </p>
          </div>
          <Link href="/">
            <Button variant="outline">Back to Chat</Button>
          </Link>
        </div>

        {loading ? (
          <p className="text-muted-foreground">Loading content...</p>
        ) : content.length === 0 ? (
          <Card className="p-8 text-center">
            <p className="text-muted-foreground">
              No content generated yet. Go to the chat to create some!
            </p>
          </Card>
        ) : (
          <div className="space-y-4">
            {content.map((item) => (
              <Card key={item.id} className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex gap-2 mb-2">
                      <Badge variant="secondary">
                        {CONTENT_TYPES[item.content_type_id] || "Unknown"}
                      </Badge>
                      <Badge variant="outline">
                        {PLATFORMS[item.platform_id] || "Unknown"}
                      </Badge>
                      {item.is_favorite && (
                        <Badge className="bg-yss-accent text-yss-navy">Favorite</Badge>
                      )}
                    </div>
                    <p className="text-sm text-foreground whitespace-pre-wrap line-clamp-4">
                      {item.body}
                    </p>
                    <p className="text-xs text-muted-foreground mt-2">
                      {new Date(item.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
