"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  ApplicationAction, ApplicationSource, ApplicationStatus, ApplicationSummary, Contact, FollowUpItem,
  FunnelStats, JobApplication, JobApplicationInput, applicationsApi, contactsApi, followUpsApi, formatApiError,
} from "../../lib/api";
import { Layout } from "../../components/Layout";
import { FormField } from "../../components/FormField";
import { StatusMessage } from "../../components/StatusMessage";
import { Badge, EmptyState, PageHeader, SectionHeader, Surface } from "../../components/ui";

const statuses: ApplicationStatus[] = ["saved", "applied", "online_assessment", "interview", "offer", "rejected", "withdrawn"];
const sources: ApplicationSource[] = ["co_op_board", "company_site", "job_board", "referral", "other"];
const resumeVersions = ["SWE", "Data", "AI/ML"];
const label = (value: string) => value.replaceAll("_", " ");
const percent = (value: number) => `${Math.round(value * 100)}%`;

const nextActions: Record<ApplicationStatus, { action: ApplicationAction; text: string }[]> = {
  saved: [{ action: "apply", text: "Mark applied" }],
  applied: [
    { action: "online-assessment", text: "Got OA" },
    { action: "interview", text: "Got interview" },
    { action: "offer", text: "Got offer" },
    { action: "reject", text: "Rejected" },
  ],
  online_assessment: [{ action: "interview", text: "Got interview" }, { action: "reject", text: "Rejected" }],
  interview: [{ action: "offer", text: "Got offer" }, { action: "reject", text: "Rejected" }],
  offer: [],
  rejected: [],
  withdrawn: [],
};

const emptyApplication: JobApplicationInput = {
  company: "", role_title: "", posting_url: null, location: null, source: "company_site",
  resume_version: null, referral_contact_id: null, deadline: null, notes: null,
};

function badgeTone(status: ApplicationStatus): "neutral" | "success" | "warning" | "info" {
  if (status === "offer") return "success";
  if (status === "interview" || status === "online_assessment") return "warning";
  if (status === "applied") return "info";
  return "neutral";
}

