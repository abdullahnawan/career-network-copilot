"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  Contact, OutreachChannel, OutreachDraft, OutreachInput, OutreachPurpose, OutreachSuggestion,
  OutreachTone, contactsApi, formatApiError, outreachApi,
} from "../../lib/api";
import { Layout } from "../../components/Layout";
import { StatusMessage } from "../../components/StatusMessage";
import { Badge, PageHeader, SectionHeader } from "../../components/ui";
import { useAuth } from "../../components/AuthProvider";

const purposes: OutreachPurpose[] = ["informational_interview", "career_advice", "project_collaboration", "internship_question", "general_networking"];
const channels: OutreachChannel[] = ["linkedin_connection_note", "linkedin_message", "email", "other"];
const tones: OutreachTone[] = ["professional", "warm", "concise"];
const CONNECTION_NOTE_LIMIT = 300;
const label = (value: string) => value.replaceAll("_", " ");

export default function OutreachPage() {
  const { profile } = useAuth();
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [contactId, setContactId] = useState("");
  const [purpose, setPurpose] = useState<OutreachPurpose>("informational_interview");
  const [channel, setChannel] = useState<OutreachChannel>("linkedin_message");
  const [tone, setTone] = useState<OutreachTone>("professional");
  const [suggestion, setSuggestion] = useState<OutreachSuggestion | null>(null);
  const [message, setMessage] = useState("");
  const [subject, setSubject] = useState("");
  const [drafts, setDrafts] = useState<OutreachDraft[]>([]);
  const [editingDraft, setEditingDraft] = useState<OutreachDraft | null>(null);
  const [filter, setFilter] = useState("");
  const [purposeFilter, setPurposeFilter] = useState("");
  const [channelFilter, setChannelFilter] = useState("");
  const [status, setStatus] = useState<{ kind: "error" | "success" | "info"; message: string } | null>(null);

  async function loadContacts() {
    try { setContacts((await contactsApi.list({ page: 1, page_size: 100 })).items); }
    catch (error) { setStatus({ kind: "error", message: formatApiError(error, "Unable to load contacts.") }); }
  }
  async function loadDrafts() {
    try { setDrafts((await outreachApi.list({ page: 1, page_size: 50, status: filter, purpose: purposeFilter, channel: channelFilter })).items); }
    catch (error) { setStatus({ kind: "error", message: formatApiError(error, "Unable to load drafts.") }); }
  }
  useEffect(() => {
    const timer = window.setTimeout(() => { void loadContacts(); void loadDrafts(); }, 0);
    return () => window.clearTimeout(timer);
    // The filter is intentionally synchronized with the draft list.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter, purposeFilter, channelFilter]);

  async function generate(event: FormEvent) {
    event.preventDefault();
    const studentProfileId = profile?.id; const contact = Number(contactId);
    if (!studentProfileId || !Number.isInteger(contact) || contact <= 0) {
      setStatus({ kind: "error", message: "Complete your profile and choose a contact." }); return;
    }
    try {
      const result = await outreachApi.suggest({ student_profile_id: studentProfileId, contact_id: contact, purpose, channel, tone });
      setSuggestion(result); setMessage(result.message); setSubject(result.subject ?? "");
      setStatus({ kind: "success", message: "Rule-based suggestion ready for your review." });
    } catch (error) { setStatus({ kind: "error", message: formatApiError(error, "Unable to generate suggestion.") }); }
  }
  async function saveDraft() {
    if (!suggestion || !message.trim() || (
      channel === "linkedin_connection_note" && message.length > CONNECTION_NOTE_LIMIT
    )) return;
    const payload: OutreachInput = {
      student_profile_id: suggestion.student_profile_id, contact_id: suggestion.contact_id,
      purpose, channel, tone, subject: subject.trim() || null, message: message.trim(), user_notes: null,
    };
    try { await outreachApi.create(payload); setStatus({ kind: "success", message: "Draft saved. It has not been sent." }); setSuggestion(null); setMessage(""); await loadDrafts(); }
    catch (error) { setStatus({ kind: "error", message: formatApiError(error, "Unable to save draft.") }); }
  }
  async function action(draft: OutreachDraft, name: "approve" | "copied" | "sent-manually" | "replied" | "archive") {
    if (name === "sent-manually" && !window.confirm("Confirm that you sent this message manually outside Career Network Copilot?")) return;
    if (name === "replied" && !window.confirm("Confirm that this contact replied?")) return;
    if (name === "archive" && !window.confirm("Archive this draft?")) return;
    try {
      if (name === "copied") { await navigator.clipboard.writeText(draft.message); }
      await outreachApi.action(draft.id, name); setStatus({ kind: "success", message: name === "copied" ? "Copied successfully; draft marked copied." : "Draft status updated." }); await loadDrafts();
    } catch (error) { setStatus({ kind: "error", message: formatApiError(error, "Unable to update draft.") }); }
  }
  async function copyLocally(draft: OutreachDraft) {
    try {
      await navigator.clipboard.writeText(draft.message);
      setStatus({ kind: "success", message: "Copied message text to the clipboard." });
    } catch (error) {
      setStatus({ kind: "error", message: formatApiError(error, "Unable to copy message.") });
    }
  }
  async function remove(draft: OutreachDraft) {
    if (!window.confirm("Delete this draft?")) return;
    try { await outreachApi.remove(draft.id); setStatus({ kind: "success", message: "Draft deleted." }); await loadDrafts(); }
    catch (error) { setStatus({ kind: "error", message: formatApiError(error, "Unable to delete draft.") }); }
  }
  async function saveEdit() {
    if (!editingDraft || !editingDraft.message.trim() || (
      editingDraft.channel === "linkedin_connection_note"
      && editingDraft.message.length > CONNECTION_NOTE_LIMIT
    )) return;
    try {
      await outreachApi.update(editingDraft.id, { subject: editingDraft.subject, message: editingDraft.message });
      setEditingDraft(null); setStatus({ kind: "success", message: "Draft updated." }); await loadDrafts();
    } catch (error) { setStatus({ kind: "error", message: formatApiError(error, "Unable to update draft.") }); }
  }
  return <Layout>
    <PageHeader eyebrow="Outreach" title="Human-controlled outreach workspace" description="Career Network Copilot does not send messages. You remain responsible for reviewing and sending outreach manually." />
    {status && <div className="mb-6"><StatusMessage kind={status.kind}>{status.message}</StatusMessage></div>}
    <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
      <form onSubmit={generate} className="surface card-accent-cobalt space-y-4">
        <SectionHeader title="Draft a suggestion" description="Choose the context and tone for a message you will review yourself." />
        <p className="text-sm text-slate-400">Template/rule-based drafting only; no LLM or automatic sending.</p>
        <p className="text-sm text-slate-400">Suggestions use your current profile automatically.</p>
        <label className="block text-sm text-slate-300">Contact<select className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" value={contactId} onChange={(e) => setContactId(e.target.value)}><option value="">Choose a contact</option>{contacts.map((contact) => <option key={contact.id} value={contact.id}>{contact.full_name}</option>)}</select></label>
        <label className="block text-sm text-slate-300">Purpose<select className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" value={purpose} onChange={(e) => setPurpose(e.target.value as OutreachPurpose)}>{purposes.map((item) => <option key={item} value={item}>{label(item)}</option>)}</select></label>
        <label className="block text-sm text-slate-300">Channel<select className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" value={channel} onChange={(e) => setChannel(e.target.value as OutreachChannel)}>{channels.map((item) => <option key={item} value={item}>{label(item)}</option>)}</select></label>
        <label className="block text-sm text-slate-300">Tone<select className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" value={tone} onChange={(e) => setTone(e.target.value as OutreachTone)}>{tones.map((item) => <option key={item} value={item}>{label(item)}</option>)}</select></label>
        <button className="ui-button ui-button-primary w-full" type="submit">Generate suggestion</button>
      </form>
      <section className="space-y-6">
        {suggestion && <article className="surface card-accent-coral"><SectionHeader accent="coral" title="Editable suggestion" description="Refine the wording before saving this draft." /><p className="mt-2 text-sm text-slate-400">{message.length} characters{suggestion.connection_note_limit ? ` · ${suggestion.connection_note_limit}-character connection-note limit` : ""}</p>{channel === "linkedin_connection_note" && message.length > CONNECTION_NOTE_LIMIT && <p className="mt-2 text-sm text-amber-300">This connection note exceeds the 300-character         limit. Shorten it before saving.</p>}{(suggestion.facts_used ?? []).length > 0 && <div className="mt-4"><h3 className="font-semibold text-cyan-200">Facts used</h3><ul className="mt-2 list-disc pl-5 text-sm text-slate-300">{(suggestion.facts_used ?? []).map((fact) => <li key={fact}>{fact}</li>)}</ul></div>}<input aria-label="Subject" className="mt-4 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="Optional email subject" /><textarea aria-label="Message" className="mt-3 min-h-48 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" value={message} onChange={(e) => setMessage(e.target.value)} /><button type="button" disabled={!message.trim() || (channel === "linkedin_connection_note" && message.length > CONNECTION_NOTE_LIMIT)} onClick={() => void saveDraft()} className="mt-3 rounded-lg bg-emerald-300 px-4 py-2 font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-50">Save draft</button></article>}
        {editingDraft && <article className="rounded-2xl border border-cyan-300/30 bg-slate-900/50 p-5"><h2 className="text-xl font-semibold text-white">Edit draft</h2><p className="mt-2 text-sm text-slate-400">{editingDraft.message.length} characters{editingDraft.channel === "linkedin_connection_note" ? " · 300-character connection-note limit" : ""}</p>{editingDraft.channel === "linkedin_connection_note" && editingDraft.message.length > CONNECTION_NOTE_LIMIT && <p className="mt-2 text-sm text-amber-300">This connection note exceeds the 300-character limit. Shorten it before saving.</p>}<input aria-label="Edit subject" className="mt-3 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" value={editingDraft.subject ?? ""} onChange={(e) => setEditingDraft({ ...editingDraft, subject: e.target.value || null })} /><textarea aria-label="Edit message" className="mt-3 min-h-40 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" value={editingDraft.message} onChange={(e) => setEditingDraft({ ...editingDraft, message: e.target.value })} /><div className="mt-3 flex gap-2"><button type="button" disabled={!editingDraft.message.trim() || (editingDraft.channel === "linkedin_connection_note" && editingDraft.message.length > CONNECTION_NOTE_LIMIT)} className="rounded-lg bg-emerald-300 px-4 py-2 font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-50" onClick={() => void saveEdit()}>Save edits</button><button type="button" className="rounded-lg border border-slate-600 px-4 py-2" onClick={() => setEditingDraft(null)}>Cancel</button></div></article>}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5"><div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-xl font-semibold text-white">Drafts</h2><div className="flex flex-wrap gap-2"><select aria-label="Status filter" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm" value={filter} onChange={(e) => setFilter(e.target.value)}><option value="">All statuses</option>{["draft", "approved", "copied", "sent_manually", "replied", "archived"].map((item) => <option key={item} value={item}>{label(item)}</option>)}</select><select aria-label="Purpose filter" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm" value={purposeFilter} onChange={(e) => setPurposeFilter(e.target.value)}><option value="">All purposes</option>{purposes.map((item) => <option key={item} value={item}>{label(item)}</option>)}</select><select aria-label="Channel filter" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm" value={channelFilter} onChange={(e) => setChannelFilter(e.target.value)}><option value="">All channels</option>{channels.map((item) => <option key={item} value={item}>{label(item)}</option>)}</select></div></div>{drafts.length === 0 ? <p className="mt-5 text-slate-400">No outreach drafts yet.</p> : <div className="mt-5 space-y-4">{drafts.map((draft) => <article key={draft.id} className="rounded-xl border border-slate-800 p-4"><div className="flex justify-between gap-3"><h3 className="font-semibold text-white">{draft.subject || "Outreach message"}</h3>        <Badge tone={draft.status === "replied" ? "success" : draft.status === "sent_manually" ? "warning" : draft.status === "approved" ? "info" : "neutral"}>{label(draft.status)}</Badge></div><p className="mt-2 whitespace-pre-wrap text-sm text-slate-300">{draft.message}</p><p className="mt-2 text-xs text-slate-500">{draft.message.length} characters · {label(draft.channel)}</p><div className="mt-3 flex flex-wrap gap-2">{draft.status === "draft" && <><button className="rounded border border-slate-600 px-3 py-1 text-sm" onClick={() => setEditingDraft(draft)}>Edit</button><button className="rounded border border-slate-600 px-3 py-1 text-sm" onClick={() => void action(draft, "approve")}>Approve</button></>}{draft.status === "approved" && <button className="rounded border border-slate-600 px-3 py-1 text-sm" onClick={() => void action(draft, "copied")}>Copy message</button>}{draft.status === "copied" && <><button className="rounded border border-slate-600 px-3 py-1 text-sm" onClick={() => void copyLocally(draft)}>Copy message</button><button className="rounded border border-amber-300/50 px-3 py-1 text-sm text-amber-200" onClick={() => void action(draft, "sent-manually")}>Mark sent manually</button></>}{draft.status === "sent_manually" && <button className="rounded border border-emerald-300/50 px-3 py-1 text-sm text-emerald-200" onClick={() => void action(draft, "replied")}>Mark replied</button>}{draft.status !== "archived" && <button className="rounded border border-slate-600 px-3 py-1 text-sm" onClick={() => void action(draft, "archive")}>Archive</button>}{draft.status === "draft" && <button className="rounded border border-rose-300/50 px-3 py-1 text-sm text-rose-200" onClick={() => void remove(draft)}>Delete</button>}</div></article>)}</div>}</div>
      </section>
    </div>
  </Layout>;
}
