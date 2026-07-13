"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, clearToken, getToken, setToken } from "./api";

export type User = {
  id: number;
  usuario: string;
  nome: string;
  ativo: boolean;
  criado_em: string;
};

type AuthCtx = {
  user: User | null;
  loading: boolean;
  login: (usuario: string, senha: string) => Promise<void>;
  logout: () => void;
};

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    api<User>("/auth/me")
      .then(setUser)
      .catch(() => clearToken())
      .finally(() => setLoading(false));
  }, []);

  async function login(usuario: string, senha: string) {
    const res = await api<{ access_token: string }>("/auth/login", {
      method: "POST",
      auth: false,
      form: { username: usuario, password: senha },
    });
    setToken(res.access_token);
    const me = await api<User>("/auth/me");
    setUser(me);
    router.push("/");
  }

  function logout() {
    clearToken();
    setUser(null);
    router.push("/login");
  }

  return <Ctx.Provider value={{ user, loading, login, logout }}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth precisa estar dentro de AuthProvider");
  return ctx;
}
