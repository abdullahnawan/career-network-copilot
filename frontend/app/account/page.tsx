"use client";
import { useState } from "react";
import { Layout } from "../../components/Layout";
import { useAuth } from "../../components/AuthProvider";
import { accountApi, formatApiError } from "../../lib/api";
import { StatusMessage } from "../../components/StatusMessage";
import { Button, PageHeader, Surface, useConfirmation } from "../../components/ui";

export default function AccountPage() {
  const { user } = useAuth();
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { confirm, dialog } = useConfirmation();
  async function downloadExport() {
    try {
      const data = await accountApi.export();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url; link.download = "career-network-copilot-export.json"; link.click();
      URL.revokeObjectURL(url); setStatus("Your data export is ready.");
    } catch (issue) { setError(formatApiError(issue, "Unable to export your data.")); }
  }
  async function deleteAccount() {
    if (!password || !(await confirm("Delete account permanently?", "This permanently deletes your account and all owned data.", "Delete account"))) return;
    try { await accountApi.delete(password); window.location.assign("/login"); }
    catch (issue) { setError(formatApiError(issue, "Unable to delete your account.")); }
  }
  return <Layout><PageHeader eyebrow="Account" title="Your account" description="Manage your identity, privacy, and the information connected to your private workspace." />
    {status && <StatusMessage kind="success">{status}</StatusMessage>}{error && <StatusMessage kind="error">{error}</StatusMessage>}
    <div className="space-y-6">
      <Surface className="card-accent-cobalt max-w-xl"><h2>Account details</h2><dl className="mt-5 space-y-4"><div><dt className="metadata-label">Name</dt><dd className="data-value">{user?.display_name || "Not provided"}</dd></div><div><dt className="metadata-label">Email</dt><dd className="data-value">{user?.email}</dd></div></dl></Surface>
      <Surface className="card-accent-yellow max-w-xl"><h2>Privacy controls</h2><p className="mt-2 text-sm text-slate-400">Your export includes your profile, goals, skills, contacts, and outreach drafts. Password hashes and session secrets are never included.</p><Button variant="secondary" className="mt-5" onClick={() => void downloadExport()}>Download personal data</Button></Surface>
      <Surface className="card-accent-coral max-w-xl"><h2>Delete account</h2><p className="mt-2 text-sm text-slate-400">This permanently deletes your account and owned data. Enter your password to continue.</p><label className="form-label mt-5" htmlFor="delete-password">Password</label><input id="delete-password" type="password" className="form-control w-full rounded-lg px-3 py-2.5" value={password} onChange={(event) => setPassword(event.target.value)} /><Button variant="danger" className="mt-5" onClick={() => void deleteAccount()}>Permanently delete account</Button></Surface>
    </div>{dialog}
  </Layout>;
}
