'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { format } from 'date-fns';
import { Eye, AlertTriangle, CheckCircle, Clock, Shield, Trash2, RefreshCw, FileCheck } from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { api } from '@/lib/api';

interface Verification {
  id: string;
  verification_type: string;
  target_url?: string;
  company_name?: string;
  status: string;
  created_at: string;
  processing_time_ms?: number;
}

const statusConfig: Record<string, { icon: React.ReactNode; badge: string; label: string }> = {
  completed:   { icon: <CheckCircle className="w-4 h-4 text-green-600" />,  badge: 'bg-green-100 text-green-800',   label: 'Completed' },
  failed:      { icon: <AlertTriangle className="w-4 h-4 text-red-600" />,   badge: 'bg-red-100 text-red-800',       label: 'Failed' },
  in_progress: { icon: <Clock className="w-4 h-4 text-amber-600" />,         badge: 'bg-amber-100 text-amber-800',   label: 'In Progress' },
  pending:     { icon: <Clock className="w-4 h-4 text-blue-600" />,          badge: 'bg-blue-100 text-blue-800',     label: 'Pending' },
};

export default function HistoryPage() {
  const [verifications, setVerifications] = useState<Verification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = useCallback(async (silent = false) => {
    if (!silent) setIsLoading(true);
    else setRefreshing(true);
    try {
      const res = await api.get('/verifications/');
      setVerifications(res.data.items || []);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load history');
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchHistory(); }, [fetchHistory]);

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete verification for "${name}"? This cannot be undone.`)) return;
    setDeletingId(id);
    try {
      await api.delete(`/verifications/${id}`);
      setVerifications((prev) => prev.filter((v) => v.id !== id));
    } catch {
      alert('Failed to delete. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-2"><div className="skeleton h-7 w-48" /><div className="skeleton h-4 w-64" /></div>
          <div className="skeleton h-9 w-24 rounded-md" />
        </div>
        <div className="skeleton h-16 rounded-xl" />
        <div className="skeleton h-16 rounded-xl" />
        <div className="skeleton h-16 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Verification History</h2>
          <p className="text-muted-foreground text-sm">{verifications.length} verification{verifications.length !== 1 ? 's' : ''} total</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => fetchHistory(true)} disabled={refreshing} className="gap-1.5">
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 text-sm text-destructive bg-destructive/10 rounded-lg">
          <AlertTriangle className="w-4 h-4" /> {error}
        </div>
      )}

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Shield className="w-4 h-4 text-primary" /> All Verifications
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {verifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center px-4">
              <div className="w-14 h-14 rounded-2xl bg-muted flex items-center justify-center mb-4">
                <FileCheck className="w-7 h-7 text-muted-foreground" />
              </div>
              <h3 className="font-semibold mb-1">No verifications yet</h3>
              <p className="text-sm text-muted-foreground mb-4">Start your first verification to protect yourself from scams.</p>
              <Link href="/verify">
                <Button size="sm" className="gap-1.5">
                  <FileCheck className="w-3.5 h-3.5" /> Start Verification
                </Button>
              </Link>
            </div>
          ) : (
            <div className="divide-y">
              {verifications.map((v) => {
                const cfg = statusConfig[v.status] || statusConfig.pending;
                const name = v.company_name || v.target_url || 'Unknown';
                return (
                  <div key={v.id} className="flex items-center justify-between px-5 py-3.5 hover:bg-accent/30 transition-colors group">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className={`p-1.5 rounded-lg ${cfg.badge} flex-shrink-0`}>{cfg.icon}</div>
                      <div className="min-w-0">
                        <p className="font-medium text-sm truncate">{name}</p>
                        <p className="text-xs text-muted-foreground">
                          {format(new Date(v.created_at), 'MMM d, yyyy · h:mm a')}
                          {v.processing_time_ms ? ` · ${(v.processing_time_ms / 1000).toFixed(1)}s` : ''}
                          {' · '}
                          <span className="capitalize">{v.verification_type.replace('_', ' ')}</span>
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className={`hidden sm:inline px-2 py-0.5 rounded-full text-xs font-medium ${cfg.badge}`}>{cfg.label}</span>
                      <Link href={`/verify/${v.id}`}>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                          <Eye className="w-3.5 h-3.5" />
                        </Button>
                      </Link>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 hover:text-destructive hover:bg-destructive/10"
                        onClick={() => handleDelete(v.id, name)}
                        disabled={deletingId === v.id}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
