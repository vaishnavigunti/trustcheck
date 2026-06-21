'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/auth';

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  '/dashboard':  { title: 'Dashboard',        subtitle: 'Overview of your verifications'    },
  '/verify':     { title: 'New Verification', subtitle: 'Start a new evidence check'         },
  '/history':    { title: 'History',          subtitle: 'All past verifications'             },
  '/reports':    { title: 'Reports',          subtitle: 'Download your verification reports' },
  '/profile':    { title: 'Profile',          subtitle: 'Manage your account'                },
  '/settings':   { title: 'Settings',         subtitle: 'Application preferences'            },
};

interface HeaderProps { className?: string }

export function Header({ className }: HeaderProps) {
  const { user } = useAuthStore();
  const pathname = usePathname();

  const pageKey = Object.keys(pageTitles).find(
    (k) => pathname === k || (k !== '/dashboard' && pathname?.startsWith(k))
  );
  const page = pageKey ? pageTitles[pageKey] : { title: 'TrustCheck', subtitle: '' };

  const initials = user?.full_name
    ? user.full_name.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2)
    : 'U';

  return (
    <header className={className}>
      <div className="flex items-center justify-between h-14 px-6 border-b bg-card/80 backdrop-blur-sm">
        <div>
          <h1 className="text-sm font-semibold leading-tight">{page.title}</h1>
          {page.subtitle && <p className="text-xs text-muted-foreground">{page.subtitle}</p>}
        </div>
        <Link href="/profile" title="View Profile"
          className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-xs font-bold text-primary-foreground hover:opacity-80 transition-opacity cursor-pointer">
          {initials}
        </Link>
      </div>
    </header>
  );
}
