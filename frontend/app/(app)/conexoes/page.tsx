"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Link2, Link2Off, Loader2, Save, ShieldAlert, CheckCircle2, Info } from "lucide-react";

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

type Limites = {
  id: number;
  limite_follows_dia: number;
  limite_convites_dia: number;
  limite_mensagens_dia: number;
  modo_chat: string;
  horario_inicio: number;
  horario_fim: number;
};

export default function ConexoesPage() {
  const [status, setStatus] = useState<Status | null>(null);
  const [limites, setLimites] = useState<Limites | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [nome, setNome] = useState("");
  const [conectando, setConectando] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [ok, setOk] = useState(false);

  async function carregar() {
    const [s, l] = await Promise.all([api<Status>("/connection/status"), api<Limites>("/connection/settings")]);
    setStatus(s);
    setLimites(l);
    setNome(s.nome || "");
  }

  useEffect(() => {
    carregar().finally(() => setCarregando(false));
  }, []);

  async function conectar() {
    setConectando(true);
    try {
      const s = await api<Status>("/connection/conectar", { method: "POST", body: { nome: nome || "Minha conta" } });
      setStatus(s);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao conectar");
    } finally {
      setConectando(false);
    }
  }

  async function desconectar() {
    if (!confirm("Desconectar a conta do LinkedIn?")) return;
    const s = await api<Status>("/connection/desconectar", { method: "DELETE" });
    setStatus(s);
  }

  async function salvarLimites() {
    if (!limites) return;
    setSalvando(true);
    setOk(false);
    try {
      const l = await api<Limites>("/connection/settings", { method: "PUT", body: limites });
      setLimites(l);
      setOk(true);
      setTimeout(() => setOk(false), 2500);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao salvar");
    } finally {
      setSalvando(false);
    }
  }

  function setL<K extends keyof Limites>(campo: K, valor: Limites[K]) {
    if (limites) setLimites({ ...limites, [campo]: valor });
  }

  if (carregando || !status || !limites) {
    return <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-brand" /></div>;
  }

  const input = "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand";

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-ink">Conexões</h1>
        <p className="text-ink-soft mt-1">Vincule a conta do LinkedIn e defina os limites de segurança.</p>
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
          <span className={`text-xs rounded-full px-3 py-1 font-medium ${
            status.conectado ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"
          }`}>
            {status.conectado ? "Conectado" : "Desconectado"}
          </span>
        </div>

        <div className="text-sm text-ink-soft">
          Provedor configurado: <strong className="text-ink">{status.provider_configurado}</strong>
          {status.conectado && status.external_account_id && (
            <> · ID: <code className="text-xs bg-slate-100 rounded px-1">{status.external_account_id}</code></>
          )}
        </div>

        {status.conectado ? (
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
            <div className="flex-1">
              <p className="text-sm font-medium text-ink">{status.nome}</p>
              {status.conectado_em && (
                <p className="text-xs text-ink-soft">Conectado em {new Date(status.conectado_em).toLocaleString("pt-BR")}</p>
              )}
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
        <p className="text-sm text-ink-soft">
          O LinkedIn restringe contas que agem como robô. Estes limites fazem a funcionária trabalhar em ritmo humano.
        </p>

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
          <button onClick={salvarLimites} disabled={salvando} className="flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-dark text-white px-5 py-2.5 text-sm font-medium disabled:opacity-60">
            {salvando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Salvar limites
          </button>
          {ok && <span className="text-sm text-emerald-600">Salvo! ✓</span>}
        </div>
      </div>
    </div>
  );
}
