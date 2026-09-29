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

export type ProfileFields = Omit<
  StudentProfile,
  "id" | "created_at" | "updated_at" | "career_goals" | "skills"
>;

export type GoalInput = Omit<
  CareerGoal,
  "id" | "student_profile_id" | "created_at"
>;

export type SkillInput = Omit<Skill, "id">;

const apiUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail ?? detail;
    } catch {
      // Keep the status-based message when the server does not return JSON.
    }
    throw new Error(detail);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const profileApi = {
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
};
