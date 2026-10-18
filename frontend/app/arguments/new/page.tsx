
"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type Category = {
  id: number;
  name: string;
  slug: string;
  description: string | null;
};

type DraftPremise = {
  statement: string;
  description: string;
};

type DraftResponse = {
  statement: string;
  description: string;
};

type DraftObjection = {
  statement: string;
  description: string;
  responses: DraftResponse[];
};

const inputClass =
  "w-full border border-black/15 bg-[#f5f0e5] px-3 py-3 text-sm text-[#252b24] outline-none transition placeholder:text-[#9a9385] focus:border-[#b89552]";

const labelClass =
  "mb-2 block text-[10px] uppercase tracking-[0.16em] text-[#777164]";

const emptyPremise = (): DraftPremise => ({
  statement: "",
  description: "",
});

const emptyResponse = (): DraftResponse => ({
  statement: "",
  description: "",
});

const emptyObjection = (): DraftObjection => ({
  statement: "",
  description: "",
  responses: [],
});

function optionalText(value: string): string | null {
  return value.trim() || null;
}

export default function NewArgumentPage() {
  const router = useRouter();

  const [categories, setCategories] = useState<Category[]>([]);
  const [categoriesLoading, setCategoriesLoading] = useState(true);
  const [categoryError, setCategoryError] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [question, setQuestion] = useState("");
  const [summary, setSummary] = useState("");
  const [claim, setClaim] = useState("");
  const [conclusion, setConclusion] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [status, setStatus] = useState("draft");

  const [premises, setPremises] = useState<DraftPremise[]>([]);
  const [objections, setObjections] = useState<DraftObjection[]>([]);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadCategories() {
      try {
        const response = await fetch(`${API_URL}/arguments/categories`, {
          signal: controller.signal,
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error("Unable to load argument categories.");
        }

        const data: Category[] = await response.json();

        if (!Array.isArray(data)) {
          throw new Error("The API returned unexpected category data.");
        }

        if (!controller.signal.aborted) {
          setCategories(data);
          setCategoryId(data.length ? String(data[0].id) : "");
          setCategoryError(
            data.length ? null : "No categories are available.",
          );
        }
      } catch (err) {
        if (controller.signal.aborted) return;

        setCategoryError(
          err instanceof Error
            ? err.message
            : "Unable to load categories.",
        );
      } finally {
        if (!controller.signal.aborted) {
          setCategoriesLoading(false);
        }
      }
    }

    void loadCategories();

    return () => controller.abort();
  }, []);

  function updatePremise(
    index: number,
    field: keyof DraftPremise,
    value: string,
  ) {
    setPremises((current) =>
      current.map((item, i) =>
        i === index ? { ...item, [field]: value } : item,
      ),
    );
  }

  function updateObjection(
    index: number,
    field: "statement" | "description",
    value: string,
  ) {
    setObjections((current) =>
      current.map((item, i) =>
        i === index ? { ...item, [field]: value } : item,
      ),
    );
  }

  function updateResponse(
    objectionIndex: number,
    responseIndex: number,
    field: keyof DraftResponse,
    value: string,
  ) {
    setObjections((current) =>
      current.map((objection, i) =>
        i === objectionIndex
          ? {
              ...objection,
              responses: objection.responses.map((response, j) =>
                j === responseIndex
                  ? { ...response, [field]: value }
                  : response,
              ),
            }
          : objection,
      ),
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!categoryId) {
      setError("Choose a discipline before saving.");
      return;
    }

    if (!title.trim() || !question.trim()) {
      setError("Title and research question are required.");
      return;
    }

    setSaving(true);

    const payload = {
      title: title.trim(),
      question: question.trim(),
      summary: optionalText(summary),
      claim: optionalText(claim),
      conclusion: optionalText(conclusion),
      category_id: Number(categoryId),
      status,
      premises: premises
        .filter((item) => item.statement.trim())
        .map((item, index) => ({
          number: index + 1,
          statement: item.statement.trim(),
          description: optionalText(item.description),
        })),
      objections: objections
        .filter((item) => item.statement.trim())
        .map((item, index) => ({
          number: index + 1,
          statement: item.statement.trim(),
          description: optionalText(item.description),
          responses: item.responses
            .filter((response) => response.statement.trim())
            .map((response, responseIndex) => ({
              number: responseIndex + 1,
              statement: response.statement.trim(),
              description: optionalText(response.description),
            })),
        })),
    };

    try {
      const response = await fetch(`${API_URL}/arguments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const result = await response.json().catch(() => null);

      if (!response.ok) {
        const detail = result?.detail;
        const message =
          typeof detail === "string"
            ? detail
            : Array.isArray(detail)
              ? detail
                  .map((item: { msg?: string }) => item.msg ?? "Invalid input")
                  .join(" ")
              : `Unable to create argument (HTTP ${response.status}).`;

        throw new Error(message);
      }

      if (!result?.id) {
        throw new Error(
          "The argument may have been saved, but the API did not return its ID. Check the library before retrying.",
        );
      }

      router.push(`/arguments/${result.id}`);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "An unexpected error occurred while saving.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#e9e0ce] text-[#252b24]">
      <header className="border-b border-black/10">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-5 py-5 sm:px-8">
          <Link href="/" className="font-serif text-xl tracking-wide">
            Burhān<span className="text-[#a17b3d]">.</span>
          </Link>

          <Link
            href="/arguments"
            className="text-xs uppercase tracking-[0.14em] text-[#777164] transition hover:text-[#92703c]"
          >
            Return to archive
          </Link>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-5 py-10 sm:px-8 sm:py-14">
        <div className="border-b border-black/15 pb-8">
          <p className="text-[10px] uppercase tracking-[0.24em] text-[#92703c]">
            The research archive
          </p>

          <h1 className="mt-4 font-serif text-4xl leading-tight sm:text-5xl">
            Begin an inquiry
          </h1>

          <p className="mt-4 max-w-2xl text-sm leading-7 text-[#625e53]">
            Establish the question, state the claim, and structure the
            reasoning. You can begin with the essentials and expand the
            argument as your research develops.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-10 py-9">
          <section>
            <h2 className="font-serif text-2xl">01. Foundations</h2>
            <p className="mt-2 text-sm leading-6 text-[#777164]">
              Define what is being investigated and why it matters.
            </p>

            <div className="mt-6 space-y-5">
              <div>
                <label htmlFor="title" className={labelClass}>
                  Argument title *
                </label>
                <input
                  id="title"
                  required
                  maxLength={255}
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  placeholder="e.g. Is God necessary for contingent existence?"
                  className={inputClass}
                />
              </div>

              <div>
                <label htmlFor="question" className={labelClass}>
                  Research question *
                </label>
                <textarea
                  id="question"
                  required
                  rows={3}
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  placeholder="What precise question should this investigation answer?"
                  className={inputClass}
                />
              </div>

              <div>
                <label htmlFor="summary" className={labelClass}>
                  Summary
                </label>
                <textarea
                  id="summary"
                  rows={3}
                  value={summary}
                  onChange={(event) => setSummary(event.target.value)}
                  placeholder="A concise overview of the issue and its significance."
                  className={inputClass}
                />
              </div>

              <div>
                <label htmlFor="claim" className={labelClass}>
                  Central claim
                </label>
                <textarea
                  id="claim"
                  rows={3}
                  value={claim}
                  onChange={(event) => setClaim(event.target.value)}
                  placeholder="What proposition is being argued for or examined?"
                  className={inputClass}
                />
              </div>

              <div>
                <label htmlFor="conclusion" className={labelClass}>
                  Provisional conclusion
                </label>
                <textarea
                  id="conclusion"
                  rows={3}
                  value={conclusion}
                  onChange={(event) => setConclusion(event.target.value)}
                  placeholder="What conclusion does the current reasoning support?"
                  className={inputClass}
                />
              </div>

              <div className="grid gap-5 sm:grid-cols-2">
                <div>
                  <label htmlFor="category" className={labelClass}>
                    Discipline *
                  </label>
                  <select
                    id="category"
                    required
                    value={categoryId}
                    onChange={(event) => setCategoryId(event.target.value)}
                    disabled={categoriesLoading || categories.length === 0}
                    className={inputClass}
                  >
                    {categories.length === 0 && (
                      <option value="">No categories available</option>
                    )}
                    {categories.map((category) => (
                      <option key={category.id} value={String(category.id)}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                  {categoryError && (
                    <p className="mt-2 text-xs text-red-800">
                      {categoryError}
                    </p>
                  )}
                </div>

                <div>
                  <label htmlFor="status" className={labelClass}>
                    Research status
                  </label>
                  <select
                    id="status"
                    value={status}
                    onChange={(event) => setStatus(event.target.value)}
                    className={inputClass}
                  >
                    <option value="draft">Draft</option>
                    <option value="review">Under review</option>
                    <option value="published">Published</option>
                    <option value="archived">Archived</option>
                  </select>
                </div>
              </div>
            </div>
          </section>

          <section className="border-t border-black/15 pt-8">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h2 className="font-serif text-2xl">02. Premises</h2>
                <p className="mt-2 text-sm leading-6 text-[#777164]">
                  Record the propositions on which the reasoning depends.
                </p>
              </div>

              <button
                type="button"
                onClick={() => setPremises((items) => [...items, emptyPremise()])}
                className="border border-[#92703c]/50 px-4 py-2 text-xs uppercase tracking-wider transition hover:bg-[#f5f0e5]"
              >
                + Add premise
              </button>
            </div>

            <div className="mt-5 space-y-5">
              {premises.length === 0 && (
                <p className="border border-dashed border-black/20 px-4 py-5 text-sm text-[#777164]">
                  No premises added. You can add them now or return to the
                  argument later.
                </p>
              )}

              {premises.map((premise, index) => (
                <div
                  key={index}
                  className="border border-black/10 bg-[#f0e8d8] p-4 sm:p-5"
                >
                  <div className="mb-4 flex items-center justify-between gap-3">
                    <h3 className="font-serif text-lg">
                      Premise {index + 1}
                    </h3>
                    <button
                      type="button"
                      onClick={() =>
                        setPremises((items) =>
                          items.filter((_, i) => i !== index),
                        )
                      }
                      className="text-xs text-[#777164] underline hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>

                  <label htmlFor={`premise-${index}`} className={labelClass}>
                    Statement
                  </label>
                  <textarea
                    id={`premise-${index}`}
                    rows={3}
                    value={premise.statement}
                    onChange={(event) =>
                      updatePremise(index, "statement", event.target.value)
                    }
                    placeholder="State one premise clearly."
                    className={inputClass}
                  />

                  <label
                    htmlFor={`premise-description-${index}`}
                    className={`${labelClass} mt-4`}
                  >
                    Explanation (optional)
                  </label>
                  <textarea
                    id={`premise-description-${index}`}
                    rows={2}
                    value={premise.description}
                    onChange={(event) =>
                      updatePremise(index, "description", event.target.value)
                    }
                    placeholder="Clarifications, definitions, or supporting reasoning."
                    className={inputClass}
                  />
                </div>
              ))}
            </div>
          </section>

          <section className="border-t border-black/15 pt-8">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h2 className="font-serif text-2xl">03. Objections & responses</h2>
                <p className="mt-2 text-sm leading-6 text-[#777164]">
                  Represent serious counterarguments fairly, then record
                  responses to each one.
                </p>
              </div>

              <button
                type="button"
                onClick={() =>
                  setObjections((items) => [...items, emptyObjection()])
                }
                className="border border-[#92703c]/50 px-4 py-2 text-xs uppercase tracking-wider transition hover:bg-[#f5f0e5]"
              >
                + Add objection
              </button>
            </div>

            <div className="mt-5 space-y-6">
              {objections.length === 0 && (
                <p className="border border-dashed border-black/20 px-4 py-5 text-sm text-[#777164]">
                  No objections added yet. Adding thoughtful objections helps
                  make an argument more rigorous.
                </p>
              )}

              {objections.map((objection, index) => (
                <div
                  key={index}
                  className="border border-black/10 bg-[#f0e8d8] p-4 sm:p-5"
                >
                  <div className="mb-4 flex items-center justify-between gap-3">
                    <h3 className="font-serif text-lg">
                      Objection {index + 1}
                    </h3>
                    <button
                      type="button"
                      onClick={() =>
                        setObjections((items) =>
                          items.filter((_, i) => i !== index),
                        )
                      }
                      className="text-xs text-[#777164] underline hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>

                  <label htmlFor={`objection-${index}`} className={labelClass}>
                    Objection statement
                  </label>
                  <textarea
                    id={`objection-${index}`}
                    rows={3}
                    value={objection.statement}
                    onChange={(event) =>
                      updateObjection(index, "statement", event.target.value)
                    }
                    placeholder="Present the strongest reasonable counterargument."
                    className={inputClass}
                  />

                  <label
                    htmlFor={`objection-description-${index}`}
                    className={`${labelClass} mt-4`}
                  >
                    Explanation (optional)
                  </label>
                  <textarea
                    id={`objection-description-${index}`}
                    rows={2}
                    value={objection.description}
                    onChange={(event) =>
                      updateObjection(index, "description", event.target.value)
                    }
                    placeholder="Explain its reasoning or assumptions."
                    className={inputClass}
                  />

                  <div className="mt-6 border-t border-black/10 pt-5">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <h4 className="font-serif text-base">Responses</h4>
                      <button
                        type="button"
                        onClick={() =>
                          setObjections((items) =>
                            items.map((item, i) =>
                              i === index
                                ? {
                                    ...item,
                                    responses: [
                                      ...item.responses,
                                      emptyResponse(),
                                    ],
                                  }
                                : item,
                            ),
                          )
                        }
                        className="text-xs text-[#92703c] hover:underline"
                      >
                        + Add response
                      </button>
                    </div>

                    {objection.responses.length === 0 && (
                      <p className="mt-3 text-xs leading-5 text-[#777164]">
                        No responses added. You can address this objection
                        now or later.
                      </p>
                    )}

                    <div className="mt-4 space-y-4">
                      {objection.responses.map((response, responseIndex) => (
                        <div
                          key={responseIndex}
                          className="border-l-2 border-[#b89552] pl-4"
                        >
                          <div className="mb-3 flex items-center justify-between gap-3">
                            <p className="text-xs uppercase tracking-wider text-[#777164]">
                              Response {responseIndex + 1}
                            </p>
                            <button
                              type="button"
                              onClick={() =>
                                setObjections((items) =>
                                  items.map((item, i) =>
                                    i === index
                                      ? {
                                          ...item,
                                          responses: item.responses.filter(
                                            (_, j) => j !== responseIndex,
                                          ),
                                        }
                                      : item,
                                  ),
                                )
                              }
                              className="text-xs text-[#777164] underline hover:text-red-800"
                            >
                              Remove
                            </button>
                          </div>

                          <label
                            htmlFor={`response-${index}-${responseIndex}`}
                            className={labelClass}
                          >
                            Response statement
                          </label>
                          <textarea
                            id={`response-${index}-${responseIndex}`}
                            rows={3}
                            value={response.statement}
                            onChange={(event) =>
                              updateResponse(
                                index,
                                responseIndex,
                                "statement",
                                event.target.value,
                              )
                            }
                            placeholder="Explain how this objection can be answered."
                            className={inputClass}
                          />

                          <label
                            htmlFor={`response-description-${index}-${responseIndex}`}
                            className={`${labelClass} mt-3`}
                          >
                            Explanation (optional)
                          </label>
                          <textarea
                            id={`response-description-${index}-${responseIndex}`}
                            rows={2}
                            value={response.description}
                            onChange={(event) =>
                              updateResponse(
                                index,
                                responseIndex,
                                "description",
                                event.target.value,
                              )
                            }
                            placeholder="Supporting reasoning or qualifications."
                            className={inputClass}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {error && (
            <div
              role="alert"
              className="border border-red-900/20 bg-red-900/5 px-4 py-3 text-sm leading-6 text-red-900"
            >
              {error}
            </div>
          )}

          <div className="flex flex-wrap items-center justify-between gap-4 border-t border-black/15 pt-6">
            <Link
              href="/arguments"
              className="text-sm text-[#777164] underline underline-offset-4 hover:text-[#252b24]"
            >
              Cancel
            </Link>

            <button
              type="submit"
              disabled={saving || categoriesLoading || categories.length === 0}
              className="bg-[#303b2d] px-6 py-4 text-xs uppercase tracking-[0.16em] text-[#f5f0e5] transition hover:bg-[#43513e] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {saving ? "Saving inquiry..." : "Create argument"}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
