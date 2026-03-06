"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import {
  getProject,
  getStringDetail,
  createTranslation,
  updateTranslation,
  getSuggestions,
} from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import Sidebar from "@/components/sidebar";
import {
  ArrowLeft,
  Check,
  Lightbulb,
  Plus,
  Save,
} from "lucide-react";

interface Translation {
  id: string;
  language_code: string;
  translated_text: string;
  status: string;
  updated_at: string;
}

interface StringDetail {
  id: string;
  key: string;
  source_text: string;
  context: string;
  max_length: number | null;
  has_plurals: boolean;
  translations: Translation[];
}

interface Suggestion {
  source_text: string;
  translated_text: string;
  similarity: number;
  project_name: string;
  string_key: string;
}

export default function StringDetailPage({
  params,
}: {
  params: Promise<{ slug: string; stringId: string }>;
}) {
  const { slug, stringId } = use(params);
  const { user } = useAuth();
  const canTranslate =
    user?.role === "admin" ||
    user?.role === "manager" ||
    user?.role === "translator";

  const [project, setProject] = useState<{ name: string; slug: string } | null>(null);
  const [string, setString] = useState<StringDetail | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [newLang, setNewLang] = useState("");
  const [newText, setNewText] = useState("");
  const [saving, setSaving] = useState(false);
  const [editingLang, setEditingLang] = useState<string | null>(null);
  const [editText, setEditText] = useState("");

  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [sugLang, setSugLang] = useState("");
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  useEffect(() => {
    getProject(slug).then(setProject);
    getStringDetail(slug, stringId).then(setString);
  }, [slug, stringId]);

  async function handleAdd() {
    if (!newLang.trim() || !newText.trim()) return;
    setSaving(true);
    try {
      await createTranslation(slug, stringId, {
        language_code: newLang,
        translated_text: newText,
      });
      const updated = await getStringDetail(slug, stringId);
      setString(updated);
      setShowAdd(false);
      setNewLang("");
      setNewText("");
    } finally {
      setSaving(false);
    }
  }

  async function handleUpdate(language: string) {
    setSaving(true);
    try {
      await updateTranslation(slug, stringId, language, {
        translated_text: editText,
      });
      const updated = await getStringDetail(slug, stringId);
      setString(updated);
      setEditingLang(null);
    } finally {
      setSaving(false);
    }
  }

  async function handleApprove(language: string) {
    await updateTranslation(slug, stringId, language, { status: "approved" });
    const updated = await getStringDetail(slug, stringId);
    setString(updated);
  }

  async function loadSuggestions() {
    if (!sugLang.trim()) return;
    setLoadingSuggestions(true);
    try {
      const data = await getSuggestions(slug, stringId, sugLang);
      setSuggestions(data.suggestions || []);
    } finally {
      setLoadingSuggestions(false);
    }
  }

  if (!string || !project) {
    return (
      <div className="min-h-screen">
        <Sidebar />
        <main className="ml-64 p-8 flex justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Sidebar />
      <main className="ml-64 p-8">
        {/* Breadcrumb */}
        <Link
          href={`/projects/${slug}`}
          className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1 mb-6"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          {project.name}
        </Link>

        {/* String info */}
        <div className="bg-white rounded-xl border p-6 mb-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-mono text-gray-400 mb-1">
                {string.key}
              </p>
              <p className="text-lg">{string.source_text}</p>
              {string.context && (
                <p className="text-sm text-gray-500 mt-2">
                  Context: {string.context}
                </p>
              )}
              {string.max_length && (
                <p className="text-xs text-gray-400 mt-1">
                  Max length: {string.max_length}
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Translations */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold">Translations</h2>
              {canTranslate && (
                <button
                  onClick={() => setShowAdd(true)}
                  className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
                >
                  <Plus className="h-3.5 w-3.5" />
                  Add Translation
                </button>
              )}
            </div>

            {showAdd && (
              <div className="bg-white rounded-xl border p-4 space-y-3">
                <div className="grid grid-cols-4 gap-3">
                  <div>
                    <label className="block text-xs font-medium mb-1">
                      Language
                    </label>
                    <input
                      value={newLang}
                      onChange={(e) => setNewLang(e.target.value)}
                      placeholder="pt-BR"
                      className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div className="col-span-3">
                    <label className="block text-xs font-medium mb-1">
                      Translation
                    </label>
                    <input
                      value={newText}
                      onChange={(e) => setNewText(e.target.value)}
                      placeholder="Translated text..."
                      className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleAdd}
                    disabled={saving}
                    className="rounded-lg bg-blue-600 text-white px-3 py-1.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                  >
                    {saving ? "Saving..." : "Save"}
                  </button>
                  <button
                    onClick={() => setShowAdd(false)}
                    className="rounded-lg border px-3 py-1.5 text-sm hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {string.translations.length === 0 ? (
              <div className="bg-white rounded-xl border p-8 text-center text-gray-400">
                No translations yet
              </div>
            ) : (
              string.translations.map((t) => (
                <div
                  key={t.id}
                  className="bg-white rounded-xl border p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="bg-gray-100 text-gray-700 text-xs font-mono px-2 py-0.5 rounded">
                        {t.language_code}
                      </span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          t.status === "approved"
                            ? "bg-green-50 text-green-700"
                            : t.status === "draft"
                              ? "bg-yellow-50 text-yellow-700"
                              : "bg-gray-50 text-gray-600"
                        }`}
                      >
                        {t.status}
                      </span>
                    </div>
                    {canTranslate && (
                      <div className="flex items-center gap-1">
                        {t.status !== "approved" && (
                          <button
                            onClick={() => handleApprove(t.language_code)}
                            className="p-1.5 rounded-lg text-green-600 hover:bg-green-50 transition-colors"
                            title="Approve"
                          >
                            <Check className="h-4 w-4" />
                          </button>
                        )}
                        <button
                          onClick={() => {
                            setEditingLang(t.language_code);
                            setEditText(t.translated_text);
                          }}
                          className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-50 hover:text-gray-600 transition-colors"
                          title="Edit"
                        >
                          <Save className="h-4 w-4" />
                        </button>
                      </div>
                    )}
                  </div>

                  {editingLang === t.language_code ? (
                    <div className="space-y-2">
                      <textarea
                        value={editText}
                        onChange={(e) => setEditText(e.target.value)}
                        rows={2}
                        className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleUpdate(t.language_code)}
                          disabled={saving}
                          className="rounded-lg bg-blue-600 text-white px-3 py-1.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                        >
                          {saving ? "Saving..." : "Update"}
                        </button>
                        <button
                          onClick={() => setEditingLang(null)}
                          className="rounded-lg border px-3 py-1.5 text-sm hover:bg-gray-50"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-700">
                      {t.translated_text}
                    </p>
                  )}

                  <p className="text-xs text-gray-400 mt-2">
                    Updated{" "}
                    {new Date(t.updated_at).toLocaleDateString()}
                  </p>
                </div>
              ))
            )}
          </div>

          {/* Translation Memory */}
          <div>
            <h2 className="font-semibold mb-4 flex items-center gap-2">
              <Lightbulb className="h-4 w-4" />
              Translation Memory
            </h2>
            <div className="bg-white rounded-xl border p-4 space-y-3">
              <div className="flex gap-2">
                <input
                  value={sugLang}
                  onChange={(e) => setSugLang(e.target.value)}
                  placeholder="Language (e.g. pt-BR)"
                  className="flex-1 rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={loadSuggestions}
                  disabled={loadingSuggestions}
                  className="rounded-lg bg-gray-100 px-3 py-2 text-sm font-medium hover:bg-gray-200 disabled:opacity-50 transition-colors"
                >
                  Search
                </button>
              </div>

              {loadingSuggestions && (
                <div className="flex justify-center py-4">
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
                </div>
              )}

              {suggestions.length === 0 && !loadingSuggestions && sugLang && (
                <p className="text-sm text-gray-400 text-center py-4">
                  No suggestions found
                </p>
              )}

              {suggestions.map((s, i) => (
                <div
                  key={i}
                  className="border rounded-lg p-3 space-y-1 hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => {
                    if (canTranslate) {
                      setShowAdd(true);
                      setNewLang(sugLang);
                      setNewText(s.translated_text);
                    }
                  }}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-400">
                      {s.project_name} / {s.string_key}
                    </span>
                    <span className="text-xs font-medium bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">
                      {Math.round(s.similarity * 100)}%
                    </span>
                  </div>
                  <p className="text-xs text-gray-500">{s.source_text}</p>
                  <p className="text-sm font-medium">{s.translated_text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
