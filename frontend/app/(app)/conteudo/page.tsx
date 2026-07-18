"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  Loader2, Wand2, Send, Trash2, Clock, CheckCircle2, XCircle,
  FileText, CalendarClock, Save, Image as ImageIcon, Upload, Repeat, Plus,
} from "lucide-react";

type Post = {
  id: number;
  texto: string;
  tema: string;
  status: string;
  agendado_para: string | null;
  publicado_em: string | null;
  imagem_path: string;
  external_id: string;
  erro: string;
  criado_em: string;
};

type Recorrencia = {
  id: number; nome: string; tema: string; frequencia: string;
  dias_semana: string; hora: number; imagem_path: string;
  gerar_imagem_ia: boolean; publicar_automatico: boolean; ativo: boolean;
  ultimo_criado_em: string | null;
};

const DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"];
const urlImagem = (caminho: string) =>
  caminho ? `/api/midia/${caminho.split(/[\\/]/).pop()}` : "";

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
  const [gerandoImg, setGerandoImg] = useState(false);
  const [enviandoImg, setEnviandoImg] = useState(false);

  // recorrencias
  const [recs, setRecs] = useState<Recorrencia[]>([]);
  const [modalRec, setModalRec] = useState(false);
  const [novaRec, setNovaRec] = useState({
    nome: "", tema: "", frequencia: "SEMANAL", dias_semana: "", hora: 9,
    gerar_imagem_ia: true, publicar_automatico: true, ativo: true,
  });

  async function carregar() {
    setCarregando(true);
    try {
      setPosts(await api<Post[]>("/posts"));
    } finally {
      setCarregando(false);
    }
  }
  async function carregarRecs() {
    setRecs(await api<Recorrencia[]>("/recorrencias"));
  }
  useEffect(() => { carregar(); carregarRecs(); }, []);

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

  async function gerarImagem() {
    if (!editando) return;
    setGerandoImg(true);
    try {
      const r = await api<{ url: string; prompt_usado: string }>(
        `/posts/${editando.id}/gerar-imagem`, { method: "POST" }
      );
      const atualizados = await api<Post[]>("/posts");
      setPosts(atualizados);
      const atual = atualizados.find((x) => x.id === editando.id);
      if (atual) setEditando(atual);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao gerar imagem");
    } finally {
      setGerandoImg(false);
    }
  }

  async function enviarImagem(arquivo: File) {
    if (!editando) return;
    setEnviandoImg(true);
    try {
      const form = new FormData();
      form.append("arquivo", arquivo);
      const token = localStorage.getItem("ialinkedyn_token");
      const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "/api"}/midia/upload`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
      });
      if (!resp.ok) throw new Error("Falha no upload");
      const dados = await resp.json();
      await api(`/posts/${editando.id}`, { method: "PUT", body: { imagem_path: dados.caminho } });
      const atualizados = await api<Post[]>("/posts");
      setPosts(atualizados);
      const atual = atualizados.find((x) => x.id === editando.id);
      if (atual) setEditando(atual);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao enviar imagem");
    } finally {
      setEnviandoImg(false);
    }
  }

  async function salvarRec() {
    if (!novaRec.nome.trim() || !novaRec.tema.trim()) return;
    if (novaRec.frequencia === "SEMANAL" && !novaRec.dias_semana) {
      alert("Escolha pelo menos um dia da semana.");
      return;
    }
    try {
      await api("/recorrencias", { method: "POST", body: novaRec });
      setModalRec(false);
      setNovaRec({ nome: "", tema: "", frequencia: "SEMANAL", dias_semana: "", hora: 9, gerar_imagem_ia: true, publicar_automatico: true, ativo: true });
      await carregarRecs();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao salvar");
    }
  }

  async function excluirRec(id: number) {
    if (!confirm("Excluir esta recorrencia?")) return;
    await api(`/recorrencias/${id}`, { method: "DELETE" });
    await carregarRecs();
  }

  function alternarDia(idx: number) {
    const dias = novaRec.dias_semana ? novaRec.dias_semana.split(",") : [];
    const alvo = String(idx);
    const novo = dias.includes(alvo) ? dias.filter((d) => d !== alvo) : [...dias, alvo];
    setNovaRec({ ...novaRec, dias_semana: novo.sort().join(",") });
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

          {/* imagem */}
          <div className="rounded-lg border border-slate-200 p-3 space-y-2">
            <p className="text-sm font-medium text-ink flex items-center gap-1"><ImageIcon className="h-4 w-4" /> Imagem do post</p>
            {editando.imagem_path && (
              <img src={urlImagem(editando.imagem_path)} alt="" className="max-h-56 rounded-lg border border-slate-200" />
            )}
            <div className="flex gap-2 flex-wrap">
              <button onClick={gerarImagem} disabled={gerandoImg}
                className="flex items-center gap-2 rounded-lg bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 text-sm font-medium disabled:opacity-60">
                {gerandoImg ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />} Gerar imagem com IA
              </button>
              <label className="flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm cursor-pointer hover:bg-slate-50">
                {enviandoImg ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />} Enviar do computador
                <input type="file" accept="image/*" className="hidden"
                  onChange={(e) => e.target.files?.[0] && enviarImagem(e.target.files[0])} />
              </label>
            </div>
          </div>

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

      {/* Recorrencias */}
      <div className="rounded-xl bg-gradient-to-br from-brand/5 to-violet-50 border border-brand/20 p-6 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-ink flex items-center gap-2"><Repeat className="h-5 w-5 text-brand" /> Publicacao automatica</h2>
          <button onClick={() => setModalRec(true)} className="flex items-center gap-1 text-sm text-brand hover:underline">
            <Plus className="h-4 w-4" /> Nova recorrencia
          </button>
        </div>
        <p className="text-sm text-ink-soft">
          Defina o tema e o ritmo. A Maya escreve um post <strong>novo</strong> a cada disparo (com imagem, se quiser) e publica sozinha.
        </p>

        {recs.length === 0 ? (
          <p className="text-sm text-ink-soft">Nenhuma recorrencia ainda.</p>
        ) : (
          <div className="space-y-2">
            {recs.map((r) => (
              <div key={r.id} className="flex items-start justify-between gap-3 rounded-lg bg-white border border-slate-200 p-3">
                <div className="flex-1">
                  <p className="text-sm font-medium text-ink">{r.nome}</p>
                  <p className="text-xs text-ink-soft">{r.tema}</p>
                  <p className="text-xs text-ink-soft mt-1">
                    {r.frequencia === "DIARIO"
                      ? `Todo dia as ${r.hora}h`
                      : `${r.dias_semana.split(",").filter(Boolean).map((d) => DIAS[Number(d)]).join(", ")} as ${r.hora}h`}
                    {r.gerar_imagem_ia && " - com imagem IA"}
                    {r.publicar_automatico ? " - publica sozinho" : " - salva como rascunho"}
                  </p>
                </div>
                <button onClick={() => excluirRec(r.id)} className="p-1.5 rounded-lg hover:bg-red-50 text-red-500">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

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
                  <div className="flex gap-3">
                    {p.imagem_path && (
                      <img src={urlImagem(p.imagem_path)} alt="" className="h-20 w-20 object-cover rounded-lg border border-slate-200 shrink-0" />
                    )}
                    <p className="text-sm text-ink whitespace-pre-wrap line-clamp-4">{p.texto}</p>
                  </div>
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
      {/* Modal nova recorrencia */}
      {modalRec && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={() => setModalRec(false)}>
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6 max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-semibold text-ink mb-4">Nova publicacao automatica</h2>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-ink mb-1">Nome</label>
                <input className={input} value={novaRec.nome} onChange={(e) => setNovaRec({ ...novaRec, nome: e.target.value })} placeholder="ex.: Dica semanal de gestao" />
              </div>
              <div>
                <label className="block text-sm font-medium text-ink mb-1">Tema (a IA varia o texto a cada post)</label>
                <textarea className={input} rows={3} value={novaRec.tema} onChange={(e) => setNovaRec({ ...novaRec, tema: e.target.value })} placeholder="ex.: como automatizar processos manuais em clinicas" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-ink mb-1">Frequencia</label>
                  <select className={input} value={novaRec.frequencia} onChange={(e) => setNovaRec({ ...novaRec, frequencia: e.target.value })}>
                    <option value="SEMANAL">Semanal</option>
                    <option value="DIARIO">Diario</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-ink mb-1">Hora</label>
                  <input type="number" min={0} max={23} className={input} value={novaRec.hora} onChange={(e) => setNovaRec({ ...novaRec, hora: Number(e.target.value) })} />
                </div>
              </div>

              {novaRec.frequencia === "SEMANAL" && (
                <div>
                  <label className="block text-sm font-medium text-ink mb-1">Dias da semana</label>
                  <div className="flex gap-1 flex-wrap">
                    {DIAS.map((d, i) => {
                      const ativo = novaRec.dias_semana.split(",").includes(String(i));
                      return (
                        <button key={d} onClick={() => alternarDia(i)} type="button"
                          className={`rounded-lg px-3 py-1.5 text-sm border ${ativo ? "bg-brand text-white border-brand" : "border-slate-300 hover:bg-slate-50"}`}>
                          {d}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              <label className="flex items-center gap-2 text-sm text-ink">
                <input type="checkbox" className="h-4 w-4 accent-brand" checked={novaRec.gerar_imagem_ia}
                  onChange={(e) => setNovaRec({ ...novaRec, gerar_imagem_ia: e.target.checked })} />
                Gerar uma imagem com IA para cada post
              </label>
              <label className="flex items-center gap-2 text-sm text-ink">
                <input type="checkbox" className="h-4 w-4 accent-brand" checked={novaRec.publicar_automatico}
                  onChange={(e) => setNovaRec({ ...novaRec, publicar_automatico: e.target.checked })} />
                Publicar sozinho (desmarque para salvar como rascunho e revisar)
              </label>
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setModalRec(false)} className="rounded-lg border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50">Cancelar</button>
              <button onClick={salvarRec} className="rounded-lg bg-brand hover:bg-brand-dark text-white px-4 py-2 text-sm font-medium">Salvar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
