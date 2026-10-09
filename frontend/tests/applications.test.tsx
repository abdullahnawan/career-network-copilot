import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import ApplicationsPage from "../app/applications/page";

vi.mock("../components/AuthProvider", () => ({
  useAuth: () => ({ profile: { id: 1 }, loading: false, user: { id: 1, email: "demo@example.com" } }),
}));

const funnel = { applied: 2, online_assessment: 1, interview: 1, offer: 0, positive_response_rate: 0.5 };
const summary = {
  total: 3,
  by_status: { saved: 1, applied: 1, online_assessment: 0, interview: 1, offer: 0, rejected: 0, withdrawn: 0 },
  funnel,
  by_resume_version: { SWE: funnel, unspecified: { ...funnel, applied: 0, online_assessment: 0, interview: 0, positive_response_rate: 0 } },
  by_source: { company_site: funnel },
  referral: { ...funnel, applied: 1 },
  cold: { ...funnel, applied: 1 },
};
const application = {
  id: 7, company: "Example Bank", role_title: "Software Developer Intern", posting_url: "https://example.test/job",
  location: "Toronto", source: "company_site", resume_version: "SWE", referral_contact_id: 2, deadline: null,
  notes: "Ask about the data team", status: "applied", applied_at: "2026-09-01T12:00:00Z",
  online_assessment_at: null, interview_at: null, offer_at: null, closed_at: null, created_at: "", updated_at: "",
};
const followUps = {
  items: [{ kind: "application_no_response", title: "Example Bank: Software Developer Intern", detail: "No response 30 days after applying.", application_id: 7, outreach_draft_id: null, since: "2026-09-01T12:00:00Z", due: null }],
  application_days: 21, outreach_days: 7, deadline_days: 7,
};

function mockApi(overrides: { applications?: unknown[] } = {}) {
  return vi.spyOn(global, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    if (url.includes("/contacts")) return new Response(JSON.stringify({ items: [{ id: 2, full_name: "Fictional Referrer" }], page: 1, page_size: 100, total: 1 }));
    if (url.includes("/applications/summary")) return new Response(JSON.stringify(summary));
    if (url.includes("/follow-ups")) return new Response(JSON.stringify(followUps));
    if (method === "POST" && url.endsWith("/applications")) return new Response(JSON.stringify({ ...application, id: 8 }), { status: 201 });
    if (method === "POST") return new Response(JSON.stringify({ ...application, status: "interview" }));
    const items = overrides.applications ?? [application];
    return new Response(JSON.stringify({ items, page: 1, page_size: 100, total: items.length }));
  });
}

afterEach(() => vi.restoreAllMocks());

describe("applications pipeline", () => {
  it("shows follow-ups, funnel metrics and tracked applications", async () => {
    mockApi();
    render(<ApplicationsPage />);
    expect(await screen.findByText("Follow-ups due")).toBeInTheDocument();
    expect(screen.getByText("No response 30 days after applying.")).toBeInTheDocument();
    expect(screen.getByText("Resume: SWE")).toBeInTheDocument();
    expect(await screen.findByText("Software Developer Intern")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText(/Referral: Fictional Referrer/)).toBeInTheDocument());
    expect(screen.getByText(/never applies to jobs/i)).toBeInTheDocument();
  });

  it("adds an application as applied with trimmed fields", async () => {
    const fetchMock = mockApi({ applications: [] });
    render(<ApplicationsPage />);
    expect(await screen.findByText("No applications yet.")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Company"), { target: { value: "  Northwind  " } });
    fireEvent.change(screen.getByLabelText("Role"), { target: { value: "Data Engineer Intern" } });
    fireEvent.click(screen.getByRole("button", { name: "Add application" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/applications", expect.objectContaining({ method: "POST" }),
    ));
    const call = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/applications") && init?.method === "POST");
    const body = JSON.parse(String(call?.[1]?.body));
    expect(body).toMatchObject({ company: "Northwind", role_title: "Data Engineer Intern", status: "applied", notes: null });
  });

  it("requires company and role before saving", async () => {
    const fetchMock = mockApi({ applications: [] });
    render(<ApplicationsPage />);
    await screen.findByText("No applications yet.");
    fireEvent.click(screen.getByRole("button", { name: "Add application" }));
    expect(await screen.findByText("Add a company and a role.")).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);
  });

  it("advances status with the next valid action only", async () => {
    const fetchMock = mockApi();
    render(<ApplicationsPage />);
    await screen.findByText("Software Developer Intern");
    expect(screen.queryByRole("button", { name: "Mark applied" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Got interview" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/applications/7/interview", expect.objectContaining({ method: "POST" }),
    ));
  });
});
