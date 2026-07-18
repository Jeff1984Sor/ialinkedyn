"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Loader2, Wand2, Check, X, User as UserIcon, Sparkles, AlertTriangle } from "lucide-react";

type MeuPerfil = { nome: string; headline: string; summary: string; foto_url: string; aviso: string };
type Sugestao = { headline: string; summary: string; headline_atual: string; summary_atual: string };

export default function MeuPerfilPage() {
  const [perfil, setPerfil] = useState<MeuPerfil | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");

  const [sugestao, setSugestao] = useState<Sugestao | null>(null);
  const [gerando, setGerando] = useState(false);
  const [aplicando, setAplicando] = useState(false);
  const [ok, setOk] = useState(false);

  // campos editáveis (partem da sugestão, mas você pode ajustar)
  const [headline, setHeadline] = useState("");
  const [summary, setSummary] = useState("");

  async function carregar() {
    setErro("");
    try {
      setPerfil(await api<MeuPerfil>("/perfil/meu"));
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao carregar seu perfil");
    }
  }
  useEffect(() => { carregar().finally(() => setCarregando(false)); }, []);

  async function melhorar() {
    setGerando(true); setSugestao(null); setOk(false);
    try {
      const s = await api<Sugestao>("/perfil/meu/melhorar", { method: "POST" });
      setSugestao(s);
      setHeadline(s.headline);
      setSummary(s.summary);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao gerar sugestão");
    } finally {
      setGerando(false);
    }
  }

  async function aplicar() {
    if (!confirm("Isso vai ALTERAR seu perfil real do LinkedIn. Confirmar?")) return;
    setAplicando(true); setOk(false);
    try {
      setPerfil(await api<MeuPerfil>("/perfil/meu", { method: "PUT", body: { headline, summary } }));
      setSugestao(null);
      setOk(true);
      setTimeout(() => setOk(false), 4000);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao aplicar");
    } finally {
      setAplicando(false);
    }
  }

  const input = "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand";

  if (carregando) {
    return <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-brand" /></div>;
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-ink">Meu Perfil</h1>
        <p className="text-ink-soft mt-1">A Maya reescreve seu título e o &quot;Sobre&quot; para atrair seu público ideal.</p>
      </div>

      {erro && (
        <div className="rounded-xl bg-red-50 border border-red-200 p-4 text-sm text-red-700">{erro}</div>
      )}

      {/* Perfil atual */}
      {perfil && (
        <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm space-y-3">
          <div className="flex items-center gap-3">
            {perfil.foto_url ? (
              <img src={perfil.foto_url} alt="" className="h-14 w-14 rounded-full object-cover" />
            ) : (
              <div className="h-14 w-14 rounded-full bg-brand/10 flex items-center justify-center">
                <UserIcon className="h-7 w-7 text-brand" />
              </div>
            )}
            <div>
              <h2 className="font-semibold text-ink">{perfil.nome || "Sua conta"}</h2>
              <p className="text-sm text-ink-soft">Perfil atual no LinkedIn</p>
            </div>
          </div>

          <div>
            <p className="text-xs font-medium text-ink-soft uppercase">Título</p>
            <p className="text-sm text-ink">{perfil.headline || <em className="text-ink-soft">(vazio)</em>}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-ink-soft uppercase">Sobre</p>
            <p className="text-sm text-ink whitespace-pre-wrap">{perfil.summary || <em className="text-ink-soft">(vazio)</em>}</p>
          </div>

          <button onClick={melhorar} disabled={gerando}
            className="flex items-center gap-2 rounded-lg bg-violet-600 hover:bg-violet-700 text-white px-5 py-2.5 text-sm font-medium disabled:opacity-60">
            {gerando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />}
            Melhorar meu perfil com IA
          </button>

          {ok && <p className="text-sm text-emerald-600">Perfil atualizado no LinkedIn! ✓</p>}
        </div>
      )}

      {/* Sugestão */}
      {sugestao && (
        <div className="rounded-xl bg-violet-50 border border-violet-200 p-6 space-y-4">
          <h2 className="font-semibold text-violet-800 flex items-center gap-2">
            <Sparkles className="h-5 w-5" /> Sugestão da Maya (edite se quiser)
          </h2>

          <div>
            <label className="block text-sm font-medium text-ink mb-1">
              Novo título <span className="text-xs text-ink-soft">({headline.length}/200)</span>
            </label>
            <textarea className={input} rows={2} maxLength={200} value={headline} onChange={(e) => setHeadline(e.target.value)} />
          </div>

          <div>
            <label className="block text-sm font-medium text-ink mb-1">Novo &quot;Sobre&quot;</label>
            <textarea className={input} rows={12} value={summary} onChange={(e) => setSummary(e.target.value)} />
          </div>

          <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 flex gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0" />
            <p className="text-sm text-amber-900">
              Ao aplicar, seu perfil <strong>real</strong> do LinkedIn será alterado. Revise antes.
            </p>
          </div>

          <div className="flex gap-2">
            <button onClick={aplicar} disabled={aplicando || (!headline && !summary)}
              className="flex items-center gap-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 text-sm font-medium disabled:opacity-60">
              {aplicando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
              Aplicar no meu LinkedIn
            </button>
            <button onClick={() => setSugestao(null)}
              className="flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2.5 text-sm hover:bg-white">
              <X className="h-4 w-4" /> Descartar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
