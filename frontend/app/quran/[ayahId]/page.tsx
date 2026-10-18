"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import NotesPanel from "@/components/NotesPanel";

type TranslationSource = {
  id: number; name: string; slug: string; source_type: string; language: string;
  author: string | null; publisher: string | null; url: string | null;
  license: string | null; version: string | null; description: string | null;
};

type Translation = {
  id: number; language: string; translator: string; text: string;
  source: TranslationSource;
};

type AyahResponse = {
  surah: {
    id: number; number: number; name_arabic: string;
    name_transliteration: string; name_english: string;
  };
  ayah: { id: number; number: number; text_arabic: string };
  translations: Translation[];
  previous: { id: number; number: number; reference: string } | null;
  next: { id: number; number: number; reference: string } | null;
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
type Surah = {
  id: number; number: number; name_arabic: string;
  name_transliteration: string; name_english: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export default function QuranReader({
  params,
}: { params: Promise<{ ayahId: string }> }) {
  const router = useRouter();
  const [data, setData] = useState<AyahResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [surahs, setSurahs] = useState<Surah[]>([]);
  const [surahMenuOpen, setSurahMenuOpen] = useState(false);
  const [surahsLoading, setSurahsLoading] = useState(false);
  const [notesOpen, setNotesOpen] = useState(false);
  const [noteToInsert, setNoteToInsert] = useState<string | null>(null);
  const [connectionsOpen, setConnectionsOpen] = useState(false);
  const [connections, setConnections] = useState<BurhanConnection[]>([]);
  const [connectionsLoading, setConnectionsLoading] = useState(false);
  const [connectionsError, setConnectionsError] = useState<string | null>(null);

  useEffect(() => {
    async function loadSurahs() {
      setSurahsLoading(true);
      try {
        const response = await fetch(`${API_URL}/surahs/`);
        if (!response.ok) throw new Error("Unable to load Surahs.");
        const result = await response.json();
        setSurahs(Array.isArray(result) ? result : result.value ?? []);
      } catch {
        setSurahs([]);
      } finally {
        setSurahsLoading(false);
      }
    }
    loadSurahs();
  }, []);

  useEffect(() => {
    async function loadAyah() {
      try {
        const { ayahId } = await params;
        const response = await fetch(`${API_URL}/quran/${ayahId}`);
        if (!response.ok) throw new Error("Unable to load this ayah.");
        setData(await response.json());
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load this ayah.");
      } finally {
        setLoading(false);
      }
    }
    loadAyah();
  }, [params]);

  const openSurah = async (surahNumber: number) => {
    try {
      const response = await fetch(`${API_URL}/surahs/${surahNumber}/ayahs/`);
      if (!response.ok) throw new Error("Unable to open Surah.");
      const result = await response.json();
      const ayahs = Array.isArray(result) ? result : result.value ?? [];
      if (!ayahs.length) throw new Error("This Surah has no ayahs.");
      setSurahMenuOpen(false);
      router.push(`/quran/${ayahs[0].id}`);
    } catch (err) {
      console.error("Failed to open Surah:", err);
    }
  };
const loadBurhanConnections = async () => {
  if (!data) return;

  setConnectionsLoading(true);
  setConnectionsError(null);
  setConnectionsOpen(true);

  try {
    const response = await fetch(
      `${API_URL}/evidence/quran/${data.ayah.id}`,
    );

    if (!response.ok) {
      throw new Error("Unable to load Burhān connections.");
    }

    const result: BurhanEvidenceResponse = await response.json();

    setConnections(result.arguments);
  } catch (err) {
    setConnections([]);
    setConnectionsError(
      err instanceof Error
        ? err.message
        : "Unable to load Burhān connections.",
    );
  } finally {
    setConnectionsLoading(false);
  }
};

  const addToNotes = () => {
    if (!data) return;
    const translation = data.translations[0];
    setNoteToInsert(`
<h2>${data.surah.name_english} ${data.surah.number}:${data.ayah.number}</h2>
<p dir="rtl"><strong>${data.ayah.text_arabic}</strong></p>
<p>“${translation?.text ?? ""}”</p>
<p><strong>Translation:</strong> ${translation?.translator ?? "Unknown"}</p>
<p><strong>Source:</strong> The Qur'an</p>
<hr />
`);
    setNotesOpen(true);
  };

  if (loading) return (
    <main className="flex min-h-screen items-center justify-center bg-[#171512] text-[#f2ead8]">
      <div className="text-center">
        <div className="mb-4 font-arabic text-3xl opacity-70">بُرْهَان</div>
        <p className="font-display text-xl tracking-wide opacity-60">Opening the manuscript…</p>
      </div>
    </main>
  );

  if (error || !data) return (
    <main className="flex min-h-screen items-center justify-center bg-[#171512] px-6 text-[#f2ead8]">
      <div className="max-w-md text-center">
        <div className="mb-5 font-arabic text-4xl text-[#cdb77d]">بُرْهَان</div>
        <h1 className="mb-3 font-display text-3xl">Evidence unavailable</h1>
        <p className="mb-8 text-[#b9ae9b]">{error ?? "This Qur'an passage could not be found."}</p>
        <Link href="/" className="inline-flex border border-[rgba(205,183,125,0.25)] px-5 py-3 text-sm text-[#cdb77d] transition hover:border-[#cdb77d]">
          Return to research
        </Link>
      </div>
    </main>
  );

  const { surah, ayah, translations } = data;

  return (
    <main className="min-h-screen bg-[#171512] text-[#f2ead8]">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-[-20%] h-[700px] w-[700px] -translate-x-1/2 rounded-full bg-[#304d68]/10 blur-[140px]" />
        <div className="absolute bottom-[-10%] right-[-10%] h-[500px] w-[500px] rounded-full bg-[#9a6847]/8 blur-[130px]" />
      </div>

      <div className="relative mx-auto min-h-screen max-w-6xl px-6 py-8 md:px-10">
        <header className="flex items-center justify-between border-b border-[rgba(205,183,125,0.14)] pb-6">
          <Link href="/" className="group">
            <div className="font-display text-2xl tracking-[0.18em] text-[#f2ead8]">BURHĀN</div>
            <div className="mt-1 text-[10px] uppercase tracking-[0.28em] text-[#81796d]">Islamic Knowledge Engine</div>
          </Link>
          <button type="button" onClick={() => setSurahMenuOpen(true)} className="group text-right">
            <div className="font-arabic text-lg text-[#cdb77d] transition group-hover:text-[#f2ead8]">القرآن</div>
            <div className="mt-1 text-[10px] uppercase tracking-[0.2em] text-[#81796d] transition group-hover:text-[#b9ae9b]">Qur&apos;an · Open Surah</div>
          </button>
        </header>

        <section className="pt-16 text-center">
          <div className="mb-3 text-xs uppercase tracking-[0.32em] text-[#9a6847]">Surah {surah.number}</div>
          <h1 className="font-display text-5xl font-medium tracking-wide md:text-6xl">{surah.name_english}</h1>
          <div className="mt-3 font-arabic text-3xl text-[#cdb77d]">{surah.name_arabic}</div>
          <div className="mt-2 text-sm tracking-[0.16em] text-[#81796d]">{surah.name_transliteration}</div>
          <div className="mx-auto mt-8 flex items-center justify-center gap-4">
            <div className="h-px w-16 bg-[#b89552]/30" />
            <div className="font-display text-sm text-[#b89552]">{surah.number}:{ayah.number}</div>
            <div className="h-px w-16 bg-[#b89552]/30" />
          </div>
        </section>

        <section className="mx-auto mt-16 max-w-4xl">
          <div className="relative border-y border-[rgba(205,183,125,0.14)] py-14 md:py-20">
            <div className="pointer-events-none absolute left-1/2 top-1/2 h-40 w-40 -translate-x-1/2 -translate-y-1/2 rounded-full border border-[#b89552]/5" />
            <p dir="rtl" lang="ar" className="relative text-center font-arabic text-4xl leading-[2.25] text-[#f7f1e4] md:text-5xl md:leading-[2.2]">{ayah.text_arabic}</p>
            <div className="mx-auto mt-12 h-px w-20 bg-[#b89552]/30" />
            <div className="mt-10 text-center text-xs uppercase tracking-[0.3em] text-[#81796d]">Translation</div>
            {translations.map((translation) => (
              <div key={translation.id} className="mt-7">
                <p className="mx-auto max-w-3xl text-center font-display text-2xl leading-relaxed text-[#e5d8bc] md:text-3xl">“{translation.text}”</p>
                <div className="mt-5 text-center">
                  <div className="text-sm text-[#b9ae9b]">{translation.translator}</div>
                  <div className="mt-1 text-[10px] uppercase tracking-[0.22em] text-[#81796d]">{translation.source.name}</div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="mx-auto mt-14 max-w-4xl">
          <div className="grid gap-px border border-[rgba(205,183,125,0.12)] bg-[rgba(205,183,125,0.08)] md:grid-cols-2">
            <div className="bg-[#1e1b18] p-7">
              <div className="text-[10px] uppercase tracking-[0.25em] text-[#9a6847]">Primary text</div>
              <div className="mt-4 font-display text-xl">The Qur&apos;an</div>
              <p className="mt-2 text-sm leading-relaxed text-[#81796d]">Arabic text preserved as the primary source record in Burhān.</p>
            </div>
            <div className="bg-[#1e1b18] p-7">
              <div className="text-[10px] uppercase tracking-[0.25em] text-[#9a6847]">Translation</div>
              {translations[0] && (
                <>
                  <div className="mt-4 font-display text-xl">{translations[0].source.name}</div>
                  <p className="mt-2 text-sm leading-relaxed text-[#81796d]">Translation by {translations[0].translator}.</p>
                </>
              )}
            </div>
          </div>
        </section>

        <section className="mx-auto mt-10 max-w-4xl pb-20">
          <div className="flex items-center justify-between border-y border-[rgba(205,183,125,0.12)] py-5">
            {data.previous ? (
              <Link href={`/quran/${data.previous.id}`} className="group text-left">
                <div className="text-[10px] uppercase tracking-[0.22em] text-[#81796d]">Previous</div>
                <div className="mt-2 font-display text-lg text-[#b9ae9b] transition group-hover:text-[#f2ead8]">← {data.previous.reference}</div>
              </Link>
            ) : <div />}
            <div className="text-center">
              <div className="font-arabic text-lg text-[#cdb77d]">{surah.number}:{ayah.number}</div>
              <div className="mt-1 text-[9px] uppercase tracking-[0.2em] text-[#81796d]">Ayah</div>
            </div>
            {data.next ? (
              <Link href={`/quran/${data.next.id}`} className="group text-right">
                <div className="text-[10px] uppercase tracking-[0.22em] text-[#81796d]">Next</div>
                <div className="mt-2 font-display text-lg text-[#b9ae9b] transition group-hover:text-[#f2ead8]">{data.next.reference} →</div>
              </Link>
            ) : <div />}
          </div>

          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <button type="button" onClick={addToNotes} className="border border-[rgba(205,183,125,0.2)] px-5 py-3 text-xs uppercase tracking-[0.16em] text-[#b9ae9b] transition hover:border-[#b89552] hover:text-[#f2ead8]">Add to notes</button>
            <button
  type="button"
  onClick={loadBurhanConnections}
  className="border border-[rgba(205,183,125,0.2)] px-5 py-3 text-xs uppercase tracking-[0.16em] text-[#b9ae9b] transition hover:border-[#b89552] hover:text-[#f2ead8]"
>
  Burhān connections
</button>
            <button type="button" className="border border-[rgba(205,183,125,0.2)] px-5 py-3 text-xs uppercase tracking-[0.16em] text-[#b9ae9b] transition hover:border-[#b89552] hover:text-[#f2ead8]">Arguments</button>
          </div>
        </section>

        <footer className="border-t border-[rgba(205,183,125,0.1)] pt-6 text-center">
          <div className="font-arabic text-lg text-[#81796d]">بُرْهَان</div>
          <div className="mt-2 text-[10px] uppercase tracking-[0.25em] text-[#5f5951]">Knowledge with provenance</div>
        </footer>
      </div>

      {surahMenuOpen && (
        <div className="fixed inset-0 z-50">
          <button type="button" aria-label="Close Surah menu" onClick={() => setSurahMenuOpen(false)} className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
          <aside className="absolute right-0 top-0 h-full w-full max-w-md overflow-y-auto border-l border-[rgba(205,183,125,0.18)] bg-[#1e1b18] shadow-2xl">
            <div className="sticky top-0 z-10 border-b border-[rgba(205,183,125,0.14)] bg-[#1e1b18]/95 px-7 py-6 backdrop-blur">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-[10px] uppercase tracking-[0.28em] text-[#9a6847]">Qur&apos;an</div>
                  <h2 className="mt-2 font-display text-3xl text-[#f2ead8]">Surahs</h2>
                  <p className="mt-1 text-sm text-[#81796d]">Choose a chapter to begin reading.</p>
                </div>
                <button type="button" onClick={() => setSurahMenuOpen(false)} className="text-2xl text-[#81796d] transition hover:text-[#f2ead8]" aria-label="Close">×</button>
              </div>
            </div>
            <div className="p-4">
              {surahsLoading ? (
                <div className="px-4 py-10 text-center font-display text-lg text-[#81796d]">Opening the index…</div>
              ) : (
                <div className="space-y-1">
                  {surahs.map((item) => {
                    const active = item.number === surah.number;
                    return (
                      <button key={item.id} type="button" onClick={() => openSurah(item.number)}
                        className={`group flex w-full items-center gap-4 border px-4 py-4 text-left transition ${active ? "border-[#b89552]/35 bg-[#b89552]/8" : "border-transparent hover:border-[rgba(205,183,125,0.14)] hover:bg-[#28231e]"}`}>
                        <div className={`flex h-8 w-8 shrink-0 items-center justify-center text-xs ${active ? "text-[#cdb77d]" : "text-[#81796d]"}`}>{item.number}</div>
                        <div className="min-w-0 flex-1">
                          <div dir="rtl" className={`font-arabic text-lg ${active ? "text-[#cdb77d]" : "text-[#b9ae9b]"}`}>{item.name_arabic}</div>
                          <div className="mt-0.5 text-xs text-[#81796d]">{item.name_transliteration}</div>
                        </div>
                        <div className="text-right">
                          <div className="font-display text-sm text-[#b9ae9b]">{item.name_english}</div>
                          {active && <div className="mt-1 text-[9px] uppercase tracking-[0.18em] text-[#9a6847]">Reading</div>}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </aside>
        </div>
      )}

{connectionsOpen && (
  <div className="fixed inset-0 z-50">
    <button
      type="button"
      aria-label="Close Burhān connections"
      onClick={() => setConnectionsOpen(false)}
      className="absolute inset-0 bg-black/60 backdrop-blur-sm"
    />

    <aside className="absolute right-0 top-0 h-full w-full max-w-xl overflow-y-auto border-l border-[rgba(205,183,125,0.18)] bg-[#1e1b18] shadow-2xl">
      <div className="sticky top-0 z-10 border-b border-[rgba(205,183,125,0.14)] bg-[#1e1b18]/95 px-7 py-6 backdrop-blur">
        <div className="flex items-start justify-between">
          <div>
            <div className="text-[10px] uppercase tracking-[0.28em] text-[#9a6847]">
              Knowledge graph
            </div>

            <h2 className="mt-2 font-display text-3xl text-[#f2ead8]">
              Burhān connections
            </h2>

            <p className="mt-1 text-sm text-[#81796d]">
              Where this ayah is used within Burhān.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setConnectionsOpen(false)}
            className="text-2xl text-[#81796d] transition hover:text-[#f2ead8]"
            aria-label="Close"
          >
            ×
          </button>
        </div>
      </div>

      <div className="p-7">
        {connectionsLoading ? (
          <div className="py-16 text-center">
            <div className="font-arabic text-2xl text-[#cdb77d]">
              بُرْهَان
            </div>

            <p className="mt-4 font-display text-lg text-[#81796d]">
              Tracing the evidence…
            </p>
          </div>
        ) : connectionsError ? (
          <div className="border border-[#633d3b]/40 bg-[#633d3b]/10 p-5">
            <div className="text-[10px] uppercase tracking-[0.22em] text-[#9a6847]">
              Connection unavailable
            </div>

            <p className="mt-3 text-sm leading-relaxed text-[#b9ae9b]">
              {connectionsError}
            </p>
          </div>
        ) : connections.length === 0 ? (
          <div className="py-16 text-center">
            <div className="font-arabic text-2xl text-[#81796d]">
              لا دليل مرتبط
            </div>

            <p className="mt-4 font-display text-xl text-[#b9ae9b]">
              No Burhān connections yet.
            </p>

            <p className="mx-auto mt-3 max-w-sm text-sm leading-relaxed text-[#81796d]">
              This ayah is currently not attached to a premise or response
              within the argument system.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-[rgba(205,183,125,0.1)] pb-4">
              <div>
                <div className="text-[10px] uppercase tracking-[0.22em] text-[#81796d]">
                  Connections found
                </div>

                <div className="mt-1 font-display text-2xl text-[#f2ead8]">
                  {connections.length}
                </div>
              </div>

              <div className="text-right">
                <div className="font-arabic text-lg text-[#cdb77d]">
                  {surah.number}:{ayah.number}
                </div>

                <div className="mt-1 text-[9px] uppercase tracking-[0.18em] text-[#81796d]">
                  Qur&apos;an
                </div>
              </div>
            </div>

            {connections.map((item) => (
              <article
                key={item.evidence_id}
                className="border border-[rgba(205,183,125,0.14)] bg-[#28231e]"
              >
                <div className="border-b border-[rgba(205,183,125,0.1)] px-6 py-5">
                  <div className="flex items-center justify-between gap-4">
                    <div className="text-[10px] uppercase tracking-[0.2em] text-[#9a6847]">
                      {item.connection.type === "premise"
                        ? "Supports a premise"
                        : item.connection.type === "response"
                          ? "Supports a response"
                          : "Evidence connection"}
                    </div>

                    <div className="text-[10px] uppercase tracking-[0.16em] text-[#81796d]">
                      {item.role}
                    </div>
                  </div>

                  {item.argument && (
                    <>
                      <h3 className="mt-4 font-display text-2xl leading-tight text-[#f2ead8]">
                        {item.argument.title}
                      </h3>

                      <p className="mt-2 text-sm leading-relaxed text-[#81796d]">
                        {item.argument.question}
                      </p>
                    </>
                  )}
                </div>

                <div className="px-6 py-6">
                  <div className="text-[10px] uppercase tracking-[0.2em] text-[#b89552]">
                    {item.connection.type === "premise"
                      ? "Premise"
                      : item.connection.type === "response"
                        ? "Response"
                        : "Connection"}
                  </div>

                  <p className="mt-3 font-display text-xl leading-relaxed text-[#e5d8bc]">
                    {item.connection.text}
                  </p>

                  {item.note && (
                    <div className="mt-6 border-l border-[#b89552]/30 pl-4">
                      <div className="text-[9px] uppercase tracking-[0.2em] text-[#81796d]">
                        Why this evidence
                      </div>

                      <p className="mt-2 text-sm leading-relaxed text-[#b9ae9b]">
                        {item.note}
                      </p>
                    </div>
                  )}

                  <div className="mt-6 flex items-center justify-between border-t border-[rgba(205,183,125,0.1)] pt-4">
                    <div className="text-[10px] uppercase tracking-[0.18em] text-[#81796d]">
                      {item.reference ?? `${surah.number}:${ayah.number}`}
                    </div>

                    {item.argument && (
                      <Link
                        href={`/arguments/${item.argument.id}${
                          item.connection.id != null && item.connection.type
                            ? `#${item.connection.type}-${item.connection.id}`
                            : ""
                        }`}
                        className="text-xs uppercase tracking-[0.16em] text-[#cdb77d] transition hover:text-[#f2ead8]"
                      >
                        Open {item.connection.type ?? "argument"} →
                      </Link>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </aside>
  </div>
)}

      <NotesPanel
        open={notesOpen}
        onClose={() => setNotesOpen(false)}
        insertContent={noteToInsert}
        onInsertComplete={() => setNoteToInsert(null)}
      />
    </main>
  );
}