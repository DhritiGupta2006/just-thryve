import React from 'react';
import { User } from '../types';
import { authApi, setToken, clearToken, getToken, ApiError } from '../services/api';

interface AuthContextType {
  user: User | null;
  login: (credentials: { email: string; password: string }) => Promise<void>;
  signup: (payload: {
    name: string;
    email: string;
    password: string;
    role: 'BORROWER' | 'LENDER';
    business_name?: string;
    sector?: string;
  }) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  authError: string | null;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

const USER_KEY = 'greenflow_user';

function savedUser(): User | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User | null>(savedUser);
  const [authError, setAuthError] = React.useState<string | null>(null);

  // On mount, re-validate a stored token to keep the user session fresh.
  React.useEffect(() => {
    if (getToken() && !user) {
      authApi.me().then((profile) => {
        const u: User = {
          id: profile.user_id,
          name: profile.name,
          email: profile.email,
          role: profile.role.toUpperCase() as 'BORROWER' | 'LENDER',
        };
        setUser(u);
        localStorage.setItem(USER_KEY, JSON.stringify(u));
      }).catch(() => {
        clearToken();
        localStorage.removeItem(USER_KEY);
        setUser(null);
      });
    }
    // This effect is intentionally run only on mount to revalidate any token
    // that survived a page reload. The `user` check is a snapshot guard, not
    // a reactive dependency; eslint-disable would hide a real warning so we
    // use an empty array and acknowledge the pattern here.
  }, []); // mount-only: revalidates persisted JWT on initial page load

  const login = async (credentials: { email: string; password: string }) => {
    setAuthError(null);
    try {
      const resp = await authApi.login({
        email: credentials.email,
        password: credentials.password,
      });
      setToken(resp.token);

      // Fetch full profile to get the display name
      const profile = await authApi.me();
      const u: User = {
        id: profile.user_id,
        name: profile.name,
        email: profile.email,
        role: profile.role.toUpperCase() as 'BORROWER' | 'LENDER',
      };
      setUser(u);
      localStorage.setItem(USER_KEY, JSON.stringify(u));
    } catch (err) {
      const message = err instanceof ApiError ? err.detail : 'Login failed. Please try again.';
      setAuthError(message);
      throw err;
    }
  };

  const signup = async (payload: {
    name: string;
    email: string;
    password: string;
    role: 'BORROWER' | 'LENDER';
    business_name?: string;
    sector?: string;
  }) => {
    setAuthError(null);
    try {
      const resp = await authApi.signup({
        name: payload.name,
        email: payload.email,
        password: payload.password,
        role: payload.role.toLowerCase(),
        business_name: payload.business_name,
        sector: payload.sector,
      });
      setToken(resp.token);

      const profile = await authApi.me();
      const u: User = {
        id: profile.user_id,
        name: profile.name,
        email: profile.email,
        role: profile.role.toUpperCase() as 'BORROWER' | 'LENDER',
        businessName: payload.business_name,
      };
      setUser(u);
      localStorage.setItem(USER_KEY, JSON.stringify(u));
    } catch (err) {
      const message = err instanceof ApiError ? err.detail : 'Sign-up failed. Please try again.';
      setAuthError(message);
      throw err;
    }
  };

  const logout = () => {
    clearToken();
    localStorage.removeItem(USER_KEY);
    setUser(null);
    setAuthError(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, isAuthenticated: !!user, authError }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = React.useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
