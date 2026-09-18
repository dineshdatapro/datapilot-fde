import { useState } from "react";
import { ChevronDown, FileSpreadsheet, X } from "lucide-react";
import type { SessionPayload, UploadedFile } from "../types";
import { Button } from "./ui/button";

type Props = {
  session: SessionPayload;
  onRemove: (fileId: string) => void;
};

function formatRows(n: number) {
  return n.toLocaleString("en-IN");
}

export function FileSidebar({ session, onRemove }: Props) {
  const { files, overview } = session;
  return (
    <aside className="space-y-6">
      <section>
        <h2 className="text-xs uppercase tracking-wide text-stone-400">Data sources</h2>
        <div className="mt-3 space-y-2">
          {files.map((file) => (
            <FileCard key={file.file_id} file={file} onRemove={onRemove} />
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xs uppercase tracking-wide text-stone-400">Data overview</h2>
        <div className="mt-3 rounded-xl border border-line bg-white p-4 text-sm">
          <dl className="grid grid-cols-2 gap-3">
            <div>
              <dt className="text-stone-400">Total rows</dt>
              <dd className="font-medium">{formatRows(overview.total_rows)}</dd>
            </div>
            <div>
              <dt className="text-stone-400">Total columns</dt>
              <dd className="font-medium">{overview.total_columns}</dd>
            </div>
            <div>
              <dt className="text-stone-400">Files</dt>
              <dd className="font-medium">{overview.file_count}</dd>
            </div>
            <div>
              <dt className="text-stone-400">Relationships</dt>
              <dd className="font-medium">{overview.relationships.length}</dd>
            </div>
          </dl>
          {overview.relationships.length > 0 && (
            <div className="mt-4 border-t border-line pt-3">
              <p className="text-xs font-medium text-accent">Potential relationship detected</p>
              <ul className="mt-2 space-y-1 text-xs text-stone-600">
                {overview.relationships.map((rel, i) => (
                  <li key={i}>
                    {rel.left_file}.{rel.left_column} → {rel.right_file}.{rel.right_column}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </section>
    </aside>
  );
}

function FileCard({ file, onRemove }: { file: UploadedFile; onRemove: (id: string) => void }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-xl border border-line bg-white p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-2">
          <FileSpreadsheet className="mt-0.5 h-4 w-4 text-accent" />
          <div>
            <p className="text-sm font-medium text-ink">{file.filename}</p>
            <p className="text-xs text-stone-500">
              {file.file_type.toUpperCase()} · {formatRows(file.row_count)} rows · {file.column_count} columns
            </p>
          </div>
        </div>
        <div className="flex items-center">
          <Button variant="ghost" size="sm" className="h-7 w-7 px-0" onClick={() => setOpen(!open)} aria-label="Show schema">
            <ChevronDown className={`h-4 w-4 transition ${open ? "rotate-180" : ""}`} />
          </Button>
          <Button variant="ghost" size="sm" className="h-7 w-7 px-0" onClick={() => onRemove(file.file_id)} aria-label="Remove file">
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>
      {open && (
        <ul className="mt-3 space-y-1 border-t border-line pt-2 text-xs text-stone-600">
          {file.columns
            .filter((c) => !["month", "year", "month_name"].includes(c.name))
            .map((col) => (
              <li key={col.name} className="flex justify-between gap-2">
                <span className="font-mono">{col.name}</span>
                <span className="text-stone-400">{col.semantic_type}</span>
              </li>
            ))}
        </ul>
      )}
    </div>
  );
}