function FunnelRow({ name, stats }: { name: string; stats: FunnelStats }) {
  return (
    <tr className="border-t border-slate-800">
      <th scope="row" className="py-2 pr-4 text-left font-medium text-white">{name}</th>
      <td className="py-2 pr-4 tabular-nums">{stats.applied}</td>
      <td className="py-2 pr-4 tabular-nums">{stats.interview}</td>
      <td className="py-2 pr-4 tabular-nums">{stats.offer}</td>
      <td className="py-2 tabular-nums">{stats.applied ? percent(stats.positive_response_rate) : "–"}</td>
    </tr>
  );
}

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<JobApplication[]>([]);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState<ApplicationSummary | null>(null);
  const [followUps, setFollowUps] = useState<FollowUpItem[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [draft, setDraft] = useState<JobApplicationInput>(emptyApplication);
  const [initialStatus, setInitialStatus] = useState<"saved" | "applied">("applied");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<{ kind: "error" | "success" | "info"; message: string } | null>(null);

  async function loadApplications() {
    try {
      const page = await applicationsApi.list({ page: 1, page_size: 100, status: statusFilter, q: search });
      setApplications(page.items);
      setTotal(page.total);
    } catch (error) { setStatus({ kind: "error", message: formatApiError(error, "Unable to load applications.") }); }
  }
  async function loadInsights() {
    try {
      const [nextSummary, nextFollowUps] = await Promise.all([applicationsApi.summary(), followUpsApi.list()]);
      setSummary(nextSummary);
      setFollowUps(nextFollowUps.items);
    } catch (error) { setStatus({ kind: "error", message: formatApiError(error, "Unable to load insights.") }); }
  }
  async function refresh() { await Promise.all([loadApplications(), loadInsights()]); }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void contactsApi.list({ page: 1, page_size: 100 }).then((page) => setContacts(page.items)).catch(() => setContacts([]));
      void loadInsights();
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => { void loadApplications(); }, 0);
    return () => window.clearTimeout(timer);
    // The list is intentionally synchronized with its filters.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, search]);

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!draft.company.trim() || !draft.role_title.trim()) {
      setStatus({ kind: "error", message: "Add a company and a role." });
      return;
    }
    try {
      if (editingId) await applicationsApi.update(editingId, draft);
      else await applicationsApi.create(draft, initialStatus);
      setStatus({ kind: "success", message: editingId ? "Application updated." : "Application added." });
      setDraft(emptyApplication);
      setEditingId(null);
      await refresh();
    } catch (error) { setStatus({ kind: "error", message: formatApiError(error, "Unable to save application.") }); }
  }

  async function act(application: JobApplication, action: ApplicationAction) {
    if ((action === "reject" || action === "withdraw") && !window.confirm(`Mark ${application.company} as ${action === "reject" ? "rejected" : "withdrawn"}? This closes the application.`)) return;
    try {
      await applicationsApi.action(application.id, action);
      setStatus({ kind: "success", message: "Status updated." });
      await refresh();
    } catch (error) { setStatus({ kind: "error", message: formatApiError(error, "Unable to update status.") }); }
  }

  async function remove(application: JobApplication) {
    if (!window.confirm(`Delete ${application.company}: ${application.role_title}? This cannot be undone.`)) return;
    try {
      await applicationsApi.remove(application.id);
      setStatus({ kind: "success", message: "Application deleted." });
      await refresh();
    } catch (error) { setStatus({ kind: "error", message: formatApiError(error, "Unable to delete application.") }); }
  }

  function startEdit(application: JobApplication) {
    setEditingId(application.id);
    setDraft({
      company: application.company, role_title: application.role_title, posting_url: application.posting_url,
      location: application.location, source: application.source, resume_version: application.resume_version,
      referral_contact_id: application.referral_contact_id, deadline: application.deadline, notes: application.notes,
    });
  }

  const contactName = (id: number | null) => contacts.find((contact) => contact.id === id)?.full_name;
  const funnel = summary?.funnel;

  return <Layout>
    <PageHeader eyebrow="Applications" title="Application pipeline" description="Log the applications you submit yourself and see what is working. Career Network Copilot never applies to jobs or contacts employers for you." />
    {status && <div className="mb-6"><StatusMessage kind={status.kind}>{status.message}</StatusMessage></div>}

    {followUps.length > 0 && <Surface className="card-accent-yellow mb-6">
      <SectionHeader accent="yellow" title="Follow-ups due" description="Applications without a response, outreach without a reply, and deadlines coming up." />
      <ul className="mt-2 space-y-3">
        {followUps.map((item) => <li key={`${item.kind}-${item.application_id ?? item.outreach_draft_id}`} className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
          <span className="font-semibold text-white">{item.title}</span>
          <span className="text-sm text-slate-400">{item.detail}</span>
        </li>)}
      </ul>
    </Surface>}

    {funnel && <Surface className="card-accent-cobalt mb-6">
      <SectionHeader title="Funnel" description={`${summary.total} tracked · positive response means an OA, interview or offer.`} />
      <div className="score-grid">
        <div className="score-detail"><span className="metadata-label">Applied</span><strong className="tabular-nums">{funnel.applied}</strong></div>
        <div className="score-detail"><span className="metadata-label">OA</span><strong className="tabular-nums">{funnel.online_assessment}</strong></div>
        <div className="score-detail"><span className="metadata-label">Interview</span><strong className="tabular-nums">{funnel.interview}</strong></div>
        <div className="score-detail"><span className="metadata-label">Offer</span><strong className="tabular-nums">{funnel.offer}</strong></div>
        <div className="score-detail"><span className="metadata-label">Positive response</span><strong className="tabular-nums">{funnel.applied ? percent(funnel.positive_response_rate) : "–"}</strong></div>
      </div>
      {funnel.applied > 0 && <div className="mt-5 overflow-x-auto">
        <table className="w-full text-sm text-slate-300">
          <caption className="sr-only">Funnel by resume version and referral</caption>
          <thead><tr className="text-left text-xs uppercase tracking-wide text-slate-400"><th className="pb-2 pr-4">Segment</th><th className="pb-2 pr-4">Applied</th><th className="pb-2 pr-4">Interview</th><th className="pb-2 pr-4">Offer</th><th className="pb-2">Positive response</th></tr></thead>
          <tbody>
            {Object.entries(summary.by_resume_version).filter(([, stats]) => stats.applied > 0).map(([name, stats]) => <FunnelRow key={name} name={`Resume: ${name}`} stats={stats} />)}
            <FunnelRow name="With referral" stats={summary.referral} />
            <FunnelRow name="Cold" stats={summary.cold} />
          </tbody>
        </table>
      </div>}
    </Surface>}

    <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
      <aside>
        <Surface as="div" className="card-accent-coral">
          <form onSubmit={save}>
            <SectionHeader accent="coral" title={editingId ? "Edit application" : "Add application"} description="Quick to log, so tracking never slows down applying." />
            <div className="space-y-4">
              <FormField label="Company" name="app-company" value={draft.company} required onChange={(value) => setDraft({ ...draft, company: value })} />
              <FormField label="Role" name="app-role" value={draft.role_title} required onChange={(value) => setDraft({ ...draft, role_title: value })} />
              <FormField label="Posting link" name="app-url" value={draft.posting_url ?? ""} placeholder="https://" onChange={(value) => setDraft({ ...draft, posting_url: value })} />
              <FormField label="Location" name="app-location" value={draft.location ?? ""} onChange={(value) => setDraft({ ...draft, location: value })} />
              <label className="block text-sm text-slate-300">Source<select className="form-control mt-1 w-full rounded-lg border px-3 py-2" value={draft.source} onChange={(e) => setDraft({ ...draft, source: e.target.value as ApplicationSource })}>{sources.map((item) => <option key={item} value={item}>{label(item)}</option>)}</select></label>
              <label className="block text-sm text-slate-300">Resume version<input list="resume-versions" className="form-control mt-1 w-full rounded-lg border px-3 py-2" value={draft.resume_version ?? ""} onChange={(e) => setDraft({ ...draft, resume_version: e.target.value })} /></label>
              <datalist id="resume-versions">{resumeVersions.map((item) => <option key={item} value={item} />)}</datalist>
              <label className="block text-sm text-slate-300">Referral contact<select className="form-control mt-1 w-full rounded-lg border px-3 py-2" value={draft.referral_contact_id ?? ""} onChange={(e) => setDraft({ ...draft, referral_contact_id: e.target.value ? Number(e.target.value) : null })}><option value="">None</option>{contacts.map((contact) => <option key={contact.id} value={contact.id}>{contact.full_name}</option>)}</select></label>
              <FormField label="Deadline" name="app-deadline" type="date" value={draft.deadline ?? ""} onChange={(value) => setDraft({ ...draft, deadline: value })} />
              <label className="block text-sm text-slate-300">Notes<textarea className="form-control mt-1 min-h-20 w-full rounded-lg border px-3 py-2" value={draft.notes ?? ""} onChange={(e) => setDraft({ ...draft, notes: e.target.value })} /></label>
              {!editingId && <label className="block text-sm text-slate-300">Starting status<select className="form-control mt-1 w-full rounded-lg border px-3 py-2" value={initialStatus} onChange={(e) => setInitialStatus(e.target.value as "saved" | "applied")}><option value="applied">applied</option><option value="saved">saved (not applied yet)</option></select></label>}
              <button className="ui-button ui-button-primary w-full" type="submit">{editingId ? "Save changes" : "Add application"}</button>
              {editingId && <button type="button" onClick={() => { setEditingId(null); setDraft(emptyApplication); }} className="w-full text-sm text-slate-400 hover:text-white">Cancel editing</button>}
            </div>
          </form>
        </Surface>
      </aside>

      <section>
        <div className="toolbar mb-4 grid gap-3 sm:grid-cols-2">
          <input aria-label="Search applications" placeholder="Search company or role" className="form-control rounded-lg border px-3 py-2" value={search} onChange={(e) => setSearch(e.target.value)} />
          <select aria-label="Status filter" className="form-control rounded-lg border px-3 py-2" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}><option value="">All statuses</option>{statuses.map((item) => <option key={item} value={item}>{label(item)}</option>)}</select>
        </div>
        <div className="contact-list overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/50">
          {applications.length === 0 ? <EmptyState title="No applications yet.">Add the first one you send. Logging takes under a minute.</EmptyState> : <div className="divide-y divide-slate-800">
            {applications.map((application) => <article key={application.id} className="p-5">
              <div className="flex flex-col justify-between gap-3 sm:flex-row">
                <div>
                  <h2>{application.company}</h2>
                  <p className="identity-line">{application.role_title}</p>
                  <p className="metadata-line">{[
                    application.location,
                    label(application.source),
                    application.resume_version && `Resume: ${application.resume_version}`,
                    contactName(application.referral_contact_id) && `Referral: ${contactName(application.referral_contact_id)}`,
                    application.applied_at && `Applied ${new Date(application.applied_at).toLocaleDateString()}`,
                    application.deadline && application.status === "saved" && `Deadline ${application.deadline}`,
                  ].filter(Boolean).join(" · ")}</p>
                  {application.notes && <p className="mt-2 whitespace-pre-wrap text-sm text-slate-300">{application.notes}</p>}
                </div>
                <div><Badge tone={badgeTone(application.status)}>{label(application.status)}</Badge></div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2 text-sm">
                {nextActions[application.status].map((next) => <button key={next.action} className="rounded border border-slate-600 px-3 py-1" onClick={() => void act(application, next.action)}>{next.text}</button>)}
                {application.status !== "rejected" && application.status !== "withdrawn" && <button className="rounded border border-slate-600 px-3 py-1" onClick={() => void act(application, "withdraw")}>Withdraw</button>}
                {application.posting_url && <a className="rounded border border-slate-600 px-3 py-1" href={application.posting_url} target="_blank" rel="noreferrer noopener">Posting</a>}
                <button className="rounded border border-slate-600 px-3 py-1" onClick={() => startEdit(application)}>Edit</button>
                <button className="rounded border border-rose-300/50 px-3 py-1 text-rose-200" onClick={() => void remove(application)}>Delete</button>
              </div>
            </article>)}
          </div>}
        </div>
        <p className="mt-4 text-sm text-slate-400">{total} application(s)</p>
      </section>
    </div>
  </Layout>;
}
