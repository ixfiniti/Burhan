"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import NotesPanel from "@/components/NotesPanel";
import { MagicCard } from "@/components/ui/magic-card";

type EvidenceRole =
  | "direct"
  | "consequence"
  | "conceptual"
  | "contextual"
  | "related"
  | "incidental";

type ResearchSource = {
  id: number;
  name: string;
  slug: string | null;
  source_type: string | null;
  language: string | null;
  author: string | null;
  publisher: string | null;
  url: string | null;
  license: string | null;
  version: string | null;
  provenance_note: string | null;
  description: string | null;
};

type SearchResult = {
  id: number;
  result_type: "quran" | "hadith" | "argument";
  reference: string;
  title: string | null;
  collection: string | null;
  book_number: number | null;
  book_name: string | null;
  narrator: string | null;
  text_arabic: string | null;
  translation: string | null;
  translator: string | null;
  match_type: string;
  evidence_role?: EvidenceRole;
  source: ResearchSource | null;
  primary_source?: ResearchSource | null;
  translation_source?: ResearchSource | null;
  score: number;

  // Argument-specific fields
  question?: string | null;
  summary?: string | null;
  claim?: string | null;
  conclusion?: string | null;
  status?: string | null;
  category?: {
    id: number;
    name: string;
    slug: string;
  } | null;
};

const researchDomains = [
  { label: "All", arabic: "الكل" },
  { label: "Qur'an", arabic: "القرآن" },
  { label: "Hadith", arabic: "الحديث" },
  { label: "Arguments", arabic: "الحجج" },
  { label: "Scholarship", arabic: "العلم" },
];

const recentResearch = [
  {
    question: "What does the Qur'an say about riba?",
    sources: "Qur'an · Hadith · Scholarship",
  },
  {
    question: "How was the Qur'an transmitted?",
    sources: "Qur'an · Manuscripts · Scholarship",
  },
  {
    question: "What is the argument for a necessary existence?",
    sources: "Philosophy · Theology · Classical scholarship",
  },
];

const evidenceRoleMeta: Record<
  EvidenceRole,
  {
    label: string;
    shortLabel: string;
    description: string;
  }
> = {
  direct: {
    label: "Direct evidence",
    shortLabel: "Direct",
    description: "Directly addresses the question or claim.",
  },
  consequence: {
    label: "Consequence",
    shortLabel: "Consequence",
    description: "Describes a consequence, ruling, warning, or result.",
  },
  conceptual: {
    label: "Conceptual",
    shortLabel: "Conceptual",
    description: "Provides a principle or underlying concept.",
  },
  contextual: {
    label: "Contextual",
    shortLabel: "Contextual",
    description: "Provides historical, textual, or surrounding context.",
  },
  related: {
    label: "Related",
    shortLabel: "Related",
    description: "Relevant to the subject but not directly responsive.",
  },
  incidental: {
    label: "Incidental",
    shortLabel: "Incidental",
    description: "Contains a weaker or incidental connection.",
  },
};

function resultLabel(result: SearchResult) {
  switch (result.result_type) {
    case "quran":
      return "Qur'an";
    case "hadith":
      return "Hadith";
    case "argument":
      return "Argument";
  }
}

function excerpt(text: string | null, length = 260) {
  if (!text) {
    return "";
  }

  const cleaned = text.replace(/\s+/g, " ").trim();

  if (cleaned.length <= length) {
    return cleaned;
  }

  return `${cleaned.slice(0, length).trim()}…`;
}

function evidenceRoleLabel(role?: EvidenceRole) {
  if (!role) {
    return "Evidence";
  }

  return evidenceRoleMeta[role]?.label ?? "Evidence";
}

function evidenceRoleDescription(role?: EvidenceRole) {
  if (!role) {
    return "";
  }

  return evidenceRoleMeta[role]?.description ?? "";
}

function evidenceRoleClasses(role?: EvidenceRole) {
  switch (role) {
    case "direct":
      return "border-gold bg-gold text-ink-deep font-bold";

    case "consequence":
      return "border-copper/35 bg-copper/[0.07] text-copper";

    case "conceptual":
      return "border-lapis/40 bg-lapis/[0.14] text-parchment-deep";

    case "contextual":
      return "border-white/15 bg-white/[0.03] text-text-secondary";

    case "related":
      return "border-white/10 bg-white/[0.02] text-text-muted";

    case "incidental":
      return "border-white/[0.08] bg-white/[0.015] text-text-muted";

    default:
      return "border-white/10 bg-white/[0.02] text-text-muted";
  }
}

function evidenceRoleAccent(role?: EvidenceRole) {
  switch (role) {
    case "direct":
      return "bg-gold";

    case "consequence":
      return "bg-copper";

    case "conceptual":
      return "bg-lapis";

    case "contextual":
      return "bg-white/30";

    case "related":
      return "bg-white/15";

    case "incidental":
      return "bg-white/10";

    default:
      return "bg-white/15";
  }
}

