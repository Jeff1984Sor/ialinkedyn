"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Target, Loader2, Copy, Check } from "lucide-react";

export default function ProspeccaoPage() {
  const [perfil, setPerfil] = useState("");
  const [abordagem, setAbordagem] = useState("");
  const [gerando, setGerando] = useState(false);
  const [copiado, setCopiado] = useState(false);

  async function gerar() {
    if (!perfil.trim()) return;
    setGerando(true);
    setAbordagem("");
    try {
      const r = await api<{ abordagem: string }>("/agents/prospectar", { method: "POST", body: { perfil_texto: perfil } });
      setAbordagem(r.abordagem);
    } catch (e) {
      setAbordagem(`⚠️ ${e instanceof Error ? e.message : "Erro ao gerar"}`);
    } finally {
      setGerando(false);
    }
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-ink">Prospecção</h1>
        <p className="text-ink-soft mt-1">Cole os dados do perfil da pessoa e o Caçador gera uma abordagem personalizada, no seu tom.</p>
      </div>

      <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm space-y-3">
        <label className="block text-sm font-medium text-ink">Dados do perfil (cargo, empresa, sobre, um post recente...)</label>
        <textarea
          value={perfil}
          onChange={(e) => setPerfil(e.target.value)}
          rows={6}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand"
          placeholder={"Ex.:\nNome: Ana Souza\nCargo: Diretora Comercial na TechCorp\nSobre: Lidera vendas B2B há 12 anos\nPost recente: falou sobre previsibilidade de receita"}
        />
        <button onClick={gerar} disabled={gerando || !perfil.trim()} className="flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-dark text-white px-5 py-2.5 text-sm font-medium disabled:opacity-60">
          {gerando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Target className="h-4 w-4" />} Gerar abordagem
        </button>
      </div>

      {abordagem && (
        <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-semibold text-ink flex items-center gap-2"><Target className="h-4 w-4 text-brand" /> Abordagem</h2>
            <button onClick={() => { navigator.clipboard.writeText(abordagem); setCopiado(true); setTimeout(() => setCopiado(false), 2000); }} className="flex items-center gap-1 text-sm text-brand hover:underline">
              {copiado ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />} {copiado ? "Copiado" : "Copiar"}
            </button>
          </div>
          <p className="text-sm text-ink whitespace-pre-wrap">{abordagem}</p>
        </div>
      )}
    </div>
  );
}
