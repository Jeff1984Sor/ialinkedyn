"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Loader2, Save, RotateCcw, Wand2, Check, X } from "lucide-react";

type Prompt = {
  chave: string;
  label: string;
  conteudo: string;
  padrao: string;
  customizado: boolean;
  placeholders: string[];
};

export default function PromptsPage() {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [chaveAtiva, setChaveAtiva] = useState<string>("");
  const [texto, setTexto] = useState("");
  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [ok, setOk] = useState(false);

  // chat com a IA
  const [instrucao, setInstrucao] = useState("");
  const [melhorando, setMelhorando] = useState(false);
  const [sugestao, setSugestao] = useState<string | null>(null);

  const atual = prompts.find((p) => p.chave === chaveAtiva);

  async function carregar(selecionar?: string) {
    const dados = await api<Prompt[]>("/prompts");
    setPrompts(dados);
    const chave = selecionar || chaveAtiva || dados[0]?.chave || "";
    setChaveAtiva(chave);
    const p = dados.find((x) => x.chave === chave);
    if (p) setTexto(p.conteudo);
  }

  useEffect(() => {
    carregar().finally(() => setCarregando(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function trocar(chave: string) {
    setChaveAtiva(chave);
    const p = prompts.find((x) => x.chave === chave);
    setTexto(p?.conteudo || "");
    setSugestao(null);
    setInstrucao("");
  }

  async function salvar() {
    if (!atual) return;
    setSalvando(true);
    setOk(false);
    try {
      await api(`/prompts/${atual.chave}`, { method: "PUT", body: { conteudo: texto } });
      await carregar(atual.chave);
      setOk(true);
      setTimeout(() => setOk(false), 2500);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao salvar");
    } finally {
      setSalvando(false);
    }
  }

  async function restaurar() {
    if (!atual) return;
    if (!confirm("Restaurar o prompt padrão? Sua customização será apagada.")) return;
    await api(`/prompts/${atual.chave}`, { method: "DELETE" });
    await carregar(atual.chave);
  }

  async function melhorar() {
    if (!atual || !instrucao.trim()) return;
    setMelhorando(true);
    setSugestao(null);
    try {
      const r = await api<{ sugestao: string }>(`/prompts/${atual.chave}/melhorar`, {
        method: "POST",
        body: { instrucao, conteudo_atual: texto },
      });
      setSugestao(r.sugestao);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao melhorar");
    } finally {
      setMelhorando(false);
    }
  }

  function aplicarSugestao() {
    if (sugestao) setTexto(sugestao);
    setSugestao(null);
    setInstrucao("");
  }

  if (carregando) {
    return <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-brand" /></div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">Prompts</h1>
        <p className="text-ink-soft mt-1">Ajuste como cada agente pensa — ou peça pra IA melhorar pra você.</p>
      </div>

      {/* Abas */}
      <div className="flex gap-2 flex-wrap">
        {prompts.map((p) => (
          <button
            key={p.chave}
            onClick={() => trocar(p.chave)}
            className={`rounded-lg px-4 py-2 text-sm font-medium border ${
              chaveAtiva === p.chave
                ? "bg-brand text-white border-brand"
                : "bg-white text-ink border-slate-300 hover:bg-slate-50"
            }`}
          >
            {p.label}
            {p.customizado && <span className="ml-2 text-[10px] opacity-80">(editado)</span>}
          </button>
        ))}
      </div>

      {atual && (
        <>
          {/* Chat com a IA */}
          <div className="rounded-xl bg-violet-50 border border-violet-200 p-5 space-y-3">
            <div className="flex items-center gap-2 text-violet-700 font-semibold">
              <Wand2 className="h-5 w-5" /> Melhorar com IA
            </div>
            <p className="text-sm text-violet-900/80">
              Diga em português o que você quer mudar. Ex.: <em>"deixa mais formal"</em>, <em>"foca em vendas"</em>,
              <em> "peça o telefone no final"</em>.
            </p>
            <div className="flex gap-2">
              <input
                value={instrucao}
                onChange={(e) => setInstrucao(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && melhorar()}
                placeholder="O que você quer mudar neste prompt?"
                className="flex-1 rounded-lg border border-violet-300 bg-white px-3 py-2 text-sm outline-none focus:border-violet-500"
              />
              <button
                onClick={melhorar}
                disabled={melhorando || !instrucao.trim()}
                className="flex items-center gap-2 rounded-lg bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 text-sm font-medium disabled:opacity-60"
              >
                {melhorando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />} Melhorar
              </button>
            </div>

            {sugestao && (
              <div className="rounded-lg bg-white border border-violet-200 p-3 space-y-3">
                <p className="text-xs font-medium text-violet-700">Sugestão da IA:</p>
                <pre className="text-xs text-ink whitespace-pre-wrap font-sans max-h-60 overflow-y-auto">{sugestao}</pre>
                <div className="flex gap-2">
                  <button onClick={aplicarSugestao} className="flex items-center gap-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1.5 text-xs font-medium">
                    <Check className="h-3.5 w-3.5" /> Usar esta versão
                  </button>
                  <button onClick={() => setSugestao(null)} className="flex items-center gap-1 rounded-lg border border-slate-300 px-3 py-1.5 text-xs hover:bg-slate-50">
                    <X className="h-3.5 w-3.5" /> Descartar
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Editor */}
          <div className="rounded-xl bg-white border border-slate-200 p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-ink">{atual.label}</h2>
              {atual.customizado && (
                <span className="text-xs bg-amber-100 text-amber-700 rounded-full px-2 py-0.5">Customizado</span>
              )}
            </div>

            <div className="flex gap-1.5 flex-wrap">
              <span className="text-xs text-ink-soft">Marcadores (não apague):</span>
              {atual.placeholders.map((ph) => (
                <code key={ph} className="text-[11px] bg-slate-100 text-brand rounded px-1.5 py-0.5">{ph}</code>
              ))}
            </div>

            <textarea
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              rows={18}
              spellCheck={false}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs font-mono outline-none focus:border-brand"
            />

            <div className="flex items-center gap-3">
              <button onClick={salvar} disabled={salvando} className="flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-dark text-white px-5 py-2.5 text-sm font-medium disabled:opacity-60">
                {salvando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Salvar
              </button>
              <button onClick={restaurar} className="flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2.5 text-sm hover:bg-slate-50">
                <RotateCcw className="h-4 w-4" /> Restaurar padrão
              </button>
              {ok && <span className="text-sm text-emerald-600">Salvo! ✓</span>}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
