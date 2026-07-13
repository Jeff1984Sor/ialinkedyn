"use client";

import { useAuth } from "@/lib/auth";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { MessagesSquare, Users, Target, TrendingUp } from "lucide-react";

// Dados de exemplo (serão substituídos por dados reais dos agentes/leads)
const DADOS = [
  { dia: "Seg", conversas: 4, leads: 2 },
  { dia: "Ter", conversas: 7, leads: 3 },
  { dia: "Qua", conversas: 5, leads: 4 },
  { dia: "Qui", conversas: 11, leads: 6 },
  { dia: "Sex", conversas: 9, leads: 5 },
  { dia: "Sáb", conversas: 3, leads: 1 },
  { dia: "Dom", conversas: 2, leads: 1 },
];

const CARDS = [
  { label: "Conversas na semana", valor: "41", icon: MessagesSquare, cor: "text-brand" },
  { label: "Leads novos", valor: "22", icon: Users, cor: "text-emerald-600" },
  { label: "Em prospecção", valor: "8", icon: Target, cor: "text-amber-600" },
  { label: "Taxa de resposta", valor: "63%", icon: TrendingUp, cor: "text-violet-600" },
];

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-ink">Olá, {user?.nome} 👋</h1>
        <p className="text-ink-soft mt-1">Aqui está o resumo do seu funcionário virtual.</p>
      </div>

      {/* Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {CARDS.map((c) => {
          const Icon = c.icon;
          return (
            <div
              key={c.label}
              className="rounded-xl bg-white border border-slate-200 p-5 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-soft">{c.label}</span>
                <Icon className={`h-5 w-5 ${c.cor}`} />
              </div>
              <p className="text-3xl font-bold text-ink mt-2">{c.valor}</p>
            </div>
          );
        })}
      </div>

      {/* Gráfico */}
      <div className="rounded-xl bg-white border border-slate-200 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-ink mb-4">Atividade da semana</h2>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={DADOS} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="gConversas" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0A66C2" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#0A66C2" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gLeads" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10B981" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#EEF2F6" />
              <XAxis dataKey="dia" stroke="#94A3B8" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#94A3B8" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{
                  borderRadius: 12,
                  border: "1px solid #E2E8F0",
                  fontSize: 13,
                }}
              />
              <Area
                type="monotone"
                dataKey="conversas"
                stroke="#0A66C2"
                strokeWidth={2}
                fill="url(#gConversas)"
                name="Conversas"
              />
              <Area
                type="monotone"
                dataKey="leads"
                stroke="#10B981"
                strokeWidth={2}
                fill="url(#gLeads)"
                name="Leads"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <p className="text-xs text-ink-soft mt-3">
          * Dados de exemplo. Serão preenchidos com sua atividade real assim que os agentes e o
          LinkedIn estiverem conectados.
        </p>
      </div>
    </div>
  );
}
