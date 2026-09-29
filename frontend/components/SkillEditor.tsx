import type { SkillInput } from "../lib/api";

const proficiencyOptions = ["Beginner", "Intermediate", "Advanced"];

export function SkillEditor({
  skills,
  onChange,
}: {
  skills: SkillInput[];
  onChange: (skills: SkillInput[]) => void;
}) {
  return (
    <div className="space-y-3">
      {skills.length === 0 && (
        <p className="rounded-lg border border-dashed border-slate-700 px-4 py-3 text-sm text-slate-400">
          No skills added yet. Add the tools and capabilities you are developing.
        </p>
      )}
      {skills.map((skill, index) => (
        <div key={index} className="flex flex-col gap-3 rounded-xl border border-slate-700 bg-slate-900/60 p-3 sm:flex-row">
          <label className="sr-only" htmlFor={`skill-name-${index}`}>Skill name</label>
          <input id={`skill-name-${index}`} value={skill.name} placeholder="e.g. Python" onChange={(event) => onChange(skills.map((item, i) => i === index ? { ...item, name: event.target.value } : item))} className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100 outline-none focus:border-cyan-300" />
          <label className="sr-only" htmlFor={`skill-level-${index}`}>Proficiency level</label>
          <select id={`skill-level-${index}`} value={skill.proficiency_level} onChange={(event) => onChange(skills.map((item, i) => i === index ? { ...item, proficiency_level: event.target.value } : item))} className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100 outline-none focus:border-cyan-300">
            <option value="">Choose level</option>
            {proficiencyOptions.map((option) => <option key={option} value={option}>{option}</option>)}
          </select>
          <button type="button" aria-label={`Remove ${skill.name || "skill"}`} onClick={() => onChange(skills.filter((_, i) => i !== index))} className="px-2 text-sm font-medium text-rose-300 hover:text-rose-200">Remove</button>
        </div>
      ))}
      <button type="button" onClick={() => onChange([...skills, { name: "", proficiency_level: "" }])} className="rounded-lg border border-cyan-300/50 px-4 py-2 text-sm font-semibold text-cyan-200 hover:bg-cyan-300/10">Add skill</button>
    </div>
  );
}
