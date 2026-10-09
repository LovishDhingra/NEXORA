import { useId } from "react";

export function Field({ label, error, hint, children }) {
  const id = useId();
  const described = error ? `${id}-err` : hint ? `${id}-hint` : undefined;
  return (
    <div className={`field${error ? " has-error" : ""}`}>
      <label htmlFor={id}>{label}</label>
      {children({ id, "aria-invalid": !!error, "aria-describedby": described })}
      {error ? (
        <p className="msg error" id={`${id}-err`} role="alert">{error}</p>
      ) : hint ? (
        <p className="msg hint" id={`${id}-hint`}>{hint}</p>
      ) : null}
    </div>
  );
}

export function TextField({ label, name, value, onChange, error, hint, ...rest }) {
  return (
    <Field label={label} error={error} hint={hint}>
      {(aria) => (
        <input name={name} value={value} onChange={(e) => onChange(name, e.target.value)} {...aria} {...rest} />
      )}
    </Field>
  );
}

export function SelectField({ label, name, value, onChange, error, options }) {
  return (
    <Field label={label} error={error}>
      {(aria) => (
        <select name={name} value={value} onChange={(e) => onChange(name, e.target.value)} {...aria}>
          {options.map(([v, text]) => (
            <option key={v} value={v}>{text}</option>
          ))}
        </select>
      )}
    </Field>
  );
}
