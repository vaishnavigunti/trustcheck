'use client';

import { useEffect, useState } from 'react';
import { Download, FileText, Eye } from 'lucide-react';
import Link from 'next/link';
import { format } from 'date-fns';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { api } from '@/lib/api';

interface Report {
  id: string;
  verification_id: string;
  title: string;
  created_at: string;
  file_size_bytes?: number;
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    api.get('/reports/').then((r) => {
      setReports(r.data.items || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleDownload = async (reportId: string, title: string) => {
    setDownloading(reportId);
    try {
      const res = await api.get(`/reports/${reportId}/download`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.replace(/\s+/g, '_')}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      alert('Download failed. Please try again.');
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-3xl font-bold tracking-tight">Reports</h2>
        <p className="text-muted-foreground">Download and manage your verification reports</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Generated Reports</CardTitle></CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-center py-8 text-muted-foreground text-sm">Loading reports...</p>
          ) : reports.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>No reports generated yet.</p>
              <p className="text-sm mt-1">
                <Link href="/verify" className="text-primary hover:underline">Complete a verification</Link> to generate a report.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {reports.map((r) => (
                <div key={r.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors">
                  <div className="flex items-center gap-3">
                    <FileText className="w-5 h-5 text-primary" />
                    <div>
                      <p className="text-sm font-medium">{r.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {format(new Date(r.created_at), 'MMM d, yyyy h:mm a')}
                        {r.file_size_bytes && ` • ${(r.file_size_bytes / 1024).toFixed(0)} KB`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Link href={`/verify/${r.verification_id}`}>
                      <Button variant="ghost" size="sm"><Eye className="w-4 h-4" /></Button>
                    </Link>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDownload(r.id, r.title)}
                      disabled={downloading === r.id}
                    >
                      <Download className="w-4 h-4 mr-1" />
                      {downloading === r.id ? 'Downloading...' : 'Download'}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
