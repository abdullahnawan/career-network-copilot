import type { GoalInput } from "../lib/api";
import { FormField } from "./FormField";

export function CareerGoalEditor({
  goals,
  onChange,
}: {
  goals: GoalInput[];
  onChange: (goals: GoalInput[]) => void;
}) {
  function update(index: number, field: keyof GoalInput, value: string) {
    onChange(goals.map((goal, i) => (i === index ? { ...goal, [field]: value } : goal)));
  }
  return (
    <div className="space-y-4">
      {goals.length === 0 && (
        <p className="rounded-lg border border-dashed border-slate-700 px-4 py-3 text-sm text-slate-400">
          No career goals yet. Add one to describe the conversations you want to pursue.
        </p>
      )}
      {goals.map((goal, index) => (
        <div key={index} className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField label="Target role" name={`goal-role-${index}`} value={goal.role} required onChange={(value) => update(index, "role", value)} />
            <FormField label="Goal type" name={`goal-type-${index}`} value={goal.goal_type} placeholder="Internship, mentorship..." required onChange={(value) => update(index, "goal_type", value)} />
            <FormField label="Industry" name={`goal-industry-${index}`} value={goal.industry ?? ""} onChange={(value) => update(index, "industry", value)} />
            <FormField label="Preferred location" name={`goal-location-${index}`} value={goal.location ?? ""} onChange={(value) => update(index, "location", value)} />
          </div>
          <label htmlFor={`goal-notes-${index}`} className="mt-4 block text-sm font-medium text-slate-200">Notes</label>
          <textarea id={`goal-notes-${index}`} value={goal.notes ?? ""} onChange={(event) => update(index, "notes", event.target.value)} className="mt-2 min-h-20 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2.5 text-slate-100 outline-none focus:border-cyan-300" />
          <button type="button" onClick={() => onChange(goals.filter((_, i) => i !== index))} className="mt-3 text-sm font-medium text-rose-300 hover:text-rose-200">Remove goal</button>
        </div>
      ))}
      <button type="button" onClick={() => onChange([...goals, { role: "", industry: "", location: "", goal_type: "", notes: "" }])} className="rounded-lg border border-cyan-300/50 px-4 py-2 text-sm font-semibold text-cyan-200 hover:bg-cyan-300/10">Add career goal</button>
    </div>
  );
}
