import { type FormEvent, useEffect, useState } from "react";
import { askAssistant, fetchAssistantTurns } from "../services/auth";
import { getErrorMessage } from "../services/api";
import { PageHeader } from "../components/common/PageHeader";
import { inputClass } from "../components/common/AuthCard";
import type { AssistantTurn } from "../types/api";

const SUGGESTIONS = [
  "What should I learn next?",
  "What is my learning path for now?",
  "Why do I need Statistics?",
  "Explain transformers.",
  "Give me a project for RAG.",
  "Why was this course recommended?",
];

function sourceLabel(type: string): string {
  if (type === "PATH_OVERVIEW" || type === "PATH") {
    return "path";
  }
  return type.toLowerCase().replaceAll("_", " ");
}

export function AssistantPage() {
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<AssistantTurn[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    void fetchAssistantTurns()
      .then(setTurns)
      .catch(() => {
        setTurns([]);
      });
  }, []);

  async function send(text: string) {
    const trimmed = text.trim();
    if (trimmed.length < 3 || pending) {
      return;
    }
    setPending(true);
    setError(null);
    try {
      const turn = await askAssistant(trimmed);
      setTurns((current) => [...current, turn]);
      setQuestion("");
    } catch (err) {
      setError(getErrorMessage(err, "Could not answer from your stored context."));
    } finally {
      setPending(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await send(question);
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Assistant" />

      <div className="flex flex-wrap gap-x-4 gap-y-2">
        {SUGGESTIONS.map((item) => (
          <button
            key={item}
            type="button"
            className="text-sm text-navy-800 underline-offset-2 hover:underline"
            onClick={() => void send(item)}
          >
            {item}
          </button>
        ))}
      </div>

      <ol className="space-y-4">
        {turns.map((turn) => (
          <li key={turn.id} className="rounded-xl border border-slate-200 bg-white p-5">
            <p className="text-sm font-medium text-navy-900">{turn.question}</p>
            <p className="mt-2 text-sm text-slate-600">{turn.answer}</p>
            {turn.used_llm ? (
              <p className="mt-2 text-xs text-slate-400">Rephrased from stored facts</p>
            ) : null}
            {turn.sources.length ? (
              <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-slate-500">
                {turn.sources.map((source) => (
                  <li key={`${source.source_type}-${source.title}`}>
                    {sourceLabel(source.source_type)}: {source.title}
                  </li>
                ))}
              </ul>
            ) : null}
          </li>
        ))}
      </ol>

      {pending ? <p className="text-sm text-slate-500">Looking up stored context…</p> : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row">
        <input
          className={inputClass}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask about your path, a skill, or a catalog project"
          maxLength={500}
        />
        <button
          type="submit"
          disabled={pending}
          className="rounded-lg bg-navy-800 px-4 py-2 text-sm font-medium text-white hover:bg-navy-700 disabled:opacity-60"
        >
          Ask
        </button>
      </form>
    </div>
  );
}
