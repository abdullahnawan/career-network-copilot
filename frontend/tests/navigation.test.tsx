import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Layout } from "../components/Layout";

vi.mock("next/navigation", () => ({ usePathname: () => "/outreach" }));

describe("application navigation", () => {
  it("marks the current workspace and keeps all primary destinations available", () => {
    render(<Layout><h1>Workspace</h1></Layout>);
    expect(screen.getByRole("link", { name: "Outreach" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Profile" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Contacts" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Matches" })).toBeInTheDocument();
  });
});
