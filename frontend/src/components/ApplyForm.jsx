import { useState } from "react";
import { ApiError, submitApplication } from "../api.js";
import { normalizeDoc, validateApplication } from "../validation.js";
import { SelectField, TextField } from "./Field.jsx";

const EMPTY = {
  first_name: "", last_name: "", date_of_birth: "", email: "", phone: "",
  employment_type: "SALARIED", employer_name: "", job_title: "", annual_salary: "", existing_credit_cards: "0",
  id_document_type: "PASSPORT", id_document_number: "",
};

export default function ApplyForm({ onChange, onResult }) {
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (name, value) => {
    const next = { ...form, [name]: value };
    setForm(next);
    if (errors[name]) setErrors((e) => ({ ...e, [name]: undefined }));
    onChange?.(next);
  };

  async function submit(ev) {
    ev.preventDefault();
    setFormError("");
    const found = validateApplication(form);
    setErrors(found);
    if (Object.keys(found).length) {
      document.querySelector('[aria-invalid="true"]')?.focus();
      return;
    }
    setBusy(true);
    try {
      const result = await submitApplication({
        ...form,
        annual_salary: String(form.annual_salary),
        existing_credit_cards: Number(form.existing_credit_cards),
        id_document_number: normalizeDoc(form.id_document_number),
      });
      onResult(result, form);
    } catch (err) {
      if (err instanceof ApiError) {
        setErrors(err.fields || {});
        setFormError(err.fields?._form?.[0] || err.message);
      } else {
        setFormError("Something went wrong. Please try again.");
      }
    } finally {
      setBusy(false);
    }
  }

  const err = (k) => (Array.isArray(errors[k]) ? errors[k][0] : errors[k]);
  const p = (name, extra = {}) => ({ name, value: form[name], onChange: set, error: err(name), ...extra });

  return (
    <form onSubmit={submit} noValidate className="form">
      <fieldset>
        <legend>About you</legend>
        <div className="grid two">
          <TextField label="First name" autoComplete="given-name" {...p("first_name")} />
          <TextField label="Last name" autoComplete="family-name" {...p("last_name")} />
          <TextField label="Date of birth" type="date" autoComplete="bday" {...p("date_of_birth")} />
          <TextField label="Phone" type="tel" autoComplete="tel" hint="Include your country code, e.g. +1 415 555 0123" {...p("phone")} />
        </div>
        <TextField label="Email" type="email" autoComplete="email" {...p("email")} />
      </fieldset>

      <fieldset>
        <legend>Your work</legend>
        <div className="grid two">
          <SelectField
            label="Employment type"
            options={[["SALARIED", "Salaried"], ["SELF_EMPLOYED", "Self-employed"]]}
            {...p("employment_type")}
          />
          <TextField label="Employer" {...p("employer_name")} />
          <TextField label="Job title" {...p("job_title")} />
          <TextField label="Annual salary (USD)" type="number" inputMode="decimal" min="0" step="any" {...p("annual_salary")} />
        </div>
        <TextField
          label="Credit cards you already hold"
          type="number" min="0" step="1" inputMode="numeric"
          hint="Cards from any bank. Enter 0 if this is your first."
          {...p("existing_credit_cards")}
        />
      </fieldset>

      <fieldset>
        <legend>Identity document</legend>
        <div className="grid two">
          <SelectField
            label="Document type"
            options={[
              ["PASSPORT", "Passport"], ["NATIONAL_ID", "National ID"],
              ["DRIVING_LICENSE", "Driving licence"], ["SSN", "Social security number"],
            ]}
            {...p("id_document_type")}
          />
          <TextField label="Document number" autoComplete="off" {...p("id_document_number")} />
        </div>
      </fieldset>

      {formError ? <div className="banner error" role="alert">{formError}</div> : null}

      <button className="btn primary" type="submit" disabled={busy}>
        {busy ? "Checking your application…" : "Submit application"}
      </button>
    </form>
  );
}
