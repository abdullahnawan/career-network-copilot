import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import HomePage from "../app/page";

const profile = {
  id: 7,
  full_name: "Demo Student",
  school: "Fictional University",
  program: "Computer Science",
  graduation_year: 2027,
  location: "Toronto",
  bio: "Learning data systems.",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  career_goals: [],
  skills: [],
};

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("student profile onboarding", () => {
  it("renders the profile form", () => {
    render(<HomePage />);
    expect(screen.getByRole("heading", { name: "Shape your next career conversation." })).toBeInTheDocument();
    expect(screen.getByLabelText(/Full name/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create profile" })).toBeInTheDocument();
  });

  it("adds and removes a career goal", () => {
    render(<HomePage />);
    fireEvent.click(screen.getByRole("button", { name: "Add career goal" }));
    expect(screen.getByLabelText(/Target role/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Remove goal" }));
    expect(screen.queryByLabelText(/Target role/)).not.toBeInTheDocument();
  });

  it("adds and removes a skill", () => {
    render(<HomePage />);
    fireEvent.click(screen.getByRole("button", { name: "Add skill" }));
    expect(screen.getByPlaceholderText("e.g. Python")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Remove skill" }));
    expect(screen.queryByPlaceholderText("e.g. Python")).not.toBeInTheDocument();
  });

  it("shows client-side validation before submitting", () => {
    render(<HomePage />);
    fireEvent.click(screen.getByRole("button", { name: "Create profile" }));
    expect(screen.getByText("Enter your full name.")).toBeInTheDocument();
    expect(screen.getByText("Review the highlighted fields before saving.")).toBeInTheDocument();
  });

  it("submits a valid profile and displays the returned ID", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify(profile), { status: 201, headers: { "Content-Type": "application/json" } }),
    );
    render(<HomePage />);
    fireEvent.change(screen.getByLabelText(/Full name/), { target: { value: "Demo Student" } });
    fireEvent.click(screen.getByRole("button", { name: "Create profile" }));
    await waitFor(() => expect(screen.getByText("Profile saved. Your profile ID is 7.")).toBeInTheDocument());
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/student-profiles",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("shows API errors", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Student profile not found" }), { status: 404 }),
    );
    render(<HomePage />);
    fireEvent.change(screen.getByLabelText(/Load an existing profile/), { target: { value: "99" } });
    fireEvent.click(screen.getByRole("button", { name: "Load profile" }));
    await waitFor(() => expect(screen.getByText("Student profile not found")).toBeInTheDocument());
  });
});
