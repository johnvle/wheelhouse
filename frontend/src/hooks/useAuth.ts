// Minimal auth stub — US-018 will replace with Supabase Auth
// For now, returns a dummy user so the app is accessible during development

import { useState } from "react";

interface AuthUser {
  id: string;
  email: string;
}

interface AuthState {
  user: AuthUser | null;
  loading: boolean;
}

export function useAuth(): AuthState {
  // TODO: Replace with Supabase auth context in US-018
  const [state] = useState<AuthState>({
    user: { id: "dev-user", email: "dev@localhost" },
    loading: false,
  });
  return state;
}
