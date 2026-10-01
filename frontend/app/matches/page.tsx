"use client";

import { FormEvent, useState } from "react";
import { ContactMatch, formatApiError, profileApi } from "../../lib/api";
import { FormField } from "../../components/FormField";
import { Layout } from "../../components/Layout";
import { StatusMessage } from "../../components/StatusMessage";
import { Badge, EmptyState, PageHeader, Score, SectionHeader } from "../../components/ui";

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
  return (
    <Layout>
      <PageHeader eyebrow="Matches" title="Explainable opportunities" description="These rankings use deterministic field overlap only. They are not AI-generated endorsements." />
      <section className="surface card-accent-cobalt mb-6">
        <SectionHeader title="Find relevant contacts" description="Choose a profile to compare against your saved contact directory." />
        <form onSubmit={loadMatches} className="flex max-w-md items-end gap-3">
          <div className="flex-1"><FormField label="Student profile ID" name="match-profile-id" value={profileId} onChange={setProfileId} type="number" /></div>
          <button type="submit" className="ui-button ui-button-primary">Find matches</button>
        </form>
      </section>
      {status && <div className="mb-6"><StatusMessage kind={status.kind}>{status.message}</StatusMessage></div>}
      {loading ? <p className="helper-text">Calculating matches...</p> : matches.length === 0 ? <EmptyState title="No ranked contacts yet">Enter a profile ID to see transparent, rule-based results.</EmptyState> : (
        <div className="space-y-4">
          {matches.map((match, index) => (
            <article key={match.contact.id} className="surface card-accent-cobalt">
              <div className="flex flex-col justify-between gap-5 sm:flex-row">
                <div className="flex gap-4">
                  <div className="rank-marker tabular-nums" aria-label={`Rank ${index + 1}`}>{index + 1}</div>
                  <div><h2 className="card-title">{match.contact.full_name}</h2><p className="identity-line">{match.contact.current_role || "Role not provided"}{match.contact.company ? ` · ${match.contact.company}` : ""}</p><p className="metadata-line">{[match.contact.industry, match.contact.location, match.contact.school].filter(Boolean).join(" · ") || "No additional details"}</p></div>
                </div>
                <Score value={match.total_score} />
              </div>
              <div className="score-grid mt-6">{Object.entries(match.breakdown).map(([key, value]) => <div key={key} className="score-detail"><span className="metadata-label">{key.replaceAll("_", " ")}</span><strong className="tabular-nums">{value}%</strong></div>)}</div>
              <div className="reason-panel mt-5"><h3>Why this matches</h3><ul>{match.reasons.map((reason) => <li key={reason}><Badge tone="info">Match reason</Badge><span>{reason}</span></li>)}</ul></div>
            </article>
          ))}
        </div>
      )}
    </Layout>
  );
}
