'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Shield, Eye, EyeOff, AlertTriangle, Loader2, ArrowRight } from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { useAuthStore } from '@/store/auth';

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading, error, clearError } = useAuthStore();

  const [formData, setFormData] = useState({ email: '', password: '' });
  const [showPwd, setShowPwd] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    try {
      await login(formData);
      const stored = localStorage.getItem('auth-storage');
      if (stored) {
        const token = JSON.parse(stored)?.state?.accessToken;
        if (token) document.cookie = `access_token=${token}; path=/; max-age=900; samesite=lax`;
      }
      router.push('/dashboard');
    } catch (err) {
      // Error handled by store
    }
  };

  const inputCls = 'w-full px-3 py-2.5 border rounded-lg bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 transition-shadow';

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-primary flex items-center justify-center shadow-md mb-3">
            <Shield className="w-6 h-6 text-primary-foreground" />
          </div>
          <h1 className="text-xl font-bold">TrustCheck</h1>
          <p className="text-xs text-muted-foreground mt-0.5">Evidence-Based Verification</p>
        </div>

        <Card className="shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl">Welcome back</CardTitle>
            <CardDescription>Sign in to your account to continue.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="flex flex-col gap-1.5 p-3 text-sm text-destructive bg-destructive/10 rounded-lg">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span>{error}</span>
                  </div>
                  {(error.toLowerCase().includes('server') || error.toLowerCase().includes('connect')) && (
                    <p className="text-xs text-muted-foreground pl-6">
                      Make sure the backend is running: <code className="bg-muted px-1 rounded">uvicorn main:app --reload</code>
                    </p>
                  )}
                </div>
              )}

              <div className="space-y-1.5">
                <label htmlFor="email" className="text-sm font-medium">Email address</label>
                <input id="email" type="email" placeholder="jane@example.com" value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className={inputCls} required autoComplete="email" />
              </div>

              <div className="space-y-1.5">
                <label htmlFor="password" className="text-sm font-medium">Password</label>
                <div className="relative">
                  <input id="password" type={showPwd ? 'text' : 'password'} placeholder="Your password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className={inputCls + ' pr-10'} required autoComplete="current-password" />
                  <button type="button" onClick={() => setShowPwd(!showPwd)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                    {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <Button type="submit" className="w-full h-11 gap-2" disabled={isLoading}>
                {isLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> Signing in…</> : <>Sign in <ArrowRight className="w-4 h-4" /></>}
              </Button>
            </form>

            <p className="mt-5 text-center text-sm text-muted-foreground">
              Don&apos;t have an account?{' '}
              <Link href="/register" className="text-primary font-medium hover:underline">Create one free</Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
