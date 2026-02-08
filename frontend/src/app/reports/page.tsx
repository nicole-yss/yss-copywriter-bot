"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";

interface Report {
  id: string;
  report_type: string;
  title: string;
  summary: string;
  full_content?: string;
  created_at: string;
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);

  const backendUrl =
    typeof window !== "undefined"
      ? process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"
      : "http://localhost:8000";

  useEffect(() => {
    fetch(`${backendUrl}/api/v1/reports/`)
      .then((res) => res.json())
      .then((data) => {
        setReports(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [backendUrl]);

  const loadFullReport = async (reportId: string) => {
    const res = await fetch(`${backendUrl}/api/v1/reports/${reportId}`);
    const data = await res.json();
    setSelectedReport(data);
  };

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-yss-cream">Reports</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Analytics and strategy reports for your social media presence
            </p>
          </div>
          <Link href="/">
            <Button variant="outline">Back to Chat</Button>
          </Link>
        </div>

        {selectedReport ? (
          <div>
            <Button
              variant="ghost"
              onClick={() => setSelectedReport(null)}
              className="mb-4"
            >
              Back to Reports
            </Button>
            <Card className="p-6">
              <h2 className="text-xl font-bold mb-2">{selectedReport.title}</h2>
              <p className="text-xs text-muted-foreground mb-4">
                {new Date(selectedReport.created_at).toLocaleDateString()}
              </p>
              <div className="prose prose-invert max-w-none text-sm whitespace-pre-wrap">
                {selectedReport.full_content}
              </div>
            </Card>
          </div>
        ) : loading ? (
          <p className="text-muted-foreground">Loading reports...</p>
        ) : reports.length === 0 ? (
          <Card className="p-8 text-center">
            <p className="text-muted-foreground">
              No reports generated yet. Trigger a report from the backend API.
            </p>
          </Card>
        ) : (
          <div className="space-y-4">
            {reports.map((report) => (
              <Card
                key={report.id}
                className="p-4 cursor-pointer hover:border-yss-accent/50 transition-colors"
                onClick={() => loadFullReport(report.id)}
              >
                <h3 className="font-semibold">{report.title}</h3>
                <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                  {report.summary}
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  {new Date(report.created_at).toLocaleDateString()} &middot;{" "}
                  {report.report_type.replace("_", " ")}
                </p>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
