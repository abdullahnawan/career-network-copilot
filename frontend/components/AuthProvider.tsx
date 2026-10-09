"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { authApi, CurrentUser, formatApiError, profileApi, StudentProfile, UnauthorizedError } from "../lib/api";

type AuthContextValue = {
  user: CurrentUser | null;
  profile: StudentProfile | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    setLoading(true);
    try {
      const current = await authApi.me();
      setUser(current);
      setProfile(current.profile ?? await profileApi.current().catch((e) => {
        if (e instanceof UnauthorizedError) throw e;
        return null;
      }));
      setError(null);
    } catch (e) {
      if (e instanceof UnauthorizedError) {
        setUser(null); setProfile(null); setError(null);
      } else setError(formatApiError(e, "Unable to load your account."));
    } finally { setLoading(false); }
  };

  useEffect(() => {
    const timer = window.setTimeout(() => { void refresh(); }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user, profile, loading, error,
    login: async (email, password) => {
      const next = await authApi.login(email, password);
      setUser(next);
      setProfile(next.profile ?? await profileApi.current().catch(() => null));
    },
    register: async (email, password, fullName) => {
      const next = await authApi.register(email, password, fullName);
      setUser(next);
      setProfile(next.profile ?? await profileApi.current().catch(() => null));
    },
    logout: async () => { try { await authApi.logout(); } finally { setUser(null); setProfile(null); } },
    refresh,
  }), [user, profile, loading, error]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  // Keeps presentational components usable in isolated unit tests.
  return context ?? {
    user: { id: 0, email: "guest@example.com", display_name: "Guest" }, profile: null, loading: false, error: null,
    login: async () => {}, register: async () => {}, logout: async () => {}, refresh: async () => {},
  };
}
