import { describe, expect, it, vi } from "vitest";
import { authApi, UnauthorizedError } from "../lib/api";

describe("authentication API", () => {
  it("uses cookie credentials and does not expose unauthorized response details", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "internal auth detail" }), { status: 401 }),
    );
    await expect(authApi.me()).rejects.toBeInstanceOf(UnauthorizedError);
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/auth/me"), expect.objectContaining({ credentials: "include" }));
  });
});
