const STAGES = [
  "Understanding your question...",
  "Checking your datasets...",
  "Running analysis...",
  "Preparing your answer...",
];

export function LoadingStages({ stage }: { stage: number }) {
  return (
    <div className="mt-8 rounded-2xl border border-line bg-white p-6">
      <ol className="space-y-3">
        {STAGES.map((label, i) => (
          <li key={label} className="flex items-center gap-3 text-sm">
            <span
              className={`h-2 w-2 rounded-full ${
                i < stage ? "bg-accent" : i === stage ? "animate-pulse bg-accent" : "bg-line"
              }`}
            />
            <span className={i <= stage ? "text-ink" : "text-stone-400"}>{label}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
