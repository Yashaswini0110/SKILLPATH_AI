import { type FormEvent, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchAssessment, submitAssessment } from "../services/auth";
import { getErrorMessage } from "../services/api";
import type { AssessmentAttempt } from "../types/api";

export function AssessmentTakePage() {
  const { assessmentId } = useParams();
  const queryClient = useQueryClient();
  const [choices, setChoices] = useState<Record<string, number>>({});
  const [result, setResult] = useState<AssessmentAttempt | null>(null);
  const detailQuery = useQuery({
    queryKey: ["assessment", assessmentId],
    queryFn: () => fetchAssessment(assessmentId ?? ""),
    enabled: Boolean(assessmentId),
  });
  const quiz = detailQuery.data;
  const mutation = useMutation({
    mutationFn: () =>
      submitAssessment(
        assessmentId ?? "",
        (quiz?.questions ?? []).map((question) => ({
          question_id: question.id,
          selected_index: choices[question.id] ?? null,
        })),
      ),
    onSuccess: (data) => {
      setResult(data);
      void queryClient.invalidateQueries({ queryKey: ["assessments"] });
      void queryClient.invalidateQueries({ queryKey: ["skill-profile"] });
      void queryClient.invalidateQueries({ queryKey: ["learning-path"] });
      void queryClient.invalidateQueries({ queryKey: ["gap-analysis"] });
    },
  });
  const unanswered = useMemo(() => {
    if (!quiz) return 0;
    return quiz.questions.filter((question) => choices[question.id] === undefined).length;
  }, [choices, quiz]);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (unanswered) return;
    mutation.mutate();
  }

  if (detailQuery.isPending) {
    return <p className="text-sm text-slate-500">Loading quiz…</p>;
  }
  if (detailQuery.isError || !quiz) {
    return (
      <p className="text-sm text-red-600">
        {getErrorMessage(detailQuery.error, "Quiz not found.")}
      </p>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-slate-500">
          <Link to="/assessments" className="text-navy-800 underline-offset-2 hover:underline">
            All quizzes
          </Link>
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-navy-900">{quiz.title}</h1>
        <p className="mt-1 text-sm text-slate-500">
          {quiz.skill.canonical_name} · pass {Math.round(quiz.pass_score * 100)}%
        </p>
      </div>

      {result ? <ResultPanel result={result} /> : null}

      <form onSubmit={onSubmit} className="space-y-6">
        <ol className="space-y-6">
          {quiz.questions.map((question) => {
            const outcome = result?.answers.find((row) => row.question_id === question.id);
            return (
              <li key={question.id}>
                <p className="font-medium text-navy-900">
                  {question.position}. {question.prompt}
                </p>
                <ul className="mt-3 space-y-2">
                  {question.choices.map((choice, index) => (
                    <li key={`${question.id}-${index}`}>
                      <label className="flex items-start gap-2 text-sm text-slate-700">
                        <input
                          type="radio"
                          name={question.id}
                          value={index}
                          checked={choices[question.id] === index}
                          disabled={Boolean(result)}
                          onChange={() =>
                            setChoices((current) => ({ ...current, [question.id]: index }))
                          }
                          className="mt-0.5"
                        />
                        <span>{choice}</span>
                      </label>
                    </li>
                  ))}
                </ul>
                {outcome ? (
                  <p className={`mt-2 text-sm ${outcome.is_correct ? "text-teal-800" : "text-red-700"}`}>
                    {outcome.is_correct ? "Correct." : "Incorrect."} {outcome.explanation}
                  </p>
                ) : null}
              </li>
            );
          })}
        </ol>
        {result ? (
          <Link to="/path" className="text-sm font-medium text-navy-800 underline-offset-2 hover:underline">
            Back to path
          </Link>
        ) : (
          <button
            type="submit"
            disabled={Boolean(unanswered) || mutation.isPending}
            className="rounded-lg bg-navy-800 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {mutation.isPending ? "Scoring…" : "Submit quiz"}
          </button>
        )}
        {mutation.isError ? (
          <p className="text-sm text-red-600">
            {getErrorMessage(mutation.error, "Unable to score this quiz.")}
          </p>
        ) : null}
      </form>
    </div>
  );
}

function ResultPanel({ result }: { result: AssessmentAttempt }) {
  const percent = Math.round(result.percent * 100);
  let effect = "Evidence added.";
  if (result.path_effect === "REFRESHER") {
    effect = "Review step added. See Path.";
  } else if (result.path_effect === "SKIP") {
    effect = "Basics skipped. See Path.";
  }
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
      <p>
        Score {result.correct_count}/{result.total} ({percent}%). Estimated level{" "}
        {result.extracted_level}/5. {result.passed ? "Passed." : "Not a passing score yet."}
      </p>
      <p className="mt-2">{effect}</p>
    </div>
  );
}
