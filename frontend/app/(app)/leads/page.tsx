"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Plus, Trash2, X, Users, Loader2, Target, Copy, Check } from "lucide-react";

type Lead = {
  id: number;
  nome: string;
  headline: string;
  empresa: string;
  cargo: string;
  linkedin_url: string;
  origem: string;
  status: string;
  notas: string;
  criado_em: string;
};

const STATUS = ["NOVO", "SEGUINDO", "CONVIDADO", "ABORDADO", "RESPONDEU", "QUALIFICADO", "GANHO", "PERDIDO"];
const CORES: Record<string, string> = {
  NOVO: "bg-slate-100 text-slate-700",
  SEGUINDO: "bg-blue-100 text-blue-700",
  CONVIDADO: "bg-indigo-100 text-indigo-700",
  ABORDADO: "bg-amber-100 text-amber-700",
  RESPONDEU: "bg-cyan-100 text-cyan-700",
  QUALIFICADO: "bg-violet-100 text-violet-700",
  GANHO: "bg-emerald-100 text-emerald-700",
  PERDIDO: "bg-red-100 text-red-700",
};

const VAZIO = { nome: "", headline: "", empresa: "", cargo: "", linkedin_url: "", origem: "", status: "NOVO", notas: "" };

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [aberto, setAberto] = useState(false);
  const [form, setForm] = useState<typeof VAZIO>(VAZIO);
  const [salvando, setSalvando] = useState(false);

  // modal de abordagem gerada
  const [abordagem, setAbordagem] = useState<string | null>(null);
  const [gerandoId, setGerandoId] = useState<number | null>(null);
  const [copiado, setCopiado] = useState(false);

  async function carregar() {
    setCarregando(true);
    try {
      setLeads(await api<Lead[]>("/leads"));
    } finally {
      setCarregando(false);
    }
  }
  useEffect(() => { carregar(); }, []);

  async function salvar() {
    setSalvando(true);
    try {
      await api("/leads", { method: "POST", body: form });
      setAberto(false);
      setForm(VAZIO);
      await carregar();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro");
    } finally {
      setSalvando(false);
    }
  }

  async function mudarStatus(lead: Lead, status: string) {
    await api(`/leads/${lead.id}`, { method: "PUT", body: { status } });
    setLeads((prev) => prev.map((l) => (l.id === lead.id ? { ...l, status } : l)));
  }

  async function excluir(id: number) {
    if (!confirm("Excluir este lead?")) return;
    await api(`/leads/${id}`, { method: "DELETE" });
    await carregar();
  }

  async function gerarAbordagem(lead: Lead) {
    setGerandoId(lead.id);
    setAbordagem(null);
    try {
      const r = await api<{ abordagem: string }>("/agents/prospectar", { method: "POST", body: { lead_id: lead.id } });
      setAbordagem(r.abordagem);
    } catch (e) {
      setAbordagem(`⚠️ ${e instanceof Error ? e.message : "Erro ao gerar"}`);
    } finally {
      setGerandoId(null);
    }
  }

  const input = "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ink">Leads (CRM)</h1>
          <p className="text-ink-soft mt-1">Seu funil de prospecção.</p>
        </div>
        <button onClick={() => { setForm(VAZIO); setAberto(true); }} className="flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-dark text-white px-4 py-2 text-sm font-medium">
          <Plus className="h-4 w-4" /> Novo Lead
        </button>
      </div>

      {carregando ? (
        <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-brand" /></div>
      ) : leads.length === 0 ? (
        <div className="rounded-xl bg-white border border-slate-200 p-10 text-center">
          <Users className="h-8 w-8 text-slate-300 mx-auto mb-2" />
          <p className="text-ink-soft">Nenhum lead ainda. Clique em "Novo Lead".</p>
        </div>
      ) : (
        <div className="rounded-xl bg-white border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-ink-soft">
              <tr>
                <th className="text-left px-4 py-3 font-medium">Nome</th>
                <th className="text-left px-4 py-3 font-medium">Empresa / Cargo</th>
                <th className="text-left px-4 py-3 font-medium">Status</th>
                <th className="text-right px-4 py-3 font-medium">Ações</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((l) => (
                <tr key={l.id} className="border-t border-slate-100">
                  <td className="px-4 py-3">
                    <p className="font-medium text-ink">{l.nome}</p>
                    {l.headline && <p className="text-xs text-ink-soft">{l.headline}</p>}
                  </td>
                  <td className="px-4 py-3 text-ink-soft">{[l.empresa, l.cargo].filter(Boolean).join(" · ")}</td>
                  <td className="px-4 py-3">
                    <select value={l.status} onChange={(e) => mudarStatus(l, e.target.value)} className={`text-xs rounded-full px-2 py-1 border-0 cursor-pointer ${CORES[l.status] || ""}`}>
                      {STATUS.map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1">
                      <button onClick={() => gerarAbordagem(l)} disabled={gerandoId === l.id} title="Gerar abordagem com IA" className="flex items-center gap-1 text-xs rounded-lg border border-brand/30 text-brand px-2 py-1 hover:bg-brand/5 disabled:opacity-50">
                        {gerandoId === l.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Target className="h-3.5 w-3.5" />} Abordagem
                      </button>
                      <button onClick={() => excluir(l.id)} className="p-1.5 rounded-lg hover:bg-red-50 text-red-500"><Trash2 className="h-4 w-4" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal novo lead */}
      {aberto && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={() => setAberto(false)}>
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-ink">Novo Lead</h2>
              <button onClick={() => setAberto(false)} className="p-1 rounded hover:bg-slate-100"><X className="h-5 w-5" /></button>
            </div>
            <div className="space-y-3">
              <input className={input} placeholder="Nome *" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} />
              <input className={input} placeholder="Headline (ex.: Diretora Comercial na X)" value={form.headline} onChange={(e) => setForm({ ...form, headline: e.target.value })} />
              <div className="grid grid-cols-2 gap-3">
                <input className={input} placeholder="Empresa" value={form.empresa} onChange={(e) => setForm({ ...form, empresa: e.target.value })} />
                <input className={input} placeholder="Cargo" value={form.cargo} onChange={(e) => setForm({ ...form, cargo: e.target.value })} />
              </div>
              <input className={input} placeholder="URL do LinkedIn" value={form.linkedin_url} onChange={(e) => setForm({ ...form, linkedin_url: e.target.value })} />
              <textarea className={input} rows={2} placeholder="Notas" value={form.notas} onChange={(e) => setForm({ ...form, notas: e.target.value })} />
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setAberto(false)} className="rounded-lg border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50">Cancelar</button>
              <button onClick={salvar} disabled={salvando || !form.nome} className="flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-dark text-white px-4 py-2 text-sm font-medium disabled:opacity-60">
                {salvando && <Loader2 className="h-4 w-4 animate-spin" />} Salvar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal abordagem gerada */}
      {abordagem !== null && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={() => setAbordagem(null)}>
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-ink flex items-center gap-2"><Target className="h-5 w-5 text-brand" /> Abordagem gerada</h2>
              <button onClick={() => setAbordagem(null)} className="p-1 rounded hover:bg-slate-100"><X className="h-5 w-5" /></button>
            </div>
            <div className="rounded-lg bg-slate-50 border border-slate-200 p-4 text-sm text-ink whitespace-pre-wrap">{abordagem}</div>
            <div className="flex justify-end mt-4">
              <button onClick={() => { navigator.clipboard.writeText(abordagem); setCopiado(true); setTimeout(() => setCopiado(false), 2000); }} className="flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-dark text-white px-4 py-2 text-sm font-medium">
                {copiado ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />} {copiado ? "Copiado!" : "Copiar"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
