import { useState } from "react";
import ApplyForm from "./components/ApplyForm.jsx";
import CardVisual from "./components/CardVisual.jsx";
import ChangePin from "./components/ChangePin.jsx";
import Decision from "./components/Decision.jsx";

export default function App() {
  const [tab, setTab] = useState("apply");
  const [draft, setDraft] = useState({ first_name: "", last_name: "" });
  const [result, setResult] = useState(null);
  const [pinCard, setPinCard] = useState("");

  const name = `${draft.first_name} ${draft.last_name}`;
  const card = result?.card;

  return (
    <div className="shell">
      <header className="top">
        <span className="brand">Harbor Bank</span>
        <nav aria-label="Sections">
          <button className={tab === "apply" ? "tab on" : "tab"} aria-current={tab === "apply"} onClick={() => setTab("apply")}>
            Apply for a card
          </button>
          <button className={tab === "pin" ? "tab on" : "tab"} aria-current={tab === "pin"} onClick={() => setTab("pin")}>
            Set your PIN
          </button>
        </nav>
      </header>

      <main className="layout">
        <aside className="visual">
          <CardVisual
            tier={card?.card_type}
            name={card ? result.applicant_name : name}
            number={card?.card_number}
            expires={card?.expires_on}
            limit={card?.credit_limit}
            state={card ? "issued" : "draft"}
          />
          <p className="visual-note">
            {card
              ? "This is your new card."
              : tab === "pin"
              ? "Use the card number and PIN from your approval."
              : "Your card takes shape as you fill in the form."}
          </p>
        </aside>

        <section className="panel">
          {tab === "apply" && !result && (
            <>
              <h1>Apply for a credit card</h1>
              <p className="lede">Five minutes, no paperwork. You'll get a decision as soon as you submit.</p>
              <ApplyForm onChange={setDraft} onResult={(r) => setResult(r)} />
            </>
          )}
          {tab === "apply" && result && (
            <Decision
              result={result}
              onSetPin={(n) => { setPinCard(n); setTab("pin"); }}
              onStartOver={() => { setResult(null); setDraft({ first_name: "", last_name: "" }); }}
            />
          )}
          {tab === "pin" && (
            <>
              <h1>Set your own PIN</h1>
              <p className="lede">Swap the first-time PIN for one only you know.</p>
              <ChangePin prefillCard={pinCard} />
            </>
          )}
        </section>
      </main>
    </div>
  );
}
