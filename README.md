# Relay — Agentic Commerce

**Relay** is an agentic-commerce demonstration where a buyer agent discovers products from independent seller agents, applies purchase guardrails, and completes a verifiable Razorpay Test Mode payment flow.

It makes AI-assisted purchasing transparent: visitors can see which tools were used, which seller responded, why a product was selected, and how payment and feedback are finalized.

## Live project

[Open Relay](https://relay-agentic-commerce-1.onrender.com/)

## What Relay demonstrates

- **Tool-mediated product discovery** — the Buyer Agent interprets a natural-language shopping request and queries approved Seller Agent tools rather than accessing merchant data directly.
- **Independent seller agents** — TechNova and ElectroHub expose isolated catalog, inventory, request, feedback, and reporting capabilities.
- **Product aggregation and ranking** — products are combined across sellers and ranked against the buyer’s stated need, budget, availability, and product fit.
- **Explicit human confirmation** — in normal mode, the buyer selects a product and confirms the purchase before checkout opens.
- **Guarded autonomous test purchases** — Full Autonomous Mode selects and completes only eligible *test* purchases inside configured category, currency, availability, and spend limits. It never uses real card credentials or real money.
- **Razorpay Test Mode integration** — the browser receives only Razorpay’s public checkout details. The backend validates the callback signature, confirms captured payment state with Razorpay, and safely handles later signed webhooks.
- **Idempotent payment finalization** — repeated callbacks or webhook deliveries cannot duplicate inventory updates, revenue, seller feedback, or audit events.
- **Live audit trail** — the architecture view surfaces persisted events across discovery, guardrails, seller tools, payment verification, webhooks, orders, and feedback.

## Purchase lifecycle

```text
Buyer request
  → Buyer Agent + guardrails
  → Seller Agent A and Seller Agent B tools
  → Product aggregation and ranking
  → User selection + confirmation (normal mode)
  → Razorpay Test Checkout
  → Signature verification + provider capture confirmation
  → Order, inventory, audit, and seller feedback updates
```

In autonomous mode, an autonomous-policy check and test-payment provider replace user selection and normal checkout.

## Trust and safety model

Relay deliberately keeps authority narrow:

- Buyer and seller agents use allowlisted tools.
- The LLM layer, when configured, never receives database credentials.
- Prompt-injection-like requests are blocked by guardrails.
- Normal purchases require explicit user confirmation.
- Autonomous purchases are constrained by a defined policy and clearly marked as test-only.
- Payment credentials and signature verification remain server-side.
- Webhook signatures are verified from the raw request body.

## Visibility for each participant

**Buyer view** provides discovery, comparison, cart, confirmation, payment status, completed orders, and activity history.

**Seller view** provides catalog access, incoming agent requests, orders, buyer-feedback metrics, and sales-oriented reporting.

**Architecture view** provides a live event stream, making the system a transparent multi-agent workflow rather than a black box.

## Future improvements

- **NLP feedback intelligence** — ingest free-text buyer feedback, classify sentiment and purchase intent, extract product attributes and recurring issues, and summarize insights per seller. For example, “great sound, but uncomfortable after an hour” can become measurable sound-quality and comfort signals.
- **Feedback-to-catalog loop** — use anonymized NLP insights to improve descriptions, ranking features, recommendation explanations, and seller inventory decisions, with human review before catalog changes.
- **Richer buyer preferences** — create an opt-in preference profile from explicit feedback and purchase history while maintaining clear user controls.
- **Multi-merchant expansion** — onboard more seller agents with scoped tool contracts, merchant-level policies, and quality benchmarks.
- **Advanced ranking** — combine semantic search, structured constraints, seller reliability, delivery estimates, and feedback-derived attribute scores.
- **Operational resilience** — add background reconciliation for delayed provider events, retry dashboards, alerting, and observability metrics.
- **Production hardening** — introduce role-based access control, encrypted secret management, database migrations, durable rate-limit storage, and full integration tests against Razorpay Test Mode.

## Core idea

Relay explores a practical version of agentic commerce: agents can make discovery and recommendation efficient, while guardrails, transparent tool use, explicit consent, and verifiable payment state keep each transaction understandable and controlled.
