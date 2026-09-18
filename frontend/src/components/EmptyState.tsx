import { Upload } from "lucide-react";
import { Button } from "./ui/button";

type Props = {
  onPick: () => void;
  onDemo: () => void;
  onFiles?: (files: FileList) => void;
  loadingDemo?: boolean;
};

export function EmptyState({ onPick, onDemo, onFiles, loadingDemo }: Props) {
  return (
    <div
      className="mx-auto flex max-w-xl flex-col items-center px-6 py-20 text-center"
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length) onFiles?.(e.dataTransfer.files);
      }}
    >
      <p className="font-display text-4xl text-ink sm:text-5xl">DataPilot</p>
      <p className="mt-4 font-display text-2xl text-stone-700">Turn your spreadsheets into answers.</p>
      <p className="mt-4 max-w-md text-stone-500">
        Upload CSV or Excel files and ask questions about them in plain English. Numbers are calculated in Pandas — not guessed by the model.
      </p>
      <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
        <Button onClick={onPick}>
          <Upload className="h-4 w-4" />
          Upload files
        </Button>
        <Button variant="secondary" onClick={onDemo} disabled={loadingDemo}>
          {loadingDemo ? "Loading demo…" : "Load demo data"}
        </Button>
      </div>
      <p className="mt-4 text-xs uppercase tracking-wide text-stone-400">Supported: CSV, XLSX, XLS</p>
      <div className="mt-10 grid w-full gap-2 text-left text-sm text-stone-600">
        <p className="text-xs uppercase tracking-wide text-stone-400">Example questions</p>
        {['"What was our total revenue?"', '"Which region performed best?"', '"Show revenue by month."'].map((q) => (
          <div key={q} className="rounded-xl border border-line bg-white px-4 py-3">
            {q}
          </div>
        ))}
      </div>
    </div>
  );
}
