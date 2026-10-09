const TIER_LABEL = { PLATINUM: "Platinum", GOLD: "Gold", VISA: "Visa" };

function formatNumber(n) {
  if (!n) return "•••• •••• •••• ••••";
  return n.replace(/(.{4})/g, "$1 ").trim();
}

function formatExpiry(iso) {
  if (!iso) return "••/••";
  const [y, m] = iso.split("-");
  return `${m}/${y.slice(2)}`;
}

/** The one expressive element: a card that fills in as the person types, then becomes their real card. */
export default function CardVisual({ tier, name, number, expires, limit, state = "draft" }) {
  const label = tier ? TIER_LABEL[tier] : "Your card";
  return (
    <figure className="card" data-tier={tier || "none"} data-state={state} aria-label={`${label} card preview`}>
      <div className="card-top">
        <span className="card-bank">Harbor</span>
        <span className="card-tier">{label}</span>
      </div>
      <div className="card-chip" aria-hidden="true" />
      <div className="card-number" aria-label={number ? "Card number" : "Card number, not issued yet"}>
        {formatNumber(number)}
      </div>
      <div className="card-bottom">
        <div>
          <span className="card-cap">Cardholder</span>
          <span className="card-name">{name?.trim() || "Your name"}</span>
        </div>
        <div>
          <span className="card-cap">Expires</span>
          <span className="card-val">{formatExpiry(expires)}</span>
        </div>
        {limit ? (
          <div>
            <span className="card-cap">Limit</span>
            <span className="card-val">${Number(limit).toLocaleString("en-US")}</span>
          </div>
        ) : null}
      </div>
    </figure>
  );
}
