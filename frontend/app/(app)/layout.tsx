"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/auth";
import {
  Bot,
  LayoutDashboard,
  MessagesSquare,
  Users,
  BookOpen,
  Sparkles,
  Target,
  FileText,
  LogOut,
  Loader2,
} from "lucide-react";

const NAV = [
  { grupo: "Visão", itens: [{ href: "/", label: "Dashboard", icon: LayoutDashboard }] },
  {
    grupo: "Operação",
    itens: [
      { href: "/inbox", label: "Conversas", icon: MessagesSquare },
      { href: "/leads", label: "Leads", icon: Users },
      { href: "/prospeccao", label: "Prospecção", icon: Target },
    ],
  },
  {
    grupo: "Cérebro",
    itens: [
      { href: "/conhecimento", label: "Base de Conhecimento", icon: BookOpen },
      { href: "/marca", label: "Marca / Voz", icon: Sparkles },
      { href: "/prompts", label: "Prompts", icon: FileText },
    ],
  },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-brand" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-60 bg-gradient-to-b from-[#0A2540] to-[#04182B] text-white flex flex-col">
        <div className="flex items-center gap-2 px-5 h-16 border-b border-white/10">
          <div className="h-8 w-8 rounded-lg bg-brand flex items-center justify-center">
            <Bot className="h-5 w-5 text-white" />
          </div>
          <span className="font-bold text-lg">IALinkedyn</span>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-6 overflow-y-auto">
          {NAV.map((g) => (
            <div key={g.grupo}>
              <p className="px-3 text-[11px] uppercase tracking-wider text-white/40 mb-1">
                {g.grupo}
              </p>
              {g.itens.map((item) => {
                const Icon = item.icon;
                const ativo = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                      ativo
                        ? "bg-white/10 text-white border-l-2 border-brand"
                        : "text-white/70 hover:bg-white/5 hover:text-white"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>

        <div className="p-3 border-t border-white/10">
          <div className="px-3 py-2 text-sm">
            <p className="font-medium">{user.nome}</p>
            <p className="text-white/40 text-xs">@{user.usuario}</p>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-white/70 hover:bg-white/5 hover:text-white"
          >
            <LogOut className="h-4 w-4" />
            Sair
          </button>
        </div>
      </aside>

      {/* Conteúdo */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto p-8">{children}</div>
      </main>
    </div>
  );
}
