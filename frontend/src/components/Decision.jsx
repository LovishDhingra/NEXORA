import { useState } from "react";

export default function Decision({ result, onSetPin, onStartOver }) {
  const [copied, setCopied] = useState(false);
  const card = result.card;

  if (result.status === "APPROVED" && card) {
    return (
      <section className="decision" aria-live="polite">
        <h2>You're approved for a {card.card_type.charAt(0) + card.card_type.slice(1).toLowerCase()} card</h2>
        <p>
          Your credit limit is <strong>${Number(card.credit_limit).toLocaleString("en-US")}</strong>. These details are
          shown once, so keep them somewhere safe before you leave this page.
        </p>
        <dl className="creds">
          <div><dt>Card number</dt><dd className="mono">{card.card_number.replace(/(.{4})/g, "$1 ").trim()}</dd></div>
          <div><dt>First-time PIN</dt><dd className="mono">{card.first_time_pin}</dd></div>
        </dl>
        <div className="actions">
          <button className="btn primary" onClick={() => onSetPin(card.card_number)}>Set your own PIN</button>
          <button
            className="btn"
            onClick={async () => {
              try {
                await navigator.clipboard.writeText(`Card ${card.card_number}\nFirst-time PIN ${card.first_time_pin}`);
                setCopied(true);
              } catch { /* clipboard unavailable */ }
            }}
          >
            {copied ? "Copied" : "Copy details"}
          </button>
        </div>
        <p className="msg hint">Application #{result.id} · credit score {result.credit_score}</p>
      </section>
    );
  }

  const docs = result.status === "DOCUMENTS_REQUESTED";
  return (
    <section className="decision" aria-live="polite">
      <h2>{docs ? "We need a few more documents" : "We can't offer a card right now"}</h2>
      <p>
        {docs
          ? "Your application is saved. We'll contact you about which additional documents to send."
          : "Your application didn't meet our minimum requirements."}
      </p>
      <p className="msg hint">{result.decision_reason} · Application #{result.id}</p>
      <div className="actions">
        <button className="btn" onClick={onStartOver}>Back to start</button>
      </div>
    </section>
  );
}
