"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  Loader2, Users, Send, RefreshCw, Clock, Mail, CheckCircle2,
  Info, ExternalLink, Zap, ArrowDownToLine,
} from "lucide-react";

type Perfil = {
  nome: string; headline: string; empresa: string; cargo: string;
  linkedin_url: string; provider_id: string; sobre: string;
};
type Conexoes = { total: number; proximo_cursor: string; perfis: Perfil[] };
type Pendentes = { total: number; itens: Record<string, unknown>[] };
type Saldo = {
  premium: number | null; recruiter: number | null; sales_navigator: number | null;
  disponivel: boolean; aviso: string;
};
type CampanhaResp = {
  enfileirados: number; leads_criados: number; ja_abordados: number;
  limite_diario: number; restante_hoje: number; aviso: string;
};

export default function RedePage() {
  const [conexoes, setConexoes] = useState<Conexoes | null>(null);
  const [pendentes, setPendentes] = useState<Pendentes | null>(null);
  const [saldo, setSaldo] = useState<Saldo | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");

  const [selecionados, setSelecionados] = useState<Set<string>>(new Set());
  const [enviando, setEnviando] = useState(false);
  const [resultado, setResultado] = useState<CampanhaResp | null>(null);

  const [sincronizando, setSincronizando] = useState(false);
  const [checando, setChecando] = useState(false);

  async function carregar() {
    setErro("");
    try {
      const [c, p, s] = await Promise.all([
        api<Conexoes>("/rede/conexoes?limite=100"),
        api<Pendentes>("/rede/convites-pendentes").catch(() => ({ total: 0, itens: [] })),
        api<Saldo>("/rede/inmail-saldo").catch(() => null),
      ]);
      setConexoes(c); setPendentes(p); setSaldo(s);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao carregar a rede");
    }
  }

  useEffect(() => { carregar().finally(() => setCarregando(false)); }, []);

  function alternar(id: string) {
    const novo = new Set(selecionados);
    novo.has(id) ? novo.delete(id) : novo.add(id);
    setSelecionados(novo);
  }

  async function enviarMensagens() {
    if (!conexoes) return;
    const perfis = conexoes.perfis.filter((p) => selecionados.has(p.provider_id));
    if (!perfis.length) return;
    if (!confirm(`A Maya vai escrever uma mensagem personalizada para ${perfis.length} conexão(ões) e colocar na fila. Continuar?`)) return;

    setEnviando(true); setResultado(null);
    try {
      const r = await api<CampanhaResp>("/campanha/enfileirar", {
        method: "POST",
        body: { perfis, tipo: "MENSAGEM" },
      });
      setResultado(r);
      setSelecionados(new Set());
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao enfileirar");
    } finally {
      setEnviando(false);
    }
  }

  async function sincronizar() {
    setSincronizando(true);
    try {
      const r = await api<{ importados: number }>("/rede/sincronizar-conexoes", { method: "POST" });
      alert(`${r.importados} conexão(ões) importada(s) para o CRM.`);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro");
    } finally {
      setSincronizando(false);
    }
  }

  async function checarAceites() {
    setChecando(true);
    try {
      const r = await api<{ aceites: number; followups: number; motivo: string }>(
        "/rede/detectar-aceites", { method: "POST" }
      );
      alert(r.aceites
        ? `${r.aceites} pessoa(s) aceitaram! ${r.followups} mensagem(ns) de follow-up na fila.`
        : `Nenhum aceite novo (${r.motivo}).`);
      await carregar();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro");
    } finally {
      setChecando(false);
    }
  }

  if (carregando) {
    return <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-brand" /></div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">Minha Rede</h1>
        <p className="text-ink-soft mt-1">Suas conexões, convites pendentes e o motor de crescimento automático.</p>
      </div>

      {erro && (
        <div className="rounded-xl bg-red-50 border border-red-200 p-4 text-sm text-red-700">{erro}</div>
      )}

      {/* Resumo */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl bg-white border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm text-ink-soft">Conexões</span>
            <Users className="h-5 w-5 text-brand" />
          </div>
          <p className="text-3xl font-bold text-ink mt-2">{conexoes?.total ?? 0}</p>
          <p className="text-xs text-ink-soft">carregadas nesta página</p>
        </div>

        <div className="rounded-xl bg-white border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm text-ink-soft">Convites aguardando</span>
            <Clock className="h-5 w-5 text-amber-500" />
          </div>
          <p className="text-3xl font-bold text-ink mt-2">{pendentes?.total ?? 0}</p>
          <p className="text-xs text-ink-soft">ainda não aceitos</p>
        </div>

        <div className="rounded-xl bg-white border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm text-ink-soft">Créditos de InMail</span>
            <Mail className="h-5 w-5 text-violet-600" />
          </div>
          <p className="text-3xl font-bold text-ink mt-2">
            {saldo ? (saldo.premium ?? 0) + (saldo.sales_navigator ?? 0) + (saldo.recruiter ?? 0) : 0}
          </p>
          <p className="text-xs text-ink-soft">{saldo?.disponivel ? "disponíveis" : "sem créditos"}</p>
        </div>
      </div>

      {/* Motor automático */}
      <div className="rounded-xl bg-gradient-to-br from-brand/5 to-violet-50 border border-brand/20 p-6 space-y-3">
        <h2 className="font-semibold text-ink flex items-center gap-2"><Zap className="h-5 w-5 text-brand" /> Motor de crescimento</h2>
        <p className="text-sm text-ink-soft">
          A cada 15 minutos o sistema verifica quem <strong>aceitou seu convite</strong> e a Maya já enfileira
          automaticamente a primeira mensagem no chat — sem você fazer nada. É assim que a conversa começa de verdade.
        </p>
        <div className="flex gap-2 flex-wrap">
          <button onClick={checarAceites} disabled={checando}
            className="flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-dark text-white px-4 py-2 text-sm font-medium disabled:opacity-60">
            {checando ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />} Checar aceites agora
          </button>
          <button onClick={sincronizar} disabled={sincronizando}
            className="flex items-center gap-2 rounded-lg border border-brand/40 text-brand px-4 py-2 text-sm hover:bg-brand/5 disabled:opacity-60">
            {sincronizando ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowDownToLine className="h-4 w-4" />} Importar conexões para o CRM
          </button>
        </div>
      </div>

      {/* Conexões */}
      <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-ink flex items-center gap-2"><Users className="h-5 w-5 text-brand" /> Mandar mensagem no chat</h2>
          <button onClick={() => carregar()} className="flex items-center gap-1 text-sm text-brand hover:underline">
            <RefreshCw className="h-4 w-4" /> Atualizar
          </button>
        </div>

        <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-3 flex gap-2">
          <Info className="h-5 w-5 text-emerald-600 shrink-0" />
          <p className="text-sm text-emerald-900">
            Estas são pessoas que <strong>já são suas conexões</strong> — com elas a mensagem cai
            direto na <strong>caixa de entrada do LinkedIn</strong> (e aparece no seu chat também).
          </p>
        </div>

        {!conexoes || conexoes.perfis.length === 0 ? (
          <p className="text-sm text-ink-soft py-6 text-center">
            Nenhuma conexão carregada. Verifique a configuração do Unipile em Conexões.
          </p>
        ) : (
          <>
            <label className="flex items-center gap-2 text-sm text-ink-soft">
              <input type="checkbox" className="h-4 w-4 accent-brand"
                checked={selecionados.size === conexoes.perfis.length && conexoes.perfis.length > 0}
                onChange={(e) => setSelecionados(e.target.checked ? new Set(conexoes.perfis.map((p) => p.provider_id)) : new Set())} />
              Selecionar todos ({conexoes.perfis.length})
            </label>

            <div className="space-y-2 max-h-96 overflow-y-auto">
              {conexoes.perfis.map((p) => (
                <div key={p.provider_id} className="flex items-start gap-3 rounded-lg border border-slate-200 p-3">
                  <input type="checkbox" className="h-4 w-4 accent-brand mt-1"
                    checked={selecionados.has(p.provider_id)} onChange={() => alternar(p.provider_id)} />
                  <div className="flex-1">
                    <p className="font-medium text-ink text-sm">{p.nome}</p>
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

            <button onClick={enviarMensagens} disabled={enviando || selecionados.size === 0}
              className="flex items-center gap-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 text-sm font-medium disabled:opacity-50">
              {enviando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              Gerar e enviar para {selecionados.size} conexão(ões)
            </button>

            {resultado && (
              <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-3 text-sm text-emerald-900">
                <p className="font-medium flex items-center gap-1"><CheckCircle2 className="h-4 w-4" /> {resultado.enfileirados} mensagem(ns) na fila!</p>
                <p className="text-xs mt-1">Restam {resultado.restante_hoje} envios hoje (limite {resultado.limite_diario}).</p>
                {resultado.aviso && <p className="text-xs text-amber-800 mt-1">⚠️ {resultado.aviso}</p>}
              </div>
            )}
          </>
        )}
      </div>

      {/* InMail */}
      {saldo && (
        <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm space-y-2">
          <h2 className="font-semibold text-ink flex items-center gap-2"><Mail className="h-5 w-5 text-violet-600" /> InMail (falar com quem não é conexão)</h2>
          {saldo.disponivel ? (
            <>
              <p className="text-sm text-ink-soft">
                Você tem créditos! Na tela de <strong>Prospecção</strong>, escolha o tipo <strong>InMail</strong> para
                mandar mensagem direto no chat de quem ainda não é sua conexão.
              </p>
              <div className="flex gap-4 text-sm text-ink-soft">
                <span>Premium: <strong className="text-ink">{saldo.premium ?? 0}</strong></span>
                <span>Sales Navigator: <strong className="text-ink">{saldo.sales_navigator ?? 0}</strong></span>
                <span>Recruiter: <strong className="text-ink">{saldo.recruiter ?? 0}</strong></span>
              </div>
            </>
          ) : (
            <p className="text-sm text-ink-soft">{saldo.aviso}</p>
          )}
        </div>
      )}
    </div>
  );
}
