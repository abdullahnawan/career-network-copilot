export type CareerGoal = {
  id: number;
  student_profile_id: number;
  role: string;
  industry: string | null;
  location: string | null;
  goal_type: string;
  notes: string | null;
  created_at: string;
};

export type Skill = {
  id: number;
  name: string;
  proficiency_level: string;
};

export type StudentProfile = {
  id: number;
  full_name: string;
  school: string | null;
  program: string | null;
  graduation_year: number | null;
  location: string | null;
  bio: string | null;
  created_at: string;
  updated_at: string;
  career_goals: CareerGoal[];
  skills: Skill[];
};

export type CurrentUser = {
  id: number;
  email: string;
  display_name: string;
  profile?: StudentProfile | null;
};

export class UnauthorizedError extends Error {
  constructor() {
    super("Your session has expired. Please sign in again.");
    this.name = "UnauthorizedError";
  }
}

export type ProfileFields = Omit<
  StudentProfile,
  "id" | "created_at" | "updated_at" | "career_goals" | "skills"
>;

export type GoalInput = Omit<
  CareerGoal,
  "id" | "student_profile_id" | "created_at"
>;

export type SkillInput = Omit<Skill, "id">;

export type Contact = {
  id: number;
  full_name: string;
  current_role: string | null;
  company: string | null;
  industry: string | null;
  location: string | null;
  school: string | null;
  skills_summary: string | null;
  profile_url: string | null;
  source_type: "manual" | "csv";
  source_name: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type ContactInput = Omit<Contact, "id" | "created_at" | "updated_at">;
export type ContactMatch = {
  contact: Contact;
  total_score: number;
  breakdown: { role: number; industry: number; location: number; school: number; skills: number };
  reasons: string[];
};

export type ContactPage = { items: Contact[]; page: number; page_size: number; total: number };
export type CsvImportSummary = { created: number; errors: { row: number; message: string }[] };
export type OutreachStatus = "draft" | "approved" | "copied" | "sent_manually" | "replied" | "archived";
export type OutreachPurpose = "informational_interview" | "career_advice" | "project_collaboration" | "internship_question" | "general_networking";
export type OutreachChannel = "linkedin_connection_note" | "linkedin_message" | "email" | "other";
export type OutreachTone = "professional" | "warm" | "concise";
export type OutreachDraft = {
  id: number; student_profile_id: number; contact_id: number; purpose: OutreachPurpose;
  channel: OutreachChannel; tone: OutreachTone; subject: string | null; message: string;
  status: OutreachStatus; user_notes: string | null; copied_at: string | null;
  sent_manually_at: string | null; replied_at: string | null; created_at: string; updated_at: string;
};
export type OutreachDraftPage = { items: OutreachDraft[]; page: number; page_size: number; total: number };
export type OutreachSuggestion = {
  student_profile_id: number; contact_id: number; purpose: OutreachPurpose; channel: OutreachChannel;
  tone: OutreachTone; subject: string | null; message: string; facts_used: string[];
  character_count: number; connection_note_limit: number | null; is_rule_based: boolean;
};
export type OutreachInput = Omit<OutreachDraft, "id" | "status" | "copied_at" | "sent_manually_at" | "replied_at" | "created_at" | "updated_at">;

const apiUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

type FastApiValidationError = {
  loc?: Array<string | number>;
  msg?: string;
};

type FastApiErrorBody = {
  detail?: string | FastApiValidationError[] | Record<string, unknown>;
};

function formatDetail(detail: FastApiErrorBody["detail"]): string | null {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (!item || typeof item !== "object") return null;
        const location = item.loc?.filter((part) => part !== "body").join(".");
        const message = item.msg?.trim();
        if (!message) return null;
        return location ? `${location}: ${message}` : message;
      })
      .filter((message): message is string => Boolean(message));
    if (messages.length) return messages.join("; ");
  }
  if (detail && typeof detail === "object") {
    try {
      return JSON.stringify(detail);
    } catch {
      return "The server returned an unreadable error.";
    }
  }
  return null;
}

export function formatApiError(error: unknown, fallback = "The request could not be completed."): string {
  if (error instanceof TypeError) return "Unable to reach the API. Check that FastAPI is running.";
  if (error instanceof Error && error.message.trim()) return error.message;
  if (typeof error === "string" && error.trim()) return error;
  return fallback;
}

function normalizeOptional(value: string | null | undefined): string | null {
  const normalized = value?.trim() ?? "";
  return normalized || null;
}

