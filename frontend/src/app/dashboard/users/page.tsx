"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { getUsers, createUser, updateUser, type UserData } from "@/lib/api";
import { Loader2, CheckCircle2, XCircle, Users, Plus } from "lucide-react";

const ROLES = ["admin", "manager", "translator", "viewer"];

const roleBadge: Record<string, string> = {
  admin: "bg-red-100 text-red-700",
  manager: "bg-blue-100 text-blue-700",
  translator: "bg-green-100 text-green-700",
  viewer: "bg-gray-100 text-gray-600",
};

export default function UsersPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [users, setUsers] = useState<UserData[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newUser, setNewUser] = useState({
    username: "",
    email: "",
    password: "",
    role: "viewer",
    first_name: "",
    last_name: "",
  });
  const [toast, setToast] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  useEffect(() => {
    if (user && user.role !== "admin") {
      router.replace("/dashboard");
    }
  }, [user, router]);

  async function load() {
    try {
      const data = await getUsers();
      setUsers(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (user?.role === "admin") load();
  }, [user]);

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  function extractError(err: unknown): string {
    if (
      err &&
      typeof err === "object" &&
      "response" in err &&
      (err as { response?: { data?: Record<string, unknown> } }).response?.data
    ) {
      const data = (err as { response: { data: Record<string, unknown> } })
        .response.data;
      const values = Object.values(data).flat();
      return values.map(String).join(" ");
    }
    return "Something went wrong.";
  }

  async function handleCreate() {
    if (!newUser.username.trim() || !newUser.email.trim() || !newUser.password.trim()) return;
    setCreating(true);
    try {
      const created = await createUser(newUser);
      setUsers((prev) => [created, ...prev]);
      setNewUser({ username: "", email: "", password: "", role: "viewer", first_name: "", last_name: "" });
      setShowCreate(false);
      setToast({ type: "success", message: `User "${created.username}" created.` });
    } catch (err) {
      setToast({ type: "error", message: extractError(err) });
    } finally {
      setCreating(false);
    }
  }

  async function handleUpdate(
    id: string,
    body: { role?: string; is_active?: boolean }
  ) {
    setUpdating(id);
    try {
      const updated = await updateUser(id, body);
      setUsers((prev) => prev.map((u) => (u.id === id ? updated : u)));
      setToast({ type: "success", message: "User updated." });
    } catch (err) {
      setToast({ type: "error", message: extractError(err) });
    } finally {
      setUpdating(null);
    }
  }

  if (user?.role !== "admin") return null;

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Users</h1>
          <p className="text-gray-500 text-sm mt-1">
            Manage user accounts and roles
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 rounded-lg bg-blue-600 text-white px-4 py-2 text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          New User
        </button>
      </div>

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

      {showCreate && (
        <div className="bg-white rounded-xl border shadow-sm p-6 mb-6 space-y-4">
          <h3 className="font-semibold">Create User</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Username</label>
              <input
                value={newUser.username}
                onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Email</label>
              <input
                type="email"
                value={newUser.email}
                onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">First Name</label>
              <input
                value={newUser.first_name}
                onChange={(e) => setNewUser({ ...newUser, first_name: e.target.value })}
                className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Last Name</label>
              <input
                value={newUser.last_name}
                onChange={(e) => setNewUser({ ...newUser, last_name: e.target.value })}
                className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Password</label>
              <input
                type="password"
                value={newUser.password}
                onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Role</label>
              <select
                value={newUser.role}
                onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 capitalize"
              >
                {ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleCreate}
              disabled={creating}
              className="rounded-lg bg-blue-600 text-white px-4 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center gap-2"
            >
              {creating && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              {creating ? "Creating..." : "Create"}
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
      ) : users.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border">
          <Users className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No users found</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50 text-left">
                <th className="px-4 py-3 font-medium">Username</th>
                <th className="px-4 py-3 font-medium">Email</th>
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Role</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Joined</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const isSelf = u.id === user?.id;
                return (
                  <tr key={u.id} className="border-b last:border-0">
                    <td className="px-4 py-3 font-medium">{u.username}</td>
                    <td className="px-4 py-3 text-gray-600">{u.email}</td>
                    <td className="px-4 py-3 text-gray-600">
                      {[u.first_name, u.last_name].filter(Boolean).join(" ") ||
                        "-"}
                    </td>
                    <td className="px-4 py-3">
                      {isSelf ? (
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium capitalize ${
                            roleBadge[u.role] ?? roleBadge.viewer
                          }`}
                        >
                          {u.role}
                        </span>
                      ) : (
                        <select
                          value={u.role}
                          disabled={updating === u.id}
                          onChange={(e) =>
                            handleUpdate(u.id, { role: e.target.value })
                          }
                          className="rounded border px-2 py-1 text-xs capitalize focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          {ROLES.map((r) => (
                            <option key={r} value={r}>
                              {r}
                            </option>
                          ))}
                        </select>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {isSelf ? (
                        <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                          Active
                        </span>
                      ) : (
                        <button
                          disabled={updating === u.id}
                          onClick={() =>
                            handleUpdate(u.id, { is_active: !u.is_active })
                          }
                          className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium cursor-pointer transition-colors ${
                            u.is_active
                              ? "bg-green-100 text-green-700 hover:bg-green-200"
                              : "bg-red-100 text-red-700 hover:bg-red-200"
                          }`}
                        >
                          {updating === u.id ? (
                            <Loader2 className="h-3 w-3 animate-spin inline" />
                          ) : u.is_active ? (
                            "Active"
                          ) : (
                            "Inactive"
                          )}
                        </button>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {new Date(u.date_joined).toLocaleDateString()}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
