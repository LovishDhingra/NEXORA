import { useEffect, useState } from "react";
import { ApiError, changePin } from "../api.js";
import { validatePinChange } from "../validation.js";
import { TextField } from "./Field.jsx";

const EMPTY = { card_number: "", first_time_pin: "", id_document_number: "", new_pin: "", confirm_pin: "" };

export default function ChangePin({ prefillCard = "" }) {
  const [form, setForm] = useState({ ...EMPTY, card_number: prefillCard });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [done, setDone] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (prefillCard) setForm((f) => ({ ...f, card_number: prefillCard }));
  }, [prefillCard]);

  const set = (name, value) => {
    setForm((f) => ({ ...f, [name]: value }));
    if (errors[name]) setErrors((e) => ({ ...e, [name]: undefined }));
  };
  const err = (k) => (Array.isArray(errors[k]) ? errors[k][0] : errors[k]);
  const p = (name, extra = {}) => ({ name, value: form[name], onChange: set, error: err(name), ...extra });
  const pin = { type: "password", inputMode: "numeric", maxLength: 4, autoComplete: "off" };

  async function submit(ev) {
    ev.preventDefault();
    setFormError("");
    const found = validatePinChange(form);
    setErrors(found);
    if (Object.keys(found).length) return;
    setBusy(true);
    try {
      const res = await changePin({ ...form, card_number: form.card_number.replace(/[\s-]/g, "") });
      setDone(res);
    } catch (e) {
      if (e instanceof ApiError) {
        setErrors(e.fields || {});
        setFormError(e.fields?._form?.[0] || e.message);
      } else setFormError("Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <section className="decision" aria-live="polite">
        <h2>Your PIN is updated</h2>
        <p>The card ending {done.masked_number.slice(-4)} now uses your new PIN. The first-time PIN no longer works.</p>
      </section>
    );
  }

  return (
    <form onSubmit={submit} noValidate className="form">
      <fieldset>
        <legend>Confirm it's you</legend>
        <TextField label="Card number" inputMode="numeric" autoComplete="off" {...p("card_number")} />
        <div className="grid two">
          <TextField label="First-time PIN" {...pin} {...p("first_time_pin")} />
          <TextField label="ID document number" autoComplete="off" hint="The one you used when applying" {...p("id_document_number")} />
        </div>
      </fieldset>
      <fieldset>
        <legend>Choose a new PIN</legend>
        <div className="grid two">
          <TextField label="New PIN" {...pin} {...p("new_pin")} />
          <TextField label="Confirm new PIN" {...pin} {...p("confirm_pin")} />
        </div>
      </fieldset>
      {formError ? <div className="banner error" role="alert">{formError}</div> : null}
      <button className="btn primary" type="submit" disabled={busy}>
        {busy ? "Updating…" : "Update PIN"}
      </button>
    </form>
  );
}
