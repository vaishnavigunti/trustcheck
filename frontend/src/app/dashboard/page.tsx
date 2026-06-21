'use client';

import { useEffect, useState } from 'react';
import {
  FileCheck, FileText, History, Shield, CheckCircle,
  AlertTriangle, Clock, TrendingUp, BarChart3, Plus, ArrowRight,
  Building2, UserCheck, Globe, Zap,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { useAuthStore } from '@/store/auth';
import { api } from '@/lib/api';
import Link from 'next/link';
import { format } from 'date-fns';

interface Verification {
  id: string;
  verification_type: string;
  target_url?: string;
  company_name?: string;
  recruiter_email?: string;
  status: string;
  created_at: string;
}

// ── helpers ───────────────────────────────────────────────────────────────────
function getGreeting(name?: string) {
  const h = new Date().getHours();
  const salutation = h < 12 ? 'Good Morning' : h < 17 ? 'Good Afternoon' : 'Good Evening';
  return `${salutation}${name ? `, ${name.split(' ')[0]}` : ''} 👋`;
}

function typeLabel(t: string) {
  return { company: 'Company', recruiter: 'Recruiter', offer_letter: 'Offer Letter', website: 'Website' }[t] ?? t;
}
function typeIcon(t: string) {
  const cls = 'w-4 h-4';
  if (t === 'company')      return <Building2 className={cls} />;
  if (t === 'recruiter')    return <UserCheck className={cls} />;
  if (t === 'offer_letter') return <FileText className={cls} />;
  return <Globe className={cls} />;
}
function displayName(v: Verification) {
  if (v.company_name) return v.company_name;
  if (v.recruiter_email) return v.recruiter_email;
  if (v.target_url) {
    try { return new URL(v.target_url).hostname.replace(/^www\./, ''); } catch { return v.target_url; }
  }
  return `${typeLabel(v.verification_type)} Verification`;
}

// ── page ──────────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const { user } = useAuthStore();
  const [items, setItems]   = useState<Verification[]>([]);
  const [reports, setReports] = useState(0);
  const [thisMonth, setThisMonth] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [verRes, repRes, sumRes] = await Promise.all([
          api.get('/verifications/').catch(() => ({ data: { items: [] } })),
          api.get('/reports/').catch(() => ({ data: { items: [] } })),
          api.get('/verifications/summary').catch(() => ({ data: { this_month: 0 } })),
        ]);
        setItems(verRes.data.items || []);
        setReports((repRes.data.items || []).length);
        setThisMonth(sumRes.data?.this_month ?? 0);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const total     = items.length;
  const completed = items.filter(v => v.status === 'completed').length;
  const pending   = items.filter(v => v.status === 'pending' || v.status === 'in_progress').length;
  const failed    = items.filter(v => v.status === 'failed').length;
  const successRate = total > 0 ? Math.round((completed / total) * 100) : 0;
  const trustScore  = total > 0 ? Math.min(100, Math.round(successRate * 0.92 + (failed === 0 ? 8 : 0))) : 0;

  // Breakdown by type
  const byType = ['company', 'recruiter', 'offer_letter', 'website'].map(t => ({
    t, label: typeLabel(t), count: items.filter(v => v.verification_type === t).length,
  }));
  const maxCount = Math.max(...byType.map(b => b.count), 1);

  // Recent (last 5)
  const recent = [...items].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 5);

  // Activity feed (last 4 events from recent)
  const activity = recent.slice(0, 4).map(v => ({
    id: v.id,
    text: v.status === 'completed'
      ? `${typeLabel(v.verification_type)} verification completed`
      : v.status === 'failed'
      ? `${typeLabel(v.verification_type)} verification failed`
      : `${typeLabel(v.verification_type)} verification started`,
    time: format(new Date(v.created_at), 'MMM d, h:mm a'),
    color: v.status === 'completed' ? 'bg-green-500' : v.status === 'failed' ? 'bg-red-500' : 'bg-amber-400',
  }));

  // ── skeleton ──
  if (loading) {
    return (
      <div className="space-y-6 p-1">
        <div className="flex items-start justify-between">
          <div className="space-y-2"><div className="skeleton h-8 w-64 rounded-lg"/><div className="skeleton h-4 w-80 rounded-lg"/></div>
          <div className="skeleton h-10 w-40 rounded-xl"/>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_,i) => <div key={i} className="skeleton h-28 rounded-2xl"/>)}
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_,i) => <div key={i} className="skeleton h-20 rounded-2xl"/>)}
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="skeleton h-64 rounded-2xl lg:col-span-2"/>
          <div className="skeleton h-64 rounded-2xl"/>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in">

      {/* ── Greeting + CTA ── */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">{getGreeting(user?.full_name)}</h2>
          <p className="text-muted-foreground mt-1 text-sm">Verify internship opportunities and job offers with confidence.</p>
        </div>
        <Link href="/verify" className="flex-shrink-0">
          <Button className="gap-2 h-10 px-5 shadow-sm">
            <Plus className="w-4 h-4" /> New Verification
          </Button>
        </Link>
      </div>

      {/* ── KPI cards ── */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          {
            title: 'Total Verifications', value: total,
            sub: `+${thisMonth} this month`,
            icon: Shield, iconBg: 'bg-blue-50', iconCl: 'text-blue-600',
          },
          {
            title: 'Completed', value: completed,
            sub: `${successRate}% success rate`,
            icon: CheckCircle, iconBg: 'bg-green-50', iconCl: 'text-green-600',
          },
          {
            title: 'Reports Generated', value: reports,
            sub: 'Available for download',
            icon: FileText, iconBg: 'bg-indigo-50', iconCl: 'text-indigo-600',
          },
          {
            title: 'Pending', value: pending,
            sub: pending === 0 ? 'All clear' : 'Awaiting analysis',
            icon: Clock, iconBg: 'bg-amber-50', iconCl: 'text-amber-600',
          },
        ].map(({ title, value, sub, icon: Icon, iconBg, iconCl }) => (
          <Card key={title} className="hover:shadow-md transition-shadow duration-200">
            <CardContent className="p-5">
              <div className="flex items-start justify-between mb-3">
                <p className="text-xs font-medium text-muted-foreground">{title}</p>
                <div className={`w-8 h-8 rounded-lg ${iconBg} flex items-center justify-center`}>
                  <Icon className={`w-4 h-4 ${iconCl}`} />
                </div>
              </div>
              <p className="text-3xl font-bold tracking-tight">{value}</p>
              <p className="text-xs text-muted-foreground mt-1">{sub}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* ── Trust metrics row ── */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          {
            label: 'Trust Score', value: total > 0 ? `${trustScore}/100` : '—',
            badge: trustScore >= 80 ? 'bg-green-100 text-green-800' : trustScore >= 60 ? 'bg-amber-100 text-amber-800' : 'bg-red-100 text-red-800',
            badgeText: trustScore >= 80 ? 'Low Risk' : trustScore >= 60 ? 'Medium Risk' : total === 0 ? 'No Data' : 'High Risk',
            icon: Shield, iconCl: 'text-blue-500',
          },
          {
            label: 'Success Rate', value: total > 0 ? `${successRate}%` : '—',
            badge: 'bg-green-100 text-green-800', badgeText: 'This session',
            icon: TrendingUp, iconCl: 'text-green-500',
          },
          {
            label: 'This Month', value: thisMonth,
            badge: 'bg-blue-100 text-blue-800', badgeText: 'Verifications',
            icon: Zap, iconCl: 'text-amber-500',
          },
          {
            label: 'Failed', value: failed,
            badge: failed === 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800',
            badgeText: failed === 0 ? 'All clear' : 'Needs review',
            icon: AlertTriangle, iconCl: 'text-red-500',
          },
        ].map(({ label, value, badge, badgeText, icon: Icon, iconCl }) => (
          <div key={label} className="flex items-center gap-3 px-4 py-3 rounded-xl border bg-card hover:shadow-sm transition-shadow">
            <Icon className={`w-5 h-5 flex-shrink-0 ${iconCl}`} />
            <div className="flex-1 min-w-0">
              <p className="text-[11px] text-muted-foreground font-medium">{label}</p>
              <p className="text-xl font-bold leading-tight">{value}</p>
            </div>
            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap ${badge}`}>{badgeText}</span>
          </div>
        ))}
      </div>

      {/* ── Bottom grid ── */}
      <div className="grid gap-4 lg:grid-cols-3">

        {/* Recent Verifications */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-sm font-semibold">Recent Verifications</CardTitle>
            <Link href="/history" className="text-xs text-primary hover:underline flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </CardHeader>
          <CardContent className="pt-0">
            {recent.length === 0 ? (
              <div className="text-center py-10">
                <Shield className="w-10 h-10 text-muted-foreground/30 mx-auto mb-3" />
                <p className="text-sm text-muted-foreground font-medium">No verifications yet</p>
                <Link href="/verify">
                  <Button size="sm" className="mt-3 gap-1.5"><Plus className="w-3.5 h-3.5"/> Start your first one</Button>
                </Link>
              </div>
            ) : (
              <div className="divide-y">
                {recent.map((v) => (
                  <Link key={v.id} href={`/verify/${v.id}`}>
                    <div className="flex items-center gap-3 py-3 hover:bg-accent/30 -mx-2 px-2 rounded-lg transition-colors cursor-pointer">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0
                        ${v.status === 'completed' ? 'bg-green-50 text-green-600' :
                          v.status === 'failed'    ? 'bg-red-50 text-red-600' :
                          'bg-amber-50 text-amber-600'}`}>
                        {typeIcon(v.verification_type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{displayName(v)}</p>
                        <p className="text-xs text-muted-foreground">
                          {typeLabel(v.verification_type)} · {format(new Date(v.created_at), 'MMM d, yyyy')}
                        </p>
                      </div>
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full capitalize flex-shrink-0
                        ${v.status === 'completed' ? 'bg-green-100 text-green-800' :
                          v.status === 'failed'    ? 'bg-red-100 text-red-800' :
                          'bg-amber-100 text-amber-800'}`}>
                        {v.status === 'in_progress' ? 'running' : v.status}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right column */}
        <div className="space-y-4">

          {/* Verification Breakdown */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-primary" /> Breakdown by Type
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0 space-y-3">
              {byType.map(({ t, label, count }) => (
                <div key={t}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">{label}</span>
                    <span className="font-semibold">{count}</span>
                  </div>
                  <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all duration-500"
                      style={{ width: `${(count / maxCount) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
              {total === 0 && <p className="text-xs text-muted-foreground text-center py-2">Run a verification to see breakdown</p>}
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold">Recent Activity</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {activity.length === 0 ? (
                <p className="text-xs text-muted-foreground text-center py-3">No activity yet</p>
              ) : (
                <div className="space-y-3">
                  {activity.map((a) => (
                    <div key={a.id} className="flex items-start gap-2.5">
                      <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${a.color}`} />
                      <div>
                        <p className="text-xs font-medium leading-snug">{a.text}</p>
                        <p className="text-[10px] text-muted-foreground mt-0.5">{a.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

        </div>
      </div>

      {/* ── Quick links row ── */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { href: '/verify',   icon: FileCheck, label: 'New Verification', cl: 'text-blue-600 bg-blue-50' },
          { href: '/history',  icon: History,   label: 'View History',     cl: 'text-indigo-600 bg-indigo-50' },
          { href: '/reports',  icon: FileText,  label: 'Reports',          cl: 'text-violet-600 bg-violet-50' },
        ].map(({ href, icon: Icon, label, cl }) => (
          <Link key={href} href={href}>
            <div className="flex items-center gap-2.5 p-3 rounded-xl border bg-card hover:shadow-sm hover:-translate-y-0.5 transition-all duration-150 cursor-pointer">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${cl}`}>
                <Icon className="w-4 h-4" />
              </div>
              <span className="text-sm font-medium">{label}</span>
            </div>
          </Link>
        ))}
      </div>

    </div>
  );
}