export function normalizeContactInput(payload: ContactInput): ContactInput {
  return {
    ...payload,
    full_name: payload.full_name.trim(),
    current_role: normalizeOptional(payload.current_role),
    company: normalizeOptional(payload.company),
    industry: normalizeOptional(payload.industry),
    location: normalizeOptional(payload.location),
    school: normalizeOptional(payload.school),
    skills_summary: normalizeOptional(payload.skills_summary),
    profile_url: normalizeOptional(payload.profile_url),
    source_name: payload.source_name.trim(),
    notes: normalizeOptional(payload.notes),
  };
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiUrl}${path}`, {
      ...options,
      credentials: "include",
      headers: { "Content-Type": "application/json", ...options?.headers },
    });
  } catch (error) {
    throw new Error(formatApiError(error));
  }
  if (!response.ok) {
    if (response.status === 401) throw new UnauthorizedError();
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = (await response.json()) as FastApiErrorBody;
      detail = formatDetail(body.detail) ?? detail;
    } catch {
      // Keep the status-based message when the server does not return JSON.
    }

    throw new Error(detail);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

async function upload<T>(path: string, file: File): Promise<T> {
  const form = new FormData();
  form.append("file", file);
  let response: Response;
  try {
    response = await fetch(`${apiUrl}${path}`, { method: "POST", body: form, credentials: "include" });
  } catch (error) {
    throw new Error(formatApiError(error));
  }
  if (!response.ok) {
    if (response.status === 401) throw new UnauthorizedError();
    const body = (await response.json().catch(() => ({}))) as FastApiErrorBody;
    throw new Error(
      formatDetail(body.detail) ?? `Request failed with status ${response.status}`,
    );
  }

  return response.json() as Promise<T>;
}

export const authApi = {
  me: () => request<CurrentUser>("/auth/me"),
  login: (email: string, password: string) => request<CurrentUser>("/auth/login", {
    method: "POST", body: JSON.stringify({ email, password }),
  }),
  register: (email: string, password: string, display_name: string) => request<CurrentUser>("/auth/register", {
    method: "POST", body: JSON.stringify({ email, password, display_name }),
  }),
  logout: () => request<void>("/auth/logout", { method: "POST" }),
};

export const accountApi = {
  export: () => request<Record<string, unknown>>("/account/export"),
  delete: (password: string) => request<void>("/account", {
    method: "DELETE",
    body: JSON.stringify({ password }),
  }),
};

export const profileApi = {
  current: () => request<StudentProfile>("/student-profiles/me"),
  get: (id: number) => request<StudentProfile>(`/student-profiles/${id}`),
  create: (fields: ProfileFields, goals: GoalInput[], skills: SkillInput[]) =>
    request<StudentProfile>("/student-profiles", {
      method: "POST",
      body: JSON.stringify({ ...fields, career_goals: goals, skills }),
    }),
  update: (id: number, fields: ProfileFields) =>
    request<StudentProfile>(`/student-profiles/${id}`, {
      method: "PATCH",
      body: JSON.stringify(fields),
    }),
  createGoal: (id: number, goal: GoalInput) =>
    request<CareerGoal>(`/student-profiles/${id}/career-goals`, {
      method: "POST",
      body: JSON.stringify(goal),
    }),
  updateGoal: (profileId: number, goalId: number, goal: Partial<GoalInput>) =>
    request<CareerGoal>(`/student-profiles/${profileId}/career-goals/${goalId}`, {
      method: "PATCH",
      body: JSON.stringify(goal),
    }),
  deleteGoal: (profileId: number, goalId: number) =>
    request<void>(`/student-profiles/${profileId}/career-goals/${goalId}`, {
      method: "DELETE",
    }),
  replaceSkills: (id: number, skills: SkillInput[]) =>
    request<StudentProfile>(`/student-profiles/${id}/skills`, {
      method: "PUT",
      body: JSON.stringify({ skills }),
    }),
  matches: (id: number) => request<ContactMatch[]>(`/student-profiles/${id}/matches`),
};

export const contactsApi = {
  list: (params: Record<string, string | number | undefined>) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== "") query.set(key, String(value));
    });
    return request<ContactPage>(`/contacts?${query.toString()}`);
  },
  create: (payload: ContactInput) =>
    request<Contact>("/contacts", {
      method: "POST",
      body: JSON.stringify(normalizeContactInput(payload)),
    }),
  update: (id: number, payload: Partial<ContactInput>) =>
    request<Contact>(`/contacts/${id}`, {
      method: "PATCH",
      body: JSON.stringify(normalizeContactInput({ ...emptyContactInput, ...payload })),
    }),
  remove: (id: number) => request<void>(`/contacts/${id}`, { method: "DELETE" }),
  importCsv: (file: File) => upload<CsvImportSummary>("/contacts/import-csv", file),
};

export const outreachApi = {
  list: (params: Record<string, string | number | undefined>) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => { if (value !== undefined && value !== "") query.set(key, String(value)); });
    return request<OutreachDraftPage>(`/outreach-drafts?${query.toString()}`);
  },
  activity: (studentProfileId?: number) => request<{ total: number; by_status: Record<OutreachStatus, number> }>(
    `/outreach-drafts/activity-summary${studentProfileId ? `?student_profile_id=${studentProfileId}` : ""}`,
  ),
  suggest: (params: { student_profile_id: number; contact_id: number; purpose: OutreachPurpose; channel: OutreachChannel; tone: OutreachTone }) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => query.set(key, String(value)));
    return request<OutreachSuggestion>(`/outreach-drafts/suggest?${query.toString()}`, { method: "POST" });
  },
  create: (payload: OutreachInput) => request<OutreachDraft>("/outreach-drafts", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: number, payload: Partial<OutreachInput>) => request<OutreachDraft>(`/outreach-drafts/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  action: (id: number, action: "approve" | "copied" | "sent-manually" | "replied" | "archive") =>
    request<OutreachDraft>(`/outreach-drafts/${id}/${action}`, { method: "POST" }),
  remove: (id: number) => request<void>(`/outreach-drafts/${id}`, { method: "DELETE" }),
};

const emptyContactInput: ContactInput = {
  full_name: "",
  current_role: null,
  company: null,
  industry: null,
  location: null,
  school: null,
  skills_summary: null,
  profile_url: null,
  source_type: "manual",
  source_name: "",
  notes: null,
};
