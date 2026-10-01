export function FormField({
  label,
  name,
  value,
  onChange,
  error,
  type = "text",
  placeholder,
  required,
  optional = !required,
}: {
  label: string;
  name: string;
  value: string | number;
  onChange: (value: string) => void;
  error?: string;
  type?: string;
  placeholder?: string;
  required?: boolean;
  optional?: boolean;
}) {
  const id = `field-${name}`;
  return (
    <div>
      <label htmlFor={id} className="form-label" data-required={required || undefined} data-optional={optional || undefined}>
        <span>{label}</span>
      </label>
      <input
        id={id}
        name={name}
        type={type}
        value={value}
        placeholder={placeholder}
        aria-required={required}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : undefined}
        onChange={(event) => onChange(event.target.value)}
        className="form-control w-full rounded-lg border px-3 py-2.5 outline-none transition"
      />
      {error && (
        <p id={`${id}-error`} className="field-error" role="alert">
          <span aria-hidden="true">!</span>
          {error}
        </p>
      )}
    </div>
  );
}
