"use client";

import { useEffect, useState, useRef, use } from "react";
import Link from "next/link";
import {
  getProject,
  getProgress,
  getStrings,
  getResources,
  uploadResource,
  getGitHubRepo,
  linkGitHubRepo,
  unlinkGitHubRepo,
  syncGitHubRepo,
} from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import ProgressBar from "@/components/progress-bar";
import Sidebar from "@/components/sidebar";
import {
  ArrowLeft,
  Upload,
  FileText,
  Search,
  Languages,
  Github,
  RefreshCw,
  Unlink,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
} from "lucide-react";

interface Project {
  id: string;
  name: string;
  slug: string;
  description: string;
  source_language: string;
}

interface LangProgress {
  code: string;
  translated: number;
  approved: number;
  progress_percent: number;
}

interface ProgressData {
  total_strings: number;
  languages: LangProgress[];
}

interface StringItem {
  id: string;
  key: string;
  source_text: string;
  context: string;
  has_plurals: boolean;
  translation_count: number;
}

interface ResourceFile {
  id: string;
  file_path: string;
  file_format: string;
  version: number;
  uploaded_at: string;
}

interface GitHubRepoData {
  id: string;
  owner: string;
  repo: string;
  branch: string;
  base_path: string;
  file_patterns: string[];
  has_token: boolean;
  last_synced_at: string | null;
  last_sync_status: string;
  last_sync_message: string;
  full_name: string;
}

