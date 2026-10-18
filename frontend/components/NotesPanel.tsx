
"use client";

import { useEffect, useState } from "react";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";

type NotesPanelProps = {
  open: boolean;
  onClose: () => void;
  insertContent?: string | null;
  onInsertComplete?: () => void;
};

const NOTE_TITLE_KEY = "burhan-note-title";
const NOTE_BODY_KEY = "burhan-note-body";

export default function NotesPanel({
  open,
  onClose,
  insertContent,
  onInsertComplete,
}: NotesPanelProps) {
  const [title, setTitle] = useState("Untitled investigation");

  const editor = useEditor({
    extensions: [StarterKit],
    content: "",
    immediatelyRender: false,

    onUpdate: ({ editor }) => {
      window.localStorage.setItem(
        NOTE_BODY_KEY,
        editor.getHTML(),
      );
    },
  });

  useEffect(() => {
    const savedTitle = window.localStorage.getItem(NOTE_TITLE_KEY);
    const savedBody = window.localStorage.getItem(NOTE_BODY_KEY);


     if (savedTitle) {
      // This effect intentionally hydrates the title from browser storage.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTitle(savedTitle);
    }

    if (savedBody && editor) {
      editor.commands.setContent(savedBody);
    }
  }, [editor]);

  useEffect(() => {
  if (!editor || !insertContent) {
    return;
  }

  editor
    .chain()
    .focus()
    .insertContent(insertContent)
    .run();

  onInsertComplete?.();
}, [editor, insertContent, onInsertComplete]);

  useEffect(() => {
    window.localStorage.setItem(NOTE_TITLE_KEY, title);
  }, [title]);

  if (!editor) {
    return null;
  }

  return (
    <>
      <div
        className={`fixed inset-0 z-40 bg-black/35 backdrop-blur-[2px] transition-opacity duration-300 ${
          open
            ? "pointer-events-auto opacity-100"
            : "pointer-events-none opacity-0"
        }`}
        onClick={onClose}
        aria-hidden={!open}
      />

      <aside
        aria-label="Research notes"
        className={`fixed right-0 top-0 z-50 flex h-full w-full max-w-md flex-col border-l border-ink/10 bg-parchment shadow-2xl shadow-black/30 transition-transform duration-500 ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <header className="flex items-center justify-between border-b border-ink/10 px-6 py-5">
          <div>
            <div className="font-ui text-[8px] font-semibold uppercase tracking-[0.28em] text-copper-deep">
              Research notebook
            </div>

            <div className="mt-1 font-arabic text-sm text-ink-soft">
              ملاحظات
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close notes"
            className="flex h-8 w-8 items-center justify-center border border-ink/10 font-ui text-sm text-ink-soft transition-colors hover:border-copper/40 hover:text-copper-deep"
          >
            ×
          </button>
        </header>

        <div className="manuscript flex min-h-0 flex-1 flex-col px-6 py-8 sm:px-8">
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            aria-label="Note title"
            className="border-0 bg-transparent font-display text-3xl font-medium text-ink outline-none placeholder:text-ink/40"
            placeholder="Untitled investigation"
          />

          <div className="mt-3 scholarly-rule opacity-50" />

          {/* Formatting toolbar */}
          <div className="mt-5 flex flex-wrap items-center gap-1 border-b border-ink/10 pb-3">
            <button
              type="button"
              onClick={() =>
                editor.chain().focus().toggleBold().run()
              }
              className={`flex h-8 min-w-8 items-center justify-center px-2 font-ui text-xs transition-colors ${
                editor.isActive("bold")
                  ? "bg-ink text-parchment"
                  : "text-ink-soft hover:bg-ink/5"
              }`}
              aria-label="Bold"
              title="Bold"
            >
              <strong>B</strong>
            </button>

            <button
              type="button"
              onClick={() =>
                editor.chain().focus().toggleItalic().run()
              }
              className={`flex h-8 min-w-8 items-center justify-center px-2 font-ui text-xs italic transition-colors ${
                editor.isActive("italic")
                  ? "bg-ink text-parchment"
                  : "text-ink-soft hover:bg-ink/5"
              }`}
              aria-label="Italic"
              title="Italic"
            >
              I
            </button>

            <button
              type="button"
              onClick={() =>
                editor
                  .chain()
                  .focus()
                  .toggleHeading({ level: 2 })
                  .run()
              }
              className={`flex h-8 min-w-8 items-center justify-center px-2 font-display text-sm transition-colors ${
                editor.isActive("heading", { level: 2 })
                  ? "bg-ink text-parchment"
                  : "text-ink-soft hover:bg-ink/5"
              }`}
              aria-label="Heading"
              title="Heading"
            >
              H
            </button>

            <div className="mx-1 h-5 w-px bg-ink/10" />

            <button
              type="button"
              onClick={() =>
                editor.chain().focus().toggleBulletList().run()
              }
              className={`flex h-8 min-w-8 items-center justify-center px-2 font-ui text-sm transition-colors ${
                editor.isActive("bulletList")
                  ? "bg-ink text-parchment"
                  : "text-ink-soft hover:bg-ink/5"
              }`}
              aria-label="Bullet list"
              title="Bullet list"
            >
              •
            </button>

            <button
              type="button"
              onClick={() =>
                editor.chain().focus().toggleOrderedList().run()
              }
              className={`flex h-8 min-w-8 items-center justify-center px-2 font-ui text-xs transition-colors ${
                editor.isActive("orderedList")
                  ? "bg-ink text-parchment"
                  : "text-ink-soft hover:bg-ink/5"
              }`}
              aria-label="Numbered list"
              title="Numbered list"
            >
              1.
            </button>
          </div>

          <EditorContent
            editor={editor}
            className="burhan-editor mt-6 min-h-0 flex-1 overflow-y-auto font-display text-lg leading-[1.8] text-ink"
          />

          <footer className="mt-6 flex items-center justify-between border-t border-ink/10 pt-4">
            <span className="font-ui text-[8px] uppercase tracking-[0.18em] text-ink/45">
              Saved locally
            </span>

            <span className="font-arabic text-sm text-ink/40">
              بسم الله
            </span>
          </footer>
        </div>
      </aside>
    </>
  );
}
