import { useState } from "react";
import type { Explanation } from "../../types/api";

export function WhyButton({ explanation }: { explanation: Explanation | undefined }) {
  const [open, setOpen] = useState(false);
  const facts = explanation?.facts ?? [];
  if (!facts.length) {
    return null;
  }
  return (
    <div className="mt-3">
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        className="text-sm font-medium text-navy-800 underline-offset-2 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy-700"
      >
        {open ? "Hide why" : "Why?"}
      </button>
      {open ? (
        <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-slate-600">
          {facts.map((fact) => (
            <li key={fact.key}>{fact.text}</li>
          ))}
        </ol>
      ) : null}
    </div>
  );
}
