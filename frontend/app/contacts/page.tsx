"use client";

import { FormEvent, useEffect, useState } from "react";
import { Contact, ContactInput, contactsApi, formatApiError } from "../../lib/api";
import { FormField } from "../../components/FormField";
import { Layout } from "../../components/Layout";
import { StatusMessage } from "../../components/StatusMessage";
import { PageHeader, SectionHeader, Surface, EmptyState } from "../../components/ui";

const emptyContact: ContactInput = {
  full_name: "", current_role: "", company: "", industry: "", location: "",
  school: "", skills_summary: "", profile_url: "", source_type: "manual", source_name: "User entered", notes: "",
};

export default function ContactsPage() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({ q: "", role: "", company: "", industry: "", location: "", school: "" });
  const [draft, setDraft] = useState<ContactInput>(emptyContact);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<{ kind: "error" | "success" | "info"; message: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const pageSize = 10;

  async function loadContacts() {
    setLoading(true);
    try {
      const result = await contactsApi.list({ ...filters, page, page_size: pageSize });
      setContacts(result.items);
      setTotal(result.total);
    } catch (error) {
      setStatus({ kind: "error", message: formatApiError(error, "Unable to load contacts.") });
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    const timer = window.setTimeout(() => { void loadContacts(); }, 0);
    return () => window.clearTimeout(timer);
    // Filters are intentionally applied as the user types.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, filters]);

  async function saveContact(event: FormEvent) {
    event.preventDefault();
    setStatus({ kind: "info", message: "Saving contact..." });
    try {
      if (!draft.full_name.trim()) throw new Error("Full name is required.");
      if (editingId) await contactsApi.update(editingId, draft);
      else await contactsApi.create(draft);
      setDraft(emptyContact); setEditingId(null);
      setStatus({ kind: "success", message: "Contact saved." });
      await loadContacts();
    } catch (error) {
      setStatus({ kind: "error", message: formatApiError(error, "Unable to save contact.") });
    }
  }

  async function removeContact(id: number) {
    if (!window.confirm("Delete this contact? This cannot be undone.")) return;
    try {
      await contactsApi.remove(id);
      setStatus({ kind: "success", message: "Contact deleted." });
      await loadContacts();
    } catch (error) {
      setStatus({ kind: "error", message: formatApiError(error, "Unable to delete contact.") });
    }
  }

  async function importCsv() {
    if (!file) return;
    try {
      const result = await contactsApi.importCsv(file);
      setStatus({ kind: result.errors.length ? "info" : "success", message: `Imported ${result.created} contact(s). ${result.errors.length} row error(s).` });
      await loadContacts();
    } catch (error) {
      setStatus({ kind: "error", message: formatApiError(error, "Unable to import CSV.") });
    }
  }

  return (
    <Layout>
      <PageHeader eyebrow="Contact directory" title="Your permitted contacts" description="Keep a clear, user-supplied directory. Profile links are stored as references only and are never fetched." />
      {status && <div className="mb-6"><StatusMessage kind={status.kind}>{status.message}</StatusMessage></div>}
      <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
        <aside className="space-y-6">
          <Surface as="div" className="card-accent-coral">
          <form onSubmit={saveContact}>
            <SectionHeader accent="coral" title={editingId ? "Edit contact" : "Add contact"} description="Keep the details you have permission to use." />
            <div className="space-y-4">
              <FormField label="Full name" name="contact-name" value={draft.full_name} required onChange={(value) => setDraft({ ...draft, full_name: value })} />
              <FormField label="Current role" name="contact-role" value={draft.current_role ?? ""} onChange={(value) => setDraft({ ...draft, current_role: value })} />
              <FormField label="Company" name="contact-company" value={draft.company ?? ""} onChange={(value) => setDraft({ ...draft, company: value })} />
              <FormField label="Industry" name="contact-industry" value={draft.industry ?? ""} onChange={(value) => setDraft({ ...draft, industry: value })} />
              <FormField label="Location" name="contact-location" value={draft.location ?? ""} onChange={(value) => setDraft({ ...draft, location: value })} />
              <FormField label="School" name="contact-school" value={draft.school ?? ""} onChange={(value) => setDraft({ ...draft, school: value })} />
              <FormField label="Skills summary" name="contact-skills" value={draft.skills_summary ?? ""} onChange={(value) => setDraft({ ...draft, skills_summary: value })} />
              <FormField label="Profile URL reference" name="contact-url" value={draft.profile_url ?? ""} onChange={(value) => setDraft({ ...draft, profile_url: value })} />
              <FormField label="Source name" name="contact-source" value={draft.source_name} required onChange={(value) => setDraft({ ...draft, source_name: value })} />
              <button className="ui-button ui-button-primary w-full" type="submit">{editingId ? "Save changes" : "Add contact"}</button>
              {editingId && <button type="button" onClick={() => { setEditingId(null); setDraft(emptyContact); }} className="w-full text-sm text-slate-400 hover:text-white">Cancel editing</button>}
            </div>
          </form>
          </Surface>
          <Surface as="div" className="card-accent-yellow">
            <SectionHeader accent="yellow" title="Import contacts" description="Use a permitted CSV with the required source fields." />
            <p className="mt-2 text-sm text-slate-400">Required: <code>full_name</code>, <code>source_name</code>. Optional fields match the contact form. You must have permission to use imported data.</p>
            <input className="mt-4 block w-full text-sm text-slate-300" type="file" accept=".csv,text/csv" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
            <button type="button" disabled={!file} onClick={() => void importCsv()} className="ui-button ui-button-secondary mt-4 disabled:opacity-50">Import selected CSV</button>
          </Surface>
        </aside>
        <section>
          <div className="toolbar mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <FormField label="Search" name="contact-search" value={filters.q} onChange={(value) => { setPage(1); setFilters({ ...filters, q: value }); }} placeholder="Name, skills, company..." />
            <FormField label="Role filter" name="filter-role" value={filters.role} onChange={(value) => { setPage(1); setFilters({ ...filters, role: value }); }} />
            <FormField label="Industry filter" name="filter-industry" value={filters.industry} onChange={(value) => { setPage(1); setFilters({ ...filters, industry: value }); }} />
          </div>
          <div className="contact-list overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/50">
            {loading ? <p className="p-8 text-slate-400">Loading contacts...</p> : contacts.length === 0 ? <EmptyState title="No contacts match these filters." /> : <div className="divide-y divide-slate-800">{contacts.map((contact) => <article key={contact.id} className="p-5"><div className="flex flex-col justify-between gap-3 sm:flex-row"><div><h2 className="font-semibold text-white">{contact.full_name}</h2><p className="text-sm text-cyan-200">{contact.current_role || "Role not provided"}{contact.company ? ` · ${contact.company}` : ""}</p><p className="mt-2 text-sm text-slate-400">{[contact.industry, contact.location, contact.school].filter(Boolean).join(" · ") || "No additional details"}</p></div><div className="flex gap-3 text-sm"><button onClick={() => { setEditingId(contact.id); setDraft({ ...contact }); }} className="text-cyan-200 hover:text-white">Edit</button><button onClick={() => void removeContact(contact.id)} className="text-rose-300 hover:text-rose-200">Delete</button></div></div></article>)}</div>}
          </div>
          <div className="mt-4 flex items-center justify-between text-sm text-slate-400"><span>{total} contact(s)</span><div className="flex gap-2"><button disabled={page === 1} onClick={() => setPage(page - 1)} className="rounded border border-slate-700 px-3 py-1 disabled:opacity-40">Previous</button><span className="px-2 py-1">Page {page}</span><button disabled={page * pageSize >= total} onClick={() => setPage(page + 1)} className="rounded border border-slate-700 px-3 py-1 disabled:opacity-40">Next</button></div></div>
        </section>
      </div>
    </Layout>
  );
}
