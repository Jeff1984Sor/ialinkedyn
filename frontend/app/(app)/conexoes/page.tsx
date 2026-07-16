"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  Link2, Link2Off, Loader2, Save, ShieldAlert, CheckCircle2, Info,
  Brain, Plug, FlaskConical, XCircle,
} from "lucide-react";

type Status = {
  provider_configurado: string;
  provider_pronto: boolean;
  conectado: boolean;
  nome: string;
  external_account_id: string;
  status: string;
  conectado_em: string | null;
  aviso: string;
};

type Config = {
  linkedin_provider: string;
  unipile_dsn: string;
  unipile_key_configurada: boolean;
  unipile_key_mascarada: string;
  gemini_key_configurada: boolean;
  gemini_key_mascarada: string;
  gemini_model: string;
};

type Limites = {
  id: number;
  limite_follows_dia: number;
  limite_convites_dia: number;
  limite_mensagens_dia: number;
  modo_chat: string;
  horario_inicio: number;
  horario_fim: number;
};

const input = "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand";

export default function ConexoesPage() {
  const [status, setStatus] = useState<Status | null>(null);
  const [config, setConfig] = useState<Config | null>(null);
  const [limites, setLimites] = useState<Limites | null>(null);
  const [carregando, setCarregando] = useState(true);

  // campos de chave (vazio = não alterar)
  const [novaGemini, setNovaGemini] = useState("");
  const [novaUnipile, setNovaUnipile] = useState("");

  const [nome, setNome] = useState("");
  const [conectando, setConectando] = useState(false);
  const [salvandoCfg, setSalvandoCfg] = useState(false);
  const [salvandoLim, setSalvandoLim] = useState(false);
  const [okCfg, setOkCfg] = useState(false);
  const [okLim, setOkLim] = useState(false);
  const [testando, setTestando] = useState(false);
  const [teste, setTeste] = useState<{ ok: boolean; mensagem: string } | null>(null);

  async function carregar() {
    const [s, c, l] = await Promise.all([
      api<Status>("/connection/status"),
      api<Config>("/connection/config"),
      api<Limites>("/connection/settings"),
    ]);
    setStatus(s); setConfig(c); setLimites(l); setNome(s.nome || "");
  }

  useEffect(() => { carregar().finally(() => setCarregando(false)); }, []);

  async function salvarConfig() {
    if (!config) return;
    setSalvandoCfg(true); setOkCfg(false); setTeste(null);
    try {
      const body: Record<string, unknown> = {
        linkedin_provider: config.linkedin_provider,
        unipile_dsn: config.unipile_dsn,
        gemini_model: config.gemini_model,
      };
      if (novaGemini.trim()) body.gemini_api_key = novaGemini.trim();
      if (novaUnipile.trim()) body.unipile_api_key = novaUnipile.trim();

      const c = await api<Config>("/connection/config", { method: "PUT", body });
      setConfig(c); setNovaGemini(""); setNovaUnipile("");
      setStatus(await api<Status>("/connection/status"));
      setOkCfg(true); setTimeout(() => setOkCfg(false), 2500);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao salvar");
    } finally {
      setSalvandoCfg(false);
    }
  }

  async function testarIA() {
    setTestando(true); setTeste(null);
    try {
      setTeste(await api<{ ok: boolean; mensagem: string }>("/connection/testar-ia", { method: "POST" }));
    } catch (e) {
      setTeste({ ok: false, mensagem: e instanceof Error ? e.message : "Erro" });
    } finally {
      setTestando(false);
    }
  }

  async function conectar() {
    setConectando(true);
    try {
      setStatus(await api<Status>("/connection/conectar", { method: "POST", body: { nome: nome || "Minha conta" } }));
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao conectar");
    } finally {
      setConectando(false);
    }
  }

  async function desconectar() {
    if (!confirm("Desconectar a conta do LinkedIn?")) return;
    setStatus(await api<Status>("/connection/desconectar", { method: "DELETE" }));
  }

  async function salvarLimites() {
    if (!limites) return;
    setSalvandoLim(true); setOkLim(false);
    try {
      setLimites(await api<Limites>("/connection/settings", { method: "PUT", body: limites }));
      setOkLim(true); setTimeout(() => setOkLim(false), 2500);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao salvar");
    } finally {
      setSalvandoLim(false);
    }
  }

  function setL<K extends keyof Limites>(campo: K, valor: Limites[K]) {
    if (limites) setLimites({ ...limites, [campo]: valor });
  }
  function setC<K extends keyof Config>(campo: K, valor: Config[K]) {
    if (config) setConfig({ ...config, [campo]: valor });
  }

  if (carregando || !status || !config || !limites) {
    return <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-brand" /></div>;
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-ink">Conexões</h1>
        <p className="text-ink-soft mt-1">Configure a IA, o provedor do LinkedIn e os limites de segurança — tudo por aqui.</p>
      </div>

      {/* IA */}
      <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-violet-600" />
            <h2 className="font-semibold text-ink">Inteligência Artificial (Google Gemini)</h2>
          </div>
          <span className={`text-xs rounded-full px-3 py-1 font-medium ${config.gemini_key_configurada ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
            {config.gemini_key_configurada ? "Configurada" : "Não configurada"}
          </span>
        </div>
        <p className="text-sm text-ink-soft">
          É a chave que faz sua funcionária pensar. Pegue em <a href="https://aistudio.google.com/apikey" target="_blank" rel="noreferrer" className="text-brand hover:underline">aistudio.google.com/apikey</a>. Ela é guardada criptografada.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-ink mb-1">Chave da API</label>
            <input
              type="password"
              className={input}
              value={novaGemini}
              onChange={(e) => setNovaGemini(e.target.value)}
              placeholder={config.gemini_key_configurada ? config.gemini_key_mascarada : "Cole sua chave aqui"}
            />
            <p className="text-xs text-ink-soft mt-1">Deixe em branco para manter a atual.</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-ink mb-1">Modelo</label>
            <select className={input} value={config.gemini_model} onChange={(e) => setC("gemini_model", e.target.value)}>
              <option value="gemini-2.5-flash">gemini-2.5-flash (rápido, recomendado)</option>
              <option value="gemini-2.5-pro">gemini-2.5-pro (mais capaz)</option>
              <option value="gemini-2.0-flash">gemini-2.0-flash</option>
            </select>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={testarIA} disabled={testando} className="flex items-center gap-2 rounded-lg border border-violet-300 text-violet-700 px-4 py-2 text-sm hover:bg-violet-50 disabled:opacity-60">
            {testando ? <Loader2 className="h-4 w-4 animate-spin" /> : <FlaskConical className="h-4 w-4" />} Testar chave
          </button>
          {teste && (
            <span className={`flex items-center gap-1 text-sm ${teste.ok ? "text-emerald-600" : "text-red-600"}`}>
              {teste.ok ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />} {teste.mensagem}
            </span>
          )}
        </div>
      </div>

      {/* Provedor */}
      <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <Plug className="h-5 w-5 text-brand" />
          <h2 className="font-semibold text-ink">Provedor do LinkedIn</h2>
        </div>
        <div>
          <label className="block text-sm font-medium text-ink mb-1">Provedor</label>
          <select className={input} value={config.linkedin_provider} onChange={(e) => setC("linkedin_provider", e.target.value)}>
            <option value="mock">Simulado (mock) — sem custo, sem risco</option>
            <option value="unipile">Unipile — conexão real (pago)</option>
          </select>
        </div>
        {config.linkedin_provider === "unipile" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-ink mb-1">Unipile API Key</label>
              <input
                type="password"
                className={input}
                value={novaUnipile}
                onChange={(e) => setNovaUnipile(e.target.value)}
                placeholder={config.unipile_key_configurada ? config.unipile_key_mascarada : "Cole a chave do Unipile"}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-ink mb-1">Unipile DSN</label>
              <input className={input} value={config.unipile_dsn} onChange={(e) => setC("unipile_dsn", e.target.value)} placeholder="ex.: api1.unipile.com:13111" />
            </div>
          </div>
        )}
        <div className="flex items-center gap-3">
          <button onClick={salvarConfig} disabled={salvandoCfg} className="flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-dark text-white px-5 py-2.5 text-sm font-medium disabled:opacity-60">
            {salvandoCfg ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Salvar configuração
          </button>
          {okCfg && <span className="text-sm text-emerald-600">Salvo! ✓</span>}
        </div>
      </div>

      {/* Aviso do provedor */}
      {status.aviso && (
        <div className="rounded-xl bg-amber-50 border border-amber-200 p-4 flex gap-3">
          <Info className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
          <p className="text-sm text-amber-900">{status.aviso}</p>
        </div>
      )}

      {/* Conta */}
      <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-ink">Conta do LinkedIn</h2>
          <span className={`text-xs rounded-full px-3 py-1 font-medium ${status.conectado ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>
            {status.conectado ? "Conectado" : "Desconectado"}
          </span>
        </div>

        {status.conectado ? (
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
            <div className="flex-1">
              <p className="text-sm font-medium text-ink">{status.nome}</p>
              {status.conectado_em && <p className="text-xs text-ink-soft">Conectado em {new Date(status.conectado_em).toLocaleString("pt-BR")}</p>}
            </div>
            <button onClick={desconectar} className="flex items-center gap-2 rounded-lg border border-red-200 text-red-600 px-4 py-2 text-sm hover:bg-red-50">
              <Link2Off className="h-4 w-4" /> Desconectar
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-ink mb-1">Apelido da conta</label>
              <input className={input} value={nome} onChange={(e) => setNome(e.target.value)} placeholder="ex.: LinkedIn da MayaCorp" />
            </div>
            <button onClick={conectar} disabled={conectando || !status.provider_pronto} className="flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-dark text-white px-5 py-2.5 text-sm font-medium disabled:opacity-60">
              {conectando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Link2 className="h-4 w-4" />} Conectar LinkedIn
            </button>
          </div>
        )}
      </div>

      {/* Limites anti-ban */}
      <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-amber-500" />
          <h2 className="font-semibold text-ink">Limites de automação (anti-ban)</h2>
        </div>
        <p className="text-sm text-ink-soft">O LinkedIn restringe contas que agem como robô. Estes limites fazem a funcionária trabalhar em ritmo humano.</p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-ink mb-1">Follows / dia</label>
            <input type="number" min={0} max={100} className={input} value={limites.limite_follows_dia} onChange={(e) => setL("limite_follows_dia", Number(e.target.value))} />
          </div>
          <div>
            <label className="block text-sm font-medium text-ink mb-1">Convites / dia</label>
            <input type="number" min={0} max={100} className={input} value={limites.limite_convites_dia} onChange={(e) => setL("limite_convites_dia", Number(e.target.value))} />
          </div>
          <div>
            <label className="block text-sm font-medium text-ink mb-1">Mensagens / dia</label>
            <input type="number" min={0} max={200} className={input} value={limites.limite_mensagens_dia} onChange={(e) => setL("limite_mensagens_dia", Number(e.target.value))} />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-ink mb-1">Início (hora)</label>
            <input type="number" min={0} max={23} className={input} value={limites.horario_inicio} onChange={(e) => setL("horario_inicio", Number(e.target.value))} />
          </div>
          <div>
            <label className="block text-sm font-medium text-ink mb-1">Fim (hora)</label>
            <input type="number" min={0} max={23} className={input} value={limites.horario_fim} onChange={(e) => setL("horario_fim", Number(e.target.value))} />
          </div>
          <div>
            <label className="block text-sm font-medium text-ink mb-1">Modo do chat</label>
            <select className={input} value={limites.modo_chat} onChange={(e) => setL("modo_chat", e.target.value)}>
              <option value="MANUAL">Aprovar e enviar (seguro)</option>
              <option value="AUTO">Automático (IA envia sozinha)</option>
            </select>
          </div>
        </div>

        <div className="flex items-center gap-3 pt-1">
          <button onClick={salvarLimites} disabled={salvandoLim} className="flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-dark text-white px-5 py-2.5 text-sm font-medium disabled:opacity-60">
            {salvandoLim ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Salvar limites
          </button>
          {okLim && <span className="text-sm text-emerald-600">Salvo! ✓</span>}
        </div>
      </div>
    </div>
  );
}
