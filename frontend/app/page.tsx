"use client";

import { FormEvent, useState } from "react";
import { CareerGoalEditor } from "../components/CareerGoalEditor";
import { FormField } from "../components/FormField";
import { Layout } from "../components/Layout";
import { SkillEditor } from "../components/SkillEditor";
import { StatusMessage } from "../components/StatusMessage";
import { CareerGoal, formatApiError, GoalInput, ProfileFields, profileApi, SkillInput, StudentProfile } from "../lib/api";

type GoalDraft = GoalInput & { id?: number };

const emptyFields: ProfileFields = {
  full_name: "",
  school: "",
  program: "",
  graduation_year: null,
  location: "",
  bio: "",
};

function toGoalInput(goal: CareerGoal): GoalDraft {
  return {
    id: goal.id,
    role: goal.role,
    industry: goal.industry ?? "",
    location: goal.location ?? "",
    goal_type: goal.goal_type,
    notes: goal.notes ?? "",
  };
}

export default function HomePage() {
  const [profileId, setProfileId] = useState("");
  const [fields, setFields] = useState<ProfileFields>(emptyFields);
  const [goals, setGoals] = useState<GoalDraft[]>([]);
  const [skills, setSkills] = useState<SkillInput[]>([]);
  const [existingGoals, setExistingGoals] = useState<CareerGoal[]>([]);
  const [status, setStatus] = useState<{ kind: "error" | "success" | "info"; message: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  function setField(field: keyof ProfileFields, value: string) {
    setFields((current) => ({
      ...current,
      [field]: field === "graduation_year" ? (value ? Number(value) : null) : value,
    }));
    setErrors((current) => ({ ...current, [field]: "" }));
  }

  function validate() {
    const nextErrors: Record<string, string> = {};
    if (!fields.full_name.trim()) nextErrors.full_name = "Enter your full name.";
    if (fields.graduation_year !== null && (fields.graduation_year < 1900 || fields.graduation_year > 2200)) {
      nextErrors.graduation_year = "Use a year between 1900 and 2200.";
    }
    goals.forEach((goal, index) => {
      if (!goal.role.trim()) nextErrors[`goal-${index}`] = "Add a target role.";
      if (!goal.goal_type.trim()) nextErrors[`goal-type-${index}`] = "Add a goal type.";
    });
    skills.forEach((skill, index) => {
      if (!skill.name.trim() || !skill.proficiency_level) nextErrors[`skill-${index}`] = "Complete the skill and proficiency.";
    });
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function loadProfile(event: FormEvent) {
    event.preventDefault();
    const id = Number(profileId);
    if (!Number.isInteger(id) || id <= 0) {
      setStatus({ kind: "error", message: "Enter a valid numeric profile ID." });
      return;
    }
    setLoading(true);
    setStatus({ kind: "info", message: "Loading your profile..." });
    try {
      const profile = await profileApi.get(id);
      applyProfile(profile);
      setStatus({ kind: "success", message: "Profile loaded. You can edit it below." });
    } catch (error) {
      setStatus({ kind: "error", message: formatApiError(error, "Unable to load profile.") });
    } finally {
      setLoading(false);
    }
  }

  function applyProfile(profile: StudentProfile) {
    setProfileId(String(profile.id));
    setFields({
      full_name: profile.full_name,
      school: profile.school ?? "",
      program: profile.program ?? "",
      graduation_year: profile.graduation_year,
      location: profile.location ?? "",
      bio: profile.bio ?? "",
    });
    setGoals(profile.career_goals.map(toGoalInput));
    setExistingGoals(profile.career_goals);
    setSkills(profile.skills.map(({ name, proficiency_level }) => ({ name, proficiency_level })));
  }

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    if (!validate()) {
      setStatus({ kind: "error", message: "Review the highlighted fields before saving." });
      return;
    }
    setLoading(true);
    setStatus({ kind: "info", message: "Saving your profile..." });
    try {
      let saved: StudentProfile;
      const id = Number(profileId);
      if (id) {
        saved = await profileApi.update(id, fields);
        const currentIds = new Set(goals.flatMap((goal) => (goal.id ? [goal.id] : [])));
        await Promise.all(existingGoals.filter((goal) => !currentIds.has(goal.id)).map((goal) => profileApi.deleteGoal(id, goal.id)));
        const savedGoals = await Promise.all(goals.map((goal) => {
          const { id: goalId, ...input } = goal;
          return goalId ? profileApi.updateGoal(id, goalId, input) : profileApi.createGoal(id, input);
        }));
        saved = await profileApi.replaceSkills(id, skills);
        saved = { ...saved, career_goals: savedGoals };
      } else {
        saved = await profileApi.create(
          fields,
          goals.map((goal) => ({
            role: goal.role,
            industry: goal.industry,
            location: goal.location,
            goal_type: goal.goal_type,
            notes: goal.notes,
          })),
          skills,
        );
      }
      applyProfile(saved);
      setStatus({ kind: "success", message: `Profile saved. Your profile ID is ${saved.id}.` });
    } catch (error) {
      setStatus({ kind: "error", message: formatApiError(error, "Unable to save profile.") });
    } finally {
      setLoading(false);
    }
  }

  return (
    <Layout>
      <div className="mb-10 max-w-3xl">
        <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">Phase 3 · Your foundation</p>
        <h1 className="text-4xl font-semibold tracking-tight text-white sm:text-5xl">Shape your next career conversation.</h1>
        <p className="mt-4 text-lg leading-8 text-slate-300">Create a clear, private career profile that will later help you discover relevant people and opportunities—always with you in control.</p>
      </div>

      <div className="mb-8 rounded-2xl border border-slate-800 bg-slate-900/50 p-5">
        <form onSubmit={loadProfile} className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="w-full sm:max-w-xs">
            <FormField label="Load an existing profile" name="profile-id" value={profileId} onChange={setProfileId} type="number" placeholder="Profile ID" />
          </div>
          <button type="submit" disabled={loading} className="rounded-lg bg-slate-100 px-5 py-2.5 font-semibold text-slate-950 hover:bg-white disabled:cursor-not-allowed disabled:opacity-60">Load profile</button>
        </form>
      </div>

      {status && <div className="mb-8"><StatusMessage kind={status.kind}>{status.message}</StatusMessage></div>}

      <form onSubmit={saveProfile} className="space-y-8">
        <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 sm:p-8">
          <div className="mb-6"><h2 className="text-xl font-semibold text-white">About you</h2><p className="mt-1 text-sm text-slate-400">Keep this practical and easy for a future professional connection to understand.</p></div>
          <div className="grid gap-5 sm:grid-cols-2">
            <FormField label="Full name" name="full_name" value={fields.full_name} onChange={(value) => setField("full_name", value)} error={errors.full_name} required />
            <FormField label="School" name="school" value={fields.school ?? ""} onChange={(value) => setField("school", value)} placeholder="Your school or university" />
            <FormField label="Program" name="program" value={fields.program ?? ""} onChange={(value) => setField("program", value)} placeholder="Degree or area of study" />
            <FormField label="Graduation year" name="graduation_year" value={fields.graduation_year ?? ""} onChange={(value) => setField("graduation_year", value)} type="number" error={errors.graduation_year} />
            <FormField label="Location" name="location" value={fields.location ?? ""} onChange={(value) => setField("location", value)} placeholder="City, region, or remote" />
          </div>
          <label htmlFor="bio" className="mt-5 block text-sm font-medium text-slate-200">Short bio</label>
          <textarea id="bio" value={fields.bio ?? ""} onChange={(event) => setField("bio", event.target.value)} placeholder="What are you learning, building, or exploring?" className="mt-2 min-h-28 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2.5 text-slate-100 outline-none focus:border-cyan-300" />
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 sm:p-8">
          <div className="mb-6"><h2 className="text-xl font-semibold text-white">Career goals</h2><p className="mt-1 text-sm text-slate-400">Add the roles and kinds of conversations you want to work toward.</p></div>
          <CareerGoalEditor goals={goals} onChange={setGoals} />
          {Object.entries(errors).filter(([key]) => key.startsWith("goal-")).map(([key, value]) => <p key={key} className="mt-2 text-sm text-rose-300">{value}</p>)}
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 sm:p-8">
          <div className="mb-6"><h2 className="text-xl font-semibold text-white">Skills</h2><p className="mt-1 text-sm text-slate-400">Be honest about your current level. You can update this as you grow.</p></div>
          <SkillEditor skills={skills} onChange={setSkills} />
          {Object.entries(errors).filter(([key]) => key.startsWith("skill-")).map(([key, value]) => <p key={key} className="mt-2 text-sm text-rose-300">{value}</p>)}
        </section>

        <div className="flex flex-col items-start justify-between gap-4 border-t border-slate-800 pt-6 sm:flex-row sm:items-center">
          <p className="text-sm text-slate-400">Your profile stays in your local development database until later privacy and account features are added.</p>
          <button type="submit" disabled={loading} className="w-full rounded-lg bg-cyan-300 px-6 py-3 font-semibold text-slate-950 hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto">{loading ? "Saving..." : profileId ? "Save changes" : "Create profile"}</button>
        </div>
      </form>
    </Layout>
  );
}
