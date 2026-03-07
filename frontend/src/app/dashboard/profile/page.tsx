"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { updateProfile, changePassword } from "@/lib/api";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";

export default function ProfilePage() {
  const { user, refresh } = useAuth();

  const [firstName, setFirstName] = useState(user?.first_name ?? "");
  const [lastName, setLastName] = useState(user?.last_name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [saving, setSaving] = useState(false);

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [changingPw, setChangingPw] = useState(false);

  const [toast, setToast] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  function showToast(type: "success" | "error", message: string) {
    setToast({ type, message });
    setTimeout(() => setToast(null), 5000);
  }

  function extractError(err: unknown): string {
    if (
      err &&
      typeof err === "object" &&
      "response" in err &&
      (err as { response?: { data?: Record<string, unknown> } }).response?.data
    ) {
      const data = (err as { response: { data: Record<string, unknown> } })
        .response.data;
      const first = Object.values(data)[0];
      if (Array.isArray(first)) return String(first[0]);
      if (typeof first === "string") return first;
    }
    return "Something went wrong.";
  }

  async function handleProfileSave() {
    setSaving(true);
    try {
      await updateProfile({
        first_name: firstName,
        last_name: lastName,
        email,
      });
      await refresh();
      showToast("success", "Profile updated successfully.");
    } catch (err) {
      showToast("error", extractError(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleChangePassword() {
    setChangingPw(true);
    try {
      await changePassword({
        old_password: oldPassword,
        new_password: newPassword,
        new_password_confirm: confirmPassword,
      });
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
      showToast("success", "Password changed successfully.");
    } catch (err) {
      showToast("error", extractError(err));
    } finally {
      setChangingPw(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-1">Profile</h1>
      <p className="text-gray-500 text-sm mb-8">
        Manage your account settings
      </p>

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

      {/* Profile Info */}
      <div className="bg-white rounded-xl border shadow-sm p-6 mb-6">
        <h2 className="font-semibold mb-4">Personal Information</h2>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Username</label>
              <input
                value={user?.username ?? ""}
                disabled
                className="w-full rounded-lg border bg-gray-50 px-3 py-2 text-sm text-gray-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Role</label>
              <input
                value={user?.role ?? ""}
                disabled
                className="w-full rounded-lg border bg-gray-50 px-3 py-2 text-sm text-gray-500 capitalize"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                First Name
              </label>
              <input
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Last Name
              </label>
              <input
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={handleProfileSave}
            disabled={saving}
            className="rounded-lg bg-blue-600 text-white px-4 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center gap-2"
          >
            {saving && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Save Changes
          </button>
        </div>
      </div>

      {/* Change Password */}
      <div className="bg-white rounded-xl border shadow-sm p-6">
        <h2 className="font-semibold mb-4">Change Password</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Current Password
            </label>
            <input
              type="password"
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
              className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              New Password
            </label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Confirm New Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={handleChangePassword}
            disabled={changingPw || !oldPassword || !newPassword || !confirmPassword}
            className="rounded-lg bg-blue-600 text-white px-4 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center gap-2"
          >
            {changingPw && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Change Password
          </button>
        </div>
      </div>
    </div>
  );
}
