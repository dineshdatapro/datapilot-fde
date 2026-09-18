import { Check } from "lucide-react";
import { useState } from "react";
import type { QueryResponse } from "../types";
import { ChartView } from "./ChartView";
import { Badge } from "./ui/badge";
import { Card } from "./ui/card";

type Props = { result: QueryResponse };

export function AnswerPanel({ result }: Props) {
  const [open, setOpen] = useState(true);
  const kpi = result.visualization.type === "kpi" || result.result?.kind === "kpi";

  return (
    <Card className="mt-8 p-6">
      <p className="text-xs uppercase tracking-wide text-stone-400">Question</p>
      <p className="mt-1 text-stone-700">“{result.question}”</p>

      {result.error ? (
        <div className="mt-6 whitespace-pre-wrap rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
          {result.error}
        </div>
      ) : (
        <>
          <p className="mt-6 text-xs uppercase tracking-wide text-stone-400">Answer</p>
          <p className="mt-2 font-display text-2xl leading-snug text-ink">{result.answer}</p>
          {kpi && result.result?.formatted_value != null && (
            <p className="mt-2 font-mono text-sm text-stone-500">{String(result.result.formatted_value)}</p>
          )}
          {result.verified && (
            <Badge className="mt-3 border-accent/20 bg-accent/5 text-accent">
              <Check className="h-3.5 w-3.5" />
              Verified against uploaded data
            </Badge>
          )}

          {result.visualization && result.visualization.type !== "none" && result.visualization.type !== "kpi" && (
            <div className="mt-6 border-t border-line pt-6">
              <ChartView viz={result.visualization} />
            </div>
          )}

          <div className="mt-6 border-t border-line pt-4">
            <button type="button" className="text-sm text-stone-600 underline-offset-2 hover:underline" onClick={() => setOpen(!open)}>
              {open ? "Hide" : "Show"} how this answer was calculated
            </button>
            {open && result.analysis && (
              <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-stone-400">Files used</dt>
                  <dd>{(result.analysis.files_used || []).join(", ") || "—"}</dd>
                </div>
                <div>
                  <dt className="text-stone-400">Rows analyzed</dt>
                  <dd>{(result.analysis.rows_analyzed || 0).toLocaleString("en-IN")}</dd>
                </div>
                <div>
                  <dt className="text-stone-400">Operation</dt>
                  <dd className="font-mono text-xs">{result.analysis.operation || "—"}</dd>
                </div>
                <div>
                  <dt className="text-stone-400">Grouping</dt>
                  <dd>{result.analysis.grouping || "None"}</dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-stone-400">Filters</dt>
                  <dd>{result.analysis.filters || "None"}</dd>
                </div>
                <div className="sm:col-span-2 rounded-xl bg-mist px-3 py-2 text-xs text-stone-600">
                  Trust layer — {result.analysis.trust}
                </div>
              </dl>
            )}
          </div>
        </>
      )}
    </Card>
  );
}
