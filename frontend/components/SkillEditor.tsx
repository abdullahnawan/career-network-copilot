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
        <p className="rounded-lg border border-dashed border-[#d8e1ef] bg-[#fff8db] px-4 py-3 text-sm text-[#61708a]">
          No skills added yet. Add the tools and capabilities you are developing.
        </p>
      )}
      {skills.map((skill, index) => (
        <div key={index} className="flex flex-col gap-3 rounded-lg border border-[#eadca5] bg-[#fff8db] p-3 sm:flex-row">
          <label className="sr-only" htmlFor={`skill-name-${index}`}>Skill name</label>
          <input id={`skill-name-${index}`} value={skill.name} placeholder="e.g. Python" onChange={(event) => onChange(skills.map((item, i) => i === index ? { ...item, name: event.target.value } : item))} className="form-control min-w-0 flex-1 rounded-lg px-3 py-2 outline-none" />
          <label className="sr-only" htmlFor={`skill-level-${index}`}>Proficiency level</label>
          <select id={`skill-level-${index}`} value={skill.proficiency_level} onChange={(event) => onChange(skills.map((item, i) => i === index ? { ...item, proficiency_level: event.target.value } : item))} className="form-control rounded-lg px-3 py-2 outline-none">
            <option value="">Choose level</option>
            {proficiencyOptions.map((option) => <option key={option} value={option}>{option}</option>)}
          </select>
          <button type="button" aria-label={`Remove ${skill.name || "skill"}`} onClick={() => onChange(skills.filter((_, i) => i !== index))} className="px-2 text-sm font-medium text-[#b91c1c] hover:text-[#8f1d1d]">Remove</button>
        </div>
      ))}
      <button type="button" onClick={() => onChange([...skills, { name: "", proficiency_level: "" }])} className="ui-button ui-button-secondary">Add skill</button>
    </div>
  );
}
