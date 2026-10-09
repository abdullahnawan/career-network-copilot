import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const auth = vi.hoisted(() => ({ value: { user: null as null | { id: number; email: string }, loading: true } }));

vi.mock("next/navigation", () => ({ usePathname: () => "/" }));
vi.mock("../components/AuthProvider", () => ({
  useAuth: () => ({ ...auth.value, logout: async () => {} }),
}));

import { Layout } from "../components/Layout";

describe("auth gate", () => {
  const assign = vi.fn();
  Object.defineProperty(window, "location", { value: { ...window.location, assign }, writable: true });
  afterEach(() => assign.mockReset());

  it("shows no app shell while the session is being checked", () => {
    auth.value = { user: null, loading: true };
    render(<Layout><p>secret</p></Layout>);
    expect(screen.getByRole("status")).toHaveTextContent("Checking your session");
    expect(screen.queryByText("secret")).toBeNull();
    expect(screen.queryByRole("navigation")).toBeNull();
    expect(assign).not.toHaveBeenCalled();
  });

  it("redirects signed-out visitors without rendering the app", () => {
    auth.value = { user: null, loading: false };
    render(<Layout><p>secret</p></Layout>);
    expect(screen.queryByText("secret")).toBeNull();
    expect(assign).toHaveBeenCalledWith("/login");
  });

  it("renders the app for a signed-in user", () => {
    auth.value = { user: { id: 1, email: "me@example.com" }, loading: false };
    render(<Layout><p>secret</p></Layout>);
    expect(screen.getByText("secret")).toBeInTheDocument();
    expect(screen.getByRole("navigation")).toBeInTheDocument();
    expect(assign).not.toHaveBeenCalled();
  });
});
