"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Plus, Trash2, Pencil, X, BookOpen, Loader2 } from "lucide-react";

type QA = {
  id: number;
  pergunta: string;
  resposta: string;
  tags: string;
  categoria: string;
  ativo: boolean;
  criado_em: string;
};

const VAZIO = { pergunta: "", resposta: "", tags: "", categoria: "", ativo: true };

export default function ConhecimentoPage() {
  const [itens, setItens] = useState<QA[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [form, setForm] = useState<typeof VAZIO>(VAZIO);
  const [editId, setEditId] = useState<number | null>(null);
  const [aberto, setAberto] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [busca, setBusca] = useState("");

  async function carregar() {
    setCarregando(true);
    try {
      const dados = await api<QA[]>(`/knowledge${busca ? `?q=${encodeURIComponent(busca)}` : ""}`);
      setItens(dados);
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function abrirNovo() {
    setForm(VAZIO);
    setEditId(null);
    setAberto(true);
  }

  function abrirEdicao(qa: QA) {
    setForm({ pergunta: qa.pergunta, resposta: qa.resposta, tags: qa.tags, categoria: qa.categoria, ativo: qa.ativo });
    setEditId(qa.id);
    setAberto(true);
  }

  async function salvar() {
    setSalvando(true);
    try {
      if (editId) {
        await api(`/knowledge/${editId}`, { method: "PUT", body: form });
      } else {
        await api("/knowledge", { method: "POST", body: form });
      }
      setAberto(false);
      await carregar();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao salvar");
    } finally {
      setSalvando(false);
    }
  }

  async function excluir(id: number) {
    if (!confirm("Excluir esta pergunta/resposta?")) return;
    await api(`/knowledge/${id}`, { method: "DELETE" });
    await carregar();
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ink">Base de Conhecimento</h1>
          <p className="text-ink-soft mt-1">Perguntas &amp; Respostas que a IA usa para responder no seu tom.</p>
        </div>
        <button onClick={abrirNovo} className="flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-dark text-white px-4 py-2 text-sm font-medium">
          <Plus className="h-4 w-4" /> Nova Q&amp;A
        </button>
      </div>

      <div className="flex gap-2">
        <input
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && carregar()}
          placeholder="Buscar..."
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand"
        />
        <button onClick={carregar} className="rounded-lg border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50">Buscar</button>
      </div>

      {carregando ? (
        <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-brand" /></div>
      ) : itens.length === 0 ? (
        <div className="rounded-xl bg-white border border-slate-200 p-10 text-center">
          <BookOpen className="h-8 w-8 text-slate-300 mx-auto mb-2" />
          <p className="text-ink-soft">Nenhuma Q&amp;A cadastrada ainda. Clique em "Nova Q&amp;A".</p>
        </div>
      ) : (
        <div className="space-y-3">
          {itens.map((qa) => (
            <div key={qa.id} className="rounded-xl bg-white border border-slate-200 p-4 shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <p className="font-medium text-ink">{qa.pergunta}</p>
                  <p className="text-sm text-ink-soft mt-1 whitespace-pre-wrap">{qa.resposta}</p>
                  {(qa.tags || qa.categoria) && (
                    <div className="flex gap-2 mt-2 flex-wrap">
                      {qa.categoria && <span className="text-xs bg-brand/10 text-brand rounded px-2 py-0.5">{qa.categoria}</span>}
                      {qa.tags.split(",").filter(Boolean).map((t) => (
                        <span key={t} className="text-xs bg-slate-100 text-ink-soft rounded px-2 py-0.5">{t.trim()}</span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex gap-1">
                  <button onClick={() => abrirEdicao(qa)} className="p-2 rounded-lg hover:bg-slate-100 text-ink-soft"><Pencil className="h-4 w-4" /></button>
                  <button onClick={() => excluir(qa.id)} className="p-2 rounded-lg hover:bg-red-50 text-red-500"><Trash2 className="h-4 w-4" /></button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {aberto && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={() => setAberto(false)}>
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-ink">{editId ? "Editar" : "Nova"} Pergunta &amp; Resposta</h2>
              <button onClick={() => setAberto(false)} className="p-1 rounded hover:bg-slate-100"><X className="h-5 w-5" /></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-ink mb-1">Pergunta</label>
                <textarea value={form.pergunta} onChange={(e) => setForm({ ...form, pergunta: e.target.value })} rows={2} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand" placeholder="ex.: Quanto custa?" />
              </div>
              <div>
                <label className="block text-sm font-medium text-ink mb-1">Resposta</label>
                <textarea value={form.resposta} onChange={(e) => setForm({ ...form, resposta: e.target.value })} rows={4} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand" placeholder="ex.: Nossos planos começam em..." />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-ink mb-1">Categoria</label>
                  <input value={form.categoria} onChange={(e) => setForm({ ...form, categoria: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand" placeholder="ex.: Preços" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-ink mb-1">Tags (vírgula)</label>
                  <input value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand" placeholder="ex.: preço, plano" />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setAberto(false)} className="rounded-lg border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50">Cancelar</button>
              <button onClick={salvar} disabled={salvando || !form.pergunta || !form.resposta} className="flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-dark text-white px-4 py-2 text-sm font-medium disabled:opacity-60">
                {salvando && <Loader2 className="h-4 w-4 animate-spin" />} Salvar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
