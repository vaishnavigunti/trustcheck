import Link from 'next/link';
import { Shield, Globe, Lock, FileText, CheckCircle, AlertTriangle, ArrowRight, Zap, Search, BarChart3 } from 'lucide-react';
import { Button } from '@/components/ui/Button';

const features = [
  {
    icon: Globe,
    title: 'Domain Verification',
    desc: 'Check domain registration age, ownership, and SSL certificates in real time.',
    color: 'text-blue-600',
    bg: 'bg-blue-50',
  },
  {
    icon: Lock,
    title: 'SSL & Security',
    desc: 'Validate HTTPS, certificate authority, and encryption standards.',
    color: 'text-green-600',
    bg: 'bg-green-50',
  },
  {
    icon: Search,
    title: 'DNS Analysis',
    desc: 'Deep-dive into DNS records to detect spoofed or suspicious domains.',
    color: 'text-purple-600',
    bg: 'bg-purple-50',
  },
  {
    icon: FileText,
    title: 'PDF Offer Analysis',
    desc: 'Extract and cross-reference data from offer letters to flag inconsistencies.',
    color: 'text-orange-600',
    bg: 'bg-orange-50',
  },
  {
    icon: Zap,
    title: 'Instant Results',
    desc: 'Get a full verification report with evidence findings in under 60 seconds.',
    color: 'text-yellow-600',
    bg: 'bg-yellow-50',
  },
  {
    icon: BarChart3,
    title: 'Detailed Reports',
    desc: 'Download PDF reports with all findings, timeline, and recommendations.',
    color: 'text-rose-600',
    bg: 'bg-rose-50',
  },
];

const steps = [
  { num: '01', title: 'Enter Details', desc: 'Provide the company website, recruiter email, or upload an offer letter PDF.' },
  { num: '02', title: 'Run Checks', desc: 'TrustCheck performs domain, SSL, DNS, and website analysis automatically.' },
  { num: '03', title: 'Review Findings', desc: 'Get a colour-coded report with passed checks, warnings, and critical flags.' },
  { num: '04', title: 'Download Report', desc: 'Save the full PDF evidence report for your records or to share.' },
];

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Navbar */}
      <header className="sticky top-0 z-50 border-b bg-card/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center shadow-sm">
              <Shield className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-bold text-lg tracking-tight">TrustCheck</span>
          </div>
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-muted-foreground">
            <a href="#features" className="hover:text-foreground transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-foreground transition-colors">How it works</a>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" size="sm">Sign in</Button>
            </Link>
            <Link href="/register">
              <Button size="sm" className="gap-1.5">
                Get Started <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero */}
        <section className="relative py-24 md:py-36 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent pointer-events-none" />
          <div className="container mx-auto px-4 text-center relative">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border bg-card text-xs font-medium text-muted-foreground mb-6">
              <CheckCircle className="w-3.5 h-3.5 text-green-600" />
              Evidence-based · Real-time checks · Instant reports
            </div>
            <h1 className="text-4xl sm:text-5xl md:text-7xl font-bold tracking-tight mb-6 leading-tight">
              Verify Before You
              <span className="text-primary"> Trust</span>
            </h1>
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
              Protect yourself from fake internships, fraudulent recruiters, and scam job offers.
              TrustCheck runs automated, objective evidence checks so you can decide with confidence.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link href="/register">
                <Button size="lg" className="gap-2 px-8">
                  Start Verifying Free
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
              <Link href="/login">
                <Button size="lg" variant="outline" className="px-8">
                  Sign In
                </Button>
              </Link>
            </div>

            {/* Trust indicators */}
            <div className="flex flex-wrap justify-center gap-6 mt-14 text-sm text-muted-foreground">
              {['Domain & DNS checks', 'SSL verification', 'PDF analysis', 'Instant report PDF'].map((item) => (
                <div key={item} className="flex items-center gap-1.5">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  {item}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Stats bar */}
        <section className="border-y bg-card">
          <div className="container mx-auto px-4 py-8">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
              {[
                { value: '15+', label: 'Evidence checks per verification' },
                { value: '< 60s', label: 'Average time to complete' },
                { value: '100%', label: 'Automated, no human bias' },
                { value: 'PDF', label: 'Downloadable evidence report' },
              ].map(({ value, label }) => (
                <div key={label}>
                  <div className="text-2xl md:text-3xl font-bold text-primary">{value}</div>
                  <div className="text-xs text-muted-foreground mt-1">{label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features */}
        <section id="features" className="py-20 md:py-28">
          <div className="container mx-auto px-4">
            <div className="text-center mb-14">
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">Everything you need to stay safe</h2>
              <p className="text-muted-foreground max-w-xl mx-auto">
                TrustCheck runs a full battery of automated checks and compiles every result into a clear, evidence-backed report.
              </p>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
              {features.map(({ icon: Icon, title, desc, color, bg }) => (
                <div key={title} className="p-6 rounded-2xl border bg-card hover:shadow-md transition-shadow">
                  <div className={`w-10 h-10 rounded-xl ${bg} flex items-center justify-center mb-4`}>
                    <Icon className={`w-5 h-5 ${color}`} />
                  </div>
                  <h3 className="font-semibold mb-2">{title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* How it works */}
        <section id="how-it-works" className="py-20 md:py-28 bg-muted/30">
          <div className="container mx-auto px-4">
            <div className="text-center mb-14">
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">How TrustCheck works</h2>
              <p className="text-muted-foreground max-w-xl mx-auto">Four simple steps to a full verification report.</p>
            </div>
            <div className="grid md:grid-cols-4 gap-8 max-w-4xl mx-auto">
              {steps.map(({ num, title, desc }) => (
                <div key={num} className="text-center">
                  <div className="w-12 h-12 rounded-2xl bg-primary/10 text-primary font-bold text-lg flex items-center justify-center mx-auto mb-4">
                    {num}
                  </div>
                  <h3 className="font-semibold mb-2">{title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Warning section */}
        <section className="py-20">
          <div className="container mx-auto px-4">
            <div className="max-w-3xl mx-auto rounded-2xl border border-amber-200 bg-amber-50 p-8 md:p-10">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center flex-shrink-0">
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-amber-900 mb-2">Scam job offers are on the rise</h3>
                  <p className="text-sm text-amber-800 leading-relaxed mb-4">
                    Fraudulent recruiters impersonate legitimate companies with convincing offer letters and professional-looking emails.
                    Always verify before sharing personal information or paying any fees.
                  </p>
                  <Link href="/register">
                    <Button size="sm" className="bg-amber-600 hover:bg-amber-700 text-white gap-1.5">
                      Verify Now — It&apos;s Free <ArrowRight className="w-3.5 h-3.5" />
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-20 md:py-28 bg-primary">
          <div className="container mx-auto px-4 text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-primary-foreground mb-4">Ready to verify?</h2>
            <p className="text-primary-foreground/80 max-w-xl mx-auto mb-8">
              Create a free account and run your first verification in under a minute.
            </p>
            <Link href="/register">
              <Button size="lg" variant="secondary" className="gap-2 px-10">
                Get Started Free <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t bg-card py-10">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center">
                <Shield className="w-4 h-4 text-primary-foreground" />
              </div>
              <span className="font-semibold">TrustCheck</span>
            </div>
            <p className="text-sm text-muted-foreground">Evidence-Based Internship &amp; Job Offer Verification</p>
            <div className="flex gap-4 text-sm text-muted-foreground">
              <Link href="/login" className="hover:text-foreground transition-colors">Sign in</Link>
              <Link href="/register" className="hover:text-foreground transition-colors">Register</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