export default function ProjectPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const { user } = useAuth();
  const canManage = user?.role === "admin" || user?.role === "manager";

  const [project, setProject] = useState<Project | null>(null);
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [strings, setStrings] = useState<StringItem[]>([]);
  const [resources, setResources] = useState<ResourceFile[]>([]);
  const [search, setSearch] = useState("");
  const [tab, setTab] = useState<"strings" | "resources" | "github">("strings");
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  // GitHub state
  const [ghRepo, setGhRepo] = useState<GitHubRepoData | null>(null);
  const [showGhForm, setShowGhForm] = useState(false);
  const [ghForm, setGhForm] = useState({
    owner: "",
    repo: "",
    branch: "main",
    base_path: "",
    file_patterns: "",
    access_token: "",
  });
  const [ghSaving, setGhSaving] = useState(false);
  const [ghSyncing, setGhSyncing] = useState(false);
  const [ghSyncResult, setGhSyncResult] = useState<string | null>(null);

  useEffect(() => {
    getProject(slug).then(setProject);
    getProgress(slug).then(setProgress);
    getStrings(slug).then(setStrings);
    getResources(slug).then(setResources);
    loadGhRepo();
  }, [slug]);

  async function loadGhRepo() {
    try {
      const data = await getGitHubRepo(slug);
      setGhRepo(data);
    } catch {
      setGhRepo(null);
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await uploadResource(slug, file);
      getResources(slug).then(setResources);
      getStrings(slug).then(setStrings);
      getProgress(slug).then(setProgress);
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function handleSearch() {
    const data = await getStrings(slug, search ? { search } : undefined);
    setStrings(data);
  }

  useEffect(() => {
    const timer = setTimeout(handleSearch, 300);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  function parseRepoUrl(input: string) {
    // Accept formats: owner/repo, github.com/owner/repo, full URL
    const match = input.match(
      /(?:https?:\/\/)?(?:github\.com\/)?([^/\s]+)\/([^/\s#?]+)/
    );
    if (match) {
      return { owner: match[1], repo: match[2].replace(/\.git$/, "") };
    }
    return null;
  }

  async function handleLinkRepo() {
    setGhSaving(true);
    try {
      const patterns = ghForm.file_patterns
        ? ghForm.file_patterns.split(",").map((p) => p.trim()).filter(Boolean)
        : [];
      await linkGitHubRepo(slug, {
        owner: ghForm.owner,
        repo: ghForm.repo,
        branch: ghForm.branch || "main",
        base_path: ghForm.base_path,
        file_patterns: patterns,
        access_token: ghForm.access_token,
      });
      await loadGhRepo();
      setShowGhForm(false);
      setGhForm({ owner: "", repo: "", branch: "main", base_path: "", file_patterns: "", access_token: "" });
    } finally {
      setGhSaving(false);
    }
  }

  async function handleUnlinkRepo() {
    if (!confirm("Unlink this GitHub repository?")) return;
    await unlinkGitHubRepo(slug);
    setGhRepo(null);
  }

  async function handleSync() {
    setGhSyncing(true);
    setGhSyncResult(null);
    try {
      const result = await syncGitHubRepo(slug);
      setGhSyncResult(
        `Synced ${result.files_synced}/${result.files_found} files` +
        (result.errors?.length ? ` (${result.errors.length} errors)` : "")
      );
      await loadGhRepo();
      getResources(slug).then(setResources);
      getStrings(slug).then(setStrings);
      getProgress(slug).then(setProgress);
    } catch {
      setGhSyncResult("Sync failed. Check repository settings.");
    } finally {
      setGhSyncing(false);
    }
  }

  if (!project) {
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
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/dashboard"
            className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1 mb-4"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to projects
          </Link>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">{project.name}</h1>
              <p className="text-gray-500 text-sm mt-1">
                {project.description || "No description"}
              </p>
            </div>
            {canManage && (
              <div className="flex items-center gap-2">
                <input
                  ref={fileRef}
                  type="file"
                  accept=".json,.po,.strings,.xliff,.xlf"
                  onChange={handleUpload}
                  className="hidden"
                />
                <button
                  onClick={() => fileRef.current?.click()}
                  disabled={uploading}
                  className="flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium hover:bg-gray-50 disabled:opacity-50 transition-colors"
                >
                  <Upload className="h-4 w-4" />
                  {uploading ? "Uploading..." : "Upload"}
                </button>
                {ghRepo && (
                  <button
                    onClick={handleSync}
                    disabled={ghSyncing}
                    className="flex items-center gap-2 rounded-lg bg-blue-600 text-white px-4 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    {ghSyncing ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4" />
                    )}
                    {ghSyncing ? "Syncing..." : "Sync GitHub"}
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Sync result toast */}
        {ghSyncResult && (
          <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-sm text-blue-800 flex items-center justify-between">
            <span>{ghSyncResult}</span>
            <button onClick={() => setGhSyncResult(null)} className="text-blue-500 hover:text-blue-700">
              &times;
            </button>
          </div>
        )}

        {/* Progress cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl border p-5">
            <p className="text-sm text-gray-500">Total Strings</p>
            <p className="text-3xl font-bold mt-1">
              {progress?.total_strings ?? 0}
            </p>
          </div>
          <div className="bg-white rounded-xl border p-5">
            <p className="text-sm text-gray-500">Languages</p>
            <p className="text-3xl font-bold mt-1">
              {progress?.languages.length ?? 0}
            </p>
          </div>
          <div className="bg-white rounded-xl border p-5">
            <p className="text-sm text-gray-500">Resources</p>
            <p className="text-3xl font-bold mt-1">{resources.length}</p>
          </div>
          <div className="bg-white rounded-xl border p-5">
            <p className="text-sm text-gray-500">Source</p>
            {ghRepo ? (
              <div className="flex items-center gap-1.5 mt-1">
                <Github className="h-4 w-4" />
                <span className="text-sm font-medium truncate">{ghRepo.full_name}</span>
              </div>
            ) : (
              <p className="text-sm text-gray-400 mt-1">Manual upload</p>
            )}
          </div>
        </div>

        {/* Language progress */}
        {progress && progress.languages.length > 0 && (
          <div className="bg-white rounded-xl border p-6 mb-8">
            <h2 className="font-semibold mb-4 flex items-center gap-2">
              <Languages className="h-4 w-4" />
              Translation Progress
            </h2>
            <div className="space-y-3">
              {progress.languages.map((lang) => (
                <ProgressBar
                  key={lang.code}
                  percent={lang.progress_percent}
                  label={`${lang.code} (${lang.translated}/${progress.total_strings})`}
                />
              ))}
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 border-b mb-6">
          <button
            onClick={() => setTab("strings")}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === "strings"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            Strings ({strings.length})
          </button>
          <button
            onClick={() => setTab("resources")}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === "resources"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            Resources ({resources.length})
          </button>
          {canManage && (
            <button
              onClick={() => setTab("github")}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
                tab === "github"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              <Github className="h-3.5 w-3.5" />
              GitHub
            </button>
          )}
        </div>

        {/* Strings tab */}
        {tab === "strings" && (
          <>
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search strings by key or text..."
                className="w-full rounded-lg border pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="bg-white rounded-xl border overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Key</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Source Text</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Translations</th>
                  </tr>
                </thead>
                <tbody>
                  {strings.length === 0 ? (
                    <tr>
                      <td colSpan={3} className="text-center text-gray-400 py-12">
                        No strings found
                      </td>
                    </tr>
                  ) : (
                    strings.map((s) => (
                      <tr key={s.id} className="border-b last:border-b-0 hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3">
                          <Link
                            href={`/projects/${slug}/strings/${s.id}`}
                            className="text-blue-600 hover:underline font-mono text-xs"
                          >
                            {s.key}
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-gray-700 max-w-md truncate">{s.source_text}</td>
                        <td className="px-4 py-3">
                          <span className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full">
                            {s.translation_count}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}

        {/* Resources tab */}
        {tab === "resources" && (
          <div className="bg-white rounded-xl border overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left px-4 py-3 font-medium text-gray-600">File</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Format</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Version</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Uploaded</th>
                </tr>
              </thead>
              <tbody>
                {resources.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="text-center text-gray-400 py-12">
                      <FileText className="h-8 w-8 mx-auto mb-2" />
                      No resource files uploaded yet
                    </td>
                  </tr>
                ) : (
                  resources.map((r) => (
                    <tr key={r.id} className="border-b last:border-b-0 hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-xs">{r.file_path}</td>
                      <td className="px-4 py-3">
                        <span className="bg-blue-50 text-blue-700 text-xs px-2 py-1 rounded-full uppercase">
                          {r.file_format}
                        </span>
                      </td>
                      <td className="px-4 py-3">v{r.version}</td>
                      <td className="px-4 py-3 text-gray-500">
                        {new Date(r.uploaded_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* GitHub tab */}
        {tab === "github" && canManage && (
          <div className="space-y-6">
            {ghRepo ? (
              <div className="bg-white rounded-xl border p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <Github className="h-8 w-8" />
                    <div>
                      <h3 className="font-semibold text-lg">{ghRepo.full_name}</h3>
                      <p className="text-sm text-gray-500">
                        Branch: <code className="bg-gray-100 px-1 rounded">{ghRepo.branch}</code>
                        {ghRepo.base_path && (
                          <> &middot; Path: <code className="bg-gray-100 px-1 rounded">{ghRepo.base_path}</code></>
                        )}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={handleUnlinkRepo}
                    className="flex items-center gap-1 text-sm text-red-500 hover:text-red-700 transition-colors"
                  >
                    <Unlink className="h-3.5 w-3.5" />
                    Unlink
                  </button>
                </div>

                {/* Sync status */}
                {ghRepo.last_synced_at && (
                  <div className={`border rounded-lg p-4 mb-4 ${
                    ghRepo.last_sync_status === "warning" ? "bg-amber-50 border-amber-200" :
                    ghRepo.last_sync_status === "error" ? "bg-red-50 border-red-200" :
                    "bg-green-50 border-green-200"
                  }`}>
                    <div className="flex items-center gap-2 mb-1">
                      {ghRepo.last_sync_status === "success" ? (
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                      ) : ghRepo.last_sync_status === "warning" ? (
                        <AlertTriangle className="h-4 w-4 text-amber-600" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-600" />
                      )}
                      <span className="text-sm font-medium">
                        Last sync: {new Date(ghRepo.last_synced_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{ghRepo.last_sync_message}</p>
                  </div>
                )}

                <div className="flex gap-2">
                  <button
                    onClick={handleSync}
                    disabled={ghSyncing}
                    className="flex items-center gap-2 rounded-lg bg-blue-600 text-white px-4 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    {ghSyncing ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4" />
                    )}
                    {ghSyncing ? "Syncing..." : "Sync Now"}
                  </button>
                  <button
                    onClick={() => {
                      setGhForm({
                        owner: ghRepo.owner,
                        repo: ghRepo.repo,
                        branch: ghRepo.branch,
                        base_path: ghRepo.base_path,
                        file_patterns: ghRepo.file_patterns.join(", "),
                        access_token: "",
                      });
                      setShowGhForm(true);
                    }}
                    className="rounded-lg border px-4 py-2 text-sm font-medium hover:bg-gray-50 transition-colors"
                  >
                    Edit Settings
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl border p-8 text-center">
                <Github className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <h3 className="font-semibold mb-1">Connect a GitHub Repository</h3>
                <p className="text-sm text-gray-500 mb-4">
                  Import localization files directly from a GitHub repo
                </p>
                <button
                  onClick={() => setShowGhForm(true)}
                  className="rounded-lg bg-blue-600 text-white px-4 py-2 text-sm font-medium hover:bg-blue-700 transition-colors"
                >
                  Connect Repository
                </button>
              </div>
            )}

            {/* GitHub form */}
            {showGhForm && (
              <div className="bg-white rounded-xl border p-6 space-y-4">
                <h3 className="font-semibold">Repository Settings</h3>

                <div>
                  <label className="block text-sm font-medium mb-1">Repository URL or owner/repo</label>
                  <input
                    value={ghForm.owner ? `${ghForm.owner}/${ghForm.repo}` : ""}
                    onChange={(e) => {
                      const parsed = parseRepoUrl(e.target.value);
                      if (parsed) {
                        setGhForm((f) => ({ ...f, owner: parsed.owner, repo: parsed.repo }));
                      } else {
                        const val = e.target.value;
                        const parts = val.split("/");
                        setGhForm((f) => ({
                          ...f,
                          owner: parts[0] || "",
                          repo: parts[1] || "",
                        }));
                      }
                    }}
                    placeholder="owner/repo or https://github.com/owner/repo"
                    className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Branch</label>
                    <input
                      value={ghForm.branch}
                      onChange={(e) => setGhForm((f) => ({ ...f, branch: e.target.value }))}
                      placeholder="main"
                      className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Base Path</label>
                    <input
                      value={ghForm.base_path}
                      onChange={(e) => setGhForm((f) => ({ ...f, base_path: e.target.value }))}
                      placeholder="src/locales (optional)"
                      className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">File Formats</label>
                  <input
                    value={ghForm.file_patterns}
                    onChange={(e) => setGhForm((f) => ({ ...f, file_patterns: e.target.value }))}
                    placeholder="json, po, xliff (leave empty for auto-detect)"
                    className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">
                    Access Token <span className="text-gray-400 font-normal">(for private repos)</span>
                  </label>
                  <input
                    type="password"
                    value={ghForm.access_token}
                    onChange={(e) => setGhForm((f) => ({ ...f, access_token: e.target.value }))}
                    placeholder="ghp_... (optional)"
                    className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={handleLinkRepo}
                    disabled={ghSaving || !ghForm.owner || !ghForm.repo}
                    className="rounded-lg bg-blue-600 text-white px-4 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    {ghSaving ? "Saving..." : "Save & Connect"}
                  </button>
                  <button
                    onClick={() => setShowGhForm(false)}
                    className="rounded-lg border px-4 py-2 text-sm font-medium hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
