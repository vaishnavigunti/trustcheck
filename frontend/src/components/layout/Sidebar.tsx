'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useRouter } from 'next/navigation';

import { cn } from '@/lib/utils';
import { useAuthStore } from '@/store/auth';
import {
  LayoutDashboard,
  FileCheck,
  FileText,
  History,
  Settings,
  User,
  Shield,
  LogOut,
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/dashboard' as const, icon: LayoutDashboard },
  { name: 'New Verification', href: '/verify' as const, icon: FileCheck },
  { name: 'History', href: '/history' as const, icon: History },
  { name: 'Reports', href: '/reports' as const, icon: FileText },
  { name: 'Profile', href: '/profile' as const, icon: User },
  { name: 'Settings', href: '/settings' as const, icon: Settings },
];

interface SidebarProps {
  className?: string;
}

export function Sidebar({ className }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    document.cookie = 'access_token=; path=/; max-age=0';
    router.push('/login');
  };

  const initials = user?.full_name
    ? user.full_name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
    : user?.email?.[0]?.toUpperCase() ?? 'U';

  return (
    <div className={cn('flex flex-col h-full bg-card border-r', className)}>
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-[18px] border-b">
        <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center shadow-sm flex-shrink-0">
          <Shield className="w-4 h-4 text-primary-foreground" />
        </div>
        <div>
          <span className="font-bold text-sm tracking-tight">TrustCheck</span>
          <p className="text-[10px] text-muted-foreground leading-none mt-0.5">Evidence-Based Verification</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname?.startsWith(item.href));
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
                isActive
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground'
              )}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* User + Logout */}
      <div className="px-3 py-3 border-t space-y-1">
        <Link href="/profile"
          className="flex items-center gap-3 px-3 py-2 rounded-lg bg-muted/50 hover:bg-accent transition-colors cursor-pointer"
          title="Go to Profile">
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-xs font-bold text-primary-foreground flex-shrink-0">
            {initials}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium truncate">{user?.full_name || 'User'}</p>
            <p className="text-[10px] text-muted-foreground truncate">{user?.email}</p>
          </div>
        </Link>
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Sign out
        </button>
      </div>
    </div>
  );
}