export default function Home() {
  const router = useRouter();

  const [notesOpen, setNotesOpen] = useState(false);

  const [query, setQuery] = useState("");
  const [selectedDomain, setSelectedDomain] = useState<string>("All");

  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const [results, setResults] = useState<SearchResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (searchQuery?: string) => {
    const trimmedQuery = (searchQuery ?? query).trim();

    if (!trimmedQuery || searching) {
      return;
    }

    if (searchQuery) {
      setQuery(searchQuery);
    }

    setHasSearched(true);
    setSearchError(null);
    setResults([]);

    if (selectedDomain === "Scholarship") {
      setSearchError(
        "Scholarship search is not available yet. Its searchable sources have not been integrated into Burhān.",
      );
      return;
    }

    setSearching(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;

      if (!apiUrl) {
        throw new Error("NEXT_PUBLIC_API_URL is not configured");
      }

      const fetchResearchDomain = async (
        domain: "quran" | "hadith",
      ): Promise<SearchResult[]> => {
        const params = new URLSearchParams({
          q: trimmedQuery,
          domain,
          limit: "20",
        });

        const response = await fetch(
          `${apiUrl}/search/research?${params.toString()}`,
        );

        if (!response.ok) {
          throw new Error(`${domain} search request failed`);
        }

        const data = await response.json();

        return data.results ?? [];
      };

      const fetchArgumentResults = async (): Promise<SearchResult[]> => {
        const params = new URLSearchParams({
          q: trimmedQuery,
          limit: "20",
        });

        const response = await fetch(
          `${apiUrl}/arguments/search?${params.toString()}`,
        );

        if (!response.ok) {
          throw new Error("Argument search request failed");
        }

        const data = await response.json();

        return (data.results ?? []).map(
          (item: {
            id: number;
            result_type: "argument";
            reference: string;
            title: string;
            question: string;
            summary: string | null;
            claim: string | null;
            conclusion: string | null;
            status: string;
            category: {
              id: number;
              name: string;
              slug: string;
            };
          }): SearchResult => ({
            id: item.id,
            result_type: "argument",
            reference: item.reference,
            title: item.title,
            collection: null,
            book_number: null,
            book_name: null,
            narrator: null,
            text_arabic: null,
            translation: null,
            translator: null,
            match_type: "argument_text",
            source: null,
            primary_source: null,
            translation_source: null,
            score: 0,
            question: item.question,
            summary: item.summary,
            claim: item.claim,
            conclusion: item.conclusion,
            status: item.status,
            category: item.category,
          }),
        );
      };

      if (selectedDomain === "Qur'an") {
        setResults(await fetchResearchDomain("quran"));
        return;
      }

      if (selectedDomain === "Hadith") {
        setResults(await fetchResearchDomain("hadith"));
        return;
      }

      if (selectedDomain === "Arguments") {
        setResults(await fetchArgumentResults());
        return;
      }

      // All: search every currently supported domain in parallel.
      const [quranResults, hadithResults, argumentResults] =
        await Promise.all([
          fetchResearchDomain("quran"),
          fetchResearchDomain("hadith"),
          fetchArgumentResults(),
        ]);

      // Interleave results so one domain cannot fill the entire list
      // before results from the other domains are represented.
      const combined: SearchResult[] = [];
      const groups = [
        quranResults,
        hadithResults,
        argumentResults,
      ];

      for (let index = 0; index < 20; index++) {
        for (const group of groups) {
          if (group[index]) {
            combined.push(group[index]);
          }
        }
      }

      setResults(combined.slice(0, 20));
    } catch (error) {
      console.error("Burhān search failed:", error);

      setResults([]);

      setSearchError(
        "The investigation could not be completed. Check that the Burhān research service is running.",
      );
    } finally {
      setSearching(false);
    }
  };

  const handleExamine = (result: SearchResult) => {
    switch (result.result_type) {
      case "quran":
        router.push(`/quran/${result.id}`);
        break;

      case "hadith":
        router.push(`/hadith/${result.id}`);
        break;

      case "argument":
        router.push(`/arguments/${result.id}`);
        break;
    }
  };

  const featuredResult = results[0];
  const relatedResults = results.slice(1);

  return (
    <main className="min-h-screen overflow-x-hidden bg-ink-deep text-parchment-light">
      {/* Ambient background */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-[-28rem] h-[55rem] w-[55rem] -translate-x-1/2 rounded-full bg-lapis/[0.22] blur-[130px]" />

        <div className="absolute bottom-[-25rem] right-[-15rem] h-[45rem] w-[45rem] rounded-full bg-copper/[0.11] blur-[130px]" />

        <div className="absolute left-1/2 top-[8rem] h-[30rem] w-[60rem] -translate-x-1/2 rounded-full bg-gold/[0.05] blur-[150px]" />

        <div className="absolute inset-0 opacity-[0.03] [background-image:linear-gradient(rgba(205,183,125,0.5)_1px,transparent_1px),linear-gradient(90deg,rgba(205,183,125,0.5)_1px,transparent_1px)] [background-size:72px_72px]" />
      </div>

      <div className="relative mx-auto min-h-screen max-w-[1500px] px-5 sm:px-8 lg:px-12">
        {/* Header */}
        <header className="flex items-center justify-between border-b border-white/[0.08] py-6">
          <div className="flex items-center gap-5">
            <div>
              <div className="font-display text-xl tracking-[0.12em] text-parchment-light">
                BURHĀN
              </div>

              <div className="mt-1 font-ui text-[10px] font-medium uppercase tracking-[0.28em] text-text-muted">
                Islamic Knowledge Engine
              </div>
            </div>

            <div className="hidden h-7 w-px bg-white/10 sm:block" />

            <div className="hidden font-arabic text-base text-text-muted/90 sm:block">
              بُرْهَان
            </div>
          </div>

          <div className="flex items-center gap-6">
            <button
              type="button"
              onClick={() => router.push("/arguments")}
              className="interactive font-ui text-[11px] uppercase tracking-[0.18em] text-text-secondary hover:text-gold-soft"
            >
              Library
            </button>

            <button
              type="button"
              onClick={() => setNotesOpen(true)}
              className="interactive rounded-sm border border-gold/50 px-3.5 py-2 font-ui text-[11px] uppercase tracking-[0.18em] text-gold-soft hover:border-gold hover:bg-gold hover:text-ink-deep"
            >
              Notes
            </button>
          </div>
        </header>

        {/* Hero / Search */}
        <section className="relative mx-auto max-w-5xl pt-24 sm:pt-32 lg:pt-40">
          <div className="pointer-events-none absolute left-1/2 top-0 h-72 w-[34rem] -translate-x-1/2 rounded-full bg-gold/[0.04] blur-[110px]" />

          <div className="relative text-center">
            <div className="font-arabic text-[4.75rem] leading-none text-gold drop-shadow-[0_0_60px_rgba(184,149,82,0.45)] sm:text-[5.75rem]">
              بُرْهَان
            </div>

            <div className="mx-auto mt-7 flex max-w-[18rem] items-center justify-center gap-3">
              <div className="h-px flex-1 bg-gradient-to-r from-transparent to-gold" />

              <div className="relative flex h-2.5 w-2.5 items-center justify-center">
                <div className="absolute h-2 w-2 rotate-45 border border-gold shadow-[0_0_12px_rgba(184,149,82,0.6)]" />
                <div className="h-1 w-1 rounded-full bg-gold" />
              </div>

              <div className="h-px flex-1 bg-gradient-to-l from-transparent to-gold" />
            </div>

            <div className="mt-6 font-ui text-[11px] font-semibold uppercase tracking-[0.42em] text-copper">
              Search for truth
            </div>

            <p className="mt-4 font-display text-2xl italic text-text-secondary sm:text-[1.75rem]">
              through evidence, logic &amp; reason
            </p>

            <p className="mx-auto mt-7 max-w-xl font-ui text-[11px] leading-[1.9] tracking-[0.06em] text-text-muted">
              Search the claim. Examine the evidence. Trace the source.
            </p>
          </div>

          <div className="relative mt-16 sm:mt-20">
            <div className="mb-4 flex items-end justify-between px-1">
              <div>
                <div className="font-ui text-[11px] font-medium uppercase tracking-[0.22em] text-text-muted">
                  Search the sources
                </div>

                <div className="mt-2 font-display text-xl text-parchment-light">
                  What are you investigating?
                </div>
              </div>

              <kbd className="hidden rounded-sm border border-white/12 bg-white/[0.02] px-2.5 py-1.5 font-ui text-[10px] text-text-muted sm:block">
                /
              </kbd>
            </div>

            {/* Search instrument */}
            <div className="group relative">
              <div className="absolute -inset-px rounded-sm bg-gradient-to-r from-transparent via-gold/70 to-transparent opacity-50 blur-sm transition-opacity duration-500 group-focus-within:opacity-100" />

              <div className="relative rounded-sm border border-gold/25 bg-surface-dark px-5 py-5 shadow-[0_25px_70px_-10px_rgba(0,0,0,0.75),0_0_50px_-15px_rgba(184,149,82,0.25)] transition-all duration-300 group-focus-within:border-gold/60 group-focus-within:shadow-[0_25px_70px_-10px_rgba(0,0,0,0.75),0_0_70px_-10px_rgba(184,149,82,0.4)] sm:px-7 sm:py-6">
                <div className="flex items-center gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center text-gold-soft/85">
                    <span className="font-display text-2xl leading-none">
                      ⌕
                    </span>
                  </div>

                  <input
                    type="text"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        handleSearch();
                      }
                    }}
                    placeholder={
                      selectedDomain === "All"
                        ? "Ask a question worth investigating..."
                        : `Search ${selectedDomain.toLowerCase()}...`
                    }
                    className="min-w-0 flex-1 bg-transparent font-display text-xl text-parchment-light outline-none placeholder:text-text-muted/70 sm:text-2xl"
                    aria-label="Research question"
                  />

                  <button
                    type="button"
                    onClick={() => handleSearch()}
                    disabled={searching || !query.trim()}
                    aria-label="Begin research"
                    className="interactive hidden h-10 shrink-0 items-center justify-center rounded-sm bg-gold px-4 font-ui text-[10px] font-bold uppercase tracking-[0.16em] text-ink-deep shadow-[0_0_25px_-5px_rgba(184,149,82,0.6)] hover:bg-gold-soft disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-text-muted disabled:shadow-none sm:flex"
                  >
                    {searching ? "Searching" : "Enter ↵"}
                  </button>
                </div>
              </div>
            </div>

            {/* Research domains */}
            <div className="mt-8 grid grid-cols-2 overflow-hidden rounded-sm border-y border-white/[0.07] sm:grid-cols-5">
              {researchDomains.map((domain, index) => {
                const isSelected = selectedDomain === domain.label;

                return (
                  <button
                    key={domain.label}
                    type="button"
                    onClick={() => {
                      setSelectedDomain(
                        domain.label === "All" || isSelected
                          ? "All"
                          : domain.label,
                      );
                    }}
                    aria-pressed={isSelected}
                    className={`group relative flex min-h-[4.75rem] flex-col items-center justify-center px-3 py-4 text-center transition-all duration-300 ${
                      index > 0 ? "border-l border-white/[0.07]" : ""
                    } ${
                      isSelected
                        ? "bg-gold/[0.07]"
                        : "hover:bg-gold/[0.04]"
                    }`}
                  >
                    <span
                      className={`font-ui text-[10px] font-medium uppercase tracking-[0.18em] transition-colors ${
                        isSelected
                          ? "text-gold-soft"
                          : "text-text-secondary group-hover:text-parchment-light"
                      }`}
                    >
                      {domain.label}
                    </span>

                    <span
                      className={`mt-1.5 font-arabic text-base transition-colors ${
                        isSelected
                          ? "text-gold-soft/90"
                          : "text-text-muted/60 group-hover:text-gold-soft/80"
                      }`}
                    >
                      {domain.arabic}
                    </span>

                    <span
                      className={`absolute bottom-0 left-1/2 h-px -translate-x-1/2 bg-gold transition-all duration-300 ${
                        isSelected
                          ? "w-10 opacity-100"
                          : "w-0 opacity-0 group-hover:w-8 group-hover:opacity-70"
                      }`}
                    />
                  </button>
                );
              })}
            </div>

            {/* Active research context */}
            <div
              className={`mt-4 flex min-h-5 items-center justify-center transition-opacity duration-300 ${
                selectedDomain
                  ? "opacity-100"
                  : "pointer-events-none opacity-0"
              }`}
            >
              {selectedDomain && (
                <div className="flex items-center gap-2.5">
                  <span className="h-1 w-1 rounded-full bg-gold/70" />

                  <span className="font-ui text-[9px] uppercase tracking-[0.2em] text-text-muted">
                    Searching within
                  </span>

                  <span className="font-ui text-[9px] font-semibold uppercase tracking-[0.2em] text-gold-soft">
                    {selectedDomain}
                  </span>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Search state */}
        {searching && (
          <section className="mx-auto mt-20 max-w-5xl pb-12">
            <div className="border-t border-white/[0.08] pt-10">
              <div className="flex items-center gap-4">
                <div className="h-px flex-1 bg-gradient-to-r from-gold/45 to-transparent" />

                <div className="font-ui text-[10px] uppercase tracking-[0.24em] text-gold-soft">
                  Examining sources
                </div>

                <div className="h-px flex-1 bg-gradient-to-l from-gold/45 to-transparent" />
              </div>

              <div className="mt-8 space-y-4">
                {[1, 2, 3].map((item) => (
                  <div
                    key={item}
                    className="h-24 animate-pulse rounded-sm border-y border-white/[0.06] bg-white/[0.02]"
                  />
                ))}
              </div>
            </div>
          </section>
        )}

        {/* Search error */}
        {!searching && searchError && (
          <section className="mx-auto mt-20 max-w-5xl pb-12">
            <div className="rounded-sm border border-copper/25 bg-copper/[0.06] px-6 py-9 text-center shadow-[0_20px_50px_-25px_rgba(0,0,0,0.6)]">
              <div className="font-ui text-[10px] uppercase tracking-[0.24em] text-copper">
                Research interrupted
              </div>

              <p className="mx-auto mt-3 max-w-md font-display text-lg leading-relaxed text-text-secondary">
                {searchError}
              </p>

              <button
                type="button"
                onClick={() => handleSearch()}
                className="interactive mt-6 rounded-sm border border-copper/35 px-5 py-2.5 font-ui text-[10px] font-medium uppercase tracking-[0.16em] text-copper hover:bg-copper/[0.08]"
              >
                Try again
              </button>
            </div>
          </section>
        )}

        {/* No results */}
        {!searching &&
          !searchError &&
          hasSearched &&
          results.length === 0 && (
            <section className="mx-auto mt-20 max-w-5xl pb-12">
              <div className="border-t border-white/[0.08] pt-12 text-center">
                <div className="font-arabic text-4xl text-gold-soft/55">
                  لا توجد نتائج
                </div>

                <div className="mt-5 font-ui text-[10px] uppercase tracking-[0.26em] text-copper">
                  No evidence found
                </div>

                <p className="mx-auto mt-3 max-w-lg font-display text-lg leading-relaxed text-text-secondary">
                  Burhān could not find evidence matching this investigation.
                  Try a broader question or different wording.
                </p>
              </div>
            </section>
          )}

        {/* =====================================================
            RESEARCH RESULTS — EVIDENCE DESK
           ===================================================== */}
        {!searching && !searchError && results.length > 0 && (
          <section className="mx-auto mt-20 max-w-5xl pb-12">
            <div className="border-t border-white/[0.08] pt-10">
              {/* Results heading */}
              <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <span className="h-px w-8 bg-gold/55" />

                    <span className="font-ui text-[10px] uppercase tracking-[0.26em] text-copper">
                      Research findings
                    </span>
                  </div>

                  <h2 className="mt-3 font-display text-3xl text-parchment-light sm:text-4xl">
                    The evidence
                  </h2>

                  <p className="mt-2 max-w-xl font-display text-base leading-relaxed text-text-secondary">
                    Sources relevant to your investigation, arranged by
                    evidentiary role.
                  </p>
                </div>

                <div className="flex items-center gap-2.5">
                  <div className="h-1.5 w-1.5 rounded-full bg-gold/65" />

                  <span className="font-ui text-[10px] uppercase tracking-[0.16em] text-text-muted">
                    {results.length} sources examined
                  </span>
                </div>
              </div>

              {/* Evidence hierarchy */}
              <div className="mt-8 flex flex-wrap items-center gap-x-5 gap-y-2.5 border-y border-white/[0.07] py-4">
                {(
                  [
                    "direct",
                    "consequence",
                    "conceptual",
                    "contextual",
                    "related",
                  ] as EvidenceRole[]
                ).map((role) => (
                  <div
                    key={role}
                    title={evidenceRoleDescription(role)}
                    className="flex items-center gap-2"
                  >
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${evidenceRoleAccent(
                        role,
                      )}`}
                    />

                    <span className="font-ui text-[9px] uppercase tracking-[0.14em] text-text-muted">
                      {evidenceRoleMeta[role].shortLabel}
                    </span>
                  </div>
                ))}
              </div>

              {/* Featured evidence */}
              {featuredResult && (
                <article className="animate-fade-slide-up relative mt-10">
                  {/* Evidence rail */}
                  <div className="absolute bottom-0 left-0 top-0 hidden w-10 flex-col items-center sm:flex">
                    <div
                      className={`h-2.5 w-2.5 rounded-full ring-4 ring-ink-deep ${evidenceRoleAccent(
                        featuredResult.evidence_role,
                      )}`}
                    />

                    <div className="mt-3 w-px flex-1 bg-gradient-to-b from-white/20 via-white/10 to-transparent" />

                    <div className="mt-3 font-ui text-[9px] uppercase tracking-[0.16em] text-text-muted [writing-mode:vertical-rl]">
                      Primary finding
                    </div>
                  </div>

                  <MagicCard
                    gradientSize={240}
                    gradientColor="#b89552"
                    gradientOpacity={0.08}
                    className="relative ml-0 overflow-hidden rounded-sm border border-gold/40 bg-surface-dark-raised shadow-[0_35px_80px_-20px_rgba(0,0,0,0.8),0_0_60px_-20px_rgba(184,149,82,0.2)] sm:ml-10"
                  >
                    {/* Gold edge */}
                    <div className="absolute left-0 top-0 h-full w-[3px] bg-gradient-to-b from-gold via-gold/50 to-transparent" />

                    <div className="p-7 sm:p-10">
                      {/* Metadata */}
                      <div className="flex flex-wrap items-center gap-3">
                        <span
                          className={`rounded-sm border px-2.5 py-1 font-ui text-[9px] font-semibold uppercase tracking-[0.16em] ${evidenceRoleClasses(
                            featuredResult.evidence_role,
                          )}`}
                          title={evidenceRoleDescription(
                            featuredResult.evidence_role,
                          )}
                        >
                          {evidenceRoleLabel(
                            featuredResult.evidence_role,
                          )}
                        </span>

                        <span className="text-white/20">·</span>

                        <span className="font-ui text-[10px] uppercase tracking-[0.22em] text-copper">
                          {resultLabel(featuredResult)}
                        </span>

                        <span className="text-white/20">·</span>

                        <span className="font-ui text-[10px] text-text-muted">
                          {featuredResult.reference}
                        </span>
                      </div>

                      {/* Main evidence */}
                      <div className="mt-7">
                        <div className="grid gap-10 lg:grid-cols-[1fr_12rem]">
                          <div>
                            <h3 className="font-display text-[1.75rem] leading-tight text-parchment-light sm:text-3xl">
                              {featuredResult.title ??
                                featuredResult.book_name ??
                                featuredResult.collection ??
                                featuredResult.reference}
                            </h3>

                            {featuredResult.collection && (
                              <div className="mt-2 font-ui text-[10px] uppercase tracking-[0.14em] text-text-muted">
                                {featuredResult.collection}
                              </div>
                            )}

                            {featuredResult.result_type === "argument" && (
                              <div className="mt-5 space-y-5">
                                {featuredResult.question && (
                                  <div>
                                    <div className="mb-2 font-ui text-[9px] uppercase tracking-[0.2em] text-text-muted">
                                      Research question
                                    </div>
                                    <p className="font-display text-lg leading-relaxed text-parchment">
                                      {featuredResult.question}
                                    </p>
                                  </div>
                                )}

                                {featuredResult.summary && (
                                  <div>
                                    <div className="mb-2 font-ui text-[9px] uppercase tracking-[0.2em] text-text-muted">
                                      Overview
                                    </div>
                                    <p className="font-display text-base leading-[1.8] text-text-secondary">
                                      {featuredResult.summary}
                                    </p>
                                  </div>
                                )}

                                {featuredResult.claim && (
                                  <div className="border-l-2 border-gold/35 pl-4">
                                    <div className="mb-2 font-ui text-[9px] uppercase tracking-[0.2em] text-text-muted">
                                      Central claim
                                    </div>
                                    <p className="font-display text-base leading-relaxed text-parchment">
                                      {featuredResult.claim}
                                    </p>
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Arabic source */}
                            {featuredResult.text_arabic && (
                              <div className="mt-9 rounded-sm border-r-2 border-gold/35 bg-white/[0.015] py-4 pl-5 pr-5">
                                <div className="mb-3 font-ui text-[9px] uppercase tracking-[0.2em] text-text-muted">
                                  Original text
                                </div>

                                <div
                                  dir="rtl"
                                  className="font-arabic text-2xl leading-[2] text-parchment sm:text-3xl"
                                >
                                  {excerpt(
                                    featuredResult.text_arabic,
                                    420,
                                  )}
                                </div>
                              </div>
                            )}

                            {/* Translation */}
                            {featuredResult.translation && (
                              <div className="mt-8">
                                <div className="mb-3 font-ui text-[9px] uppercase tracking-[0.2em] text-text-muted">
                                  Translation
                                </div>

                                <p className="max-w-2xl font-display text-lg leading-[1.8] text-text-secondary">
                                  {excerpt(
                                    featuredResult.translation,
                                    360,
                                  )}
                                </p>

                                {featuredResult.translator && (
                                  <div className="mt-3 font-ui text-[10px] text-text-muted">
                                    {featuredResult.translator}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>

                          {/* Source column */}
                          <aside className="border-t border-white/[0.08] pt-5 lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
                            {featuredResult.result_type === "argument" ? (
                              <>
                                <div className="font-ui text-[9px] uppercase tracking-[0.18em] text-text-muted">
                                  Category
                                </div>

                                <div className="mt-2 font-display text-base leading-snug text-parchment">
                                  {featuredResult.category?.name ?? "Uncategorised"}
                                </div>

                                <div className="mt-7 font-ui text-[9px] uppercase tracking-[0.18em] text-text-muted">
                                  Status
                                </div>

                                <div className="mt-2 font-ui text-[10px] uppercase tracking-[0.14em] text-copper">
                                  {featuredResult.status ?? "Unspecified"}
                                </div>

                                {featuredResult.conclusion && (
                                  <div className="mt-7">
                                    <div className="font-ui text-[9px] uppercase tracking-[0.18em] text-text-muted">
                                      Conclusion
                                    </div>
                                    <p className="mt-2 font-display text-sm leading-relaxed text-text-secondary">
                                      {featuredResult.conclusion}
                                    </p>
                                  </div>
                                )}
                              </>
                            ) : (
                              <>
                                <div className="font-ui text-[9px] uppercase tracking-[0.18em] text-text-muted">
                                  Source
                                </div>

                                <div className="mt-2 font-display text-base leading-snug text-parchment">
                                  {featuredResult.source?.name ?? "Unknown source"}
                                </div>

                                {featuredResult.source?.author && (
                                  <div className="mt-2 font-ui text-[10px] leading-relaxed text-text-muted">
                                    {featuredResult.source.author}
                                  </div>
                                )}

                                {featuredResult.narrator && (
                                  <div className="mt-7">
                                    <div className="font-ui text-[9px] uppercase tracking-[0.18em] text-text-muted">
                                      Narrator
                                    </div>
                                    <div className="mt-2 font-display text-sm leading-relaxed text-text-secondary">
                                      {featuredResult.narrator}
                                    </div>
                                  </div>
                                )}

                                <div className="mt-7">
                                  <div className="font-ui text-[9px] uppercase tracking-[0.18em] text-text-muted">
                                    Evidence role
                                  </div>
                                  <div className="mt-2 font-ui text-[10px] leading-relaxed text-text-secondary">
                                    {evidenceRoleDescription(featuredResult.evidence_role)}
                                  </div>
                                </div>
                              </>
                            )}
                          </aside>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="mt-9 flex flex-wrap items-center gap-3 border-t border-white/[0.08] pt-5">
                        <button
                          type="button"
                          onClick={() => handleExamine(featuredResult)}
                          className="interactive group flex items-center gap-3 rounded-sm bg-gold px-4 py-2.5 font-ui text-[10px] font-bold uppercase tracking-[0.16em] text-ink-deep shadow-[0_0_30px_-8px_rgba(184,149,82,0.7)] hover:bg-gold-soft"
                        >
                          Examine evidence

                          <span className="transition-transform duration-300 group-hover:translate-x-1">
                            →
                          </span>
                        </button>

                        <button
                          type="button"
                          onClick={() => setNotesOpen(true)}
                          className="interactive rounded-sm border border-white/[0.1] px-4 py-2.5 font-ui text-[10px] font-medium uppercase tracking-[0.16em] text-text-secondary hover:border-white/20 hover:text-parchment-light"
                        >
                          Save note
                        </button>
                      </div>
                    </div>
                  </MagicCard>
                </article>
              )}

              {/* Supporting evidence */}
              {relatedResults.length > 0 && (
                <div className="mt-12 border-t border-white/[0.08] pt-10">
                  <div className="flex items-end justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-3">
                        <span className="h-px w-6 bg-gold/40" />

                        <span className="font-ui text-[9px] uppercase tracking-[0.24em] text-copper">
                          Supporting evidence
                        </span>
                      </div>

                      <h3 className="mt-3 font-display text-2xl text-parchment-light">
                        Additional sources
                      </h3>

                      <p className="mt-2 max-w-xl font-display text-sm leading-relaxed text-text-secondary">
                        Further evidence relevant to this investigation,
                        ranked by evidentiary strength.
                      </p>
                    </div>

                    <div className="hidden font-ui text-[9px] uppercase tracking-[0.16em] text-text-muted sm:block">
                      {relatedResults.length} additional
                    </div>
                  </div>

                  <div className="mt-7 divide-y divide-white/[0.07] border-y border-white/[0.07]">
                    {relatedResults.map((result, index) => (
                      <article
                        key={`${result.result_type}-${result.id}`}
                        className="group relative py-7 transition-colors duration-300 hover:bg-white/[0.015]"
                      >
                        <div className="grid gap-5 sm:grid-cols-[auto_1fr_auto] sm:items-start">
                          {/* Result number */}
                          <div className="hidden w-8 pt-1 font-ui text-[9px] tabular-nums tracking-[0.12em] text-text-muted sm:block">
                            {String(index + 2).padStart(2, "0")}
                          </div>

                          <div className="min-w-0">
                            {/* Metadata */}
                            <div className="flex flex-wrap items-center gap-2.5">
                              <span
                                className={`rounded-sm border px-2 py-1 font-ui text-[8px] font-semibold uppercase tracking-[0.14em] ${evidenceRoleClasses(
                                  result.evidence_role,
                                )}`}
                                title={evidenceRoleDescription(
                                  result.evidence_role,
                                )}
                              >
                                {evidenceRoleLabel(
                                  result.evidence_role,
                                )}
                              </span>

                              <span className="text-white/15">·</span>

                              <span className="font-ui text-[9px] uppercase tracking-[0.16em] text-copper">
                                {resultLabel(result)}
                              </span>

                              <span className="text-white/15">·</span>

                              <span className="font-ui text-[9px] text-text-muted">
                                {result.reference}
                              </span>
                            </div>

                            {/* Title */}
                            <div className="mt-4">
                              <h4 className="font-display text-xl leading-snug text-parchment-light">
                                {result.title ??
                                  result.book_name ??
                                  result.collection ??
                                  result.reference}
                              </h4>

                              {result.collection && (
                                <div className="mt-1 font-ui text-[9px] uppercase tracking-[0.14em] text-text-muted">
                                  {result.collection}
                                  {result.book_name
                                    ? ` · ${result.book_name}`
                                    : ""}
                                </div>
                              )}
                            </div>

                            {result.result_type === "argument" && (
                              <div className="mt-3 space-y-2">
                                {result.question && (
                                  <p className="font-display text-base leading-relaxed text-parchment">
                                    {result.question}
                                  </p>
                                )}

                                {result.summary && (
                                  <p className="max-w-3xl font-display text-sm leading-[1.8] text-text-secondary">
                                    {excerpt(result.summary, 280)}
                                  </p>
                                )}

                                {result.category && (
                                  <span className="inline-block font-ui text-[9px] uppercase tracking-[0.14em] text-text-muted">
                                    {result.category.name}
                                    {result.status ? ` · ${result.status}` : ""}
                                  </span>
                                )}
                              </div>
                            )}

                            {/* Arabic */}
                            {result.text_arabic && (
                              <div
                                dir="rtl"
                                className="mt-5 font-arabic text-xl leading-[2] text-parchment/90"
                              >
                                {excerpt(result.text_arabic, 300)}
                              </div>
                            )}

                            {/* Translation */}
                            {result.translation && (
                              <p className="mt-4 max-w-3xl font-display text-sm leading-[1.8] text-text-secondary">
                                {excerpt(result.translation, 280)}
                              </p>
                            )}

                            {/* Source metadata */}
                            <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2">
                              {result.narrator && (
                                <span className="font-ui text-[9px] text-text-muted">
                                  Narrator: {result.narrator}
                                </span>
                              )}

                              {result.source?.name && (
                                <span className="font-ui text-[9px] text-text-muted">
                                  Source: {result.source.name}
                                </span>
                              )}
                            </div>
                          </div>

                          {/* Examine */}
                          <button
                            type="button"
                            onClick={() => handleExamine(result)}
                            className="interactive self-start rounded-sm border border-white/[0.1] px-3.5 py-2 font-ui text-[9px] font-medium uppercase tracking-[0.14em] text-text-secondary opacity-100 transition-all hover:border-gold/40 hover:bg-gold/[0.06] hover:text-gold-soft sm:opacity-0 sm:group-hover:opacity-100"
                          >
                            Examine →
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </section>
        )}

        {/* =====================================================
            RECENT RESEARCH
           ===================================================== */}
        <section className="mx-auto max-w-5xl pb-28 pt-20">
          <div className="border-t border-white/[0.08] pt-10">
            <div className="flex items-end justify-between gap-6">
              <div>
                <div className="flex items-center gap-3">
                  <span className="h-px w-8 bg-gold/45" />

                  <span className="font-ui text-[10px] uppercase tracking-[0.26em] text-copper">
                    Recent investigations
                  </span>
                </div>

                <h2 className="mt-3 font-display text-3xl text-parchment-light sm:text-4xl">
                  Continue your research
                </h2>

                <p className="mt-2 max-w-xl font-display text-base leading-relaxed text-text-secondary">
                  Return to questions that deserve further examination.
                </p>
              </div>

              <div className="hidden font-arabic text-2xl text-gold/40 sm:block">
                العلم
              </div>
            </div>

            <div className="mt-8 divide-y divide-white/[0.07] border-y border-white/[0.07]">
              {recentResearch.map((item, index) => (
                <button
                  key={item.question}
                  type="button"
                  onClick={() => {
                    setQuery(item.question);
                    setSelectedDomain("All");
                    window.scrollTo({
                      top: 0,
                      behavior: "smooth",
                    });
                  }}
                  className="group flex w-full items-center gap-5 py-6 text-left transition-colors duration-300 hover:bg-white/[0.015]"
                >
                  <div className="hidden w-8 shrink-0 font-ui text-[9px] tabular-nums tracking-[0.14em] text-text-muted sm:block">
                    {String(index + 1).padStart(2, "0")}
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="font-display text-lg leading-relaxed text-parchment-light transition-colors group-hover:text-gold-soft sm:text-xl">
                      {item.question}
                    </div>

                    <div className="mt-2 font-ui text-[9px] uppercase tracking-[0.14em] text-text-muted">
                      {item.sources}
                    </div>
                  </div>

                  <div className="shrink-0 font-ui text-[9px] uppercase tracking-[0.14em] text-text-muted transition-all group-hover:translate-x-1 group-hover:text-gold-soft">
                    Investigate →
                  </div>
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-white/[0.08] py-10">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="font-arabic text-xl text-gold/70">
                بُرْهَان
              </div>

              <div className="mt-2 font-ui text-[9px] uppercase tracking-[0.2em] text-text-muted">
                Knowledge with provenance
              </div>
            </div>

            <div className="font-ui text-[9px] uppercase tracking-[0.16em] text-text-muted">
              Search · Examine · Understand
            </div>
          </div>
        </footer>
      </div>

      <NotesPanel
        open={notesOpen}
        onClose={() => setNotesOpen(false)}
      />
    </main>
  );
}