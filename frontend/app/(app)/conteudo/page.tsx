"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  Loader2, Wand2, Send, Trash2, Clock, CheckCircle2, XCircle,
  FileText, CalendarClock, Save,
} from "lucide-react";

type Post = {
  id: number;
  texto: string;
  tema: string;
  status: string;
  agendado_para: string | null;
  publicado_em: string | null;
  external_id: string;
  erro: string;
  criado_em: string;
};

const CORES: Record<string, string> = {
  RASCUNHO: "bg-slate-100 text-slate-700",
  AGENDADO: "bg-amber-100 text-amber-700",
  PUBLICADO: "bg-emerald-100 text-emerald-700",
  ERRO: "bg-red-100 text-red-700",
};

const input = "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand";

export default function ConteudoPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [carregando, setCarregando] = useState(true);

  const [tema, setTema] = useState("");
  const [gerando, setGerando] = useState(false);

  const [editando, setEditando] = useState<Post | null>(null);
  const [texto, setTexto] = useState("");
  const [quando, setQuando] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [publicando, setPublicando] = useState<number | null>(null);

  async function carregar() {
    setCarregando(true);
    try {
      setPosts(await api<Post[]>("/posts"));
    } finally {
      setCarregando(false);
    }
  }
  useEffect(() => { carregar(); }, []);

  async function gerar() {
    if (!tema.trim()) return;
    setGerando(true);
    try {
      const r = await api<{ texto: string; post_id: number | null }>("/posts/gerar", {
        method: "POST", body: { tema, salvar: true },
      });
      setTema("");
      await carregar();
      if (r.post_id) {
        setEditando({ ...(await api<Post[]>("/posts")).find((p) => p.id === r.post_id)! });
        setTexto(r.texto);
        setQuando("");
      }
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao gerar");
    } finally {
      setGerando(false);
    }
  }

  function abrir(p: Post) {
    setEditando(p);
    setTexto(p.texto);
    setQuando(p.agendado_para ? p.agendado_para.slice(0, 16) : "");
  }

  async function salvar() {
    if (!editando) return;
    setSalvando(true);
    try {
      await api(`/posts/${editando.id}`, {
        method: "PUT",
        body: { texto, agendado_para: quando ? new Date(quando).toISOString() : null },
      });
      setEditando(null);
      await carregar();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao salvar");
    } finally {
      setSalvando(false);
    }
  }

  async function publicar(p: Post) {
    if (!confirm("Publicar agora no seu feed do LinkedIn?")) return;
    setPublicando(p.id);
    try {
      await api(`/posts/${p.id}/publicar`, { method: "POST" });
      await carregar();
      setEditando(null);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao publicar");
      await carregar();
    } finally {
      setPublicando(null);
    }
  }

  async function excluir(id: number) {
    if (!confirm("Excluir este post?")) return;
    await api(`/posts/${id}`, { method: "DELETE" });
    if (editando?.id === id) setEditando(null);
    await carregar();
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">Conteúdo</h1>
        <p className="text-ink-soft mt-1">A Maya escreve os posts, você agenda e o sistema publica sozinho.</p>
      </div>

      {/* Gerar */}
      <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm space-y-3">
        <label className="block text-sm font-medium text-ink">Sobre o que a Maya deve escrever?</label>
        <div className="flex gap-2">
          <input className={input} value={tema} onChange={(e) => setTema(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && gerar()}
            placeholder="ex.: por que projeto de software atrasa e como evitamos isso" />
          <button onClick={gerar} disabled={gerando || !tema.trim()}
            className="flex items-center gap-2 rounded-lg bg-violet-600 hover:bg-violet-700 text-white px-5 py-2 text-sm font-medium disabled:opacity-60 whitespace-nowrap">
            {gerando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />} Escrever post
          </button>
        </div>
      </div>

      {/* Editor */}
      {editando && (
        <div className="rounded-xl bg-white border-2 border-brand/30 p-6 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-ink">Editar post</h2>
            <span className={`text-xs rounded-full px-2 py-0.5 ${CORES[editando.status]}`}>{editando.status}</span>
          </div>

          <textarea className={input} rows={14} value={texto} onChange={(e) => setTexto(e.target.value)} />
          <p className="text-xs text-ink-soft">{texto.length} caracteres</p>

          <div>
            <label className="block text-sm font-medium text-ink mb-1 flex items-center gap-1">
              <CalendarClock className="h-4 w-4" /> Agendar para (deixe vazio para manter rascunho)
            </label>
            <input type="datetime-local" className={input} value={quando} onChange={(e) => setQuando(e.target.value)} />
          </div>

          <div className="flex gap-2 flex-wrap">
            <button onClick={salvar} disabled={salvando}
              className="flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-dark text-white px-4 py-2 text-sm font-medium disabled:opacity-60">
              {salvando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              {quando ? "Salvar e agendar" : "Salvar rascunho"}
            </button>
            <button onClick={() => publicar(editando)} disabled={publicando === editando.id}
              className="flex items-center gap-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 text-sm font-medium disabled:opacity-60">
              {publicando === editando.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />} Publicar agora
            </button>
            <button onClick={() => setEditando(null)} className="rounded-lg border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50">Fechar</button>
          </div>
        </div>
      )}

      {/* Lista */}
      {carregando ? (
        <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-brand" /></div>
      ) : posts.length === 0 ? (
        <div className="rounded-xl bg-white border border-slate-200 p-10 text-center">
          <FileText className="h-8 w-8 text-slate-300 mx-auto mb-2" />
          <p className="text-ink-soft">Nenhum post ainda. Escreva um tema acima e deixe a Maya criar.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {posts.map((p) => (
            <div key={p.id} className="rounded-xl bg-white border border-slate-200 p-4 shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 cursor-pointer" onClick={() => abrir(p)}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs rounded-full px-2 py-0.5 ${CORES[p.status]}`}>{p.status}</span>
                    {p.status === "AGENDADO" && p.agendado_para && (
                      <span className="flex items-center gap-1 text-xs text-ink-soft">
                        <Clock className="h-3 w-3" /> {new Date(p.agendado_para).toLocaleString("pt-BR")}
                      </span>
                    )}
                    {p.status === "PUBLICADO" && p.publicado_em && (
                      <span className="flex items-center gap-1 text-xs text-emerald-600">
                        <CheckCircle2 className="h-3 w-3" /> {new Date(p.publicado_em).toLocaleString("pt-BR")}
                      </span>
                    )}
                  </div>
                  {p.tema && <p className="text-xs text-ink-soft mb-1">Tema: {p.tema}</p>}
                  <p className="text-sm text-ink whitespace-pre-wrap line-clamp-4">{p.texto}</p>
                  {p.erro && (
                    <p className="flex items-center gap-1 text-xs text-red-600 mt-1">
                      <XCircle className="h-3 w-3" /> {p.erro}
                    </p>
                  )}
                </div>
                <button onClick={() => excluir(p.id)} className="p-2 rounded-lg hover:bg-red-50 text-red-500 shrink-0">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
