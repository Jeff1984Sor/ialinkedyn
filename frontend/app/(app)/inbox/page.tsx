"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { MessagesSquare, Loader2, Sparkles, Send, Plus, Copy, Check } from "lucide-react";

type Resumo = { id: number; lead_id: number; lead_nome: string; ultima_mensagem: string };
type Msg = { id: number; autor: string; conteudo: string; criado_em: string };
type Detalhe = { id: number; lead_id: number; lead_nome: string; mensagens: Msg[] };
type Lead = { id: number; nome: string };

export default function InboxPage() {
  const [conversas, setConversas] = useState<Resumo[]>([]);
  const [atual, setAtual] = useState<Detalhe | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [novaMsg, setNovaMsg] = useState("");
  const [gerando, setGerando] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [copiado, setCopiado] = useState<number | null>(null);

  // criar conversa
  const [leads, setLeads] = useState<Lead[]>([]);
  const [modalNova, setModalNova] = useState(false);

  async function carregarLista() {
    setCarregando(true);
    try {
      setConversas(await api<Resumo[]>("/conversations"));
    } finally {
      setCarregando(false);
    }
  }
  useEffect(() => { carregarLista(); }, []);

  async function abrir(id: number) {
    setAtual(await api<Detalhe>(`/conversations/${id}`));
  }

  async function adicionarMsgLead() {
    if (!atual || !novaMsg.trim()) return;
    setEnviando(true);
    try {
      await api(`/conversations/${atual.id}/messages`, { method: "POST", body: { autor: "LEAD", conteudo: novaMsg } });
      setNovaMsg("");
      await abrir(atual.id);
    } finally {
      setEnviando(false);
    }
  }

  async function responderIA() {
    if (!atual) return;
    setGerando(true);
    try {
      await api("/agents/responder", { method: "POST", body: { conversation_id: atual.id, salvar_rascunho: true } });
      await abrir(atual.id);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao gerar resposta");
    } finally {
      setGerando(false);
    }
  }

  async function abrirModalNova() {
    setLeads(await api<Lead[]>("/leads"));
    setModalNova(true);
  }

  async function criarConversa(leadId: number) {
    const d = await api<Detalhe>("/conversations", { method: "POST", body: { lead_id: leadId } });
    setModalNova(false);
    await carregarLista();
    setAtual(d);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ink">Conversas</h1>
          <p className="text-ink-soft mt-1">A IA sugere respostas com base no seu Banco de Q&amp;A.</p>
        </div>
        <button onClick={abrirModalNova} className="flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-dark text-white px-4 py-2 text-sm font-medium">
          <Plus className="h-4 w-4" /> Nova conversa
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 h-[70vh]">
        {/* Lista */}
        <div className="rounded-xl bg-white border border-slate-200 shadow-sm overflow-y-auto">
          {carregando ? (
            <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-brand" /></div>
          ) : conversas.length === 0 ? (
            <div className="p-6 text-center text-ink-soft text-sm">
              <MessagesSquare className="h-8 w-8 text-slate-300 mx-auto mb-2" />
              Nenhuma conversa. Crie uma.
            </div>
          ) : (
            conversas.map((c) => (
              <button key={c.id} onClick={() => abrir(c.id)} className={`w-full text-left px-4 py-3 border-b border-slate-100 hover:bg-slate-50 ${atual?.id === c.id ? "bg-brand/5" : ""}`}>
                <p className="font-medium text-ink text-sm">{c.lead_nome || "Lead"}</p>
                <p className="text-xs text-ink-soft truncate">{c.ultima_mensagem || "(sem mensagens)"}</p>
              </button>
            ))
          )}
        </div>

        {/* Detalhe */}
        <div className="md:col-span-2 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col">
          {!atual ? (
            <div className="flex-1 flex items-center justify-center text-ink-soft text-sm">Selecione uma conversa</div>
          ) : (
            <>
              <div className="px-4 py-3 border-b border-slate-100 font-medium text-ink">{atual.lead_nome || "Lead"}</div>
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {atual.mensagens.length === 0 && <p className="text-center text-ink-soft text-sm">Sem mensagens. Cole abaixo a mensagem que o lead te mandou.</p>}
                {atual.mensagens.map((m) => (
                  <div key={m.id} className={`flex ${m.autor === "LEAD" ? "justify-start" : "justify-end"}`}>
                    <div className={`max-w-[80%] rounded-2xl px-3 py-2 text-sm ${
                      m.autor === "LEAD" ? "bg-slate-100 text-ink" :
                      m.autor === "IA_RASCUNHO" ? "bg-amber-50 border border-amber-200 text-ink" :
                      "bg-brand text-white"
                    }`}>
                      {m.autor === "IA_RASCUNHO" && (
                        <div className="flex items-center gap-1 text-[11px] text-amber-600 mb-1"><Sparkles className="h-3 w-3" /> Rascunho da IA</div>
                      )}
                      <p className="whitespace-pre-wrap">{m.conteudo}</p>
                      {m.autor === "IA_RASCUNHO" && (
                        <button onClick={() => { navigator.clipboard.writeText(m.conteudo); setCopiado(m.id); setTimeout(() => setCopiado(null), 2000); }} className="mt-1 flex items-center gap-1 text-[11px] text-amber-700 hover:underline">
                          {copiado === m.id ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />} {copiado === m.id ? "Copiado" : "Copiar"}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              <div className="p-3 border-t border-slate-100 space-y-2">
                <button onClick={responderIA} disabled={gerando} className="w-full flex items-center justify-center gap-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-white py-2 text-sm font-medium disabled:opacity-60">
                  {gerando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />} Responder com IA
                </button>
                <div className="flex gap-2">
                  <input value={novaMsg} onChange={(e) => setNovaMsg(e.target.value)} onKeyDown={(e) => e.key === "Enter" && adicionarMsgLead()} placeholder="Cole aqui a mensagem do lead..." className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand" />
                  <button onClick={adicionarMsgLead} disabled={enviando || !novaMsg.trim()} className="rounded-lg bg-slate-800 hover:bg-slate-900 text-white px-3 py-2 disabled:opacity-60"><Send className="h-4 w-4" /></button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {modalNova && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={() => setModalNova(false)}>
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-semibold text-ink mb-3">Nova conversa — escolha o lead</h2>
            {leads.length === 0 ? (
              <p className="text-sm text-ink-soft">Nenhum lead cadastrado. Crie um lead primeiro na aba Leads.</p>
            ) : (
              <div className="space-y-1 max-h-72 overflow-y-auto">
                {leads.map((l) => (
                  <button key={l.id} onClick={() => criarConversa(l.id)} className="w-full text-left px-3 py-2 rounded-lg hover:bg-slate-50 text-sm text-ink">{l.nome}</button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
