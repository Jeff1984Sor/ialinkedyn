import { Construction } from "lucide-react";

export function EmConstrucao({ titulo, descricao }: { titulo: string; descricao: string }) {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-ink">{titulo}</h1>
      <div className="rounded-xl bg-white border border-slate-200 p-10 shadow-sm flex flex-col items-center text-center">
        <div className="h-12 w-12 rounded-xl bg-amber-50 flex items-center justify-center mb-3">
          <Construction className="h-6 w-6 text-amber-500" />
        </div>
        <p className="text-ink font-medium">Em construção</p>
        <p className="text-ink-soft text-sm mt-1 max-w-md">{descricao}</p>
      </div>
    </div>
  );
}
