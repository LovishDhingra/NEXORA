import { useState } from "react";
import { ApiError, submitApplication } from "../api.js";
import { normalizeDoc, validateApplication } from "../validation.js";
import { Field, SelectField, TextField } from "./Field.jsx";

const EMPTY = {
  first_name: "", last_name: "", date_of_birth: "", email: "", phone: "",
  employment_type: "SALARIED", employer_name: "", job_title: "", annual_salary: "", existing_credit_cards: "0",
  other_cards: [],
  id_document_type: "PASSPORT", id_document_number: "",
};

const NETWORKS = [
  ["VISA", "Visa"], ["MASTERCARD", "Mastercard"], ["AMEX", "American Express"], ["RUPAY", "RuPay"], ["OTHER", "Other"],
];

// One blank row per card the applicant says they hold; rows already filled in are kept.
const resizeCards = (cards, count) => {
  const n = Math.min(Math.max(parseInt(count, 10) || 0, 0), 50);
  return Array.from({ length: n }, (_, i) => cards[i] || { issuer: "", network: "VISA" });
};

export default function ApplyForm({ onChange, onResult }) {
  const [form, setForm] = useState(EMPTY);
  const [countryCode, setCountryCode] = useState("+91");
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (name, value) => {
    const next = { ...form, [name]: value };
    if (name === "existing_credit_cards") next.other_cards = resizeCards(form.other_cards, value);
    setForm(next);
    if (errors[name]) setErrors((e) => ({ ...e, [name]: undefined }));
    onChange?.(next);
  };

  const setCard = (i, key, value) =>
    set("other_cards", form.other_cards.map((c, n) => (n === i ? { ...c, [key]: value } : c)));

  async function submit(ev) {
    ev.preventDefault();
    setFormError("");
    const application = { ...form, phone: form.phone.trim() ? `${countryCode}${form.phone.replace(/[\s()-]/g, "")}` : "" };
    const found = validateApplication(application);
    if (!/^\+[1-9]\d{0,2}$/.test(countryCode)) found.phone = "Enter a country code such as +91 or +1.";
    setErrors(found);
    if (Object.keys(found).length) {
      document.querySelector('[aria-invalid="true"]')?.focus();
      return;
    }
    setBusy(true);
    try {
      const result = await submitApplication({
        ...application,
        annual_salary: String(form.annual_salary),
        existing_credit_cards: Number(form.existing_credit_cards),
        id_document_number: normalizeDoc(form.id_document_number),
      });
      onResult(result, application);
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
          <Field label="Phone" error={err("phone")} hint="Country code and phone number, e.g. +91 73559 04515">
            {(aria) => (
              <div className="phone-inputs">
                <input
                  aria-label="Country calling code" aria-describedby={aria["aria-describedby"]}
                  type="tel" name="country_code" autoComplete="tel-country-code"
                  value={countryCode} maxLength={4} placeholder="+91"
                  onChange={(e) => {
                    setCountryCode(e.target.value);
                    setErrors((current) => ({ ...current, phone: undefined }));
                  }}
                />
                <input {...aria} type="tel" name="phone" autoComplete="tel-national"
                  value={form.phone} placeholder="73559 04515"
                  onChange={(e) => set("phone", e.target.value)} />
              </div>
            )}
          </Field>
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
        {form.other_cards.map((card, i) => (
          <div className="grid two" key={i}>
            <TextField
              label={`Card ${i + 1}: issuing bank`} name={`issuer_${i}`} maxLength={60}
              value={card.issuer} onChange={(_, v) => setCard(i, "issuer", v)}
            />
            <SelectField
              label={`Card ${i + 1}: type`} name={`network_${i}`} options={NETWORKS}
              value={card.network} onChange={(_, v) => setCard(i, "network", v)}
            />
          </div>
        ))}
        {typeof err("other_cards") === "string" ? <p className="msg error" role="alert">{err("other_cards")}</p> : null}
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
