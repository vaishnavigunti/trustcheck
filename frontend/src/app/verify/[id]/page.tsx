'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Download, Clock, Shield, AlertTriangle, CheckCircle, Info, Loader2, ArrowLeft, XCircle } from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { api } from '@/lib/api';

interface Verification {
  id: string;
  status: string;
  target_url?: string;
  company_name?: string;
  recruiter_email?: string;
  findings: Finding[];
  timeline: TimelineEvent[];
  processing_time_ms?: number;
  created_at: string;
}

interface Finding {
  id: string;
  category: string;
  severity: 'passed' | 'warning' | 'critical' | 'info';
  title: string;
  description?: string;
  recommendation?: string;
}

interface TimelineEvent {
  id: string;
  event_type: string;
  title: string;
  description?: string;
  timestamp: string;
  duration_ms?: number;
}

// ─── Trust Score helpers ─────────────────────────────────────────────────────
function calcTrustScore(findings: Finding[]) {
  const critical = findings.filter(f => f.severity === 'critical').length;
  const warnings  = findings.filter(f => f.severity === 'warning').length;
  const score = Math.max(0, 10 - critical * 2.5 - warnings * 0.8);
  return Math.round(score * 10) / 10;
}

function getVerdict(score: number, status: string) {
  if (status === 'failed') return { label: 'Check failed', sub: 'Could not complete the verification.', color: 'text-gray-600', bg: 'bg-gray-50 border-gray-200', ring: 'text-gray-400' };
  if (score >= 8)  return { label: 'Looks Legitimate', sub: 'Our checks found no significant red flags. This appears to be a genuine opportunity.', color: 'text-green-700', bg: 'bg-green-50 border-green-200', ring: 'text-green-500' };
  if (score >= 5)  return { label: 'Exercise Caution', sub: 'Some warning signs were detected. Verify further before sharing personal details.', color: 'text-amber-700', bg: 'bg-amber-50 border-amber-200', ring: 'text-amber-500' };
  return           { label: 'Likely Fraudulent', sub: 'Multiple red flags detected. This may be a scam. Do not proceed.', color: 'text-red-700', bg: 'bg-red-50 border-red-200', ring: 'text-red-500' };
}

const severityConfig = {
  passed:   { icon: CheckCircle,    cls: 'text-green-600', badge: 'bg-green-100 text-green-800', label: 'Passed'   },
  warning:  { icon: AlertTriangle,  cls: 'text-amber-600', badge: 'bg-amber-100 text-amber-800', label: 'Warning'  },
  critical: { icon: XCircle,        cls: 'text-red-600',   badge: 'bg-red-100 text-red-800',     label: 'Critical' },
  info:     { icon: Info,            cls: 'text-blue-600',  badge: 'bg-blue-100 text-blue-800',   label: 'Info'     },
};

