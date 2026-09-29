import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ContactsPage from "../app/contacts/page";
import MatchesPage from "../app/matches/page";

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(global, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ items: [], page: 1, page_size: 10, total: 0 }), { status: 200 }),
  );
});

describe("contact directory", () => {
  it("renders contacts and supports search/filter interaction", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({
        items: [{
          id: 1, full_name: "Fictional Contact", current_role: "Data Engineer",
          company: "Example Labs", industry: "Technology", location: "Toronto",
          school: null, skills_summary: "Python", profile_url: null,
          source_type: "manual", source_name: "Notes", notes: null,
          created_at: "", updated_at: "",
        }],
        page: 1, page_size: 10, total: 1,
      }), { status: 200 }),
    );
    render(<ContactsPage />);
    expect(await screen.findByText("Fictional Contact")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Search"), { target: { value: "Python" } });
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
  });

  it("creates a contact through the API", async () => {
    const fetchMock = vi.spyOn(global, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], page: 1, page_size: 10, total: 0 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        id: 2, full_name: "New Fictional Contact", current_role: null, company: null,
        industry: null, location: null, school: null, skills_summary: null,
        profile_url: null, source_type: "manual", source_name: "Notes",
        notes: null, created_at: "", updated_at: "",
      }), { status: 201 }))
      .mockResolvedValue(new Response(JSON.stringify({ items: [], page: 1, page_size: 10, total: 0 }), { status: 200 }));
    render(<ContactsPage />);
      await waitFor(() => expect(fetchMock).toHaveBeenCalled());
      fireEvent.change(screen.getByLabelText(/Full name/), { target: { value: "New Fictional Contact" } });
    fireEvent.click(screen.getByRole("button", { name: "Add contact" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8000/contacts", expect.objectContaining({ method: "POST" })));
  });

  it("sends a blank optional profile URL as null", async () => {
    const fetchMock = vi.spyOn(global, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], page: 1, page_size: 10, total: 0 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        id: 4, full_name: "Blank URL Contact", current_role: null, company: null,
        industry: null, location: null, school: null, skills_summary: null,
        profile_url: null, source_type: "manual", source_name: "Notes",
        notes: null, created_at: "", updated_at: "",
      }), { status: 201 }))
      .mockResolvedValue(new Response(JSON.stringify({ items: [], page: 1, page_size: 10, total: 0 }), { status: 200 }));
    render(<ContactsPage />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    fireEvent.change(screen.getByLabelText(/Full name/), { target: { value: "Blank URL Contact" } });
    fireEvent.click(screen.getByRole("button", { name: "Add contact" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const request = fetchMock.mock.calls[1][1];
    expect(JSON.parse(String(request?.body)).profile_url).toBeNull();
  });

  it("renders structured FastAPI validation errors as readable field text", async () => {
    const fetchMock = vi.spyOn(global, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], page: 1, page_size: 10, total: 0 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        detail: [{
          type: "value_error",
          loc: ["body", "profile_url"],
          msg: "Input should be a valid URL",
        }],
      }), { status: 422 }));
    render(<ContactsPage />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    fireEvent.change(screen.getByLabelText(/Full name/), { target: { value: "Invalid URL Contact" } });
    fireEvent.click(screen.getByRole("button", { name: "Add contact" }));
    expect(await screen.findByText("profile_url: Input should be a valid URL")).toBeInTheDocument();
    expect(screen.queryByText("[object Object]")).not.toBeInTheDocument();
  });

  it("requires delete confirmation before removing a contact", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({
        items: [{
          id: 3, full_name: "Deleteable Fictional Contact", current_role: null,
          company: null, industry: null, location: null, school: null,
          skills_summary: null, profile_url: null, source_type: "manual",
          source_name: "Notes", notes: null, created_at: "", updated_at: "",
        }], page: 1, page_size: 10, total: 1,
      }), { status: 200 }),
    );
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    render(<ContactsPage />);
    expect(await screen.findByText("Deleteable Fictional Contact")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    expect(confirm).toHaveBeenCalled();
  });
});

describe("rule-based matches", () => {
  it("displays ranked scores and explanations", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify([{
        contact: { id: 1, full_name: "Fictional Match", current_role: "Engineer", company: "Example Labs" },
        total_score: 80, breakdown: { role: 100, industry: 100, location: 0, school: 0, skills: 100 },
        reasons: ["Matches your target role.", "Matches your skills."],
      }]), { status: 200 }),
    );
    render(<MatchesPage />);
    fireEvent.change(screen.getByLabelText("Student profile ID"), { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "Find matches" }));
    expect(await screen.findByText("Fictional Match")).toBeInTheDocument();
    expect(screen.getByText("Matches your target role.")).toBeInTheDocument();
    expect(screen.getByText("80%")).toBeInTheDocument();
  });

  it("shows API errors", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(new Response(JSON.stringify({ detail: "Student profile not found" }), { status: 404 }));
    render(<MatchesPage />);
    fireEvent.change(screen.getByLabelText("Student profile ID"), { target: { value: "999" } });
    fireEvent.click(screen.getByRole("button", { name: "Find matches" }));
    expect(await screen.findByText("Student profile not found")).toBeInTheDocument();
  });
});
