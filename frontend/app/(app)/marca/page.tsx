"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Loader2, Save, Sparkles } from "lucide-react";

type Brand = {
  id: number;
  nome_assistente: string;
  persona: string;
  avatar_url: string;
  assina_mensagens: boolean;
  descricao_empresa: string;
  tom: string;
  icp: string;
  cta: string;
};

export default function MarcaPage() {
  const [brand, setBrand] = useState<Brand | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [ok, setOk] = useState(false);

  useEffect(() => {
    api<Brand>("/brand").then(setBrand).finally(() => setCarregando(false));
  }, []);

  async function salvar() {
    if (!brand) return;
    setSalvando(true);
    setOk(false);
    try {
      const atualizado = await api<Brand>("/brand", { method: "PUT", body: brand });
      setBrand(atualizado);
      setOk(true);
      setTimeout(() => setOk(false), 2500);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao salvar");
    } finally {
      setSalvando(false);
    }
  }

  function set<K extends keyof Brand>(campo: K, valor: Brand[K]) {
    if (brand) setBrand({ ...brand, [campo]: valor });
  }

  if (carregando || !brand) {
    return <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-brand" /></div>;
  }

  const input = "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand";

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-ink">Marca / Voz</h1>
        <p className="text-ink-soft mt-1">Dê nome e personalidade à sua funcionária virtual. Isso guia o tom de todos os agentes.</p>
      </div>

      <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-2 text-brand font-semibold">
          <Sparkles className="h-5 w-5" /> Sua funcionária
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-ink mb-1">Nome da funcionária</label>
            <input className={input} value={brand.nome_assistente} onChange={(e) => set("nome_assistente", e.target.value)} placeholder="ex.: Sofia" />
          </div>
          <div>
            <label className="block text-sm font-medium text-ink mb-1">Avatar (URL, opcional)</label>
            <input className={input} value={brand.avatar_url} onChange={(e) => set("avatar_url", e.target.value)} placeholder="https://..." />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-ink mb-1">Personalidade / estilo</label>
          <textarea className={input} rows={2} value={brand.persona} onChange={(e) => set("persona", e.target.value)} placeholder="ex.: consultiva, simpática, direta ao ponto" />
        </div>
        <label className="flex items-center gap-2 text-sm text-ink">
          <input type="checkbox" checked={brand.assina_mensagens} onChange={(e) => set("assina_mensagens", e.target.checked)} className="h-4 w-4 accent-brand" />
          Assinar as mensagens com o nome da funcionária
        </label>
      </div>

      <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="font-semibold text-ink">Voz da empresa</div>
        <div>
          <label className="block text-sm font-medium text-ink mb-1">Descrição da empresa</label>
          <textarea className={input} rows={3} value={brand.descricao_empresa} onChange={(e) => set("descricao_empresa", e.target.value)} placeholder="O que a empresa faz, o que vende..." />
        </div>
        <div>
          <label className="block text-sm font-medium text-ink mb-1">Tom de voz</label>
          <textarea className={input} rows={2} value={brand.tom} onChange={(e) => set("tom", e.target.value)} placeholder="ex.: profissional, mas próximo; sem jargão" />
        </div>
        <div>
          <label className="block text-sm font-medium text-ink mb-1">Público ideal (ICP)</label>
          <textarea className={input} rows={2} value={brand.icp} onChange={(e) => set("icp", e.target.value)} placeholder="ex.: donos de clínicas em SP, 30-50 anos" />
        </div>
        <div>
          <label className="block text-sm font-medium text-ink mb-1">Chamada para ação (CTA)</label>
          <input className={input} value={brand.cta} onChange={(e) => set("cta", e.target.value)} placeholder="ex.: Posso te mandar uma proposta?" />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button onClick={salvar} disabled={salvando} className="flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-dark text-white px-5 py-2.5 text-sm font-medium disabled:opacity-60">
          {salvando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Salvar
        </button>
        {ok && <span className="text-sm text-emerald-600">Salvo! ✓</span>}
      </div>
    </div>
  );
}
