'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Building2, UserCheck, FileText, Globe, Upload, X, ArrowRight, Loader2, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

type VerifType = 'company' | 'recruiter' | 'offer_letter' | 'website';

const types: { id: VerifType; label: string; desc: string; icon: React.ElementType; emoji: string; hint: string }[] = [
  { id: 'company',      label: 'Company',      emoji: '🏢', desc: 'Verify company legitimacy and registration',   icon: Building2, hint: 'We check domain age, SSL certificate, DNS records, and website legitimacy signals.' },
  { id: 'recruiter',    label: 'Recruiter',    emoji: '👤', desc: 'Validate recruiter identity and email domain', icon: UserCheck, hint: 'We verify the email domain matches the company and check for known spam patterns.' },
  { id: 'offer_letter', label: 'Offer Letter', emoji: '📄', desc: 'Analyse an uploaded offer letter PDF',        icon: FileText,  hint: 'Upload a PDF offer letter — we extract and cross-check company details, salary data, and document authenticity.' },
  { id: 'website',      label: 'Website',      emoji: '🌐', desc: 'Perform full trust and security analysis',    icon: Globe,     hint: 'Full DNS, SSL, WHOIS, and content trust analysis for any website URL.' },
];

export default function VerifyPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verType, setVerType] = useState<VerifType>('company');
  const [formData, setFormData] = useState({ target_url: '', recruiter_email: '', company_name: '' });
  const [file, setFile] = useState<File | null>(null);

  const selected = types.find((t) => t.id === verType)!;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      let fileId = null;
      if (file) {
        const fd = new FormData();
        fd.append('file', file);
        const up = await api.post('/verifications/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
        fileId = up.data.file_id;
      }

      const res = await api.post('/verifications/', {
        verification_type: verType,
        target_url: formData.target_url || undefined,
        recruiter_email: formData.recruiter_email || undefined,
        company_name: formData.company_name || undefined,
        file_id: fileId,
      });

      router.push(`/verify/${res.data.id}`);
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.response?.data?.detail || 'Verification failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const needsUrl = verType === 'company' || verType === 'website';
  const needsEmail = verType === 'recruiter';
  const needsPdf = verType === 'offer_letter';

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-in">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight mb-1">New Verification</h2>
        <p className="text-muted-foreground text-sm">Choose what you want to verify, fill in the details, and we&apos;ll run the checks automatically.</p>
      </div>

      {/* Type selector — larger premium cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {types.map(({ id, label, desc, emoji }) => (
          <button
            key={id}
            type="button"
            onClick={() => { setVerType(id); setError(null); }}
            className={cn(
              'flex flex-col items-start gap-3 p-4 rounded-2xl border-2 text-left transition-all duration-150 cursor-pointer',
              'hover:-translate-y-0.5 hover:shadow-md',
              verType === id
                ? 'border-primary bg-primary/5 shadow-sm'
                : 'border-border hover:border-primary/40 bg-card'
            )}
          >
            <span className="text-2xl">{emoji}</span>
            <div>
              <p className="text-sm font-semibold leading-tight">{label}</p>
              <p className="text-[11px] text-muted-foreground leading-snug mt-0.5">{desc}</p>
            </div>
            {verType === id && (
              <span className="text-[10px] font-semibold bg-primary text-primary-foreground px-2 py-0.5 rounded-full">Selected</span>
            )}
          </button>
        ))}
      </div>

      {/* Info hint */}
      <div className="flex items-start gap-2.5 px-4 py-3 rounded-xl bg-blue-50 border border-blue-100 text-sm text-blue-800">
        <span className="text-base flex-shrink-0">ℹ️</span>
        <p className="leading-relaxed">{selected.hint}</p>
      </div>

      {/* Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <selected.icon className="w-5 h-5 text-primary" />
            {selected.label} Verification
          </CardTitle>
          <CardDescription>Fill in the details below to start the automated check.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="flex items-start gap-2 p-3 text-sm text-destructive bg-destructive/10 rounded-lg">
                <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                {error}
              </div>
            )}

            {(needsUrl || verType === 'offer_letter') && (
              <div className="space-y-1.5">
                <label className="text-sm font-medium">
                  Company Website {needsUrl ? <span className="text-destructive">*</span> : <span className="text-muted-foreground font-normal">(optional)</span>}
                </label>
                <input
                  type="url"
                  placeholder="https://company.com"
                  value={formData.target_url}
                  onChange={(e) => setFormData({ ...formData, target_url: e.target.value })}
                  className="w-full px-3 py-2.5 border rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 transition-shadow"
                  required={needsUrl}
                />
                <p className="text-[11px] text-muted-foreground">Enter the official company website URL starting with https://</p>
              </div>
            )}

            {needsEmail && (
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Recruiter Email <span className="text-destructive">*</span></label>
                <input
                  type="email"
                  placeholder="recruiter@company.com"
                  value={formData.recruiter_email}
                  onChange={(e) => setFormData({ ...formData, recruiter_email: e.target.value })}
                  className="w-full px-3 py-2.5 border rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 transition-shadow"
                  required
                />
                <p className="text-[11px] text-muted-foreground">The email address the recruiter used to contact you</p>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-sm font-medium">Company Name <span className="text-muted-foreground font-normal">(optional)</span></label>
              <input
                type="text"
                placeholder="Acme Corporation"
                value={formData.company_name}
                onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                className="w-full px-3 py-2.5 border rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 transition-shadow"
              />
              <p className="text-[11px] text-muted-foreground">Helps us identify and label this verification in your history</p>
            </div>

            {needsPdf && (
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Offer Letter PDF *</label>
                {!file ? (
                  <label className="flex flex-col items-center justify-center gap-2 p-8 border-2 border-dashed rounded-lg cursor-pointer hover:bg-accent/30 transition-colors">
                    <Upload className="w-6 h-6 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Click to upload PDF</span>
                    <span className="text-xs text-muted-foreground">Max 10MB</span>
                    <input type="file" accept=".pdf" className="hidden" required={needsPdf} onChange={(e) => setFile(e.target.files?.[0] || null)} />
                  </label>
                ) : (
                  <div className="flex items-center gap-3 p-3 border rounded-lg bg-muted/30">
                    <FileText className="w-5 h-5 text-primary flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{file.name}</p>
                      <p className="text-xs text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                    <button type="button" onClick={() => setFile(null)} className="text-muted-foreground hover:text-destructive">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            )}

            {!needsPdf && (
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Offer Letter PDF <span className="text-muted-foreground font-normal">(optional)</span></label>
                {!file ? (
                  <label className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-accent/30 transition-colors">
                    <Upload className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Upload PDF for extra analysis</span>
                    <input type="file" accept=".pdf" className="hidden" onChange={(e) => setFile(e.target.files?.[0] || null)} />
                  </label>
                ) : (
                  <div className="flex items-center gap-3 p-3 border rounded-lg bg-muted/30">
                    <FileText className="w-5 h-5 text-primary flex-shrink-0" />
                    <span className="text-sm flex-1 truncate">{file.name}</span>
                    <button type="button" onClick={() => setFile(null)} className="text-muted-foreground hover:text-destructive">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            )}

            <Button type="submit" className="w-full gap-2 h-11" disabled={isLoading}>
              {isLoading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Starting verification...</>
              ) : (
                <>Start Verification <ArrowRight className="w-4 h-4" /></>
              )}
            </Button>

            <p className="text-xs text-center text-muted-foreground">
              Checks run in the background — results appear automatically on the next page.
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
