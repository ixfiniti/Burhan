"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type Source = {
  id: number;
  name: string;
  slug: string;
  url: string | null;
  author: string | null;
  license: string | null;
  provenance_note: string | null;
};

type ResolvedEvidence = {
  title?: string | null;
  text_arabic?: string | null;
  translation?: string | null;
  translator?: string | null;
  source?: Source | null;
  primary_source?: Source | null;
  translation_source?: Source | null;
};

type Evidence = {
  id: number;
  result_type: string;
  result_id: number;
  reference: string | null;
  role: string;
  note: string | null;
  resolved?: ResolvedEvidence | null;
};

type Premise = {
  id: number;
  number: number;
  statement: string;
  description: string | null;
  evidence: Evidence[];
};

type ResponseItem = {
  id: number;
  number: number;
  statement: string;
  description: string | null;
  evidence: Evidence[];
};

type Objection = {
  id: number;
  number: number;
  statement: string;
  description: string | null;
  responses: ResponseItem[];
};

type Argument = {
  id: number;
  title: string;
  question: string;
  summary: string;
  claim: string;
  conclusion: string;
  status: string;
  category: {
    name: string;
    slug: string;
    description: string | null;
  };
  premises: Premise[];
  objections: Objection[];
};

/*
 * The inference section below explains the logic of the argument from
 * contingency. It is specific to that argument, so it is shown only for
 * the argument IDs listed here.
 */
const INFERENCE_ARGUMENT_IDS: number[] = [1];

const EVIDENCE_ROLE_DESCRIPTIONS: Record<string, string> = {
  direct:
    "Directly addresses the claim or proposition being examined.",
  consequence:
    "Supports a result that follows from the claim or premise, if the reasoning holds.",
  conceptual:
    "Clarifies a concept, definition, or principle relevant to the reasoning.",
  contextual:
    "Provides relevant theological, historical, or textual context, but is not by itself direct proof of the claim.",
  related:
    "Has a relevant connection to the argument, but its support is indirect.",
  incidental:
    "Has a limited or tangential connection and should not carry significant argumentative weight on its own.",
  supporting:
    "Recorded as supporting material. Examine the source and note to determine the precise relationship to the claim.",
};

function getEvidenceRoleDescription(role: string): string {
  const normalizedRole = role.trim().toLowerCase().replaceAll(" ", "_");

  return (
    EVIDENCE_ROLE_DESCRIPTIONS[normalizedRole] ??
    "The relationship between this source and the claim has not yet been defined."
  );
}

const EVIDENCE_ROLES = [
  "direct",
  "consequence",
  "conceptual",
  "contextual",
  "related",
  "incidental",
  "supporting",
] as const;

