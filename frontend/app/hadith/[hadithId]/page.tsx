"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type HadithTranslation = {
  id: number;
  language: string;
  translator: string;
  text: string;
};

type HadithSource = {
  id: number;
  name: string;
  slug: string;
  source_type: string;
  language: string;
  author: string | null;
  publisher: string | null;
  url: string | null;
  license: string | null;
  version: string | null;
  description: string | null;
};

type HadithBook = {
  id: number;
  number: number;
  name: string;
  description: string | null;
};

type HadithResponse = {
  id: number;
  number: string;
  reference: string;
  in_book_reference: string | null;

  text_arabic: string;
  isnad_arabic: string | null;
  matn_arabic: string | null;
  closing_arabic: string | null;

  narrator: string | null;
  has_variants: boolean;
  source_reference: string | null;
  source_url: string | null;

  collection_name: string | null;
  book: HadithBook | null;

  chapter: {
    id: number;
    number: number | null;
    name: string;
    description: string | null;
  } | null;

  translations: HadithTranslation[];
  gradings: unknown[];

  source: HadithSource | null;
};

type BurhanArgument = {
  id: number;
  title: string;
  question: string;
  status: string;
};

type BurhanConnection = {
  evidence_id: number;
  argument: BurhanArgument | null;
  connection: {
    type: "premise" | "response" | null;
    id: number | null;
    text: string | null;
  };
  role: string;
  reference: string | null;
  note: string | null;
};

