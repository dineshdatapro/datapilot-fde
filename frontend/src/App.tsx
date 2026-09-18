import { useEffect, useRef, useState } from "react";
import { AnswerPanel } from "./components/AnswerPanel";
import { EmptyState } from "./components/EmptyState";
import { FileSidebar } from "./components/FileSidebar";
import { Header } from "./components/Header";
import { LoadingStages } from "./components/LoadingStages";
import { QuestionInput } from "./components/QuestionInput";
import { useLoadingStage } from "./hooks/useLoadingStage";
import { askQuestion, deleteFile, loadDemo, resetSession, uploadFiles } from "./services/api";
import type { QueryResponse, SessionPayload } from "./types";

const DEMO_QUESTIONS = [
  "What is the total revenue across all files?",
  "Which region generated the highest revenue?",
  "Compare January and February revenue.",
  "What are the top 5 products by revenue?",
  "Show the revenue trend by month.",
  "Which customer segment generated the most revenue?",
  "What is the average order value?",
  "Which cities generated more than ₹1 lakh in revenue?",
];

export default function App() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [session, setSession] = useState<SessionPayload | null>(null);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [ollama, setOllama] = useState<string | null>(null);
  const stage = useLoadingStage(busy);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((h) => {
        if (h.ollama === "reachable") setOllama(`Ollama Cloud · ${h.model}`);
        else if (h.api_key_configured === false) setOllama("Set OLLAMA_API_KEY");
        else setOllama("Ollama Cloud offline");
      })
      .catch(() => setOllama("API offline"));
  }, []);

  const applySession = (payload: SessionPayload) => {
    setSession(payload);
    localStorage.setItem("datapilot_session", payload.session_id);
  };

  const onFiles = async (list: FileList | File[]) => {
    const files = Array.from(list);
    if (!files.length) return;
    const unsupported = files.filter((f) => !/\.(csv|xlsx|xls)$/i.test(f.name));
    if (unsupported.length) {
      setToast("Unsupported file type. Please upload a CSV or Excel file.");
      return;
    }
    try {
      setToast(null);
      setUploading(true);
      const payload = await uploadFiles(files, session?.session_id);
      applySession(payload);
    } catch (err) {
      setToast(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const onDemo = async () => {
    try {
      setDemoLoading(true);
      setToast(null);
      const payload = await loadDemo(session?.session_id);
      applySession(payload);
    } catch (err) {
      setToast(err instanceof Error ? err.message : "Could not load demo data.");
    } finally {
      setDemoLoading(false);
    }
  };

  const onAsk = async (override?: string) => {
    const q = (override ?? question).trim();
    if (!q || !session) return;
    setBusy(true);
    setResult(null);
    try {
      const response = await askQuestion(session.session_id, q);
      setResult(response);
    } catch (err) {
      setResult({
        question: q,
        answer: "",
        verified: false,
        files_used: [],
        rows_analyzed: 0,
        plan: {},
        result: {},
        visualization: { type: "none", title: "", data: [] },
        analysis: {},
        error: err instanceof Error ? err.message : "Something went wrong.",
      });
    } finally {
      setBusy(false);
    }
  };

  const onNewSession = async () => {
    if (session) {
      try {
        await resetSession(session.session_id);
      } catch {
        /* ignore */
      }
    }
    setSession(null);
    setResult(null);
    setQuestion("");
    localStorage.removeItem("datapilot_session");
  };

  const hasFiles = !!session && session.files.length > 0;

  return (
    <div className="min-h-screen">
      <Header fileCount={session?.files.length ?? 0} onNewSession={onNewSession} status={ollama} />
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.xlsx,.xls"
        multiple
        className="hidden"
        onChange={(e) => e.target.files && onFiles(e.target.files)}
      />

      {!hasFiles ? (
        <EmptyState onPick={() => inputRef.current?.click()} onDemo={onDemo} onFiles={onFiles} loadingDemo={demoLoading} />
      ) : (
        <main className="mx-auto grid max-w-6xl gap-8 px-6 py-8 lg:grid-cols-[280px_1fr]">
          <div>
            <FileSidebar
              session={session}
              onRemove={async (id) => {
                const payload = await deleteFile(session.session_id, id);
                applySession(payload);
                if (!payload.files.length) {
                  setSession(null);
                  setResult(null);
                }
              }}
            />
            <button
              type="button"
              className="mt-4 text-sm text-accent underline-offset-2 hover:underline"
              onClick={() => inputRef.current?.click()}
            >
              Add more files
            </button>
          </div>
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              if (e.dataTransfer.files.length) onFiles(e.dataTransfer.files);
            }}
          >
            <QuestionInput value={question} onChange={setQuestion} onSubmit={() => onAsk()} onAsk={onAsk} disabled={busy} />
            <div className="mt-4 flex flex-wrap gap-2">
              {DEMO_QUESTIONS.map((q) => (
                <button
                  key={q}
                  type="button"
                  className="rounded-full border border-line bg-white px-3 py-1.5 text-left text-xs text-stone-600 hover:bg-mist"
                  onClick={() => {
                    setQuestion(q);
                    onAsk(q);
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
            {busy && <LoadingStages stage={stage} />}
            {result && !busy && <AnswerPanel result={result} />}
          </div>
        </main>
      )}

      {uploading && (
        <div className="fixed bottom-6 left-1/2 z-10 -translate-x-1/2 rounded-xl border border-line bg-white px-4 py-2 text-sm shadow-sm">
          Profiling uploaded files…
        </div>
      )}
      {toast && (
        <div className="fixed bottom-6 left-1/2 z-10 -translate-x-1/2 rounded-xl border border-line bg-white px-4 py-2 text-sm shadow-sm">
          {toast}
        </div>
      )}
    </div>
  );
}
