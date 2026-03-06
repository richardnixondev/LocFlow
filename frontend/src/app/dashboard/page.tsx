"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  getProjects,
  createProject,
  deleteProject,
  linkGitHubRepo,
  syncGitHubRepo,
} from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import {
  Plus,
  FolderOpen,
  Trash2,
  Languages,
  Github,
  Loader2,
  CheckCircle2,
  XCircle,
} from "lucide-react";

interface Project {
  id: string;
  name: string;
  slug: string;
  description: string;
  source_language: string;
  created_at: string;
  github_repo?: {
    full_name: string;
    last_sync_status: string;
  } | null;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newLang, setNewLang] = useState("en");
  const [newRepoUrl, setNewRepoUrl] = useState("");
  const [creating, setCreating] = useState(false);
  const [createStep, setCreateStep] = useState("");
  const [toast, setToast] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const canManage = user?.role === "admin" || user?.role === "manager";

  async function load() {
    try {
      const data = await getProjects();
      setProjects(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 6000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  function parseRepoUrl(input: string) {
    const match = input
      .trim()
      .match(
        /(?:https?:\/\/)?(?:github\.com\/)?([^/\s]+)\/([^/\s#?]+)/
      );
    if (match) {
      return { owner: match[1], repo: match[2].replace(/\.git$/, "") };
    }
    return null;
  }

  async function handleCreate() {
    if (!newName.trim()) return;
    setCreating(true);
    setCreateStep("Creating project...");

    try {
      const project = await createProject({
        name: newName,
        description: newDesc,
        source_language: newLang,
      });

      if (newRepoUrl.trim()) {
        const parsed = parseRepoUrl(newRepoUrl);
        if (parsed) {
          setCreateStep("Connecting GitHub repository...");
          await linkGitHubRepo(project.slug, {
            owner: parsed.owner,
            repo: parsed.repo,
          });

          setCreateStep("Syncing resource files...");
          const syncResult = await syncGitHubRepo(project.slug);

          if (syncResult.errors?.length > 0 && syncResult.files_synced === 0) {
            setToast({
              type: "error",
              message: `Project created but sync failed: ${syncResult.errors[0]?.error || "Unknown error"}. Check repository settings in the project GitHub tab.`,
            });
          } else if (syncResult.files_synced > 0) {
            setToast({
              type: "success",
              message: `Project created! Imported ${syncResult.files_synced} file(s) from ${parsed.owner}/${parsed.repo}.`,
            });
          } else {
            setToast({
              type: "error",
              message: `Project created and linked to ${parsed.owner}/${parsed.repo}, but no localization files (.json, .po, .strings, .xliff) were found. Check the GitHub tab in project settings to adjust the path or file patterns.`,
            });
          }
        } else {
          setToast({
            type: "error",
            message:
              'Project created, but the repository URL could not be parsed. Use the format "owner/repo" or a full GitHub URL.',
          });
        }
      } else {
        setToast({
          type: "success",
          message: "Project created successfully!",
        });
      }

      setNewName("");
      setNewDesc("");
      setNewLang("en");
      setNewRepoUrl("");
      setShowCreate(false);
      setCreateStep("");
      load();
    } catch (err: unknown) {
      const message =
        err &&
        typeof err === "object" &&
        "response" in err &&
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail
          ? (err as { response: { data: { detail: string } } }).response.data
              .detail
          : "Failed to create project.";
      setToast({ type: "error", message });
    } finally {
      setCreating(false);
      setCreateStep("");
    }
  }

  async function handleDelete(slug: string) {
    if (!confirm("Delete this project? This action cannot be undone.")) return;
    await deleteProject(slug);
    load();
  }

  return (
    <div>
      {/* Toast notification */}
      {toast && (
        <div
          className={`mb-6 rounded-lg border px-4 py-3 text-sm flex items-start gap-3 ${
            toast.type === "success"
              ? "bg-green-50 border-green-200 text-green-800"
              : "bg-red-50 border-red-200 text-red-800"
          }`}
        >
          {toast.type === "success" ? (
            <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" />
          ) : (
            <XCircle className="h-4 w-4 mt-0.5 shrink-0" />
          )}
          <span className="flex-1">{toast.message}</span>
          <button
            onClick={() => setToast(null)}
            className="shrink-0 opacity-60 hover:opacity-100"
          >
            &times;
          </button>
        </div>
      )}

      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Projects</h1>
          <p className="text-gray-500 text-sm mt-1">
            Manage your localization projects
          </p>
        </div>
        {canManage && (
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 rounded-lg bg-blue-600 text-white px-4 py-2 text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            New Project
          </button>
        )}
      </div>

      {showCreate && (
        <div className="bg-white rounded-xl border shadow-sm p-6 mb-6 space-y-4">
          <h3 className="font-semibold">Create Project</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name</label>
              <input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="My App"
                className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Source Language
              </label>
              <input
                value={newLang}
                onChange={(e) => setNewLang(e.target.value)}
                placeholder="en"
                className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Description
            </label>
            <textarea
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              rows={2}
              className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1 flex items-center gap-1.5">
              <Github className="h-3.5 w-3.5" />
              GitHub Repository
              <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <input
              value={newRepoUrl}
              onChange={(e) => setNewRepoUrl(e.target.value)}
              placeholder="https://github.com/owner/repo or owner/repo"
              className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-400 mt-1">
              Resource files will be automatically detected and imported. You can
              adjust branch and path in the project settings.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleCreate}
              disabled={creating}
              className="rounded-lg bg-blue-600 text-white px-4 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center gap-2"
            >
              {creating && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              {creating ? createStep || "Creating..." : "Create"}
            </button>
            <button
              onClick={() => setShowCreate(false)}
              disabled={creating}
              className="rounded-lg border px-4 py-2 text-sm font-medium hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border">
          <FolderOpen className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No projects yet</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => (
            <div
              key={project.id}
              className="bg-white rounded-xl border shadow-sm hover:shadow-md transition-shadow"
            >
              <Link href={`/projects/${project.slug}`} className="block p-6">
                <div className="flex items-start justify-between">
                  <div className="min-w-0">
                    <h3 className="font-semibold truncate">{project.name}</h3>
                    <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                      {project.description || "No description"}
                    </p>
                  </div>
                  <div className="flex items-center gap-1 text-xs bg-gray-100 rounded-full px-2 py-1 ml-2 shrink-0">
                    <Languages className="h-3 w-3" />
                    {project.source_language}
                  </div>
                </div>
                <div className="flex items-center gap-3 mt-4">
                  {project.github_repo && (
                    <span className="flex items-center gap-1 text-xs text-gray-500">
                      <Github className="h-3 w-3" />
                      {project.github_repo.full_name}
                    </span>
                  )}
                  <span className="text-xs text-gray-400">
                    {new Date(project.created_at).toLocaleDateString()}
                  </span>
                </div>
              </Link>
              {canManage && (
                <div className="border-t px-6 py-3">
                  <button
                    onClick={() => handleDelete(project.slug)}
                    className="text-sm text-red-500 hover:text-red-700 flex items-center gap-1 transition-colors"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Delete
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
