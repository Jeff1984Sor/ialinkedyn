"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { MessagesSquare, Users, BookOpen, Target, Loader2 } from "lucide-react";

type Stats = {
  total_leads: number;
  total_conversas: number;
  total_qa: number;
  leads_por_status: Record<string, number>;
};

const COR_STATUS: Record<string, string> = {
  NOVO: "#94A3B8",
  SEGUINDO: "#3B82F6",
  CONVIDADO: "#6366F1",
  ABORDADO: "#F59E0B",
  RESPONDEU: "#06B6D4",
  QUALIFICADO: "#8B5CF6",
  GANHO: "#10B981",
  PERDIDO: "#EF4444",
};

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<Stats | null>(null);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    api<Stats>("/dashboard/stats").then(setStats).finally(() => setCarregando(false));
  }, []);

  const cards = [
    { label: "Leads", valor: stats?.total_leads ?? 0, icon: Users, cor: "text-brand" },
    { label: "Conversas", valor: stats?.total_conversas ?? 0, icon: MessagesSquare, cor: "text-emerald-600" },
    { label: "Q&A cadastradas", valor: stats?.total_qa ?? 0, icon: BookOpen, cor: "text-violet-600" },
    {
      label: "Leads qualificados",
      valor: stats?.leads_por_status?.QUALIFICADO ?? 0,
      icon: Target,
      cor: "text-amber-600",
    },
  ];

  const dadosGrafico = stats
    ? Object.entries(stats.leads_por_status)
        .filter(([, v]) => v > 0)
        .map(([status, valor]) => ({ status, valor }))
    : [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-ink">Olá, {user?.nome} 👋</h1>
        <p className="text-ink-soft mt-1">Resumo do seu funcionário virtual.</p>
      </div>

      {carregando ? (
        <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-brand" /></div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {cards.map((c) => {
              const Icon = c.icon;
              return (
                <div key={c.label} className="rounded-xl bg-white border border-slate-200 p-5 shadow-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-ink-soft">{c.label}</span>
                    <Icon className={`h-5 w-5 ${c.cor}`} />
                  </div>
                  <p className="text-3xl font-bold text-ink mt-2">{c.valor}</p>
                </div>
              );
            })}
          </div>

          <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-ink mb-4">Funil de leads</h2>
            {dadosGrafico.length === 0 ? (
              <p className="text-sm text-ink-soft py-10 text-center">
                Ainda não há leads. Cadastre leads na aba <strong>Leads</strong> para ver o funil aqui.
              </p>
            ) : (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={dadosGrafico} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#EEF2F6" />
                    <XAxis dataKey="status" stroke="#94A3B8" fontSize={11} tickLine={false} axisLine={false} />
                    <YAxis stroke="#94A3B8" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} />
                    <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #E2E8F0", fontSize: 13 }} />
                    <Bar dataKey="valor" radius={[6, 6, 0, 0]}>
                      {dadosGrafico.map((d) => (
                        <Cell key={d.status} fill={COR_STATUS[d.status] || "#0A66C2"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
