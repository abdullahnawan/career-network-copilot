import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import OutreachPage from "../app/outreach/page";

const contacts = { items: [{ id: 2, full_name: "Fictional Contact" }], page: 1, page_size: 100, total: 1 };
const suggestion = {
  student_profile_id: 1, contact_id: 2, purpose: "career_advice", channel: "linkedin_message",
  tone: "professional", subject: null, message: "Hello Fictional Contact,\n\nA grounded draft.",
  facts_used: ["Contact role: Engineer"], character_count: 45, connection_note_limit: null, is_rule_based: true,
};

describe("outreach workspace", () => {
  it("generates a suggestion, displays facts, edits, and saves only explicitly", async () => {
    const fetchMock = vi.spyOn(global, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify(contacts)))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], page: 1, page_size: 50, total: 0 })))
      .mockResolvedValueOnce(new Response(JSON.stringify(suggestion)))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: 5, ...suggestion, status: "draft", user_notes: null, copied_at: null, sent_manually_at: null, replied_at: null, created_at: "", updated_at: "" }), { status: 201 }))
      .mockResolvedValue(new Response(JSON.stringify({ items: [], page: 1, page_size: 50, total: 0 })));
    render(<OutreachPage />);
    await waitFor(() => expect(screen.getByText("Fictional Contact")).toBeInTheDocument());
    fireEvent.change(screen.getByLabelText(/Student profile ID/), { target: { value: "1" } });
    fireEvent.change(screen.getByLabelText("Contact"), { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: "Generate suggestion" }));
    expect(await screen.findByText("Facts used")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Message"), { target: { value: "Edited message" } });
    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8000/outreach-drafts", expect.objectContaining({ method: "POST" })));
    expect(JSON.parse(String(fetchMock.mock.calls[3][1]?.body)).message).toBe("Edited message");
  });

  it("requires confirmation for manual send and clearly states no automatic sending", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(new Response(JSON.stringify({ items: [], page: 1, page_size: 50, total: 0 })));
    render(<OutreachPage />);
    expect(screen.getByText(/does not send messages/i)).toBeInTheDocument();
    expect(screen.getByText(/sending outreach manually/i)).toBeInTheDocument();
  });

  it("counts edited connection notes live and prevents oversized saves", async () => {
    vi.spyOn(global, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify(contacts)))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], page: 1, page_size: 50, total: 0 })))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        ...suggestion,
        channel: "linkedin_connection_note",
        message: "Short note",
        character_count: 10,
        connection_note_limit: 300,
      })));
    render(<OutreachPage />);
    await waitFor(() => expect(screen.getByText("Fictional Contact")).toBeInTheDocument());
    fireEvent.change(screen.getByLabelText(/Student profile ID/), { target: { value: "1" } });
    fireEvent.change(screen.getByLabelText("Contact"), { target: { value: "2" } });
    fireEvent.change(screen.getByLabelText("Channel"), { target: { value: "linkedin_connection_note" } });
    fireEvent.click(screen.getByRole("button", { name: "Generate suggestion" }));
    const message = await screen.findByLabelText("Message");
    fireEvent.change(message, { target: { value: "x".repeat(301) } });
    expect(screen.getByText(/exceeds the 300-character limit/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save draft" })).toBeDisabled();
  });
});
