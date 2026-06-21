import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthSync } from '@/components/auth/AuthSync';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'TrustCheck - Evidence-Based Internship & Job Offer Verification',
  description:
    'Verify internship opportunities, recruiter emails, and job offers using objective, evidence-based checks.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans`}>
        <AuthSync />
        {children}
      </body>
    </html>
  );
}
