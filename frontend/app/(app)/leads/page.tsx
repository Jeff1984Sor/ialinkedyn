"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Plus, Trash2, X, Users, Loader2, Target, Copy, Check, Send, ShieldAlert, Clock, Mail, ExternalLink, User as UserIcon } from "lucide-react";

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
  ja_abordado: boolean;
  ultimo_contato_em: string | null;
  ultimo_contato_tipo: string;
  ultimo_contato_status: string;
};

type Perfil = {
  nome: string; headline: string; sobre: string; localidade: string;
  linkedin_url: string; foto_url: string; seguidores: number | null; conexoes: number | null;
  emails: string[]; telefones: string[]; sites: string[];
  experiencias: { empresa: string; cargo: string; periodo: string; local: string }[];
  formacoes: { instituicao: string; curso: string; periodo: string }[];
  habilidades: string[]; aviso: string;
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

  // selecao em massa
  const [selecionados, setSelecionados] = useState<Set<number>>(new Set());
  const [tipoMassa, setTipoMassa] = useState<"CONVITE" | "MENSAGEM" | "INMAIL">("CONVITE");
  const [enviandoMassa, setEnviandoMassa] = useState(false);

  // modal de perfil completo
  const [perfil, setPerfil] = useState<Perfil | null>(null);
  const [carregandoPerfil, setCarregandoPerfil] = useState<number | null>(null);
  const [erroPerfil, setErroPerfil] = useState("");

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

  function alternarSel(id: number) {
    const novo = new Set(selecionados);
    novo.has(id) ? novo.delete(id) : novo.add(id);
    setSelecionados(novo);
  }

  async function enviarEmMassa() {
    if (selecionados.size === 0) return;
    if (!confirm(
      `A Maya vai escrever uma abordagem personalizada para ${selecionados.size} lead(s) e colocar na fila.\n\n` +
      `O envio e gradual, respeitando seu limite diario. Continuar?`
    )) return;

    setEnviandoMassa(true);
    try {
      const r = await api<{ enfileirados: number; ja_abordados: number; restante_hoje: number; limite_diario: number; aviso: string }>(
        "/campanha/enfileirar-leads",
        { method: "POST", body: { lead_ids: Array.from(selecionados), tipo: tipoMassa } }
      );
      alert(
        `${r.enfileirados} abordagem(ns) na fila!\n` +
        (r.ja_abordados ? `${r.ja_abordados} ja tinham sido abordados.\n` : "") +
        `Restam ${r.restante_hoje} envios hoje (limite ${r.limite_diario}).` +
        (r.aviso ? `\n\n${r.aviso}` : "")
      );
      setSelecionados(new Set());
      await carregar();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao enfileirar");
    } finally {
      setEnviandoMassa(false);
    }
  }

  async function abrirPerfil(lead: Lead) {
    setCarregandoPerfil(lead.id);
    setPerfil(null);
    setErroPerfil("");
    try {
      setPerfil(await api<Perfil>(`/perfil/lead/${lead.id}`));
    } catch (e) {
      setErroPerfil(e instanceof Error ? e.message : "Erro ao buscar perfil");
      setPerfil({
        nome: lead.nome, headline: lead.headline, sobre: "", localidade: "",
        linkedin_url: lead.linkedin_url, foto_url: "", seguidores: null, conexoes: null,
        emails: [], telefones: [], sites: [], experiencias: [], formacoes: [],
        habilidades: [], aviso: "",
      });
    } finally {
      setCarregandoPerfil(null);
    }
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

  const naoAbordados = leads.filter((l) => !l.ja_abordado);

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
          <p className="text-ink font-medium">Nenhum lead ainda</p>
          <p className="text-ink-soft text-sm mt-1 max-w-md mx-auto">
            O jeito normal é o Caçador trazer os leads do LinkedIn automaticamente.
          </p>
          <a href="/prospeccao" className="inline-flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-dark text-white px-4 py-2 text-sm font-medium mt-4">
            <Target className="h-4 w-4" /> Buscar leads no LinkedIn
          </a>
          <p className="text-xs text-ink-soft mt-3">ou use "Novo Lead" para cadastrar manualmente.</p>
        </div>
      ) : (
        <div className="space-y-3">
        {/* barra de envio em massa */}
        <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-4 flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-ink">
            <input type="checkbox" className="h-4 w-4 accent-brand"
              checked={naoAbordados.length > 0 && selecionados.size === naoAbordados.length}
              onChange={(e) => setSelecionados(e.target.checked ? new Set(naoAbordados.map((l) => l.id)) : new Set())} />
            Selecionar nao abordados ({naoAbordados.length})
          </label>

          <span className="text-sm text-ink-soft">{selecionados.size} selecionado(s)</span>

          <select value={tipoMassa} onChange={(e) => setTipoMassa(e.target.value as "CONVITE" | "MENSAGEM" | "INMAIL")}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand">
            <option value="CONVITE">Convite de conexao</option>
            <option value="MENSAGEM">Mensagem no chat (so conexoes)</option>
            <option value="INMAIL">InMail (consome credito)</option>
          </select>

          <button onClick={enviarEmMassa} disabled={enviandoMassa || selecionados.size === 0}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 text-sm font-medium disabled:opacity-50">
            {enviandoMassa ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            Enviar abordagem em massa
          </button>

          <span className="flex items-center gap-1 text-xs text-ink-soft">
            <ShieldAlert className="h-3.5 w-3.5 text-amber-500" /> envio gradual, respeitando o limite diario
          </span>
        </div>

        <div className="rounded-xl bg-white border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-ink-soft">
              <tr>
                <th className="w-10 px-4 py-3"></th>
                <th className="text-left px-4 py-3 font-medium">Nome</th>
                <th className="text-left px-4 py-3 font-medium">Empresa / Cargo</th>
                <th className="text-left px-4 py-3 font-medium">Status</th>
                <th className="text-left px-4 py-3 font-medium">Abordagem</th>
                <th className="text-right px-4 py-3 font-medium">Ações</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((l) => (
                <tr key={l.id} className="border-t border-slate-100">
                  <td className="px-4 py-3">
                    <input type="checkbox" className="h-4 w-4 accent-brand disabled:opacity-40"
                      disabled={l.ja_abordado}
                      title={l.ja_abordado ? "Ja abordado" : ""}
                      checked={selecionados.has(l.id)} onChange={() => alternarSel(l.id)} />
                  </td>
                  <td className="px-4 py-3">
                    <button onClick={() => abrirPerfil(l)} className="font-medium text-ink hover:text-brand hover:underline text-left flex items-center gap-1">
                      {carregandoPerfil === l.id && <Loader2 className="h-3 w-3 animate-spin" />}
                      {l.nome}
                    </button>
                    {l.headline && <p className="text-xs text-ink-soft">{l.headline}</p>}
                  </td>
                  <td className="px-4 py-3 text-ink-soft">{[l.empresa, l.cargo].filter(Boolean).join(" · ")}</td>
                  <td className="px-4 py-3">
                    <select value={l.status} onChange={(e) => mudarStatus(l, e.target.value)} className={`text-xs rounded-full px-2 py-1 border-0 cursor-pointer ${CORES[l.status] || ""}`}>
                      {STATUS.map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    {l.ja_abordado ? (
                      <div className="flex flex-col">
                        <span className={`inline-flex items-center gap-1 text-[11px] rounded-full px-2 py-0.5 w-fit ${
                          l.ultimo_contato_status === "ENVIADO"
                            ? "bg-emerald-100 text-emerald-700"
                            : "bg-amber-100 text-amber-700"
                        }`}>
                          {l.ultimo_contato_status === "ENVIADO" ? <Check className="h-3 w-3" /> : <Clock className="h-3 w-3" />}
                          {l.ultimo_contato_status === "ENVIADO" ? "Enviado" : "Na fila"}
                        </span>
                        <span className="text-[11px] text-ink-soft mt-0.5">
                          {l.ultimo_contato_tipo}
                          {l.ultimo_contato_em ? ` - ${new Date(l.ultimo_contato_em).toLocaleDateString("pt-BR")}` : ""}
                        </span>
                      </div>
                    ) : (
                      <span className="text-[11px] text-ink-soft">-</span>
                    )}
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

      {/* Modal perfil completo */}
      {perfil && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={() => setPerfil(null)}>
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[85vh] overflow-y-auto p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                {perfil.foto_url ? (
                  <img src={perfil.foto_url} alt="" className="h-14 w-14 rounded-full object-cover" />
                ) : (
                  <div className="h-14 w-14 rounded-full bg-brand/10 flex items-center justify-center">
                    <UserIcon className="h-7 w-7 text-brand" />
                  </div>
                )}
                <div>
                  <h2 className="text-lg font-semibold text-ink">{perfil.nome}</h2>
                  <p className="text-sm text-ink-soft">{perfil.headline}</p>
                  {perfil.localidade && <p className="text-xs text-ink-soft">{perfil.localidade}</p>}
                </div>
              </div>
              <button onClick={() => setPerfil(null)} className="p-1 rounded hover:bg-slate-100"><X className="h-5 w-5" /></button>
            </div>

            {erroPerfil && (
              <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700 mb-3">{erroPerfil}</div>
            )}

            {(perfil.seguidores || perfil.conexoes) && (
              <div className="flex gap-4 text-sm text-ink-soft mb-4">
                {perfil.conexoes != null && <span><strong className="text-ink">{perfil.conexoes}</strong> conexoes</span>}
                {perfil.seguidores != null && <span><strong className="text-ink">{perfil.seguidores}</strong> seguidores</span>}
              </div>
            )}

            {/* CONTATOS */}
            <div className="rounded-xl border border-slate-200 p-4 mb-4">
              <h3 className="font-semibold text-ink text-sm mb-2 flex items-center gap-2">
                <Mail className="h-4 w-4 text-brand" /> Contatos
              </h3>
              {perfil.emails.length === 0 && perfil.telefones.length === 0 && perfil.sites.length === 0 ? (
                <p className="text-sm text-ink-soft">{perfil.aviso || "Nenhum contato disponivel."}</p>
              ) : (
                <div className="space-y-2">
                  {perfil.emails.map((e) => (
                    <div key={e} className="flex items-center justify-between gap-2 text-sm">
                      <span className="text-ink">{e}</span>
                      <button onClick={() => navigator.clipboard.writeText(e)} className="text-xs text-brand hover:underline">copiar</button>
                    </div>
                  ))}
                  {perfil.telefones.map((t) => (
                    <div key={t} className="flex items-center justify-between gap-2 text-sm">
                      <span className="text-ink">{t}</span>
                      <button onClick={() => navigator.clipboard.writeText(t)} className="text-xs text-brand hover:underline">copiar</button>
                    </div>
                  ))}
                  {perfil.sites.map((w) => (
                    <a key={w} href={w} target="_blank" rel="noreferrer" className="block text-sm text-brand hover:underline truncate">{w}</a>
                  ))}
                </div>
              )}
            </div>

            {perfil.sobre && (
              <div className="mb-4">
                <h3 className="font-semibold text-ink text-sm mb-1">Sobre</h3>
                <p className="text-sm text-ink-soft whitespace-pre-wrap">{perfil.sobre}</p>
              </div>
            )}

            {perfil.experiencias.length > 0 && (
              <div className="mb-4">
                <h3 className="font-semibold text-ink text-sm mb-2">Experiencia</h3>
                <div className="space-y-2">
                  {perfil.experiencias.map((x, i) => (
                    <div key={i} className="text-sm">
                      <p className="text-ink font-medium">{x.cargo}</p>
                      <p className="text-ink-soft">{[x.empresa, x.periodo, x.local].filter(Boolean).join(" - ")}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {perfil.formacoes.length > 0 && (
              <div className="mb-4">
                <h3 className="font-semibold text-ink text-sm mb-2">Formacao</h3>
                {perfil.formacoes.map((f, i) => (
                  <p key={i} className="text-sm text-ink-soft">{[f.instituicao, f.curso, f.periodo].filter(Boolean).join(" - ")}</p>
                ))}
              </div>
            )}

            {perfil.habilidades.length > 0 && (
              <div className="mb-4">
                <h3 className="font-semibold text-ink text-sm mb-2">Habilidades</h3>
                <div className="flex flex-wrap gap-1">
                  {perfil.habilidades.map((h) => (
                    <span key={h} className="text-xs bg-slate-100 text-ink-soft rounded px-2 py-0.5">{h}</span>
                  ))}
                </div>
              </div>
            )}

            {perfil.linkedin_url && (
              <a href={perfil.linkedin_url} target="_blank" rel="noreferrer"
                className="inline-flex items-center gap-1 text-sm text-brand hover:underline">
                <ExternalLink className="h-4 w-4" /> Abrir no LinkedIn
              </a>
            )}
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
