import {
  createContext,
  PropsWithChildren,
  useContext,
  useEffect,
  useMemo,
  useState
} from "react";
import { api, AuthSessionTokens, registerAuthHandlers } from "../api/client";
import { LoginResponse, User } from "../api/types";


const SESSION_STORAGE_KEY = "lesson-review-auth-session";

interface RegisterPayload {
  username: string;
  email: string;
  display_name: string;
  password: string;
  password_confirm: string;
  organization: string;
  title: string;
  role: string;
}

interface AuthContextValue {
  user: User | null;
  tokens: AuthSessionTokens | null;
  isAuthenticated: boolean;
  isBootstrapping: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function loadStoredSession(): { user: User | null; tokens: AuthSessionTokens | null } {
  const raw = window.localStorage.getItem(SESSION_STORAGE_KEY);
  if (!raw) {
    return { user: null, tokens: null };
  }

  try {
    return JSON.parse(raw) as { user: User | null; tokens: AuthSessionTokens | null };
  } catch {
    return { user: null, tokens: null };
  }
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [session, setSession] = useState(() => loadStoredSession());
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  const persistSession = (nextUser: User | null, nextTokens: AuthSessionTokens | null) => {
    const nextSession = { user: nextUser, tokens: nextTokens };
    setSession(nextSession);
    window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(nextSession));
  };

  const logout = () => {
    setSession({ user: null, tokens: null });
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
  };

  useEffect(() => {
    registerAuthHandlers({
      getTokens: () => session.tokens,
      setTokens: (tokens) => {
        setSession((current) => {
          const nextSession = { user: current.user, tokens };
          window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(nextSession));
          return nextSession;
        });
      },
      logout
    });
  }, [session.tokens]);

  useEffect(() => {
    const bootstrap = async () => {
      if (!session.tokens?.access) {
        setIsBootstrapping(false);
        return;
      }

      try {
        const response = await api.get<User>("/auth/me/");
        persistSession(response.data, session.tokens);
      } catch {
        logout();
      } finally {
        setIsBootstrapping(false);
      }
    };

    void bootstrap();
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: session.user,
      tokens: session.tokens,
      isAuthenticated: Boolean(session.user && session.tokens),
      isBootstrapping,
      login: async (username: string, password: string) => {
        const response = await api.post<LoginResponse>("/auth/login/", { username, password });
        persistSession(response.data.user, {
          access: response.data.access,
          refresh: response.data.refresh
        });
      },
      register: async (payload: RegisterPayload) => {
        await api.post("/auth/register/", payload);
        const response = await api.post<LoginResponse>("/auth/login/", {
          username: payload.username,
          password: payload.password
        });
        persistSession(response.data.user, {
          access: response.data.access,
          refresh: response.data.refresh
        });
      },
      logout
    }),
    [isBootstrapping, session.tokens, session.user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
