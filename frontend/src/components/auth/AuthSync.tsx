'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/store/auth';

export function AuthSync() {
  const { accessToken, hasHydrated } = useAuthStore();

  useEffect(() => {
    if (!hasHydrated) return;

    if (accessToken) {
      document.cookie = `access_token=${accessToken}; path=/; max-age=900; samesite=lax`;
    } else {
      document.cookie = 'access_token=; path=/; max-age=0';
    }
  }, [accessToken, hasHydrated]);

  return null;
}