function EvidenceCard({
  item,
  argumentId,
  onSaved,
  onDeleted,
}: {
  item: Evidence;
  argumentId: number;
  onSaved: (evidenceId: number, updated: { role: string; note: string | null }) => void;
  onDeleted: () => void;
}) {
  const resolved = item.resolved;
  const primarySource = resolved?.primary_source ?? resolved?.source;
  const translationSource = resolved?.translation_source;

  const [editing, setEditing] = useState(false);
  const [role, setRole] = useState(item.role);
  const [note, setNote] = useState(item.note ?? "");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  async function deleteEvidence() {
    const confirmed = window.confirm(
      "Remove this evidence from the argument? This cannot be undone.",
    );
    if (!confirmed) return;

    setDeleting(true);
    setDeleteError(null);

    try {
      const response = await fetch(
        `${API_URL}/arguments/${argumentId}/evidence/${item.id}`,
        { method: "DELETE" },
      );

      if (!response.ok) {
        const result = await response.json().catch(() => null);
        throw new Error(
          result?.detail ?? `Unable to delete evidence (HTTP ${response.status}).`,
        );
      }

      onDeleted();
    } catch (err) {
      setDeleteError(
        err instanceof Error ? err.message : "Unable to delete evidence.",
      );
    } finally {
      setDeleting(false);
    }
  }

  async function saveEvidence() {
    setSaving(true);
    setSaveError(null);

    try {
      const response = await fetch(
        `${API_URL}/arguments/${argumentId}/evidence/${item.id}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            role,
            note: note.trim() || null,
          }),
        },
      );

      if (!response.ok) {
        const result = await response.json().catch(() => null);
        throw new Error(
          result?.detail ?? `Unable to save evidence (HTTP ${response.status}).`,
        );
      }

      onSaved(item.id, {
        role,
        note: note.trim() || null,
      });

      setEditing(false);
    } catch (err) {
      setSaveError(
        err instanceof Error ? err.message : "Unable to save evidence.",
      );
    } finally {
      setSaving(false);
    }
  }

  const href =
    item.result_type === "quran"
      ? `/quran/${item.result_id}`
      : item.result_type === "hadith"
        ? `/hadith/${item.result_id}`
        : null;

  return (
    <article className="mt-4 border border-[rgba(184,149,82,0.22)] bg-[#111b1a]/[0.035] p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-[10px] uppercase tracking-[0.18em] text-[#9a7844]">
          {primarySource?.name ?? item.result_type}
        </span>

        <span className="text-xs text-[#81796d]">
          {item.reference ?? "Reference unavailable"}
        </span>
      </div>

      {resolved?.text_arabic && (
        <p
          dir="rtl"
          lang="ar"
          className="mt-4 font-arabic text-2xl leading-[2.2] text-[#252b24]"
        >
          {resolved.text_arabic}
        </p>
      )}

      {resolved?.translation && (
        <p className="mt-3 font-serif text-base leading-7 text-[#45443b]">
          {resolved.translation}
        </p>
      )}

      {resolved?.translator && (
        <p className="mt-2 text-xs text-[#81796d]">
          Translation: {resolved.translator}
        </p>
      )}

      <div className="mt-4 border-l-2 border-[#b89552] pl-3">
        <p className="text-[10px] uppercase tracking-[0.16em] text-[#9a7844]">
          Why this evidence
        </p>
        {editing ? (
          <textarea
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="Explain how this source relates to the argument..."
            rows={3}
            className="mt-2 w-full border border-black/15 bg-[#f5f0e5] p-3 text-sm leading-6 text-[#252b24] outline-none focus:border-[#b89552]"
          />
        ) : (
          <p className="mt-2 text-sm leading-6 text-[#625e53]">
            {item.note || "No explanatory note has been added yet."}
          </p>
        )}
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <div className="mt-4 flex flex-col items-start gap-2">
          {editing ? (
            <>
              <label className="text-[10px] uppercase tracking-[0.14em] text-[#92703c]">
                Evidence role
              </label>
              <select
                value={role}
                onChange={(event) => setRole(event.target.value)}
                className="border border-black/15 bg-[#f5f0e5] px-3 py-2 text-sm text-[#252b24] outline-none focus:border-[#b89552]"
              >
                {EVIDENCE_ROLES.map((option) => (
                  <option key={option} value={option}>
                    {option.charAt(0).toUpperCase() + option.slice(1)}
                  </option>
                ))}
              </select>
            </>
          ) : (
            <>
              <span className="inline-flex items-center border border-[#b89552]/40 bg-[#b89552]/[0.08] px-2 py-1 text-[10px] uppercase tracking-[0.14em] text-[#92703c]">
                {item.role.replaceAll("_", " ")}
              </span>
              <p className="max-w-2xl text-xs leading-5 text-[#777164]">
                {getEvidenceRoleDescription(item.role)}
              </p>
            </>
          )}

          {editing && saveError && (
            <p role="alert" className="text-sm text-red-700">
              {saveError}
            </p>
          )}

          <div className="flex flex-wrap gap-2">
            {editing ? (
              <>
                <button
                  type="button"
                  onClick={saveEvidence}
                  disabled={saving}
                  className="border border-[#92703c] bg-[#92703c] px-3 py-2 text-xs text-[#fffaf0] transition hover:bg-[#614823] disabled:opacity-50"
                >
                  {saving ? "Saving..." : "Save changes"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setRole(item.role);
                    setNote(item.note ?? "");
                    setSaveError(null);
                    setEditing(false);
                  }}
                  disabled={saving}
                  className="border border-black/15 px-3 py-2 text-xs text-[#625e53] transition hover:bg-black/5 disabled:opacity-50"
                >
                  Cancel
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={() => {
                  setRole(item.role);
                  setNote(item.note ?? "");
                  setSaveError(null);
                  setEditing(true);
                }}
                className="border border-[#b89552]/50 px-3 py-2 text-xs text-[#92703c] transition hover:bg-[#b89552]/10"
              >
                Edit evidence
              </button>
            )}
          </div>
          {!editing && (
            <button
              type="button"
              onClick={deleteEvidence}
              disabled={deleting}
              className="border border-red-900/25 px-3 py-2 text-xs text-red-800 transition hover:bg-red-900/[0.06] disabled:opacity-50"
            >
              {deleting ? "Removing..." : "Remove evidence"}
            </button>
          )}
          {deleteError && (
            <p role="alert" className="text-sm text-red-700">
              {deleteError}
            </p>
          )}
        </div>

        {href && (
          <Link
            href={href}
            className="text-xs text-[#92703c] transition hover:text-[#614823]"
          >
            Open source →
          </Link>
        )}
      </div>

      {(primarySource?.provenance_note ||
        translationSource?.provenance_note ||
        primarySource?.url ||
        translationSource?.url) && (
        <details className="mt-4 border-t border-black/10 pt-3">
          <summary className="cursor-pointer text-xs text-[#81796d]">
            Source provenance
          </summary>

          {primarySource && (
            <div className="mt-3">
              <p className="text-[10px] uppercase tracking-[0.14em] text-[#92703c]">
                Original text source
              </p>
              <p className="mt-1 text-sm text-[#45443b]">
                {primarySource.name}
              </p>

              {primarySource.author && (
                <p className="mt-1 text-xs text-[#81796d]">
                  Author: {primarySource.author}
                </p>
              )}

              {primarySource.license && (
                <p className="mt-1 text-xs text-[#81796d]">
                  License: {primarySource.license}
                </p>
              )}

              {primarySource.provenance_note && (
                <p className="mt-2 text-xs leading-5 text-[#625e53]">
                  {primarySource.provenance_note}
                </p>
              )}

              {primarySource.url && (
                <a
                  href={primarySource.url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 inline-block text-xs text-[#92703c] underline"
                >
                  Visit original source
                </a>
              )}
            </div>
          )}

          {translationSource && (
            <div className="mt-4 border-t border-black/10 pt-3">
              <p className="text-[10px] uppercase tracking-[0.14em] text-[#92703c]">
                Translation source
              </p>
              <p className="mt-1 text-sm text-[#45443b]">
                {translationSource.name}
              </p>

              {resolved?.translator && (
                <p className="mt-1 text-xs text-[#81796d]">
                  Translator: {resolved.translator}
                </p>
              )}

              {translationSource.provenance_note && (
                <p className="mt-2 text-xs leading-5 text-[#625e53]">
                  {translationSource.provenance_note}
                </p>
              )}

              {translationSource.url && (
                <a
                  href={translationSource.url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 inline-block text-xs text-[#92703c] underline"
                >
                  Visit translation source
                </a>
              )}
            </div>
          )}

          {!primarySource && !translationSource && (
            <p className="mt-2 text-xs leading-5 text-[#625e53]">
              Separate source records are not available for this evidence.
            </p>
          )}
        </details>
      )}
    </article>
  );
}

type QuranSearchResult = {
  id: number;
  reference: string;
  surah_name_arabic: string;
  surah_name_english: string;
  surah_name_transliteration: string;
  ayah_number: number;
  text_arabic: string;
  translation: string | null;
  translator: string | null;
};

type HadithSearchResult = {
  id: number;
  number: string | number;
  reference: string;
  in_book_reference: string | null;
  collection_name: string;
  book_number: number | null;
  book_name: string | null;
  text_arabic: string | null;
  translation: string | null;
  translator: string | null;
  narrator: string | null;
  source_url: string | null;
  score: number | null;
};

type EvidenceSearchResult =
  | ({ resultType: "quran" } & QuranSearchResult)
  | ({ resultType: "hadith" } & HadithSearchResult);

function AddEvidenceForm({
  argumentId,
  targetType,
  targetId,
  onCreated,
}: {
  argumentId: number;
  targetType: "premise" | "response";
  targetId: number;
  onCreated: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [resultType, setResultType] = useState<"quran" | "hadith">("quran");
  const [searchText, setSearchText] = useState("");
  const [results, setResults] = useState<EvidenceSearchResult[]>([]);
  const [selected, setSelected] = useState<EvidenceSearchResult | null>(null);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [role, setRole] = useState("supporting");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  function changeResultType(nextType: "quran" | "hadith") {
    setResultType(nextType);
    setResults([]);
    setSelected(null);
    setSearchError(null);
    setFormError(null);
  }

  async function searchEvidence(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const query = searchText.trim();
    if (!query) {
      setSearchError("Enter Arabic or translated text to search.");
      return;
    }

    setSearching(true);
    setSearchError(null);
    setSelected(null);
    setResults([]);

    try {
      const endpoint = resultType === "quran" ? "quran/search" : "hadiths/search";
      const response = await fetch(
        `${API_URL}/${endpoint}?q=${encodeURIComponent(query)}&limit=20`,
        { cache: "no-store" },
      );

      if (!response.ok) {
        const result = await response.json().catch(() => null);
        throw new Error(
          result?.detail ?? `Search failed (HTTP ${response.status}).`,
        );
      }

      const data: unknown = await response.json();
      if (!Array.isArray(data)) {
        throw new Error("The search endpoint returned an unexpected response.");
      }

      const mapped: EvidenceSearchResult[] = data.map((item) => ({
        ...item,
        resultType,
      })) as EvidenceSearchResult[];

      setResults(mapped);
      if (mapped.length === 0) {
        setSearchError("No matches found. Try different wording or another language.");
      }
    } catch (err) {
      setSearchError(
        err instanceof Error ? err.message : "Unable to search for evidence.",
      );
    } finally {
      setSearching(false);
    }
  }

  async function createEvidence(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);

    if (!selected) {
      setFormError("Search for and select a source before saving.");
      return;
    }

    const reference =
      selected.resultType === "quran"
        ? `Qur'an ${selected.reference}`
        : selected.reference || `${selected.collection_name} ${selected.number}`;

    setSaving(true);
    try {
      const endpoint =
        targetType === "premise"
          ? `${API_URL}/arguments/${argumentId}/premises/${targetId}/evidence`
          : `${API_URL}/arguments/${argumentId}/responses/${targetId}/evidence`;

      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          result_type: selected.resultType,
          result_id: selected.id,
          reference,
          role,
          note: note.trim() || null,
        }),
      });

      if (!response.ok) {
        const result = await response.json().catch(() => null);
        throw new Error(
          result?.detail ?? `Unable to add evidence (HTTP ${response.status}).`,
        );
      }

      setSearchText("");
      setResults([]);
      setSelected(null);
      setRole("supporting");
      setNote("");
      setOpen(false);
      onCreated();
    } catch (err) {
      setFormError(
        err instanceof Error ? err.message : "Unable to add evidence.",
      );
    } finally {
      setSaving(false);
    }
  }

  function getResultTitle(item: EvidenceSearchResult) {
    if (item.resultType === "quran") {
      return `${item.surah_name_english} ${item.reference}`;
    }
    return `${item.collection_name} · ${item.reference || `Hadith ${item.number}`}`;
  }

  return (
    <div className="mt-4">
      <button
        type="button"
        onClick={() => {
          setOpen((current) => !current);
          setFormError(null);
          setSearchError(null);
        }}
        className="border border-[#b89552]/50 px-3 py-2 text-xs text-[#92703c] transition hover:bg-[#b89552]/10"
      >
        {open ? "Cancel adding evidence" : "+ Add evidence"}
      </button>

      {open && (
        <div className="mt-3 space-y-4 border border-[#b89552]/30 bg-[#f5f0e5] p-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="flex flex-col gap-2 text-xs text-[#625e53]">
              Evidence type
              <select
                value={resultType}
                onChange={(event) =>
                  changeResultType(event.target.value as "quran" | "hadith")
                }
                className="border border-black/15 bg-white/60 px-3 py-2 text-sm text-[#252b24]"
              >
                <option value="quran">Qur'an ayah</option>
                <option value="hadith">Hadith</option>
              </select>
            </label>
            <p className="self-end text-xs leading-5 text-[#81796d]">
              Search by Arabic text or an English translation, then select the
              exact passage you want to attach.
            </p>
          </div>

          <form onSubmit={searchEvidence} className="space-y-3">
            <label className="flex flex-col gap-2 text-xs text-[#625e53]">
              Search source text
              <input
                value={searchText}
                onChange={(event) => setSearchText(event.target.value)}
                placeholder={
                  resultType === "quran"
                    ? "e.g. الله or mercy"
                    : "e.g. إنما الأعمال or intentions"
                }
                className="border border-black/15 bg-white/60 px-3 py-2 text-sm text-[#252b24]"
              />
            </label>
            <button
              type="submit"
              disabled={searching}
              className="border border-[#92703c] px-4 py-2 text-xs text-[#92703c] transition hover:bg-[#b89552]/10 disabled:opacity-50"
            >
              {searching ? "Searching..." : "Search"}
            </button>
          </form>

          {searchError && (
            <p role="status" className="text-sm text-[#8a4a32]">
              {searchError}
            </p>
          )}

          {results.length > 0 && (
            <div className="space-y-3">
              <p className="text-[10px] uppercase tracking-[0.16em] text-[#92703c]">
                Search results · {results.length}
              </p>
              {results.map((item) => {
                const isSelected =
                  selected?.resultType === item.resultType &&
                  selected.id === item.id;
                return (
                  <article
                    key={`${item.resultType}-${item.id}`}
                    className={`border p-3 ${
                      isSelected
                        ? "border-[#92703c] bg-[#b89552]/10"
                        : "border-black/10 bg-white/40"
                    }`}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <h3 className="text-sm font-medium text-[#252b24]">
                        {getResultTitle(item)}
                      </h3>
                      <button
                        type="button"
                        onClick={() => {
                          setSelected(item);
                          setFormError(null);
                        }}
                        className={`shrink-0 border px-3 py-1.5 text-xs ${
                          isSelected
                            ? "border-[#92703c] bg-[#92703c] text-[#fffaf0]"
                            : "border-[#b89552]/50 text-[#92703c] hover:bg-[#b89552]/10"
                        }`}
                      >
                        {isSelected ? "Selected" : "Select"}
                      </button>
                    </div>
                    {item.text_arabic && (
                      <p
                        dir="rtl"
                        lang="ar"
                        className="mt-3 font-arabic text-xl leading-[2] text-[#252b24]"
                      >
                        {item.text_arabic}
                      </p>
                    )}
                    {item.translation && (
                      <p className="mt-2 text-sm leading-6 text-[#625e53]">
                        {item.translation}
                      </p>
                    )}
                    {item.translator && (
                      <p className="mt-1 text-xs text-[#81796d]">
                        Translation: {item.translator}
                      </p>
                    )}
                    {item.resultType === "quran" && (
                      <p className="mt-2 text-xs text-[#81796d]">
                        {item.surah_name_arabic} · {item.surah_name_transliteration}
                      </p>
                    )}
                    {item.resultType === "hadith" && item.narrator && (
                      <p className="mt-2 text-xs text-[#81796d]">
                        Narrator: {item.narrator}
                      </p>
                    )}
                  </article>
                );
              })}
            </div>
          )}

          {selected && (
            <div className="border-l-2 border-[#b89552] pl-3">
              <p className="text-[10px] uppercase tracking-[0.14em] text-[#92703c]">
                Selected source
              </p>
              <p className="mt-1 text-sm text-[#252b24]">
                {getResultTitle(selected)}
              </p>
            </div>
          )}

          <form onSubmit={createEvidence} className="space-y-4 border-t border-black/10 pt-4">
            <label className="flex flex-col gap-2 text-xs text-[#625e53]">
              Evidence role
              <select
                value={role}
                onChange={(event) => setRole(event.target.value)}
                className="border border-black/15 bg-white/60 px-3 py-2 text-sm text-[#252b24]"
              >
                {EVIDENCE_ROLES.map((option) => (
                  <option key={option} value={option}>
                    {option.charAt(0).toUpperCase() + option.slice(1)}
                  </option>
                ))}
              </select>
              <span className="text-xs leading-5 text-[#81796d]">
                {getEvidenceRoleDescription(role)}
              </span>
            </label>

            <label className="flex flex-col gap-2 text-xs text-[#625e53]">
              Why is this source relevant? (optional)
              <textarea
                value={note}
                onChange={(event) => setNote(event.target.value)}
                rows={3}
                placeholder="Explain how the source relates to this premise or response..."
                className="border border-black/15 bg-white/60 p-3 text-sm leading-6 text-[#252b24]"
              />
            </label>

            {formError && (
              <p role="alert" className="text-sm text-red-700">
                {formError}
              </p>
            )}

            <button
              type="submit"
              disabled={saving || !selected}
              className="border border-[#92703c] bg-[#92703c] px-4 py-2 text-xs text-[#fffaf0] transition hover:bg-[#614823] disabled:opacity-50"
            >
              {saving ? "Adding evidence..." : "Attach selected evidence"}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

function PremiseCard({
  premise,
  argumentId,
  onEvidenceSaved,
  onEvidenceChanged,
}: {
  premise: Premise;
  argumentId: number;
  onEvidenceSaved: (
    evidenceId: number,
    updated: { role: string; note: string | null },
  ) => void;
  onEvidenceChanged: () => void;
}) {
  return (
    <article
      id={`premise-${premise.id}`}
      className="border border-black/10 bg-[#f5f0e5] p-5 sm:p-6"
    >
      <div className="text-[10px] uppercase tracking-[0.2em] text-[#9a7844]">
        Premise {premise.number}
      </div>

      <h3 className="mt-3 font-serif text-xl leading-8 text-[#252b24]">
        {premise.statement}
      </h3>

      {premise.description && (
        <p className="mt-2 text-sm leading-6 text-[#777164]">
          {premise.description}
        </p>
      )}

      {premise.evidence.length > 0 ? (
        <div className="mt-5">
          <div className="text-[10px] uppercase tracking-[0.18em] text-[#81796d]">
            Linked evidence · {premise.evidence.length}
          </div>

          {premise.evidence.map((item) => (
            <EvidenceCard
              key={item.id}
              item={item}
              argumentId={argumentId}
              onSaved={onEvidenceSaved}
              onDeleted={onEvidenceChanged}
            />
          ))}
        </div>
      ) : (
        <div className="mt-5 border border-dashed border-black/15 px-4 py-3">
          <p className="text-xs uppercase tracking-[0.12em] text-[#81796d]">
            No evidence linked yet
          </p>
          <p className="mt-1 text-sm leading-6 text-[#777164]">
            This premise has not been linked to supporting material in Burhān.
            That does not, by itself, mean the premise is false.
          </p>
        </div>
      )}

      <AddEvidenceForm
        argumentId={argumentId}
        targetType="premise"
        targetId={premise.id}
        onCreated={onEvidenceChanged}
      />
    </article>
  );
}

export default function ArgumentReaderPage() {
  const params = useParams<{ argumentId: string }>();
  const argumentId = params.argumentId;

  const [argument, setArgument] = useState<Argument | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  function refreshArgument() {
    setRefreshKey((current) => current + 1);
  }

  function handleEvidenceSaved(
    evidenceId: number,
    updated: { role: string; note: string | null },
  ) {
    setArgument((current) => {
      if (!current) return current;

      return {
        ...current,

        premises: current.premises.map((premise) => ({
          ...premise,
          evidence: premise.evidence.map((item) =>
            item.id === evidenceId ? { ...item, ...updated } : item,
          ),
        })),

        objections: current.objections.map((objection) => ({
          ...objection,
          responses: objection.responses.map((response) => ({
            ...response,
            evidence: response.evidence.map((item) =>
              item.id === evidenceId ? { ...item, ...updated } : item,
            ),
          })),
        })),
      };
    });
  }

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);

    async function loadArgument() {
      try {
        const response = await fetch(
          `${API_URL}/arguments/${encodeURIComponent(argumentId)}`,
          { signal: controller.signal, cache: "no-store" },
        );

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error("This argument could not be found.");
          }
          throw new Error(
            `Unable to load the argument (HTTP ${response.status}).`,
          );
        }

        const result: Argument = await response.json();

        if (!controller.signal.aborted) {
          setArgument(result);
          setError(null);
        }
      } catch (err) {
        if (controller.signal.aborted) return;

        setArgument(null);
        setError(
          err instanceof Error
            ? err.message
            : "An unexpected error occurred.",
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void loadArgument();

    return () => controller.abort();
  }, [argumentId, refreshKey]);

  return (
    <main className="min-h-screen bg-[#e9e0ce] text-[#252b24]">
      <header className="border-b border-black/10">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-5 py-5 sm:px-8">
          <Link href="/" className="font-serif text-xl tracking-wide">
            Burhān<span className="text-[#a17b3d]">.</span>
          </Link>

          <Link
            href="/quran/4803"
            className="text-xs uppercase tracking-[0.14em] text-[#777164] transition hover:text-[#92703c]"
          >
            Qur&apos;an research
          </Link>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-5 py-10 sm:px-8 sm:py-16">
        {loading ? (
          <p className="py-20 text-center text-sm text-[#777164]">
            Retrieving argument and evidence…
          </p>
        ) : error ? (
          <section className="border border-red-900/20 bg-red-950/[0.035] p-6">
            <h1 className="font-serif text-2xl">Argument unavailable</h1>
            <p className="mt-3 text-sm leading-6 text-[#777164]">
              {error}
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-5 border border-black/15 px-4 py-2 text-xs uppercase tracking-wider"
            >
              Try again
            </button>
          </section>
        ) : argument ? (
          <>
            <section id="overview" className="border-b border-black/15 pb-9">
              <div className="flex flex-wrap items-center gap-3 text-[10px] uppercase tracking-[0.2em] text-[#92703c]">
                <span>{argument.category?.name ?? "Research"}</span>
                <span className="text-black/25">/</span>
                <span>Argument {argument.id}</span>
                <span className="border border-black/15 px-2 py-1 text-[#777164]">
                  {argument.status}
                </span>
              </div>

              <h1 className="mt-6 max-w-4xl font-serif text-4xl leading-tight sm:text-5xl">
                {argument.title}
              </h1>

              <p className="mt-5 max-w-3xl text-lg leading-8 text-[#625e53]">
                {argument.question}
              </p>

              <p className="mt-5 max-w-3xl text-sm leading-7 text-[#777164]">
                {argument.summary}
              </p>
            </section>

            <section id="claim" className="grid gap-4 border-b border-black/10 py-8 md:grid-cols-2">
              <div className="border-l-2 border-[#b89552] bg-[#f5f0e5] p-5">
                <div className="text-[10px] uppercase tracking-[0.2em] text-[#92703c]">
                  Central claim
                </div>
                <p className="mt-3 font-serif text-xl leading-8">
                  {argument.claim}
                </p>
              </div>

              <div className="border-l-2 border-[#7b8770] bg-[#f5f0e5] p-5">
                <div className="text-[10px] uppercase tracking-[0.2em] text-[#777164]">
                  Conclusion
                </div>
                <p className="mt-3 font-serif text-xl leading-8">
                  {argument.conclusion}
                </p>
              </div>
            </section>

            <nav
              aria-label="Argument contents"
              className="flex flex-wrap gap-x-5 gap-y-3 border-b border-black/10 py-5 text-xs uppercase tracking-[0.12em] text-[#777164]"
            >
              <a href="#overview" className="transition hover:text-[#92703c]">
                Overview
              </a>
              <a href="#claim" className="transition hover:text-[#92703c]">
                Claim
              </a>
              <a href="#premises" className="transition hover:text-[#92703c]">
                Premises
              </a>
              <a href="#objections" className="transition hover:text-[#92703c]">
                Objections &amp; responses
              </a>
            </nav>

            <section id="premises" className="py-10">
              <div className="mb-6">
                <div className="text-[10px] uppercase tracking-[0.2em] text-[#92703c]">
                  I · The reasoning
                </div>
                <h2 className="mt-2 font-serif text-3xl">
                  Premises
                </h2>
                <p className="mt-2 text-sm leading-6 text-[#777164]">
                  Examine each premise and the evidence associated with it.
                </p>
              </div>

              {argument.premises.length ? (
                <div className="space-y-4">
                  {argument.premises.map((premise) => (
                    <PremiseCard
                      key={premise.id}
                      premise={premise}
                      argumentId={argument.id}
                      onEvidenceSaved={handleEvidenceSaved}
                      onEvidenceChanged={refreshArgument}
                    />
                  ))}
                </div>
              ) : (
                <p className="text-sm text-[#777164]">
                  No premises have been added yet.
                </p>
              )}
            </section>

            {INFERENCE_ARGUMENT_IDS.includes(argument.id) && (
              <section id="inference" className="border-t border-black/10 py-10">
                <div className="mb-6">
                  <div className="text-[10px] uppercase tracking-[0.2em] text-[#92703c]">
                    Logic of the argument
                  </div>
                  <h2 className="mt-2 font-serif text-3xl">
                    From premises to inference
                  </h2>
                  <p className="mt-2 max-w-3xl text-sm leading-6 text-[#777164]">
                    This section explains how the premises are meant to lead to
                    the conclusion. It describes the structure of the reasoning;
                    it does not claim that every step has been established.
                  </p>
                </div>

                <div className="grid gap-4 md:grid-cols-3">
                  <div className="border border-black/10 bg-[#f5f0e5] p-5">
                    <div className="text-[10px] uppercase tracking-[0.18em] text-[#9a7844]">
                      1 · The premises
                    </div>
                    <p className="mt-3 text-sm leading-6 text-[#45443b]">
                      The premises claim that things in the world are
                      contingent: each could have failed to exist, so each
                      needs an explanation for why it exists rather than not.
                      They also claim that this need for explanation is real
                      and cannot simply be set aside.
                    </p>
                  </div>

                  <div className="border border-black/10 bg-[#f5f0e5] p-5">
                    <div className="text-[10px] uppercase tracking-[0.18em] text-[#9a7844]">
                      2 · The inference
                    </div>
                    <p className="mt-3 text-sm leading-6 text-[#45443b]">
                      If every contingent thing is explained only by other
                      contingent things, the question of why there are any
                      contingent things at all is left unanswered. The argument
                      infers that a complete explanation must ultimately rest
                      on something that does not depend on anything else for
                      its existence.
                    </p>
                  </div>

                  <div className="border border-black/10 bg-[#f5f0e5] p-5">
                    <div className="text-[10px] uppercase tracking-[0.18em] text-[#9a7844]">
                      3 · The open question
                    </div>
                    <p className="mt-3 text-sm leading-6 text-[#45443b]">
                      Whether this establishes a necessary foundation depends
                      on whether the premises are accepted; the objections
                      below challenge them. Even if a necessary foundation is
                      granted, further reasoning is needed to show that it is
                      God and to say what attributes it has.
                    </p>
                  </div>
                </div>
              </section>
            )}

            <section id="objections" className="border-t border-black/10 py-10">
              <div className="text-[10px] uppercase tracking-[0.2em] text-[#92703c]">
                II · Critical examination
              </div>
              <h2 className="mt-2 font-serif text-3xl">
                Objections &amp; responses
              </h2>

              {argument.objections.length ? (
                <div className="mt-6 space-y-6">
                  {argument.objections.map((objection) => (
                    <article
                      key={objection.id}
                      id={`objection-${objection.id}`}
                      className="border border-black/10 bg-[#f5f0e5] p-5 sm:p-6"
                    >
                      <div className="text-[10px] uppercase tracking-[0.18em] text-[#9a7844]">
                        Objection {objection.number}
                      </div>

                      <h3 className="mt-3 font-serif text-xl leading-8">
                        {objection.statement}
                      </h3>

                      {objection.description && (
                        <p className="mt-2 text-sm leading-6 text-[#777164]">
                          {objection.description}
                        </p>
                      )}

                      {objection.responses.length > 0 && (
                        <div className="mt-6 space-y-4 border-l border-[#b89552]/50 pl-4 sm:pl-5">
                          {objection.responses.map((response) => (
                            <div key={response.id} id={`response-${response.id}`}>
                              <div className="text-[10px] uppercase tracking-[0.18em] text-[#92703c]">
                                Response {response.number}
                              </div>

                              <p className="mt-2 font-serif text-lg leading-7">
                                {response.statement}
                              </p>

                              {response.description && (
                                <p className="mt-2 text-sm leading-6 text-[#777164]">
                                  {response.description}
                                </p>
                              )}

                              <div className="mt-4">
                                <div className="text-[10px] uppercase tracking-[0.18em] text-[#81796d]">
                                  Response evidence · {response.evidence.length}
                                </div>

                                {response.evidence.length > 0 ? (
                                  response.evidence.map((item) => (
                                    <EvidenceCard
                                      key={item.id}
                                      item={item}
                                      argumentId={argument.id}
                                      onSaved={handleEvidenceSaved}
                                      onDeleted={refreshArgument}
                                    />
                                  ))
                                ) : (
                                  <p className="mt-2 border border-dashed border-black/15 px-4 py-3 text-sm leading-6 text-[#777164]">
                                    No evidence has been linked to this response yet. This does not
                                    establish whether the response is correct or incorrect.
                                  </p>
                                )}
                                <AddEvidenceForm
                                  argumentId={argument.id}
                                  targetType="response"
                                  targetId={response.id}
                                  onCreated={refreshArgument}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </article>
                  ))}
                </div>
              ) : (
                <p className="mt-4 text-sm text-[#777164]">
                  No objections have been recorded yet.
                </p>
              )}
            </section>

            <footer className="border-t border-black/10 py-6 text-xs leading-6 text-[#81796d]">
              Burhān · Evidence-led Islamic research
              <p className="mt-1">
                Arguments are structured investigations. Their premises,
                interpretations, and conclusions should be examined critically.
              </p>
            </footer>
          </>
        ) : null}
      </div>
    </main>
  );
}