# MyDTDC concept prototype

A Streamlit first draft for the DPM solution-space prototype. It demonstrates pickup booking, browser device-location capture, camera photo capture, collector contact details, pickup request tracking, sample consignment tracking, parcel events and ETA, a masked delivery-partner call request, wallet interactions, and GPT-5 nano support.

## Run locally

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

## Demo interactions

- Sample consignment numbers: `D1234567890` and `D9876543210`.
- Allow location access in the browser; the app attempts to capture device coordinates on open. Complete or correct the street address and PIN code before submitting.
- Book a pickup with the person handing over the parcel; use the camera on a phone or upload a location photo.
- Find booking references and the pickup progress view under **My Pickups**.
- Try the tracking issue flow, delivery-partner call request, demo wallet credit, and support assistant.
- Demo records are temporary and reset when the Streamlit session restarts.
- No actual pickup, payment, delivery-partner call, or DTDC live tracking action is triggered.

For automatic device location and camera access, use HTTPS (or `localhost` for local development) and allow the browser permission prompt. The prototype stores coordinates, not a verified street address: the user must review the address and add a PIN code. If location permission is declined or unavailable, type the address manually.

## Supabase connection

The app reads `SUPABASE_URL` and `SUPABASE_KEY` from Streamlit secrets or environment variables. To enable pickup request persistence, create a `pickup_requests` table:

```sql
create table public.pickup_requests (
  booking_id text primary key,
  sender_name text not null,
  phone text not null,
  pickup_address text not null,
  collector_name text not null,
  collector_phone text not null,
  pickup_latitude double precision,
  pickup_longitude double precision,
  pickup_date date not null,
  time_slot text not null,
  contents text not null,
  weight text not null,
  priority boolean not null default false,
  note text,
  status text not null default 'Pickup requested',
  created_at timestamptz not null default now()
);
```

Set secrets in `.streamlit/secrets.toml` (do not commit this file):

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key"
OPENAI_API_KEY = "your-openai-api-key"
```

The support assistant sends the recent chat conversation to OpenAI's Responses API using `gpt-5-nano`. Tell prototype testers that messages are sent to OpenAI. Keep the API key in server-side secrets; never put it in browser code or commit it. If the key is missing, the assistant explains that live AI is unavailable.

Use the Supabase anon key only with appropriate Row Level Security policies. Pickup requests are written to and loaded from `pickup_requests` when Supabase is configured. This prototype does not persist shipment records, support cases, wallet balances, user accounts, or photo files. Photos remain in the current Streamlit session only. Those need appropriate table design, access policies, and storage policies before a shared deployment.

The delivery-partner action is a UI demonstration only. A real masked call relay requires DTDC telephony integration and registered-customer verification. The sample shipment events and any shown partner details are fictional.

## Screenshot reference

The current theme is a clean, mobile-friendly approximation using DTDC red and navy. Replace the temporary wordmark, colors, labels, and typography details once the reference screenshot is added.

