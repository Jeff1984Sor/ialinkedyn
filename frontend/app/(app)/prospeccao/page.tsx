"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Target, Loader2, Copy, Check, Search, UserPlus, Info, ExternalLink } from "lucide-react";

type Perfil = {
  nome: string;
  headline: string;
  empresa: string;
  cargo: string;
  linkedin_url: string;
  sobre: string;
  posts_recentes: string[];
  ja_importado: boolean;
};

type BuscaResp = {
  termo_usado: string;
  provider: string;
  simulado: boolean;
  perfis: Perfil[];
};

export default function ProspeccaoPage() {
  const [termo, setTermo] = useState("");
  const [busca, setBusca] = useState<BuscaResp | null>(null);
  const [buscando, setBuscando] = useState(false);
  const [selecionados, setSelecionados] = useState<Set<string>>(new Set());
  const [importando, setImportando] = useState(false);
  const [msgImport, setMsgImport] = useState("");

  // abordagem gerada
  const [abordagem, setAbordagem] = useState("");
  const [gerandoUrl, setGerandoUrl] = useState<string | null>(null);
  const [copiado, setCopiado] = useState(false);

  async function buscar() {
    setBuscando(true);
    setBusca(null);
    setMsgImport("");
    setSelecionados(new Set());
    try {
      const r = await api<BuscaResp>("/agents/buscar", { method: "POST", body: { termo: termo || null, limite: 10 } });
      setBusca(r);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro na busca");
    } finally {
      setBuscando(false);
    }
  }

  function alternar(url: string) {
    const novo = new Set(selecionados);
    if (novo.has(url)) novo.delete(url);
    else novo.add(url);
    setSelecionados(novo);
  }

  async function importar() {
    if (!busca) return;
    const perfis = busca.perfis.filter((p) => selecionados.has(p.linkedin_url) && !p.ja_importado);
    if (perfis.length === 0) return;
    setImportando(true);
    try {
      const r = await api<{ importados: number; ignorados: number }>("/agents/importar-leads", {
        method: "POST",
        body: { perfis },
      });
      setMsgImport(`${r.importados} lead(s) importado(s) para o CRM${r.ignorados ? ` · ${r.ignorados} já existiam` : ""}.`);
      await buscar();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao importar");
    } finally {
      setImportando(false);
    }
  }

  async function gerarAbordagem(p: Perfil) {
    setGerandoUrl(p.linkedin_url);
    setAbordagem("");
    try {
      const texto = [
        `Nome: ${p.nome}`,
        `Headline: ${p.headline}`,
        `Empresa: ${p.empresa}`,
        `Cargo: ${p.cargo}`,
        p.sobre ? `Sobre: ${p.sobre}` : "",
        p.posts_recentes.length ? `Posts recentes: ${p.posts_recentes.join(" | ")}` : "",
      ].filter(Boolean).join("\n");
      const r = await api<{ abordagem: string }>("/agents/prospectar", { method: "POST", body: { perfil_texto: texto } });
      setAbordagem(r.abordagem);
    } catch (e) {
      setAbordagem(`⚠️ ${e instanceof Error ? e.message : "Erro ao gerar"}`);
    } finally {
      setGerandoUrl(null);
    }
  }

  const selecionaveis = busca?.perfis.filter((p) => !p.ja_importado) ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">Prospecção</h1>
        <p className="text-ink-soft mt-1">O Caçador busca pessoas no LinkedIn, importa como leads e escreve a abordagem.</p>
      </div>

      {/* Busca */}
      <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm space-y-3">
        <label className="block text-sm font-medium text-ink">Quem você quer encontrar?</label>
        <div className="flex gap-2">
          <input
            value={termo}
            onChange={(e) => setTermo(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && buscar()}
            placeholder="ex.: diretores comerciais de SaaS em São Paulo (vazio = usa seu ICP)"
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand"
          />
          <button onClick={buscar} disabled={buscando} className="flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-dark text-white px-5 py-2 text-sm font-medium disabled:opacity-60">
            {buscando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />} Buscar no LinkedIn
          </button>
        </div>
        <p className="text-xs text-ink-soft">Se deixar vazio, o Caçador usa o Público Ideal (ICP) que você cadastrou em Marca / Voz.</p>
      </div>

      {/* Resultados */}
      {busca && (
        <div className="space-y-3">
          {busca.simulado && (
            <div className="rounded-xl bg-amber-50 border border-amber-200 p-4 flex gap-3">
              <Info className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
              <p className="text-sm text-amber-900">
                Resultados <strong>simulados</strong> (provedor mock) — servem para você ver o fluxo funcionando.
                Ao configurar o Unipile em <strong>Conexões</strong>, virão perfis reais do LinkedIn, sem mudar mais nada.
              </p>
            </div>
          )}

          <div className="flex items-center justify-between">
            <p className="text-sm text-ink-soft">
              {busca.perfis.length} perfil(is) para <strong className="text-ink">"{busca.termo_usado}"</strong>
            </p>
            <div className="flex items-center gap-2">
              {msgImport && <span className="text-sm text-emerald-600">{msgImport}</span>}
              <button
                onClick={importar}
                disabled={importando || selecionados.size === 0}
                className="flex items-center gap-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 text-sm font-medium disabled:opacity-50"
              >
                {importando ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserPlus className="h-4 w-4" />}
                Importar {selecionados.size > 0 ? `(${selecionados.size})` : ""}
              </button>
            </div>
          </div>

          {selecionaveis.length > 0 && (
            <label className="flex items-center gap-2 text-sm text-ink-soft">
              <input
                type="checkbox"
                className="h-4 w-4 accent-brand"
                checked={selecionados.size === selecionaveis.length && selecionaveis.length > 0}
                onChange={(e) => setSelecionados(e.target.checked ? new Set(selecionaveis.map((p) => p.linkedin_url)) : new Set())}
              />
              Selecionar todos
            </label>
          )}

          {busca.perfis.map((p) => (
            <div key={p.linkedin_url || p.nome} className="rounded-xl bg-white border border-slate-200 p-4 shadow-sm">
              <div className="flex items-start gap-3">
                {!p.ja_importado ? (
                  <input type="checkbox" className="h-4 w-4 accent-brand mt-1" checked={selecionados.has(p.linkedin_url)} onChange={() => alternar(p.linkedin_url)} />
                ) : (
                  <div className="w-4 mt-1" />
                )}
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-ink">{p.nome}</p>
                    {p.ja_importado && <span className="text-[11px] bg-slate-100 text-ink-soft rounded-full px-2 py-0.5">já no CRM</span>}
                  </div>
                  <p className="text-sm text-ink-soft">{p.headline}</p>
                  {p.sobre && <p className="text-xs text-ink-soft mt-1">{p.sobre}</p>}
                  {p.linkedin_url && (
                    <a href={p.linkedin_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-brand hover:underline mt-1">
                      <ExternalLink className="h-3 w-3" /> Ver perfil
                    </a>
                  )}
                </div>
                <button
                  onClick={() => gerarAbordagem(p)}
                  disabled={gerandoUrl === p.linkedin_url}
                  className="flex items-center gap-1 text-xs rounded-lg border border-brand/30 text-brand px-3 py-1.5 hover:bg-brand/5 disabled:opacity-50 shrink-0"
                >
                  {gerandoUrl === p.linkedin_url ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Target className="h-3.5 w-3.5" />} Abordagem
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Abordagem gerada */}
      {abordagem && (
        <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-semibold text-ink flex items-center gap-2"><Target className="h-4 w-4 text-brand" /> Abordagem gerada</h2>
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
