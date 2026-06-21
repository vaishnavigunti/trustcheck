'use client';

import { useEffect, useState } from 'react';
import { User, Mail, Shield } from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { useAuthStore } from '@/store/auth';
import { api } from '@/lib/api';

interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  email_verified: boolean;
  last_login_at?: string;
  created_at: string;
}

export default function ProfilePage() {
  const { user: authUser } = useAuthStore();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [fullName, setFullName] = useState('');

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await api.get('/auth/me');
        setProfile(res.data);
        setFullName(res.data.full_name);
      } catch (err: any) {
        console.error('Failed to load profile');
      } finally {
        setIsLoading(false);
      }
    };

    fetchProfile();
  }, []);

  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [passwords, setPasswords] = useState({ current: '', new: '', confirm: '' });

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsUpdating(true);
    setMessage(null);
    try {
      await api.patch('/auth/me', { full_name: fullName });
      setMessage('Profile updated successfully');
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Profile update is not yet supported by the server');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (passwords.new !== passwords.confirm) {
      setMessage('New passwords do not match');
      return;
    }
    setIsUpdating(true);
    setMessage(null);
    try {
      await api.post('/auth/change-password', {
        current_password: passwords.current,
        new_password: passwords.new,
      });
      setMessage('Password changed successfully');
      setShowPasswordForm(false);
      setPasswords({ current: '', new: '', confirm: '' });
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Failed to change password');
    } finally {
      setIsUpdating(false);
    }
  };

  if (isLoading) {
    return (
      <div>
        <div className="mb-6">
          <h2 className="text-3xl font-bold tracking-tight">Profile</h2>
          <p className="text-muted-foreground">Manage your account settings</p>
        </div>
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">Loading profile...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-3xl font-bold tracking-tight">Profile</h2>
        <p className="text-muted-foreground">Manage your account settings</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Profile Info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="w-5 h-5" />
              Personal Information
            </CardTitle>
            <CardDescription>Update your personal details</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleUpdate} className="space-y-4">
              {message && (
                <div
                  className={`p-3 text-sm rounded-md ${
                    message.includes('success')
                      ? 'bg-green-100 text-green-800'
                      : 'bg-destructive/10 text-destructive'
                  }`}
                >
                  {message}
                </div>
              )}

              <div className="space-y-2">
                <label className="text-sm font-medium">Email</label>
                <div className="flex items-center gap-2 px-3 py-2 border rounded-md bg-muted">
                  <Mail className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">{profile?.email}</span>
                </div>
                <p className="text-xs text-muted-foreground">Email cannot be changed</p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Full Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md bg-background"
                />
              </div>

              <Button type="submit" className="w-full" disabled={isUpdating}>
                {isUpdating ? 'Updating...' : 'Update Profile'}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Account Stats */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Account Status
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm">Status</span>
                <span
                  className={`px-2 py-1 rounded text-xs font-medium ${
                    profile?.is_active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {profile?.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm">Email Verified</span>
                <span
                  className={`px-2 py-1 rounded text-xs font-medium ${
                    profile?.email_verified
                      ? 'bg-green-100 text-green-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }`}
                >
                  {profile?.email_verified ? 'Verified' : 'Not Verified'}
                </span>
              </div>

              {profile?.last_login_at && (
                <div className="flex items-center justify-between">
                  <span className="text-sm">Last Login</span>
                  <span className="text-sm text-muted-foreground">
                    {new Date(profile.last_login_at).toLocaleString()}
                  </span>
                </div>
              )}

              <div className="flex items-center justify-between">
                <span className="text-sm">Member Since</span>
                <span className="text-sm text-muted-foreground">
                  {profile?.created_at && new Date(profile.created_at).toLocaleDateString()}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Security</CardTitle>
              <CardDescription>Manage your password</CardDescription>
            </CardHeader>
            <CardContent>
              {!showPasswordForm ? (
                <Button variant="outline" className="w-full" onClick={() => setShowPasswordForm(true)}>
                  Change Password
                </Button>
              ) : (
                <form onSubmit={handleChangePassword} className="space-y-3">
                  {['current', 'new', 'confirm'].map((field) => (
                    <input
                      key={field}
                      type="password"
                      placeholder={field === 'current' ? 'Current password' : field === 'new' ? 'New password' : 'Confirm new password'}
                      value={(passwords as any)[field]}
                      onChange={(e) => setPasswords({ ...passwords, [field]: e.target.value })}
                      className="w-full px-3 py-2 border rounded-md bg-background text-sm"
                      required
                      minLength={field === 'new' ? 8 : undefined}
                    />
                  ))}
                  <div className="flex gap-2">
                    <Button type="submit" size="sm" disabled={isUpdating}>
                      {isUpdating ? 'Saving...' : 'Update'}
                    </Button>
                    <Button type="button" variant="outline" size="sm" onClick={() => setShowPasswordForm(false)}>
                      Cancel
                    </Button>
                  </div>
                </form>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
