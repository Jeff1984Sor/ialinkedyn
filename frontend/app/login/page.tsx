"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { Bot, Loader2 } from "lucide-react";

export default function LoginPage() {
  const { login } = useAuth();
  const [usuario, setUsuario] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro("");
    setCarregando(true);
    try {
      await login(usuario, senha);
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Falha no login");
    } finally {
      setCarregando(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-dark via-brand to-brand-light px-4">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-xl p-8">
        <div className="flex flex-col items-center mb-8">
          <div className="h-14 w-14 rounded-xl bg-brand flex items-center justify-center mb-3">
            <Bot className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-ink">IALinkedyn</h1>
          <p className="text-sm text-ink-soft mt-1">Seu funcionário virtual de LinkedIn</p>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-ink mb-1">Usuário</label>
            <input
              type="text"
              value={usuario}
              onChange={(e) => setUsuario(e.target.value)}
              autoFocus
              className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
              placeholder="ex.: jefferson"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-ink mb-1">Senha</label>
            <input
              type="password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
              placeholder="••••••••"
            />
          </div>

          {erro && <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{erro}</p>}

          <button
            type="submit"
            disabled={carregando}
            className="w-full rounded-lg bg-brand hover:bg-brand-dark text-white font-medium py-2.5 flex items-center justify-center gap-2 transition-colors disabled:opacity-60"
          >
            {carregando && <Loader2 className="h-4 w-4 animate-spin" />}
            Entrar
          </button>
        </form>
      </div>
    </div>
  );
}
