// Client-side checks mirror the backend rules so people get feedback before submitting.
// The backend remains the source of truth.
export const DOC_RULES = {
  PASSPORT: { re: /^[A-Z0-9]{6,9}$/, msg: "Passport numbers have 6–9 letters or digits." },
  NATIONAL_ID: { re: /^[A-Z0-9]{8,16}$/, msg: "National ID numbers have 8–16 letters or digits." },
  DRIVING_LICENSE: { re: /^[A-Z0-9]{8,20}$/, msg: "Driving licence numbers have 8–20 letters or digits." },
  SSN: { re: /^\d{9}$/, msg: "A social security number has 9 digits." },
};

export const normalizeDoc = (v = "") => v.replace(/[\s-]/g, "").toUpperCase();

export function ageOf(iso) {
  const born = new Date(iso);
  if (Number.isNaN(born.getTime())) return null;
  const now = new Date();
  let age = now.getFullYear() - born.getFullYear();
  const before = now.getMonth() < born.getMonth() || (now.getMonth() === born.getMonth() && now.getDate() < born.getDate());
  return before ? age - 1 : age;
}

export function validateApplication(f) {
  const e = {};
  const req = (k, msg = "This field is required.") => {
    if (!String(f[k] ?? "").trim()) e[k] = msg;
  };
  ["first_name", "last_name", "date_of_birth", "email", "phone", "employer_name", "job_title", "annual_salary", "id_document_number"].forEach((k) => req(k));

  for (const k of ["first_name", "last_name"]) {
    if (!e[k] && !/^[\p{L} '.-]+$/u.test(f[k].trim())) e[k] = "Use letters only.";
  }
  if (!e.date_of_birth) {
    const age = ageOf(f.date_of_birth);
    if (age === null || age > 100) e.date_of_birth = "Enter a valid date of birth.";
    else if (age < 18) e.date_of_birth = "Applicants must be at least 18 years old.";
  }
  if (!e.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email)) e.email = "Enter a valid email address.";
  if (!e.phone && !/^\+?\d{10,15}$/.test(f.phone.replace(/[\s()-]/g, ""))) e.phone = "Enter 10–15 digits, with an optional leading +.";
  if (!e.annual_salary && !(Number(f.annual_salary) > 0)) e.annual_salary = "Annual salary must be greater than zero.";
  if (f.existing_credit_cards === "" || Number(f.existing_credit_cards) < 0 || !Number.isInteger(Number(f.existing_credit_cards)))
    e.existing_credit_cards = "Enter 0 or a whole number.";
  if (f.other_cards.some((c) => !c.issuer.trim())) e.other_cards = "Enter the issuing bank for each card.";
  if (!e.id_document_number) {
    const rule = DOC_RULES[f.id_document_type];
    if (rule && !rule.re.test(normalizeDoc(f.id_document_number))) e.id_document_number = rule.msg;
  }
  return e;
}

const WEAK = new Set(["0000", "1111", "2222", "3333", "4444", "5555", "6666", "7777", "8888", "9999", "1234", "4321", "2580", "0852"]);

export function validatePinChange(f) {
  const e = {};
  const digits = f.card_number.replace(/[\s-]/g, "");
  if (!/^\d{16}$/.test(digits)) e.card_number = "Enter your 16-digit card number.";
  if (!/^\d{4}$/.test(f.first_time_pin)) e.first_time_pin = "The first-time PIN is 4 digits.";
  if (!f.id_document_number.trim()) e.id_document_number = "Enter the ID document number from your application.";
  if (!/^\d{4}$/.test(f.new_pin)) e.new_pin = "A PIN must be exactly 4 digits.";
  else if (WEAK.has(f.new_pin)) e.new_pin = "That PIN is too easy to guess. Avoid repeated or sequential digits.";
  else if (f.new_pin === f.first_time_pin) e.new_pin = "Choose a PIN different from the first-time PIN.";
  if (!e.new_pin && f.confirm_pin !== f.new_pin) e.confirm_pin = "The two PINs do not match.";
  if (!f.confirm_pin && !e.confirm_pin) e.confirm_pin = "Confirm your new PIN.";
  return e;
}
