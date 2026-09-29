"use client";

import { FormEvent, useState } from "react";
import { ContactMatch, formatApiError, profileApi } from "../../lib/api";
import { FormField } from "../../components/FormField";
import { Layout } from "../../components/Layout";
import { StatusMessage } from "../../components/StatusMessage";

export default function MatchesPage() {
  const [profileId, setProfileId] = useState("");
  const [matches, setMatches] = useState<ContactMatch[]>([]);
  const [status, setStatus] = useState<{ kind: "error" | "success" | "info"; message: string } | null>(null);
  const [loading, setLoading] = useState(false);
  async function loadMatches(event: FormEvent) {
    event.preventDefault();
    const id = Number(profileId);
    if (!Number.isInteger(id) || id <= 0) { setStatus({ kind: "error", message: "Enter a valid numeric profile ID." }); return; }
    setLoading(true); setStatus({ kind: "info", message: "Calculating transparent rule-based matches..." });
    try { const result = await profileApi.matches(id); setMatches(result); setStatus({ kind: "success", message: `Ranked ${result.length} contact(s) using deterministic overlap rules.` }); }
    catch (error) { setStatus({ kind: "error", message: formatApiError(error, "Unable to calculate matches.") }); }
    finally { setLoading(false); }
  }
  return <Layout><div className="mb-8"><p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">Phase 4 · Matches</p><h1 className="mt-3 text-4xl font-semibold text-white">Explainable opportunities</h1><p className="mt-3 max-w-2xl text-slate-300">These rankings use deterministic field overlap only. They are not AI-generated endorsements.</p></div><form onSubmit={loadMatches} className="mb-6 flex max-w-md items-end gap-3"><div className="flex-1"><FormField label="Student profile ID" name="match-profile-id" value={profileId} onChange={setProfileId} type="number" /></div><button type="submit" className="rounded-lg bg-cyan-300 px-5 py-2.5 font-semibold text-slate-950">Find matches</button></form>{status && <div className="mb-6"><StatusMessage kind={status.kind}>{status.message}</StatusMessage></div>}{loading ? <p className="text-slate-400">Calculating matches...</p> : matches.length === 0 ? <p className="rounded-2xl border border-dashed border-slate-700 p-8 text-slate-400">Enter a profile ID to see ranked contacts.</p> : <div className="space-y-4">{matches.map((match) => <article key={match.contact.id} className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6"><div className="flex flex-col justify-between gap-4 sm:flex-row"><div><h2 className="text-xl font-semibold text-white">{match.contact.full_name}</h2><p className="text-cyan-200">{match.contact.current_role || "Role not provided"}{match.contact.company ? ` · ${match.contact.company}` : ""}</p></div><div className="text-3xl font-semibold text-cyan-200">{match.total_score}%</div></div><div className="mt-5 grid gap-2 text-sm text-slate-300 sm:grid-cols-5">{Object.entries(match.breakdown).map(([key, value]) => <div key={key} className="rounded-lg bg-slate-800/70 p-3"><span className="block capitalize text-slate-400">{key}</span><strong>{value}%</strong></div>)}</div><ul className="mt-5 list-disc space-y-1 pl-5 text-sm text-slate-300">{match.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul></article>)}</div>}</Layout>;
}
