"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  Target, Loader2, Search, Send, Info, ExternalLink, Plus, Trash2, X,
  Users, ShieldAlert, CheckCircle2, Clock,
} from "lucide-react";

type Perfil = {
  nome: string;
  headline: string;
  empresa: string;
  cargo: string;
  linkedin_url: string;
  provider_id: string;
  sobre: string;
  posts_recentes: string[];
  ja_importado: boolean;
};

type BuscaResp = { termo_usado: string; provider: string; simulado: boolean; perfis: Perfil[] };
type Publico = { id: number; nome: string; termo: string; descricao: string; ativo: boolean };
type CampanhaResp = {
  enfileirados: number; leads_criados: number; ja_abordados: number;
  limite_diario: number; restante_hoje: number; aviso: string;
};
type Tarefa = {
  id: number; lead_id: number; tipo: string; mensagem: string; status: string;
  erro: string; enviado_em: string | null; lead_nome: string;
};
type Fila = {
  pendentes: number; enviados_hoje: number; erros: number;
  limite_diario: number; restante_hoje: number; dentro_do_horario: boolean;
  horario: string; tarefas: Tarefa[];
};

const input = "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand";

export default function ProspeccaoPage() {
  const [publicos, setPublicos] = useState<Publico[]>([]);
  const [publicoId, setPublicoId] = useState<number | "">("");
  const [termoLivre, setTermoLivre] = useState("");

  const [busca, setBusca] = useState<BuscaResp | null>(null);
  const [buscando, setBuscando] = useState(false);
  const [selecionados, setSelecionados] = useState<Set<string>>(new Set());

  const [tipo, setTipo] = useState<"CONVITE" | "MENSAGEM" | "INMAIL">("CONVITE");
  const [enviando, setEnviando] = useState(false);
  const [resultado, setResultado] = useState<CampanhaResp | null>(null);

  const [fila, setFila] = useState<Fila | null>(null);
  const [modalPublico, setModalPublico] = useState(false);
  const [novoPublico, setNovoPublico] = useState({ nome: "", termo: "", descricao: "" });

  async function carregarPublicos() {
    setPublicos(await api<Publico[]>("/audiences"));
  }
  async function carregarFila() {
    setFila(await api<Fila>("/campanha/status"));
  }
  useEffect(() => {
    carregarPublicos();
    carregarFila();
  }, []);

  async function buscar() {
    setBuscando(true); setBusca(null); setResultado(null); setSelecionados(new Set());
    try {
      const escolhido = publicos.find((p) => p.id === publicoId);
      const termo = termoLivre.trim() || escolhido?.termo || null;
      const r = await api<BuscaResp>("/agents/buscar", { method: "POST", body: { termo, limite: 20 } });
      setBusca(r);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro na busca");
    } finally {
      setBuscando(false);
    }
  }

  function alternar(url: string) {
    const novo = new Set(selecionados);
    novo.has(url) ? novo.delete(url) : novo.add(url);
    setSelecionados(novo);
  }

  async function enviarCampanha() {
    if (!busca) return;
    const perfis = busca.perfis.filter((p) => selecionados.has(p.linkedin_url));
    if (perfis.length === 0) return;
    if (!confirm(
      `A IA vai escrever uma mensagem personalizada para ${perfis.length} pessoa(s) e colocar na fila.\n\n` +
      `O envio é gradual (ritmo humano), respeitando seu limite diário. Continuar?`
    )) return;

    setEnviando(true); setResultado(null);
    try {
      const r = await api<CampanhaResp>("/campanha/enfileirar", {
        method: "POST",
        body: { perfis, audience_id: publicoId || null, tipo },
      });
      setResultado(r);
      setSelecionados(new Set());
      await carregarFila();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao enfileirar");
    } finally {
      setEnviando(false);
    }
  }

  async function salvarPublico() {
    if (!novoPublico.nome.trim() || !novoPublico.termo.trim()) return;
    await api("/audiences", { method: "POST", body: novoPublico });
    setNovoPublico({ nome: "", termo: "", descricao: "" });
    setModalPublico(false);
    await carregarPublicos();
  }

  async function excluirPublico(id: number) {
    if (!confirm("Excluir este público?")) return;
    await api(`/audiences/${id}`, { method: "DELETE" });
    if (publicoId === id) setPublicoId("");
    await carregarPublicos();
  }

  async function enviarAgora() {
    const r = await api<{ enviados: number; motivo: string }>("/campanha/enviar-agora", { method: "POST" });
    alert(r.enviados ? "1 abordagem enviada!" : `Nada enviado: ${r.motivo}`);
    await carregarFila();
  }

  const selecionaveis = busca?.perfis ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">Prospecção</h1>
        <p className="text-ink-soft mt-1">Escolha o público, busque no LinkedIn e dispare abordagens personalizadas.</p>
      </div>

      {/* 1. Público */}
      <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-ink flex items-center gap-2"><Users className="h-5 w-5 text-brand" /> 1. Público-alvo</h2>
          <button onClick={() => setModalPublico(true)} className="flex items-center gap-1 text-sm text-brand hover:underline">
            <Plus className="h-4 w-4" /> Novo público
          </button>
        </div>

        {publicos.length === 0 ? (
          <p className="text-sm text-ink-soft">
            Nenhum público salvo ainda. Crie um (ex.: "Donos de clínica em SP") ou use a busca livre abaixo.
          </p>
        ) : (
          <div className="space-y-2">
            {publicos.map((p) => (
              <label key={p.id} className={`flex items-start gap-3 rounded-lg border p-3 cursor-pointer ${
                publicoId === p.id ? "border-brand bg-brand/5" : "border-slate-200 hover:bg-slate-50"
              }`}>
                <input type="radio" name="publico" className="h-4 w-4 accent-brand mt-0.5"
                  checked={publicoId === p.id} onChange={() => { setPublicoId(p.id); setTermoLivre(""); }} />
                <div className="flex-1">
                  <p className="text-sm font-medium text-ink">{p.nome}</p>
                  <p className="text-xs text-ink-soft">{p.termo}</p>
                </div>
                <button onClick={(e) => { e.preventDefault(); excluirPublico(p.id); }} className="p-1 rounded hover:bg-red-50 text-red-500">
                  <Trash2 className="h-4 w-4" />
                </button>
              </label>
            ))}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-ink mb-1">Ou busca livre</label>
          <div className="flex gap-2">
            <input className={input} value={termoLivre}
              onChange={(e) => { setTermoLivre(e.target.value); if (e.target.value) setPublicoId(""); }}
              onKeyDown={(e) => e.key === "Enter" && buscar()}
              placeholder="ex.: diretores comerciais de SaaS em São Paulo" />
            <button onClick={buscar} disabled={buscando} className="flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-dark text-white px-5 py-2 text-sm font-medium disabled:opacity-60 whitespace-nowrap">
              {buscando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />} Buscar
            </button>
          </div>
          <p className="text-xs text-ink-soft mt-1">Vazio + nenhum público = usa o ICP da sua Marca / Voz.</p>
        </div>
      </div>

      {/* 2. Resultados */}
      {busca && (
        <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm space-y-4">
          <h2 className="font-semibold text-ink flex items-center gap-2"><Search className="h-5 w-5 text-brand" /> 2. Encontrados ({busca.perfis.length})</h2>

          {busca.simulado && (
            <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 flex gap-2">
              <Info className="h-5 w-5 text-amber-600 shrink-0" />
              <p className="text-sm text-amber-900">Resultados <strong>simulados</strong> (provedor mock). Configure o Unipile em Conexões para buscar pessoas reais.</p>
            </div>
          )}

          {selecionaveis.length > 0 && (
            <label className="flex items-center gap-2 text-sm text-ink-soft">
              <input type="checkbox" className="h-4 w-4 accent-brand"
                checked={selecionados.size === selecionaveis.length && selecionaveis.length > 0}
                onChange={(e) => setSelecionados(e.target.checked ? new Set(selecionaveis.map((p) => p.linkedin_url)) : new Set())} />
              Selecionar todos
            </label>
          )}

          <div className="space-y-2">
            {busca.perfis.map((p) => (
              <div key={p.linkedin_url || p.nome} className="flex items-start gap-3 rounded-lg border border-slate-200 p-3">
                <input type="checkbox" className="h-4 w-4 accent-brand mt-1"
                  checked={selecionados.has(p.linkedin_url)} onChange={() => alternar(p.linkedin_url)} />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-ink text-sm">{p.nome}</p>
                    {p.ja_importado && <span className="text-[11px] bg-slate-100 text-ink-soft rounded-full px-2 py-0.5">já no CRM</span>}
                  </div>
                  <p className="text-sm text-ink-soft">{p.headline}</p>
                  {p.linkedin_url && (
                    <a href={p.linkedin_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-brand hover:underline mt-1">
                      <ExternalLink className="h-3 w-3" /> Ver perfil
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* 3. Disparar */}
          <div className="border-t border-slate-100 pt-4 space-y-3">
            <h3 className="font-semibold text-ink flex items-center gap-2"><Send className="h-4 w-4 text-brand" /> 3. Enviar abordagem</h3>
            <div>
              <label className="block text-sm font-medium text-ink mb-1">Como enviar</label>
              <select className={input} value={tipo} onChange={(e) => setTipo(e.target.value as "CONVITE" | "MENSAGEM" | "INMAIL")}>
                <option value="CONVITE">Convite de conexão com nota (recomendado — aparece em Minha rede)</option>
                <option value="MENSAGEM">Mensagem no chat (só para quem JÁ é sua conexão)</option>
                <option value="INMAIL">InMail (chat com não-conexões — consome crédito Premium/Sales Navigator)</option>
              </select>
              <p className="text-xs text-ink-soft mt-1">
                Convite não aparece na caixa de mensagens do LinkedIn — ele fica em <strong>Minha rede</strong>.
                Quando a pessoa aceitar, a Maya manda a 1ª mensagem no chat automaticamente.
              </p>
            </div>

            <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 flex gap-2">
              <ShieldAlert className="h-5 w-5 text-amber-600 shrink-0" />
              <p className="text-sm text-amber-900">
                O envio é <strong>gradual</strong>, em ritmo humano, respeitando seu limite diário e horário de trabalho
                (ajustáveis em Conexões). Isso protege sua conta de restrição.
              </p>
            </div>

            <button onClick={enviarCampanha} disabled={enviando || selecionados.size === 0}
              className="flex items-center gap-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 text-sm font-medium disabled:opacity-50">
              {enviando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              Gerar e enfileirar para {selecionados.size} pessoa(s)
            </button>

            {resultado && (
              <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-3 text-sm text-emerald-900 space-y-1">
                <p className="flex items-center gap-1 font-medium"><CheckCircle2 className="h-4 w-4" /> {resultado.enfileirados} abordagem(ns) na fila!</p>
                <p className="text-xs">
                  {resultado.leads_criados} lead(s) novo(s) · {resultado.ja_abordados} já abordado(s) ·
                  restam {resultado.restante_hoje} envios hoje (limite {resultado.limite_diario})
                </p>
                {resultado.aviso && <p className="text-xs text-amber-800">⚠️ {resultado.aviso}</p>}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Fila */}
      {fila && (
        <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-ink flex items-center gap-2"><Clock className="h-5 w-5 text-brand" /> Fila de envio</h2>
            <div className="flex gap-2">
              <button onClick={carregarFila} className="text-sm text-brand hover:underline">Atualizar</button>
              <button onClick={enviarAgora} className="text-sm text-brand hover:underline">Enviar 1 agora</button>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            <div className="rounded-lg bg-slate-50 p-3">
              <p className="text-2xl font-bold text-ink">{fila.pendentes}</p>
              <p className="text-xs text-ink-soft">na fila</p>
            </div>
            <div className="rounded-lg bg-slate-50 p-3">
              <p className="text-2xl font-bold text-emerald-600">{fila.enviados_hoje}</p>
              <p className="text-xs text-ink-soft">enviados hoje</p>
            </div>
            <div className="rounded-lg bg-slate-50 p-3">
              <p className="text-2xl font-bold text-brand">{fila.restante_hoje}</p>
              <p className="text-xs text-ink-soft">restam hoje</p>
            </div>
            <div className="rounded-lg bg-slate-50 p-3">
              <p className="text-2xl font-bold text-red-500">{fila.erros}</p>
              <p className="text-xs text-ink-soft">erros</p>
            </div>
          </div>

          <p className="text-xs text-ink-soft">
            Horário de envio: {fila.horario} ·{" "}
            {fila.dentro_do_horario ? <span className="text-emerald-600">enviando agora</span> : <span className="text-amber-600">fora do horário (aguardando)</span>}
          </p>

          {fila.tarefas.length > 0 && (
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {fila.tarefas.map((t) => (
                <div key={t.id} className="rounded-lg border border-slate-200 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium text-ink">{t.lead_nome}</p>
                    <span className={`text-[11px] rounded-full px-2 py-0.5 ${
                      t.status === "ENVIADO" ? "bg-emerald-100 text-emerald-700" :
                      t.status === "ERRO" ? "bg-red-100 text-red-700" :
                      t.status === "CANCELADO" ? "bg-slate-100 text-slate-600" :
                      "bg-amber-100 text-amber-700"
                    }`}>{t.status}</span>
                  </div>
                  <p className="text-xs text-ink-soft mt-1 whitespace-pre-wrap">{t.mensagem}</p>
                  {t.erro && <p className="text-xs text-red-600 mt-1">{t.erro}</p>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Modal novo público */}
      {modalPublico && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={() => setModalPublico(false)}>
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-ink">Novo público-alvo</h2>
              <button onClick={() => setModalPublico(false)} className="p-1 rounded hover:bg-slate-100"><X className="h-5 w-5" /></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-ink mb-1">Nome</label>
                <input className={input} value={novoPublico.nome} onChange={(e) => setNovoPublico({ ...novoPublico, nome: e.target.value })} placeholder="ex.: Donos de clínica em SP" />
              </div>
              <div>
                <label className="block text-sm font-medium text-ink mb-1">Termo de busca no LinkedIn</label>
                <input className={input} value={novoPublico.termo} onChange={(e) => setNovoPublico({ ...novoPublico, termo: e.target.value })} placeholder="ex.: proprietário clínica São Paulo" />
              </div>
              <div>
                <label className="block text-sm font-medium text-ink mb-1">Contexto (ajuda a IA a personalizar)</label>
                <textarea className={input} rows={3} value={novoPublico.descricao} onChange={(e) => setNovoPublico({ ...novoPublico, descricao: e.target.value })} placeholder="ex.: costumam sofrer com agenda no papel e faltas de pacientes" />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setModalPublico(false)} className="rounded-lg border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50">Cancelar</button>
              <button onClick={salvarPublico} disabled={!novoPublico.nome.trim() || !novoPublico.termo.trim()}
                className="rounded-lg bg-brand hover:bg-brand-dark text-white px-4 py-2 text-sm font-medium disabled:opacity-60">Salvar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