type BurhanEvidenceResponse = {
  result_type: string;
  result_id: number;
  total: number;
  arguments: BurhanConnection[];
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export default function HadithReader({
  params,
}: {
  params: Promise<{ hadithId: string }>;
}) {
  const [data, setData] = useState<HadithResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [previousId, setPreviousId] = useState<number | null>(null);
  const [nextId, setNextId] = useState<number | null>(null);

  const [isnadOpen, setIsnadOpen] = useState(false);
  const [connections, setConnections] = useState<BurhanConnection[]>([]);
  const [connectionsLoading, setConnectionsLoading] = useState(true);

  useEffect(() => {
    async function loadHadith() {
      try {
        const { hadithId } = await params;

        const response = await fetch(
          `${API_URL}/hadiths/${hadithId}`,
        );

        if (!response.ok) {
          throw new Error("Unable to load this hadith.");
        }

        const result: HadithResponse = await response.json();

        setData(result);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load this hadith.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadHadith();
  }, [params]);

  /*
   * Hadith IDs are the canonical database IDs.
   *
   * We do not assume that ID - 1 or ID + 1 necessarily exists,
   * because the database can contain gaps between collections.
   *
   * Starting from the current ID, find the nearest actual hadith.
   */
  useEffect(() => {
    async function loadNavigation() {
      if (!data) {
        return;
      }

      const currentId = data.id;

      async function hadithExists(id: number) {
        if (id <= 0) {
          return false;
        }

        try {
          const response = await fetch(
            `${API_URL}/hadiths/${id}`,
          );

          return response.ok;
        } catch {
          return false;
        }
      }

      let foundPrevious: number | null = null;

      for (
        let candidate = currentId - 1;
        candidate >= Math.max(1, currentId - 20);
        candidate--
      ) {
        if (await hadithExists(candidate)) {
          foundPrevious = candidate;
          break;
        }
      }

      let foundNext: number | null = null;

      for (
        let candidate = currentId + 1;
        candidate <= currentId + 20;
        candidate++
      ) {
        if (await hadithExists(candidate)) {
          foundNext = candidate;
          break;
        }
      }

      setPreviousId(foundPrevious);
      setNextId(foundNext);
    }

    loadNavigation();
  }, [data]);

  useEffect(() => {
    let cancelled = false;

    async function loadConnections() {
      setConnectionsLoading(true);

      try {
        const response = await fetch(
          `${API_URL}/evidence/hadith/${data!.id}`,
        );

        if (!response.ok) {
          throw new Error("Unable to load evidence connections.");
        }

        const result: BurhanEvidenceResponse = await response.json();

        if (!cancelled) {
          setConnections(result.arguments ?? []);
        }
      } catch {
        if (!cancelled) {
          setConnections([]);
        }
      } finally {
        if (!cancelled) {
          setConnectionsLoading(false);
        }
      }
    }

    if (data) {
      loadConnections();
    }

    return () => {
      cancelled = true;
    };
  }, [data]);

  if (loading) {
    return (
      <main className="min-h-screen bg-[#171512] text-[#f2ead8] flex items-center justify-center">
        <div className="text-center">
          <div className="mb-4 font-arabic text-3xl opacity-70">
            بُرْهَان
          </div>

          <p className="font-display text-xl tracking-wide opacity-60">
            Opening the manuscript…
          </p>
        </div>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="min-h-screen bg-[#171512] text-[#f2ead8] flex items-center justify-center px-6">
        <div className="max-w-md text-center">
          <div className="mb-5 font-arabic text-4xl text-[#cdb77d]">
            بُرْهَان
          </div>

          <h1 className="font-display text-3xl mb-3">
            Evidence unavailable
          </h1>

          <p className="text-[#b9ae9b] mb-8">
            {error ?? "This hadith could not be found."}
          </p>

          <Link
            href="/"
            className="inline-flex border border-[rgba(205,183,125,0.25)] px-5 py-3 text-sm text-[#cdb77d] transition hover:border-[#cdb77d]"
          >
            Return to research
          </Link>
        </div>
      </main>
    );
  }

  const translation = data.translations.find(
    (item) => item.language.toLowerCase() === "en",
  ) ?? data.translations[0];

  return (
    <main className="min-h-screen bg-[#171512] text-[#f2ead8]">
      {/* Ambient light */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-[-20%] h-[700px] w-[700px] -translate-x-1/2 rounded-full bg-[#304d68]/10 blur-[140px]" />

        <div className="absolute right-[-10%] bottom-[-10%] h-[500px] w-[500px] rounded-full bg-[#9a6847]/8 blur-[130px]" />
      </div>

      <div className="relative mx-auto min-h-screen max-w-6xl px-6 py-8 md:px-10">
        {/* Header */}
        <header className="flex items-center justify-between border-b border-[rgba(205,183,125,0.14)] pb-6">
          <Link href="/" className="group">
            <div className="font-display text-2xl tracking-[0.18em] text-[#f2ead8]">
              BURHĀN
            </div>

            <div className="mt-1 text-[10px] uppercase tracking-[0.28em] text-[#81796d]">
              Islamic Knowledge Engine
            </div>
          </Link>

          <Link
            href="/"
            className="group text-right"
          >
            <div className="font-arabic text-lg text-[#cdb77d] transition group-hover:text-[#f2ead8]">
              الحديث
            </div>

            <div className="mt-1 text-[10px] uppercase tracking-[0.2em] text-[#81796d] transition group-hover:text-[#b9ae9b]">
              Hadith · Research
            </div>
          </Link>
        </header>

        {/* Manuscript heading */}
        <section className="pt-16 text-center">
          <div className="mb-3 text-xs uppercase tracking-[0.32em] text-[#9a6847]">
            {data.collection_name ?? "Hadith"}
          </div>

          <h1 className="font-display text-5xl font-medium tracking-wide md:text-6xl">
            {data.book?.name ?? data.collection_name ?? "Hadith"}
          </h1>

          {data.book && (
            <div className="mt-3 text-lg text-[#cdb77d]">
              Book {data.book.number}
            </div>
          )}

          <div className="mt-2 text-sm tracking-[0.16em] text-[#81796d]">
            {data.reference}
          </div>

          <div className="mx-auto mt-8 flex items-center justify-center gap-4">
            <div className="h-px w-16 bg-[#b89552]/30" />

            <div className="font-display text-sm text-[#b89552]">
              {data.in_book_reference ?? `Hadith ${data.number}`}
            </div>

            <div className="h-px w-16 bg-[#b89552]/30" />
          </div>
        </section>

        {/* Hadith */}
        <section className="mx-auto mt-16 max-w-4xl">
          <div className="relative border-y border-[rgba(205,183,125,0.14)] py-14 md:py-20">
            <div className="pointer-events-none absolute left-1/2 top-1/2 h-40 w-40 -translate-x-1/2 -translate-y-1/2 rounded-full border border-[#b89552]/5" />

            <div className="relative">
              <div className="mb-8 text-center text-xs uppercase tracking-[0.3em] text-[#81796d]">
                Original text
              </div>

              <p
                dir="rtl"
                lang="ar"
                className="text-right font-arabic text-3xl leading-[2.3] text-[#f7f1e4] md:text-4xl md:leading-[2.25]"
              >
                {data.text_arabic}
              </p>

              <div className="mx-auto mt-12 h-px w-20 bg-[#b89552]/30" />

              {/* Translation */}
              <div className="mt-10 text-center text-xs uppercase tracking-[0.3em] text-[#81796d]">
                Translation
              </div>

              {translation ? (
                <div className="mt-7">
                  <p className="mx-auto max-w-3xl text-center font-display text-2xl leading-relaxed text-[#e5d8bc] md:text-3xl">
                    “{translation.text}”
                  </p>

                  <div className="mt-5 text-center">
                    <div className="text-sm text-[#b9ae9b]">
                      {translation.translator}
                    </div>

                    <div className="mt-1 text-[10px] uppercase tracking-[0.22em] text-[#81796d]">
                      English translation
                    </div>
                  </div>
                </div>
              ) : (
                <p className="mt-7 text-center text-sm text-[#81796d]">
                  No English translation is available for this hadith.
                </p>
              )}
            </div>
          </div>
        </section>

        {/* Narrator */}
        {data.narrator && (
          <section className="mx-auto mt-14 max-w-4xl">
            <div className="border border-[rgba(205,183,125,0.12)] bg-[#1e1b18] p-7">
              <div className="text-[10px] uppercase tracking-[0.25em] text-[#9a6847]">
                Narrator
              </div>

              <div className="mt-4 font-display text-xl text-[#e5d8bc]">
                {data.narrator}
              </div>
            </div>
          </section>
        )}

        {/* Isnād */}
        {data.isnad_arabic && (
          <section className="mx-auto mt-6 max-w-4xl">
            <div className="border border-[rgba(205,183,125,0.12)] bg-[#1e1b18]">
              <button
                type="button"
                onClick={() => setIsnadOpen((value) => !value)}
                className="flex w-full items-center justify-between p-7 text-left"
              >
                <div>
                  <div className="text-[10px] uppercase tracking-[0.25em] text-[#9a6847]">
                    Transmission
                  </div>

                  <div className="mt-2 font-display text-xl text-[#e5d8bc]">
                    Isnād
                  </div>
                </div>

                <div className="text-xl text-[#81796d]">
                  {isnadOpen ? "−" : "+"}
                </div>
              </button>

              {isnadOpen && (
                <div className="border-t border-[rgba(205,183,125,0.1)] px-7 pb-7 pt-6">
                  <p
                    dir="rtl"
                    lang="ar"
                    className="text-right font-arabic text-xl leading-[2.2] text-[#b9ae9b]"
                  >
                    {data.isnad_arabic}
                  </p>
                </div>
              )}
            </div>
          </section>
        )}

        {/* Provenance */}
        <section className="mx-auto mt-14 max-w-4xl">
          <div className="grid gap-px border border-[rgba(205,183,125,0.12)] bg-[rgba(205,183,125,0.08)] md:grid-cols-2">
            <div className="bg-[#1e1b18] p-7">
              <div className="text-[10px] uppercase tracking-[0.25em] text-[#9a6847]">
                Primary source
              </div>

              <div className="mt-4 font-display text-xl">
                {data.collection_name ?? "Hadith collection"}
              </div>

              <p className="mt-2 text-sm leading-relaxed text-[#81796d]">
                {data.source?.author
                  ? `Collected by ${data.source.author}.`
                  : "Primary hadith source record preserved in Burhān."}
              </p>
            </div>

            <div className="bg-[#1e1b18] p-7">
              <div className="text-[10px] uppercase tracking-[0.25em] text-[#9a6847]">
                Translation
              </div>

              {translation ? (
                <>
                  <div className="mt-4 font-display text-xl">
                    {translation.translator}
                  </div>

                  <p className="mt-2 text-sm leading-relaxed text-[#81796d]">
                    English translation associated with this hadith record.
                  </p>
                </>
              ) : (
                <p className="mt-4 text-sm leading-relaxed text-[#81796d]">
                  No translation is currently available.
                </p>
              )}
            </div>
          </div>

          {/* Book / source details */}
          <div className="mt-px grid gap-px border-x border-b border-[rgba(205,183,125,0.12)] bg-[rgba(205,183,125,0.08)] md:grid-cols-2">
            <div className="bg-[#1e1b18] p-7">
              <div className="text-[10px] uppercase tracking-[0.25em] text-[#9a6847]">
                Book
              </div>

              <div className="mt-4 font-display text-xl">
                {data.book
                  ? `${data.book.number}. ${data.book.name}`
                  : "Unknown"}
              </div>
            </div>

            <div className="bg-[#1e1b18] p-7">
              <div className="text-[10px] uppercase tracking-[0.25em] text-[#9a6847]">
                Reference
              </div>

              <div className="mt-4 font-display text-xl">
                {data.reference}
              </div>
            </div>
          </div>
        </section>

        {/* Burhān Connections */}
        <section className="mx-auto mt-14 max-w-4xl">
          <div className="mb-6 flex items-end justify-between gap-4">
            <div>
              <div className="text-[10px] uppercase tracking-[0.25em] text-[#9a6847]">
                Evidence network
              </div>

              <h2 className="mt-2 font-display text-3xl text-[#f2ead8]">
                Burhān Connections
              </h2>

              <p className="mt-2 text-sm text-[#81796d]">
                Arguments linked to this narration and the role it plays in their reasoning.
              </p>
            </div>

            {!connectionsLoading && (
              <div className="shrink-0 text-xs text-[#81796d]">
                {connections.length} connection{connections.length === 1 ? "" : "s"}
              </div>
            )}
          </div>

          {connectionsLoading ? (
            <div className="border border-[rgba(205,183,125,0.12)] bg-[#1e1b18] p-6 text-sm text-[#81796d]">
              Tracing evidence connections…
            </div>
          ) : connections.length === 0 ? (
            <div className="border border-[rgba(205,183,125,0.12)] bg-[#1e1b18] p-6">
              <p className="font-display text-lg text-[#e5d8bc]">
                No linked arguments yet
              </p>

              <p className="mt-2 text-sm leading-relaxed text-[#81796d]">
                This hadith has no recorded argument connections in Burhān.
                That does not mean it lacks relevance; the evidence network
                has simply not linked it to an argument yet.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {connections.map((item) => (
                <article
                  key={item.evidence_id}
                  className="border border-[rgba(205,183,125,0.12)] bg-[#1e1b18] p-6"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="border border-[rgba(205,183,125,0.2)] px-2 py-1 text-[10px] uppercase tracking-[0.16em] text-[#cdb77d]">
                      {item.role}
                    </span>

                    {item.connection.type && (
                      <span className="text-[10px] uppercase tracking-[0.16em] text-[#81796d]">
                        Linked {item.connection.type}
                      </span>
                    )}
                  </div>

                  {item.connection.text && (
                    <blockquote className="mt-4 border-l-2 border-[#9a6847]/60 pl-4 font-display text-lg leading-relaxed text-[#e5d8bc]">
                      {item.connection.text}
                    </blockquote>
                  )}

                  {item.note && (
                    <div className="mt-4">
                      <div className="text-[10px] uppercase tracking-[0.2em] text-[#9a6847]">
                        Why this evidence
                      </div>

                      <p className="mt-2 text-sm leading-relaxed text-[#b9ae9b]">
                        {item.note}
                      </p>
                    </div>
                  )}

                  {item.reference && (
                    <p className="mt-3 text-xs text-[#81796d]">
                      Reference: {item.reference}
                    </p>
                  )}

                  {item.argument && (
                    <div className="mt-5 border-t border-[rgba(205,183,125,0.1)] pt-4">
                      <h3 className="font-display text-xl text-[#f2ead8]">
                        {item.argument.title}
                      </h3>

                      <p className="mt-2 text-sm leading-relaxed text-[#b9ae9b]">
                        {item.argument.question}
                      </p>

                      <Link
                        href={`/arguments/${item.argument.id}${
                          item.connection.id != null && item.connection.type
                            ? `#${item.connection.type}-${item.connection.id}`
                            : ""
                        }`}
                        className="mt-4 inline-flex text-xs uppercase tracking-[0.16em] text-[#cdb77d] transition hover:text-[#f2ead8]"
                      >
                        Open {item.connection.type ?? "argument"} →
                      </Link>
                    </div>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>

        {/* Actions */}
        <section className="mx-auto mt-10 max-w-4xl pb-20">
          <div className="flex items-center justify-between border-y border-[rgba(205,183,125,0.12)] py-5">
            {previousId ? (
              <Link
                href={`/hadith/${previousId}`}
                className="group text-left"
              >
                <div className="text-[10px] uppercase tracking-[0.22em] text-[#81796d]">
                  Previous
                </div>

                <div className="mt-2 font-display text-lg text-[#b9ae9b] transition group-hover:text-[#f2ead8]">
                  ← Previous hadith
                </div>
              </Link>
            ) : (
              <div>
                <div className="text-[10px] uppercase tracking-[0.22em] text-[#5f5951]">
                  Previous
                </div>

                <div className="mt-2 font-display text-lg text-[#5f5951]">
                  Beginning
                </div>
              </div>
            )}

            <div className="text-center">
              <div className="font-arabic text-lg text-[#cdb77d]">
                {data.number}
              </div>

              <div className="mt-1 text-[9px] uppercase tracking-[0.2em] text-[#81796d]">
                Hadith
              </div>
            </div>

            {nextId ? (
              <Link
                href={`/hadith/${nextId}`}
                className="group text-right"
              >
                <div className="text-[10px] uppercase tracking-[0.22em] text-[#81796d]">
                  Next
                </div>

                <div className="mt-2 font-display text-lg text-[#b9ae9b] transition group-hover:text-[#f2ead8]">
                  Next hadith →
                </div>
              </Link>
            ) : (
              <div>
                <div className="text-right text-[10px] uppercase tracking-[0.22em] text-[#5f5951]">
                  Next
                </div>

                <div className="mt-2 font-display text-lg text-[#5f5951]">
                  End
                </div>
              </div>
            )}
          </div>

          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <button className="border border-[rgba(205,183,125,0.2)] px-5 py-3 text-xs uppercase tracking-[0.16em] text-[#b9ae9b] transition hover:border-[#b89552] hover:text-[#f2ead8]">
              Add to notes
            </button>

            <button className="border border-[rgba(205,183,125,0.2)] px-5 py-3 text-xs uppercase tracking-[0.16em] text-[#b9ae9b] transition hover:border-[#b89552] hover:text-[#f2ead8]">
              Related evidence
            </button>

            <button className="border border-[rgba(205,183,125,0.2)] px-5 py-3 text-xs uppercase tracking-[0.16em] text-[#b9ae9b] transition hover:border-[#b89552] hover:text-[#f2ead8]">
              Arguments
            </button>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-[rgba(205,183,125,0.1)] pt-6 text-center">
          <div className="font-arabic text-lg text-[#81796d]">
            بُرْهَان
          </div>

          <div className="mt-2 text-[10px] uppercase tracking-[0.25em] text-[#5f5951]">
            Knowledge with provenance
          </div>
        </footer>
      </div>
    </main>
  );
}