import { FormEvent } from "react";
import { Button } from "./ui/button";

const SUGGESTIONS = [
  { label: "Total revenue", q: "What is the total revenue across all files?" },
  { label: "Top products", q: "What are the top 5 products by revenue?" },
  { label: "Compare months", q: "Compare January and February revenue." },
  { label: "Revenue trend", q: "Show the revenue trend by month." },
];

type Props = {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  onAsk?: (q: string) => void;
  disabled?: boolean;
};

export function QuestionInput({ value, onChange, onSubmit, onAsk, disabled }: Props) {
  const handle = (e: FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <div>
      <h1 className="font-display text-3xl text-ink">Ask your data</h1>
      <form onSubmit={handle} className="mt-4">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Ask a question about your uploaded data..."
          className="min-h-[96px] w-full resize-y rounded-2xl border border-line bg-white px-4 py-3 text-base outline-none ring-accent/30 focus:ring-2"
        />
        <div className="mt-3 flex items-center justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s.label}
                type="button"
                className="rounded-full border border-line bg-white px-3 py-1 text-xs text-stone-600 hover:bg-mist"
                onClick={() => {
                  onChange(s.q);
                  onAsk?.(s.q);
                }}
              >
                {s.label}
              </button>
            ))}
          </div>
          <Button type="submit" disabled={disabled || !value.trim()}>
            Ask
          </Button>
        </div>
      </form>
    </div>
  );
}
