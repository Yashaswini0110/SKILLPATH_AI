import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";
import { fetchResume, fetchResumes, uploadResume } from "../services/auth";
import { getErrorMessage } from "../services/api";
import { PageHeader } from "../components/common/PageHeader";
import { inputClass } from "../components/common/AuthCard";

export function ResumePage() {
  const queryClient = useQueryClient();
  const resumesQuery = useQuery({ queryKey: ["resumes"], queryFn: fetchResumes });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const latest = resumesQuery.data?.[0];
  const activeId = selectedId ?? latest?.id ?? null;

  const detailQuery = useQuery({
    queryKey: ["resume", activeId],
    queryFn: () => fetchResume(activeId as string),
    enabled: Boolean(activeId),
  });

  const upload = useMutation({
    mutationFn: uploadResume,
    onSuccess: async (resume) => {
      setSelectedId(resume.id);
      setMessage(resume.skills.length
        ? `Extracted ${resume.skills.length} skills.`
        : "No catalog skills were found. Unknown terms are left unmatched.");
      setError(null);
      await queryClient.invalidateQueries({ queryKey: ["resumes"] });
      await queryClient.invalidateQueries({ queryKey: ["skill-profile"] });
    },
    onError: (err) => setError(getErrorMessage(err, "Unable to process resume")),
  });

  async function onUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const file = form.get("file");
    if (!(file instanceof File) || file.size === 0) {
      setError("Choose a PDF, DOCX, or TXT resume first.");
      return;
    }
    await upload.mutateAsync(file);
  }

  const detail = detailQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader title="Resume" note="PDF, DOCX, or TXT." />

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-navy-900">Upload</h2>
        <form className="mt-4 flex flex-col gap-3 md:flex-row md:items-end" onSubmit={onUpload}>
          <input name="file" type="file" accept=".pdf,.docx,.txt,application/pdf,text/plain" required className={inputClass} />
          <button
            type="submit"
            disabled={upload.isPending}
            className="rounded-lg bg-navy-800 px-4 py-2 text-sm font-medium text-white hover:bg-navy-700 disabled:opacity-60"
          >
            {upload.isPending ? "Processing..." : "Extract skills"}
          </button>
        </form>
        {message ? <p className="mt-3 text-sm text-teal-800">{message}</p> : null}
        {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-navy-900">Uploads</h2>
        <ul className="mt-3 space-y-2">
          {(resumesQuery.data ?? []).map((item) => (
            <li key={item.id}>
              <button
                type="button"
                className="w-full rounded-lg bg-slate-50 p-3 text-left hover:bg-slate-100"
                onClick={() => setSelectedId(item.id)}
              >
                <p className="font-medium text-slate-800">{item.original_filename}</p>
                <p className="text-sm text-slate-500">
                  {item.status} · {item.skill_count} inferred skills
                </p>
              </button>
            </li>
          ))}
        </ul>
        {!resumesQuery.data?.length ? (
          <p className="mt-2 text-sm text-slate-500">No resumes uploaded yet.</p>
        ) : null}
      </section>

      {activeId && detail ? (
        <section className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="text-lg font-semibold text-navy-900">
            {detail.original_filename}
          </h2>
          <ul className="mt-4 space-y-3">
            {detail.skills.map((item) => (
              <li key={item.id} className="rounded-lg border border-slate-200 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-medium text-navy-900">{item.skill.canonical_name}</p>
                  <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
                    inferred
                  </span>
                </div>
                <p className="mt-1 text-sm text-slate-500">
                  Estimated level {item.extracted_level}/5 · confidence {item.confidence}
                  {item.section ? ` · ${item.section}` : ""}
                </p>
              </li>
            ))}
          </ul>
          {!detail.skills.length ? (
            <p className="mt-3 text-sm text-slate-500">No catalog skills were extracted.</p>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
