# Relay — Agentic Commerce Demonstration

A deployable demonstration of one guarded buyer agent coordinating independent TechNova and ElectroHub seller agents. The deterministic tool selector is always available; an LLM is optional and intentionally never gets database credentials.

## Run locally

1. Copy `.env.example` to `.env` and set values as needed. No credentials are required for the end-to-end demo mode.
2. Backend: `cd backend; python -m venv .venv; .venv\Scripts\activate; pip install -r requirements.txt; uvicorn app.main:app --reload --port 8000`
3. Frontend: `cd frontend; npm install; npm run dev`
4. Open `http://localhost:5173`; API docs are at `http://localhost:8000/docs` and the split-screen flow is `http://localhost:5173/flow`.

## Production deployment

Deploy `frontend` to a static host (Cloudflare Pages, GitHub Pages, or Netlify free tier) with `VITE_API_URL=https://YOUR-API`. Deploy `backend` to a Python host with HTTPS, set `DATABASE_URL` to a free PostgreSQL connection and `FRONTEND_URL` to the deployed frontend. Run `uvicorn app.main:app --host 0.0.0.0 --port $PORT` as the start command. Configure Razorpay Test webhook to `https://YOUR-API/api/payments/webhook` and set the matching `RAZORPAY_WEBHOOK_SECRET`.

For test checkout, set `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, and `RAZORPAY_WEBHOOK_SECRET`; the current UI uses secure demo payment verification when no credentials exist. Never put secrets in the frontend.

## Payment and autonomous-demo configuration

Normal mode uses Razorpay **Test Mode**. The browser receives only the public key and checkout order id. Its callback is signature-verified by the backend, then the UI polls the backend payment-status endpoint until the signed `payment.captured` webhook has made the order `PAID`.

Configure the following only in the backend environment (never commit values):

- `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`
- `RAZORPAY_DASHBOARD_URL` (optional inspection link)
- `RAZORPAY_WEBHOOK_URL=https://YOUR_API/api/payments/webhook`
- `AUTONOMOUS_MODE_MAX_AMOUNT=5000`
- `AUTONOMOUS_MODE_ALLOWED_CURRENCY=INR`
- `AUTONOMOUS_MODE_ALLOWED_CATEGORIES=headphones,electronics`

In the Razorpay dashboard, add `RAZORPAY_WEBHOOK_URL` as a public HTTPS webhook and configure the same webhook secret. Localhost is not reachable by Razorpay; use a temporary HTTPS tunnel for local webhook testing or deploy the backend. Webhook delivery is idempotent, so retries do not duplicate inventory, feedback, revenue, or audit effects.

Full Autonomous Mode is deliberately an **AUTONOMOUS TEST PAYMENT** path. It has no card credentials and no real-money capability. It uses the payment-provider abstraction, emits test capture/webhook events, and performs the same server-side payment-finalization path as a provider event.

## Three-minute demonstration

Launch **Buyer**, submit the prefilled headphones request, choose ElectroHub's Sony product, and confirm the test order. Open **Live flow** in a second tab to see every guardrail/tool/cache/seller event. Then use **Failure demo** to show TechNova rate-limited while ElectroHub remains available, and finish on **Reports** or **Audit**.
