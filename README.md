# Harbor Bank – Credit Card Application

Django REST + React + PostgreSQL implementation of the credit-card hackathon use case
(apply → credit rating → approve/reject/request documents → card + first-time PIN → PIN change).

## Run it

### Local setup
```bash
# 1. PostgreSQL (any running instance; these are the defaults the app expects)
#    user=cardapp password=cardapp db=cardapp host=localhost port=5432

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver            # http://localhost:8000

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev                           # http://localhost:5173  (proxies /api to Django)
```
Settings come from env vars: `POSTGRES_DB/USER/PASSWORD/HOST/PORT`, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`.
`USE_SQLITE=1` switches to SQLite for a quick run without Postgres.

### Tests
```bash
cd backend && python manage.py test        # 31 tests; needs Postgres (or USE_SQLITE=1)
```

## Business rules implemented

| Credit score rule (evaluated top to bottom) | Score |
|---|---|
| Holds 2+ credit cards | 300 |
| Salary > 200,000 USD | 500 |
| Salary 50,000–200,000 USD (inclusive) | 150 |
| Salary < 50,000 USD | 50 |

| Score | Decision | Limit |
|---|---|---|
| 500 | Platinum | 40,000 |
| 300 | Gold | 20,000 |
| 150 | Visa | 10,000 |
| 50 | Documents requested (no card) | – |
| below 50 | Rejected | – |

* An existing customer score is reused; otherwise it is calculated and saved on the customer.
* "Cards held" = cards the applicant declares at other banks + cards issued by this system.
* Cards get a Luhn-valid 16-digit number; the first-time PIN is random, stored **hashed**, and returned once.
* PIN change needs card number + first-time PIN + the ID document number used in the application.
  Weak PINs (1234, 0000…) are refused, the first-time PIN works only once, and 5 failed attempts lock the card.
* Every important step writes an `AuditLog` row (visible in `/admin/`).

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/applications/` | Flow 1–3: apply, rate, decide, issue card |
| GET | `/api/applications/<id>/` | Application status (card number masked) |
| POST | `/api/cards/change-pin/` | Flow 4: change first-time PIN |
| GET | `/api/health/` | Health check |

All errors share one shape: `{"error": {"code", "message", "fields": {field: [messages]}}}`.
Status codes: 400 validation, 409 conflict (duplicate application, identity mismatch, PIN already changed),
422 failed verification, 423 locked card.

## Layout

```
backend/
  core/            audit log, event outbox, error envelope, pure validators
  applications/    Customer + CreditApplication, Flow 1 orchestration
  credit_rating/   Flow 2 – scoring service
  cards/           Flow 3 (decision, issuance) and Flow 4 (PIN change)
frontend/          React (Vite): apply form, decision screen, PIN change
```

## Design decisions and assumptions

* **Services vs. apps:** the brief suggests microservices; this is a modular monolith with the same
  boundaries as separate Django apps (`applications`, `credit_rating`, `cards`). Each could be split out later.
* **Events:** domain events (`application.submitted`, `credit.score.determined`, `application.decided`,
  `card.issued`, `card.pin_changed`) are stored in a `DomainEvent` outbox table. If you set
  `KAFKA_BOOTSTRAP_SERVERS` and install `kafka-python`, they are also published to Kafka (topic `cardapp.events`).
  Flows run synchronously so the applicant gets an instant decision.
* **Gateway:** in development the Vite dev server proxies `/api` to Django. For production, put any reverse proxy (nginx, Caddy) in front and route `/api/` to Django and `/` to the built React files (`npm run build`).
* **Rule precedence:** when a customer holds 2+ cards *and* has a high salary, the card rule wins (300),
  following the order of the table in the problem statement.
* **No login:** the spec has none. Add authentication before using this for anything real, and move the
  first-time PIN to a secure channel (delivery is out of scope here, so the UI shows it once).
* "Reject" has no listed score, so scores below 50 (only possible for pre-existing scores) are rejected.
