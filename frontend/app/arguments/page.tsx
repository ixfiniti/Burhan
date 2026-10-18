"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type ArgumentCategory = {
  id: number;
  name: string;
  slug: string;
  description: string | null;
};

type ArgumentSummary = {
  id: number;
  title: string;
  question: string;
  summary: string;
  claim: string;
  conclusion: string;
  status: string;
  category_id: number;
  category: ArgumentCategory;
  premises: { id: number; number: number }[];
  objections: { id: number; number: number }[];
};

export default function ArgumentsLibraryPage() {
  const [argumentsList, setArgumentsList] = useState<ArgumentSummary[]>([]);
  const [categories, setCategories] = useState<ArgumentCategory[]>([]);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadLibrary() {
      try {
        const [argumentsResponse, categoriesResponse] = await Promise.all([
          fetch(`${API_URL}/arguments`, {
            signal: controller.signal,
            cache: "no-store",
          }),
          fetch(`${API_URL}/arguments/categories`, {
            signal: controller.signal,
            cache: "no-store",
          }),
        ]);

        if (!argumentsResponse.ok || !categoriesResponse.ok) {
          throw new Error(
            "Unable to retrieve the arguments library. Check that the Burhān API is running.",
          );
        }

        const [argumentsData, categoriesData] = await Promise.all([
          argumentsResponse.json(),
          categoriesResponse.json(),
        ]);

        if (!Array.isArray(argumentsData) || !Array.isArray(categoriesData)) {
          throw new Error("The API returned an unexpected response.");
        }

        if (!controller.signal.aborted) {
          setArgumentsList(argumentsData);
          setCategories(categoriesData);
          setError(null);
        }
      } catch (err) {
        if (controller.signal.aborted) return;

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

    void loadLibrary();

    return () => controller.abort();
  }, []);

  const filteredArguments = useMemo(() => {
    const query = search.trim().toLowerCase();

    return argumentsList.filter((item) => {
      const matchesSearch =
        !query ||
        [
          item.title,
          item.question,
          item.summary,
          item.claim,
          item.conclusion,
          item.category?.name,
        ].some((value) => value?.toLowerCase().includes(query));

      const matchesCategory =
        selectedCategory === "all" ||
        String(item.category_id) === selectedCategory;

      const matchesStatus =
        selectedStatus === "all" || item.status === selectedStatus;

      return matchesSearch && matchesCategory && matchesStatus;
    });
  }, [argumentsList, search, selectedCategory, selectedStatus]);

  return (
    <main className="min-h-screen bg-[#e9e0ce] text-[#252b24]">
      <header className="border-b border-black/10">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-5 sm:px-8">
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

      <div className="mx-auto max-w-6xl px-5 py-10 sm:px-8 sm:py-16">
        <section className="border-b border-black/15 pb-9">
          <div className="flex flex-wrap items-start justify-between gap-5">
            <div>
              <div className="text-[10px] uppercase tracking-[0.24em] text-[#92703c]">
                The research archive
              </div>

              <h1 className="mt-5 font-serif text-4xl leading-tight sm:text-6xl">
                Arguments &amp; inquiry
              </h1>
            </div>

            <Link
              href="/arguments/new"
              className="inline-flex items-center gap-2 border border-[#92703c]/50 bg-[#f5f0e5] px-5 py-3 text-xs uppercase tracking-[0.12em] text-[#614823] transition hover:border-[#92703c] hover:bg-[#e3d7bf] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#92703c]"
            >
              <span className="text-base leading-none">+</span>
              New argument
            </Link>
          </div>

          <p className="mt-5 max-w-2xl text-sm leading-7 text-[#625e53] sm:text-base">
            Explore structured investigations into theology, philosophy,
            knowledge, ethics, and Islamic questions. Examine claims through
            premises, objections, responses, and evidence.
          </p>

          <div className="mt-7 flex flex-wrap gap-x-8 gap-y-3 text-xs text-[#777164]">
            <span>
              <strong className="font-medium text-[#252b24]">
                {loading ? "—" : argumentsList.length}
              </strong>{" "}
              arguments
            </span>
            <span>
              <strong className="font-medium text-[#252b24]">
                {categories.length || "—"}
              </strong>{" "}
              disciplines
            </span>
            <span>
              <strong className="font-medium text-[#252b24]">
                {loading ? "—" : filteredArguments.length}
              </strong>{" "}
              results
            </span>
          </div>
        </section>

        <section className="py-7">
          <label
            htmlFor="argument-search"
            className="mb-2 block text-[10px] uppercase tracking-[0.18em] text-[#777164]"
          >
            Search the archive
          </label>

          <input
            id="argument-search"
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search titles, questions, claims, or concepts…"
            className="w-full border border-black/15 bg-[#f5f0e5] px-4 py-4 text-sm text-[#252b24] outline-none transition placeholder:text-[#9a9385] focus:border-[#b89552]"
          />

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div>
              <label
                htmlFor="argument-category"
                className="mb-2 block text-[10px] uppercase tracking-[0.16em] text-[#777164]"
              >
                Discipline
              </label>

              <select
                id="argument-category"
                value={selectedCategory}
                onChange={(event) => setSelectedCategory(event.target.value)}
                className="w-full border border-black/15 bg-[#f5f0e5] px-3 py-3 text-sm outline-none focus:border-[#b89552]"
              >
                <option value="all">All disciplines</option>
                {categories.map((category) => (
                  <option key={category.id} value={String(category.id)}>
                    {category.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label
                htmlFor="argument-status"
                className="mb-2 block text-[10px] uppercase tracking-[0.16em] text-[#777164]"
              >
                Research status
              </label>

              <select
                id="argument-status"
                value={selectedStatus}
                onChange={(event) => setSelectedStatus(event.target.value)}
                className="w-full border border-black/15 bg-[#f5f0e5] px-3 py-3 text-sm outline-none focus:border-[#b89552]"
              >
                <option value="all">All statuses</option>
                <option value="draft">Draft</option>
                <option value="review">Under review</option>
                <option value="published">Published</option>
                <option value="archived">Archived</option>
              </select>
            </div>
          </div>

          {(search || selectedCategory !== "all" || selectedStatus !== "all") && (
            <button
              type="button"
              onClick={() => {
                setSearch("");
                setSelectedCategory("all");
                setSelectedStatus("all");
              }}
              className="mt-3 text-xs text-[#92703c] underline underline-offset-4"
            >
              Clear filters
            </button>
          )}
        </section>

        {loading ? (
          <div className="border-t border-black/10 py-16 text-center text-sm text-[#777164]">
            Gathering the research archive…
          </div>
        ) : error ? (
          <section className="border border-red-900/20 bg-red-950/[0.035] p-6">
            <h2 className="font-serif text-2xl">Archive unavailable</h2>
            <p className="mt-3 text-sm leading-6 text-[#777164]">{error}</p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-5 border border-black/15 px-4 py-2 text-xs uppercase tracking-wider"
            >
              Try again
            </button>
          </section>
        ) : filteredArguments.length > 0 ? (
          <section className="grid gap-4 border-t border-black/10 pt-6 md:grid-cols-2">
            {filteredArguments.map((item, index) => (
              <article
                key={item.id}
                className="group flex flex-col border border-black/10 bg-[#f5f0e5] p-5 transition duration-200 hover:border-[#b89552]/70 sm:p-7"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <span className="text-[10px] uppercase tracking-[0.18em] text-[#92703c]">
                    {item.category?.name ?? "Uncategorised"}
                  </span>

                  <span className="border border-black/10 px-2 py-1 text-[9px] uppercase tracking-[0.12em] text-[#777164]">
                    {item.status.replaceAll("_", " ")}
                  </span>
                </div>

                <h2 className="mt-5 font-serif text-2xl leading-snug">
                  <Link
                    href={`/arguments/${item.id}`}
                    className="transition group-hover:text-[#92703c]"
                  >
                    {item.title}
                  </Link>
                </h2>

                <p className="mt-3 text-sm leading-6 text-[#625e53]">
                  {item.question}
                </p>

                <p className="mt-4 line-clamp-3 text-sm leading-6 text-[#777164]">
                  {item.summary}
                </p>

                <div className="mt-5 border-l-2 border-[#b89552] pl-3">
                  <div className="text-[9px] uppercase tracking-[0.17em] text-[#92703c]">
                    Central claim
                  </div>
                  <p className="mt-2 text-sm leading-6 text-[#45443b]">
                    {item.claim}
                  </p>
                </div>

                <div className="mt-auto flex flex-wrap items-center justify-between gap-3 border-t border-black/10 pt-5 mt-6">
                  <div className="flex flex-wrap gap-3 text-[10px] text-[#81796d]">
                    <span>{item.premises.length} premises</span>
                    <span>{item.objections.length} objections</span>
                  </div>

                  <Link
                    href={`/arguments/${item.id}`}
                    className="text-xs text-[#92703c] transition group-hover:text-[#614823]"
                  >
                    Examine argument →
                  </Link>
                </div>

                <span className="sr-only">Archive entry {index + 1}</span>
              </article>
            ))}
          </section>
        ) : (
          <section className="border-t border-black/10 py-16 text-center">
            <h2 className="font-serif text-2xl">No matching arguments</h2>
            <p className="mt-3 text-sm text-[#777164]">
              Try another search term or broaden your filters.
            </p>
            <button
              type="button"
              onClick={() => {
                setSearch("");
                setSelectedCategory("all");
                setSelectedStatus("all");
              }}
              className="mt-5 text-xs text-[#92703c] underline underline-offset-4"
            >
              Reset search
            </button>
          </section>
        )}

        <footer className="mt-12 border-t border-black/10 py-6 text-xs leading-6 text-[#81796d]">
          Burhān · A growing archive of structured inquiry
        </footer>
      </div>
    </main>
  );
}