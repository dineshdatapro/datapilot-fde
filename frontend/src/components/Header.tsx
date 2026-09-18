import { FileSpreadsheet, Plus } from "lucide-react";
import { Button } from "./ui/button";

type Props = {
  fileCount: number;
  onNewSession: () => void;
  status?: string | null;
};

export function Header({ fileCount, onNewSession, status }: Props) {
  return (
    <header className="border-b border-line bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <div>
          <div className="font-display text-xl tracking-tight text-ink">DataPilot</div>
          <p className="text-sm text-stone-500">Ask questions. Understand your data.</p>
        </div>
        <div className="flex items-center gap-3">
          {status && <p className="hidden text-xs text-stone-400 md:block">{status}</p>}
          <div className="hidden items-center gap-2 rounded-full border border-line px-3 py-1.5 text-sm text-stone-600 sm:flex">
            <FileSpreadsheet className="h-4 w-4" />
            {fileCount} {fileCount === 1 ? "file" : "files"}
          </div>
          <Button variant="secondary" size="sm" onClick={onNewSession}>
            <Plus className="h-4 w-4" />
            New session
          </Button>
        </div>
      </div>
    </header>
  );
}