// ─── Page component ───────────────────────────────────────────────────────────
export default function VerificationResultPage() {
  const params = useParams();
  const router = useRouter();
  const [verification, setVerification] = useState<Verification | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);

  useEffect(() => {
    if (!params.id) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    const fetchVerification = async () => {
      try {
        const res = await api.get(`/verifications/${params.id}`);
        if (cancelled) return;
        setVerification(res.data);
        setError(null);
        const s = res.data?.status;
        if (s === 'pending' || s === 'in_progress') timer = setTimeout(fetchVerification, 2500);
      } catch (err: any) {
        if (cancelled) return;
        setError(err.response?.data?.error?.message || 'Failed to load verification');
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };

    fetchVerification();
    return () => { cancelled = true; clearTimeout(timer); };
  }, [params.id]);

  const handleDownloadReport = async () => {
    if (!verification) return;
    setIsGeneratingReport(true);
    try {
      const res = await api.post('/reports/', { verification_id: verification.id });
      const downloadRes = await api.get(`/reports/${res.data.id}/download`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([downloadRes.data]));
      const a = document.createElement('a');
      a.href = url;
      a.setAttribute('download', `TrustCheck_Report_${verification.id}.pdf`);
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to generate report');
    } finally {
      setIsGeneratingReport(false);
    }
  };

  // ── Loading ──
  if (isLoading) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="skeleton h-52 rounded-2xl mb-6" />
        <div className="skeleton h-10 rounded-xl mb-3" />
        <div className="skeleton h-10 rounded-xl mb-3" />
        <div className="skeleton h-10 rounded-xl" />
      </div>
    );
  }

  // ── Error ──
  if (error || !verification) {
    return (
      <div className="max-w-3xl mx-auto">
        <Card>
          <CardContent className="py-12 text-center">
            <XCircle className="w-10 h-10 text-destructive mx-auto mb-3" />
            <p className="font-semibold text-destructive">{error || 'Verification not found'}</p>
            <Button variant="outline" size="sm" className="mt-4" onClick={() => router.back()}>
              <ArrowLeft className="w-4 h-4 mr-1" /> Go back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const isRunning = verification.status === 'pending' || verification.status === 'in_progress';
  const findings  = verification.findings || [];
  const passed    = findings.filter(f => f.severity === 'passed').length;
  const warnings  = findings.filter(f => f.severity === 'warning').length;
  const critical  = findings.filter(f => f.severity === 'critical').length;
  const score     = isRunning ? null : calcTrustScore(findings);
  const verdict   = score !== null ? getVerdict(score, verification.status) : null;
  const name      = verification.company_name || verification.target_url || verification.recruiter_email || 'Unknown';

  return (
    <div className="max-w-3xl mx-auto space-y-5 animate-in">

      {/* Back + download row */}
      <div className="flex items-center justify-between">
        <button onClick={() => router.back()} className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
        <Button onClick={handleDownloadReport} disabled={isGeneratingReport || verification.status !== 'completed'} size="sm" variant="outline" className="gap-1.5">
          {isGeneratingReport ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
          {isGeneratingReport ? 'Generating…' : 'Download PDF Report'}
        </Button>
      </div>

      {/* ── TRUST SCORE CARD ── */}
      {isRunning ? (
        <div className="rounded-2xl border bg-card p-8 text-center">
          <Loader2 className="w-10 h-10 animate-spin text-primary mx-auto mb-4" />
          <h2 className="text-xl font-bold mb-1">Running checks…</h2>
          <p className="text-muted-foreground text-sm">This page updates automatically. Hang tight.</p>
          <div className="mt-4 flex justify-center gap-1">
            {['Domain', 'SSL', 'DNS', 'Website'].map((s) => (
              <span key={s} className="px-2 py-0.5 rounded-full bg-muted text-xs text-muted-foreground">{s}</span>
            ))}
          </div>
        </div>
      ) : score !== null && verdict && (
        <div className={`rounded-2xl border p-8 ${verdict.bg}`}>
          <div className="flex flex-col sm:flex-row items-center gap-6">
            {/* Score ring */}
            <div className="flex-shrink-0 text-center">
              <div className={`w-28 h-28 rounded-full border-8 ${verdict.ring} border-current flex flex-col items-center justify-center`}>
                <span className={`text-4xl font-black ${verdict.color}`}>{score}</span>
                <span className={`text-xs font-semibold ${verdict.color} -mt-1`}>/10</span>
              </div>
              <p className="text-xs text-muted-foreground mt-2">Trust Score</p>
            </div>
            {/* Verdict */}
            <div className="text-center sm:text-left flex-1">
              <p className={`text-2xl font-black mb-1 ${verdict.color}`}>{verdict.label}</p>
              <p className="text-sm text-muted-foreground leading-relaxed">{verdict.sub}</p>
              <div className="flex flex-wrap gap-3 mt-4 justify-center sm:justify-start">
                <div className="flex items-center gap-1.5 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span className="font-semibold">{passed}</span>
                  <span className="text-muted-foreground">passed</span>
                </div>
                <div className="flex items-center gap-1.5 text-sm">
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                  <span className="font-semibold">{warnings}</span>
                  <span className="text-muted-foreground">warning{warnings !== 1 ? 's' : ''}</span>
                </div>
                <div className="flex items-center gap-1.5 text-sm">
                  <XCircle className="w-4 h-4 text-red-600" />
                  <span className="font-semibold">{critical}</span>
                  <span className="text-muted-foreground">critical</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── META ── */}
      <div className="flex flex-wrap items-center gap-3 px-1 text-sm text-muted-foreground">
        <Shield className="w-4 h-4 text-primary" />
        <span className="font-medium text-foreground">{name}</span>
        {verification.processing_time_ms && (
          <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" />{(verification.processing_time_ms / 1000).toFixed(1)}s</span>
        )}
        <span className={`ml-auto px-2 py-0.5 rounded-full text-xs font-medium capitalize
          ${verification.status === 'completed' ? 'bg-green-100 text-green-800' :
            verification.status === 'failed'    ? 'bg-red-100 text-red-800' :
            'bg-amber-100 text-amber-800'}`}>
          {verification.status}
        </span>
      </div>

      {/* ── FINDINGS ── */}
      <div>
        <h3 className="font-semibold mb-3 text-base">
          {findings.length > 0 ? `${findings.length} Evidence Checks` : 'Evidence Checks'}
        </h3>

        {findings.length === 0 ? (
          <div className="rounded-xl border bg-card p-8 text-center text-muted-foreground text-sm">
            No findings yet — checks still running.
          </div>
        ) : (
          <div className="space-y-2">
            {/* critical first, then warnings, then passed, then info */}
            {(['critical', 'warning', 'passed', 'info'] as const).map((sev) => {
              const group = findings.filter(f => f.severity === sev);
              if (group.length === 0) return null;
              return group.map((finding) => {
                const cfg = severityConfig[finding.severity] || severityConfig.info;
                const Icon = cfg.icon;
                return (
                  <div key={finding.id} className="flex items-start gap-3 p-4 rounded-xl border bg-card hover:bg-accent/20 transition-colors">
                    <Icon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${cfg.cls}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-0.5">
                        <span className="font-semibold text-sm">{finding.title}</span>
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${cfg.badge}`}>{cfg.label}</span>
                        <span className="text-[10px] text-muted-foreground capitalize">{finding.category}</span>
                      </div>
                      {finding.description && <p className="text-sm text-muted-foreground leading-relaxed">{finding.description}</p>}
                      {finding.recommendation && (
                        <p className="text-xs mt-1.5 text-amber-700 bg-amber-50 border border-amber-100 rounded-lg px-2.5 py-1.5">
                          💡 <strong>What to do:</strong> {finding.recommendation}
                        </p>
                      )}
                    </div>
                  </div>
                );
              });
            })}
          </div>
        )}
      </div>

      {/* ── TIMELINE (collapsible feel) ── */}
      {verification.timeline?.length > 0 && (
        <div>
          <h3 className="font-semibold mb-3 text-base text-muted-foreground text-sm uppercase tracking-wide">Check Timeline</h3>
          <div className="rounded-xl border bg-card divide-y">
            {verification.timeline.map((event, index) => (
              <div key={event.id} className="flex items-start gap-3 px-4 py-3">
                <div className="w-2 h-2 rounded-full bg-primary mt-1.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{event.title}</p>
                  {event.description && <p className="text-xs text-muted-foreground">{event.description}</p>}
                </div>
                <p className="text-xs text-muted-foreground flex-shrink-0">{new Date(event.timestamp).toLocaleTimeString()}</p>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
