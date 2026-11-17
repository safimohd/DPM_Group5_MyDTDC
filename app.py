from __future__ import annotations

import os
import json
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

try:
    from supabase import create_client
except ImportError:
    create_client = None
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

st.set_page_config(page_title="MyDTDC | Ship with confidence", page_icon="📦", layout="wide", initial_sidebar_state="auto")
location_component = components.declare_component("mydtdc_location", path=str(Path(__file__).parent / "location_component"))
NAVY, RED, PALE, INK, MUTED = "#102A43", "#D71920", "#F4F7FA", "#243B53", "#627D98"
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{{font-family:Inter,system-ui,sans-serif;color:{INK}}}.stApp{{background:{PALE}}}[data-testid="stHeader"]{{background:transparent}}
.block-container{{max-width:1160px;padding-top:1.15rem;padding-bottom:3rem}}.brandbar{{background:white;border:1px solid #E3EAF0;border-radius:16px;padding:14px 20px;display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;box-shadow:0 3px 14px #102a4308}}
.brand{{display:flex;gap:12px;align-items:center}}.brandmark{{height:42px;width:42px;display:grid;place-items:center;border-radius:12px;background:{RED};color:white;font-size:21px}}.brandname{{color:{NAVY};font-weight:800;font-size:20px;letter-spacing:-.5px}}.brandtag{{color:{MUTED};font-size:11px;margin-top:2px}}.demo-pill{{border-radius:999px;background:#FFF3E8;color:#9A4D00;padding:7px 11px;font-size:11px;font-weight:700}}
.role-pill-user{{border-radius:999px;background:#E8F4FF;color:#0A4580;padding:5px 10px;font-size:11px;font-weight:700;display:inline-block}}.role-pill-partner{{border-radius:999px;background:#FFF0F0;color:#8B0000;padding:5px 10px;font-size:11px;font-weight:700;display:inline-block}}.role-pill-franchise{{border-radius:999px;background:#F0F8F0;color:#1A5C1A;padding:5px 10px;font-size:11px;font-weight:700;display:inline-block}}
.hero{{background:linear-gradient(120deg,#102A43,#174B73);color:#fff;border-radius:20px;padding:28px 30px;margin-bottom:18px}}.hero h1{{font-size:30px;line-height:1.15;margin:0 0 8px;letter-spacing:-.8px;color:white}}.hero p{{margin:0;color:#D9E7F2;font-size:14px}}.hero-chip{{display:inline-block;margin-top:16px;border:1px solid #ffffff42;border-radius:999px;padding:7px 11px;font-size:11px;color:#EFF6FB}}
.hero-partner{{background:linear-gradient(120deg,#5C0A0A,#8B1A1A);color:#fff;border-radius:20px;padding:28px 30px;margin-bottom:18px}}.hero-partner h1{{font-size:30px;line-height:1.15;margin:0 0 8px;letter-spacing:-.8px;color:white}}.hero-partner p{{margin:0;color:#FFD9D9;font-size:14px}}
.card{{background:white;border:1px solid #E3EAF0;border-radius:16px;padding:19px;box-shadow:0 3px 14px #102a4308;margin-bottom:14px}}.card-title{{font-weight:750;color:{NAVY};font-size:16px;margin-bottom:4px}}.card-sub{{color:{MUTED};font-size:12px;margin-bottom:14px}}.kpi{{background:white;border:1px solid #E3EAF0;border-radius:14px;padding:15px}}.kpi-label{{color:{MUTED};font-size:11px}}.kpi-value{{color:{NAVY};font-size:18px;font-weight:750;margin-top:4px}}
.status{{display:inline-block;background:#E8F7EF;color:#16794B;border-radius:999px;padding:5px 9px;font-size:11px;font-weight:700}}.status-warn{{background:#FFF5E5;color:#9A6400}}.status-red{{background:#FFE9E9;color:#8B0000}}.status-delay{{background:#FEF3C7;color:#92400E;border:1px solid #FCD34D}}.timeline{{border-left:2px solid #D9E2EC;margin:10px 0 8px 8px;padding-left:19px}}.event{{position:relative;padding:1px 0 17px}}.event:before{{content:"";width:10px;height:10px;border-radius:50%;background:#2F855A;border:2px solid white;position:absolute;left:-25px;top:4px;box-shadow:0 0 0 1px #2F855A}}.event.future:before{{background:white;box-shadow:0 0 0 1px #9FB3C8}}.event b{{color:{NAVY};font-size:13px}}.event small{{display:block;color:{MUTED};margin-top:3px;font-size:11px}}.feature-note{{color:{MUTED};font-size:11px;padding:10px 12px;background:#F4F7FA;border-radius:10px}}
.order-summary-card{{background:#F0F7FF;border:1px solid #BFDBFE;border-radius:12px;padding:14px;margin-bottom:10px;cursor:pointer}}.order-summary-card:hover{{background:#DBEAFE}}.partner-order-card{{background:white;border:1px solid #E3EAF0;border-radius:14px;padding:16px;margin-bottom:12px;box-shadow:0 2px 8px #102a4308}}
div.stButton>button{{border-radius:10px;font-weight:650}}div[data-testid="stForm"]{{background:white;border:1px solid #E3EAF0;padding:18px;border-radius:15px}}.footer{{text-align:center;color:#829AB1;font-size:11px;padding:16px 0 2px}}@media(max-width:700px){{.hero h1{{font-size:24px}}.hero{{padding:22px}}.brandbar{{padding:12px 14px}}}}
</style>""", unsafe_allow_html=True)

# ── helpers ────────────────────────────────────────────────────────────────────

def get_db():
    try:
        secrets = st.secrets
        url = secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
        key = secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
    if url and key and create_client:
        try:
            return create_client(url, key)
        except Exception as exc:
            st.warning(f"Supabase unavailable; using demo data for this session. ({exc})")
    return None

def get_secret(name):
    try:
        return st.secrets.get(name, os.getenv(name, ""))
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return os.getenv(name, "")

IIMB_PICKUP_ADDRESS = {
    "address_house": "Main Gate", "address_road": "Bannerghatta Road",
    "address_area": "IIM Bangalore, Bannerghatta Main Road",
    "address_city": "Bengaluru", "address_state": "Karnataka",
    "address_pincode": "560076",
}

@st.cache_resource()
def db():
    return get_db()

@st.cache_data(ttl=3600)
def _load_ground_photo() -> str:
    """Read the IIMB ground photo once per session and cache it."""
    _b64_path = Path(__file__).parent / "iimb_ground_photo.b64"
    if _b64_path.exists():
        return _b64_path.read_text().strip()
    return ""

@st.cache_data
def sample_shipments():
    today = date.today()
    return {
        "D1234567890": {"consignment_no":"D1234567890","recipient":"Aarav Mehta","origin":"Bengaluru, Karnataka","destination":"Mumbai, Maharashtra","status":"In transit","eta":(today+timedelta(days=2)).isoformat(),"overall_eta_label":f"Expected delivery by {(today+timedelta(days=2)).strftime('%a, %d %b')} · 2 days away","updated":datetime.now().strftime("%d %b, %I:%M %p"),"events":[{"title":"Shipment picked up","place":"Indiranagar, Bengaluru","time":"Today, 10:42 AM","done":True,"phase_eta":None},{"title":"Arrived at Bengaluru hub","place":"Bengaluru, Karnataka","time":"Today, 02:15 PM","done":True,"phase_eta":None},{"title":"In transit to destination","place":"Next scan pending","time":"On the way","done":False,"phase_eta":"Expected at Mumbai hub by 11 PM tonight"},{"title":"Out for delivery","place":"Mumbai, Maharashtra","time":"Estimated delivery day","done":False,"phase_eta":f"Expected out for delivery on {(today+timedelta(days=2)).strftime('%d %b')}"}],"delivery_partner":"Will be shared when out for delivery"},
        "D9876543210": {"consignment_no":"D9876543210","recipient":"Demo Receiver","origin":"Delhi, NCR","destination":"Pune, Maharashtra","status":"Out for delivery","eta":date.today().isoformat(),"overall_eta_label":f"Expected delivery today · {date.today().strftime('%d %b')} · Out for delivery now","updated":datetime.now().strftime("%d %b, %I:%M %p"),"events":[{"title":"Shipment picked up","place":"Connaught Place, Delhi","time":"Yesterday, 09:10 AM","done":True,"phase_eta":None},{"title":"Arrived at Pune hub","place":"Pune, Maharashtra","time":"Today, 06:20 AM","done":True,"phase_eta":None},{"title":"Out for delivery","place":"Pune, Maharashtra","time":"Today, 09:05 AM","done":True,"phase_eta":None},{"title":"Delivered","place":"Your delivery address","time":"Pending","done":False,"phase_eta":"Expected by 6 PM today"}],"delivery_partner":"Rohit S."},
        "D7777777777": {"consignment_no":"D7777777777","recipient":"Priya Sharma","origin":"Chennai, Tamil Nadu","destination":"Hyderabad, Telangana","status":"Delayed","eta":(today+timedelta(days=1)).isoformat(),"overall_eta_label":f"Delayed — originally expected {date.today().strftime('%d %b')} · now expected {(today+timedelta(days=1)).strftime('%a, %d %b')}","updated":datetime.now().strftime("%d %b, %I:%M %p"),"events":[{"title":"Shipment picked up","place":"Chennai, Tamil Nadu","time":"Yesterday, 08:30 AM","done":True,"phase_eta":None},{"title":"Arrived at Chennai hub","place":"Chennai Hub","time":"Yesterday, 02:00 PM","done":True,"phase_eta":None},{"title":"In transit — delayed","place":"Held at Bengaluru sorting facility","time":"Today, 06:45 AM","done":False,"phase_eta":"Delay of approx. 24 hrs due to sorting backlog"},{"title":"Out for delivery","place":"Hyderabad, Telangana","time":"Rescheduled","done":False,"phase_eta":f"Expected out for delivery {(today+timedelta(days=1)).strftime('%d %b')}"}],"delivery_partner":"Will be shared when out for delivery"}
    }

@st.cache_data
def sample_partner_deliveries():
    """Deliveries the partner must drop off today — destinations near IIM Bangalore."""
    return [
        {"order_id":"DLV-7832","recipient_area":"Koramangala, 5th Block","recipient_name":"A. Sharma","weight":"1.2 kg","contents":"Electronics","lat":12.9352,"lng":77.6245,"eta_window":"10 AM – 1 PM","status":"Pending delivery","distance_km":"4.2"},
        {"order_id":"DLV-7849","recipient_area":"HSR Layout, Sector 2","recipient_name":"P. Nair","weight":"0.5 kg","contents":"Documents","lat":12.9116,"lng":77.6389,"eta_window":"11 AM – 2 PM","status":"Pending delivery","distance_km":"6.8"},
        {"order_id":"DLV-7861","recipient_area":"JP Nagar, Phase 3","recipient_name":"S. Reddy","weight":"2.4 kg","contents":"Clothing","lat":12.9063,"lng":77.5857,"eta_window":"1 PM – 4 PM","status":"Pending delivery","distance_km":"3.1"},
    ]

@st.cache_data
def sample_partner_pickups():
    """Pickups the partner must collect today — sources near IIM Bangalore."""
    return [
        {"order_id":"PKP-5021","sender_area":"IIM Bangalore, Main Gate","sender_name":"Demo User","weight":"Up to 0.5 kg","contents":"Documents","lat":12.9343,"lng":77.5953,"slot":"9 AM – 12 PM","status":"Awaiting collection","distance_km":"0.0","note":"Ring the bell at the gate"},
        {"order_id":"PKP-5035","sender_area":"Bilekahalli, Bannerghatta Road","sender_name":"R. Kumar","weight":"0.5–2 kg","contents":"Personal items","lat":12.9124,"lng":77.5987,"slot":"12 PM – 3 PM","status":"Awaiting collection","distance_km":"2.5","note":"Call on arrival"},
        {"order_id":"PKP-5047","sender_area":"Arekere Gate, Bannerghatta Road","sender_name":"M. Verma","weight":"2–5 kg","contents":"Clothing","lat":12.8975,"lng":77.6012,"slot":"3 PM – 6 PM","status":"Awaiting collection","distance_km":"4.8","note":""},
    ]

# ── session state ──────────────────────────────────────────────────────────────

if "shipments" not in st.session_state: st.session_state.shipments = sample_shipments()
if "pickup_requests" not in st.session_state:
    _demo_pickup_date = (date.today() + timedelta(days=1)).isoformat()
    st.session_state.pickup_requests = [{
        "booking_id": "PU4A8B2C1D","sender_name": "Demo User","phone": "9876543210",
        "pickup_address": "Main Gate, Bannerghatta Road, IIM Bangalore, Bengaluru, Karnataka, 560076",
        "house_number": "Main Gate","road": "Bannerghatta Road",
        "area": "IIM Bangalore, Bannerghatta Main Road","city": "Bengaluru",
        "state": "Karnataka","pincode": "560076","collector_name": "Demo User",
        "collector_phone": "9876543210","pickup_latitude": None,"pickup_longitude": None,
        "photo_data": None,"pickup_date": _demo_pickup_date,"time_slot": "9 AM – 12 PM",
        "contents": "Documents","weight": "Up to 0.5 kg","priority": False,
        "note": "Ring the bell at the gate","status": "Pickup partner on the way",
        "partner_name": "Rahul M.","created_at": datetime.now().isoformat(),
    }]
if "wallet_balance" not in st.session_state: st.session_state.wallet_balance = 250
if "chat" not in st.session_state: st.session_state.chat = []
if "nav" not in st.session_state: st.session_state.nav = "Home"
if "pending_nav" not in st.session_state: st.session_state.pending_nav = None
# saved addresses for repeat booking
if "saved_addresses" not in st.session_state: st.session_state.saved_addresses = []
# toast dismissal tracking per shipment
if "toast_dismissed" not in st.session_state: st.session_state.toast_dismissed = set()
# stale-status watchdog: shipments with no scan in 48h (demo: D7777777777 is hardcoded stale)
if "stale_watchdog_dismissed" not in st.session_state: st.session_state.stale_watchdog_dismissed = set()
if "pickup_requests_loaded" not in st.session_state: st.session_state.pickup_requests_loaded = False
if "iimb_address_prefilled" not in st.session_state: st.session_state.iimb_address_prefilled = False
# location: only triggered on explicit button click
if "location_triggered" not in st.session_state: st.session_state.location_triggered = False
if "location_permission_granted" not in st.session_state: st.session_state.location_permission_granted = False
if "location_lat" not in st.session_state: st.session_state.location_lat = None
if "location_lng" not in st.session_state: st.session_state.location_lng = None
if "location_confirmed" not in st.session_state: st.session_state.location_confirmed = False
# camera: only shown after explicit button click
if "show_camera" not in st.session_state: st.session_state.show_camera = False
# role selector
if "app_role" not in st.session_state: st.session_state.app_role = "User"
# partner call states
if "partner_deliveries" not in st.session_state: st.session_state.partner_deliveries = sample_partner_deliveries()
if "partner_pickups" not in st.session_state: st.session_state.partner_pickups = sample_partner_pickups()
if "partner_nav" not in st.session_state: st.session_state.partner_nav = "Deliveries Today"

for field in ("address_house","address_road","address_area","address_city","address_state","address_pincode"):
    if field not in st.session_state: st.session_state[field] = ""
if not st.session_state.iimb_address_prefilled:
    for field, value in IIMB_PICKUP_ADDRESS.items():
        if not st.session_state[field]: st.session_state[field] = value
    st.session_state.iimb_address_prefilled = True
if "pickup_call_requested" not in st.session_state: st.session_state.pickup_call_requested = set()
if "track_pickup_id" not in st.session_state: st.session_state.track_pickup_id = "PU4A8B2C1D"

client = db()
backend = "Supabase connected" if client else "Demo mode · session data"

# ── brandbar + role selector ───────────────────────────────────────────────────

role_labels = {"User": "🧑  User", "Delivery Partner": "🚴  Delivery Partner", "Franchisee": "🏢  Franchisee"}
role_pill_class = {"User": "role-pill-user", "Delivery Partner": "role-pill-partner", "Franchisee": "role-pill-franchise"}
current_role = st.session_state.app_role

bar_left, bar_right = st.columns([2, 1.4])
with bar_left:
    st.markdown(f"<div class='brand' style='padding:10px 0'><div class='brandmark'>D</div><div><div class='brandname'>MyDTDC</div><div class='brandtag'>Ship with confidence</div></div></div>", unsafe_allow_html=True)
with bar_right:
    role_cols = st.columns([1, 1.6])
    role_cols[0].markdown(f"<div style='padding-top:10px'><span class='{role_pill_class[current_role]}'>{role_labels[current_role]}</span> &nbsp; <span style='color:{MUTED};font-size:11px'>{backend}</span></div>", unsafe_allow_html=True)
    new_role = role_cols[1].selectbox("Switch role", list(role_labels.keys()), index=list(role_labels.keys()).index(current_role), label_visibility="collapsed", key="role_selector")
    if new_role != st.session_state.app_role:
        st.session_state.app_role = new_role
        st.session_state.nav = "Home"
        st.session_state.partner_nav = "Deliveries Today"
        st.rerun()

st.markdown("<hr style='margin:0 0 18px;border:none;border-top:1px solid #E3EAF0'>", unsafe_allow_html=True)

# ── Sidebar — persistent support shortcut and delay alerts ────────────────────
with st.sidebar:
    st.markdown(f"<div style='font-size:16px;font-weight:800;color:{NAVY};padding-bottom:4px'>MyDTDC</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:11px;color:#627D98;margin-bottom:14px'>Quick access</div>", unsafe_allow_html=True)
    if st.button("💬  Help & Support", key="sidebar_help", use_container_width=True):
        st.session_state.pending_nav = "Help & Support"; st.rerun()
    if st.button("📦  My Shipments", key="sidebar_shipments", use_container_width=True):
        st.session_state.pending_nav = "My Shipments"; st.rerun()
    if st.button("🗓  My Pickups", key="sidebar_pickups", use_container_width=True):
        st.session_state.pending_nav = "My Pickups"; st.rerun()
    if st.button("📍  My Saved Addresses", key="sidebar_saved_addr", use_container_width=True):
        st.session_state.pending_nav = "My Saved Addresses"; st.rerun()
    # Delay alerts in sidebar (User role only)
    _sb_delayed = [k for k, v in st.session_state.shipments.items() if v.get("status") == "Delayed"]
    if _sb_delayed and st.session_state.app_role == "User":
        st.markdown("<hr style='margin:12px 0;border:none;border-top:1px solid #E3EAF0'>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:11px;font-weight:700;color:#92400E;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px'>⚠️ Delay alerts</div>", unsafe_allow_html=True)
        for _dk in _sb_delayed:
            _ds = st.session_state.shipments[_dk]
            st.markdown(f"<div style='font-size:11px;color:#78350F;background:#FEF3C7;border-radius:8px;padding:8px 10px;margin-bottom:6px'><b>{_dk}</b><br>{_ds['origin']} → {_ds['destination']}</div>", unsafe_allow_html=True)
            if st.button(f"Track {_dk}", key=f"sb_track_{_dk}", use_container_width=True):
                st.session_state.track_number = _dk; st.session_state.pending_nav = "Track Shipment"; st.rerun()
    # Saved addresses quick-access in sidebar (User role only)
    if st.session_state.app_role == "User" and st.session_state.saved_addresses:
        st.markdown("<hr style='margin:12px 0;border:none;border-top:1px solid #E3EAF0'>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:11px;font-weight:700;color:{NAVY};text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px'>📍 Saved addresses</div>", unsafe_allow_html=True)
        for _sa in st.session_state.saved_addresses:
            st.markdown(f"<div style='font-size:11px;color:{INK};background:#EFF6FF;border-radius:8px;padding:8px 10px;margin-bottom:6px'><b>{_sa['label']}</b><br><span style='color:{MUTED}'>{_sa.get('area','')}, {_sa.get('city','')}</span></div>", unsafe_allow_html=True)
            if st.button("Book from here", key=f"sb_book_{_sa['label']}", use_container_width=True):
                for _fld in ("house","road","area","city","state","pincode"):
                    st.session_state[f"address_{_fld}"] = _sa.get(_fld, "")
                st.session_state.last_saved_fill = _sa["label"]
                st.session_state.pending_nav = "Book a Pickup"
                st.rerun()

# ── shared helpers ─────────────────────────────────────────────────────────────

def save_pickup(record):
    st.session_state.pickup_requests.insert(0, record)
    if client:
        try:
            db_record = {k: v for k, v in record.items() if k not in {"photo_data", "location_accuracy"}}
            client.table("pickup_requests").insert(db_record).execute()
        except Exception as exc:
            st.info(f"Saved for this session. Supabase write did not complete: {exc}")

def load_pickups():
    if client and not st.session_state.pickup_requests_loaded:
        try:
            rows = client.table("pickup_requests").select("*").order("created_at", desc=True).limit(50).execute().data or []
            known = {p.get("booking_id") for p in st.session_state.pickup_requests}
            st.session_state.pickup_requests.extend(p for p in rows if p.get("booking_id") not in known)
        except Exception:
            st.info("Showing pickup requests from this session.")
        st.session_state.pickup_requests_loaded = True

def _smart_reply(prompt, context):
    p = prompt.lower()
    loc_q = any(w in p for w in ["where","location","map","track","how far","distance","when","eta","arrive","coming","reach","status","update","order"])
    cancel_q = any(w in p for w in ["cancel","reschedule","change","modify","update address","rebook","new slot","new time"])
    agent_q = any(w in p for w in ["agent","executive","human","call","speak","talk","connect","escalate"])
    complaint_q = any(w in p for w in ["complaint","damage","lost","missing","wrong","delay","late","not delivered"])
    charge_q = any(w in p for w in ["charge","charges","price","pricing","cost","rate","fee","payment","how much","billing","invoice","paid","pay"])
    after_collect_q = any(w in p for w in ["after collect","once collected","parcel collected","after pickup","what next","next step","transit","then what","consignment"])
    delivery_q = any(w in p for w in ["deliver","delivery","receiving","receive","incoming","someone sending","being sent","arriving","shipment arriving","expecting"])

    if cancel_q:
        ref_hint = ""
        if context and "No sample" not in context:
            try:
                rec = json.loads(context); ref_hint = f" (Ref: {rec.get('booking_id') or rec.get('consignment_no','')})"
            except Exception: pass
        return (f"Cancellations and rescheduling{ref_hint} need to go through our operations team since a partner may already be assigned. "
                f"Please use the support request form below, select 'Booking and Tracking' and choose 'Update booking details'. "
                f"Our team typically responds within 2 hours during office hours.")
    if agent_q:
        return ("You can reach a DTDC support executive at 1800-123-3339 (toll-free, 9 AM to 6 PM, Mon to Sat). "
                "Outside those hours, submit a support request below and we'll call you back within the next business day.")
    if complaint_q:
        return ("I'm sorry to hear that. For complaints about damage, delays, or missing parcels, please file a support request below "
                "with your consignment number. Our team will investigate and respond within 24 hours.")
    if charge_q:
        return ("Shipping charges depend on the parcel weight, dimensions, service type (local or national), and pickup location. "
                "You can get an instant quote on the Book a Pickup screen before confirming. "
                "If you've already been charged and have a concern, please raise a support request below with your booking reference.")
    if after_collect_q:
        ref_hint = ""
        if context and "No sample" not in context:
            try:
                rec = json.loads(context); ref_hint = f" for booking {rec.get('booking_id','')}" if rec.get('booking_id') else ""
            except Exception: pass
        return (f"Once your parcel is collected{ref_hint}, DTDC assigns a consignment number within a few hours. "
                f"From that point you can track the shipment's journey under Track Shipment using that number. "
                f"You'll move through: In Transit, then Out for Delivery, then Delivered. "
                f"For intercity shipments, typical transit is 2 to 5 business days depending on the route.")
    if delivery_q:
        return ("To track an incoming shipment, you'll need the consignment number from the sender. "
                "Head to Track Shipment and enter that number. You'll see the current stage, the expected delivery date, "
                "and each checkpoint the parcel has passed through. "
                "If the sender hasn't shared the number yet, ask them to check their MyDTDC booking confirmation.")

    if context and "No sample" not in context:
        try:
            rec = json.loads(context)
        except Exception:
            rec = {}
        kind = rec.get("kind", "")
        status = rec.get("status", "")
        ref = rec.get("booking_id") or rec.get("consignment_no", "")

        if kind == "pickup request":
            slot = rec.get("time_slot", "your scheduled slot")
            pdate = rec.get("pickup_date", "")
            date_str = f" on {pdate}" if pdate else ""
            if status == "Pickup partner on the way":
                if loc_q:
                    return (f"Your pickup partner Rahul M. is on the way to your location right now! "
                            f"He's about 1.8 km away and should reach you in roughly 10 to 15 minutes{date_str} during {slot}. "
                            f"Please keep your parcel ready and stay near the pickup address. "
                            f"You can see his live position on the Track Pickup screen.")
                return (f"Your pickup (Ref: {ref}) is active. Rahul M. is heading to you{date_str} during {slot}. "
                        f"Tap 'Track pickup partner' to follow him on the map.")
            elif status == "Parcel collected":
                return (f"Your parcel has been collected by DTDC! Booking {ref} is now in transit. "
                        f"You can track the shipment status under Track Shipment once a consignment number is assigned.")
            else:
                return f"Your pickup {ref} is currently showing status: {status}. If you need more details or have a concern, please raise a support request below."

        elif kind == "sample shipment":
            eta = rec.get("eta", ""); dest = rec.get("destination", "")
            eta_str = f" Expected delivery: {eta}." if eta else ""
            dest_str = f" to {dest}" if dest else ""
            if status == "Out for delivery":
                if loc_q:
                    return (f"Your shipment {ref} is out for delivery{dest_str} today!{eta_str} "
                            f"The delivery executive is on their route and should reach you shortly. "
                            f"Please keep your phone accessible and ensure someone is available at the address.")
                return f"Your shipment {ref} is out for delivery{dest_str}.{eta_str} Stay available at the delivery address."
            elif "transit" in status.lower():
                return (f"Your shipment {ref} is in transit{dest_str}.{eta_str} "
                        f"It's moving through the DTDC network and will be out for delivery on the expected date.")
            elif "delivered" in status.lower():
                return f"Your shipment {ref} has been delivered{dest_str}. If you haven't received it, please raise a support request below."
            else:
                return f"Your shipment {ref} is currently: {status}.{eta_str} For detailed tracking, check the Track Shipment screen."

    if loc_q:
        return ("I can look up your order status right away. Please select one of your active orders above, "
                "or enter your pickup booking ID or shipment consignment number in the reference field. "
                "For the demo, try entering **PU4A8B2C1D**.")
    return ("I'm here to help with your DTDC shipments and pickups. "
            "Could you share your booking or consignment number, or select an active order above?")

def support_answer(history, prompt, service, topic, context):
    return _smart_reply(prompt, context)

def support_record_context(reference):
    reference = (reference or "").strip().upper()
    if not reference:
        return ""
    shipment = st.session_state.shipments.get(reference)
    if shipment:
        return json.dumps({"kind":"sample shipment","consignment_no":reference,"status":shipment.get("status"),"eta":shipment.get("eta"),"updated":shipment.get("updated"),"origin":shipment.get("origin"),"destination":shipment.get("destination")},ensure_ascii=False)
    pickup = next((p for p in st.session_state.pickup_requests if p.get("booking_id","").upper() == reference), None)
    if pickup:
        return json.dumps({"kind":"pickup request","booking_id":reference,"status":pickup.get("status"),"pickup_date":pickup.get("pickup_date"),"time_slot":pickup.get("time_slot")},ensure_ascii=False)
    return f"No sample shipment or pickup record matches reference {reference}. Do not infer a status."

SUPPORT_MENU = {
    "Local (Intracity)": {
        "General Information":["General query","Service availability","Contact support"],
        "Booking and Tracking":["Book a pickup","Shipment status","Update booking details"],
        "Pricing and Payment":["Check charges","Payment methods","Payment and refund details"],
        "Safety, Security and Support":["Report a delivery issue","On-field staff issue","Parcel safety"],
        "Special Services & Business Solutions":["Business shipping","Special handling","Other services"],
        "General Queries":["Shipment Status","Updating Order Details","Accepting Your Order","Managing Returns","Reporting Issues About Delivered Shipments","Payment and Refund Details","Service Related Queries","On Field Staff Issues"],
    },
    "National Courier": {
        "General queries":["General query","Booking a shipment","Pickup service"],
        "Shipment Status":["Track a shipment","Tracking has not updated","Estimated delivery"],
        "Address and Contact Detail Update":["Change delivery address","Update contact details","Add delivery instructions"],
        "Issue Reporting":["Marked delivered but not received","Delivery attempt did not happen","Report a parcel issue"],
    },
}

SUPPORT_SUGGESTIONS = {
    "General query":["What can MyDTDC help me with?","How do I track my parcel?","How do I book a pickup?"],
    "General Information":["What services does DTDC offer?","How do I contact DTDC support?","What are the available pickup time slots?"],
    "Shipment Status":["Where is my shipment?","My tracking has not updated. What can I check?","It says delivered but I have not received it."],
    "Book a pickup":["How do I schedule a pickup?","Where can I see my pickup booking?","How do I change my pickup time?"],
    "Issue Reporting":["My parcel is marked delivered, but I do not have it.","A delivery attempt did not happen.","I need to report a parcel issue."],
    "Reporting Issues About Delivered Shipments":["My parcel is marked delivered, but I do not have it."],
    "Pricing and Payment":["How can I check the price?","What payment options are available?","I need help with a refund."],
    "Address and Contact Detail Update":["How can I update my delivery address?","Can I change the contact number?"],
}

def header(title, subtitle):
    st.markdown(f"<div class='card-title' style='font-size:23px'>{title}</div><div class='card-sub'>{subtitle}</div>", unsafe_allow_html=True)

def partner_map(lat_dest, lng_dest, label_dest, lat_partner=12.9490, lng_partner=77.5930):
    center_lat = (lat_dest + lat_partner) / 2
    center_lng = (lng_dest + lng_partner) / 2
    return f"""
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<div id="pmap_{uuid.uuid4().hex[:6]}" style="height:260px;border-radius:14px;overflow:hidden;border:1px solid #E3EAF0;" id="pmap"></div>
<script>
(function(){{
var map=L.map(document.querySelectorAll('[style*="height:260px"]')[document.querySelectorAll('[style*="height:260px"]').length-1]).setView([{center_lat},{center_lng}],13);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{maxZoom:19,attribution:'© OpenStreetMap'}}).addTo(map);
var destIcon=L.divIcon({{html:'<div style="background:#102A43;color:white;border-radius:50%;width:34px;height:34px;display:flex;align-items:center;justify-content:center;font-size:16px;border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,.35)">📍</div>',iconSize:[34,34],iconAnchor:[17,17],className:''}});
var youIcon=L.divIcon({{html:'<div style="background:#D71920;color:white;border-radius:50%;width:36px;height:36px;display:flex;align-items:center;justify-content:center;font-size:17px;border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,.35)">🚴</div>',iconSize:[36,36],iconAnchor:[18,18],className:''}});
L.marker([{lat_dest},{lng_dest}],{{icon:destIcon}}).addTo(map).bindPopup('<b>{label_dest}</b>').openPopup();
L.marker([{lat_partner},{lng_partner}],{{icon:youIcon}}).addTo(map).bindPopup('<b>Your location (demo)</b>');
L.polyline([[{lat_partner},{lng_partner}],[{(lat_dest+lat_partner)/2},{(lng_dest+lng_partner)/2}],[{lat_dest},{lng_dest}]],{{color:'#D71920',weight:3,dashArray:'6,6',opacity:0.7}}).addTo(map);
}})();
</script>"""

# ══════════════════════════════════════════════════════════════════════════════
# ROLE: USER
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state.app_role == "User":
    pages = ["Home","Book a Pickup","Track Shipment","Track Pickup","My Shipments","My Pickups","Wallet","Help & Support"]
    # My Saved Addresses is sidebar-only — handle pending_nav before the radio renders
    if st.session_state.pending_nav == "My Saved Addresses":
        st.session_state.nav = "My Saved Addresses"
        st.session_state.pending_nav = None
    elif st.session_state.pending_nav in pages:
        st.session_state.nav = st.session_state.pending_nav
        st.session_state.pending_nav = None
    # Only show radio when not on the sidebar-only page
    if st.session_state.get("nav") != "My Saved Addresses":
        selected = st.radio("Navigation", pages, horizontal=True, label_visibility="collapsed", key="nav")
    else:
        selected = "My Saved Addresses"

    # ── HOME ──────────────────────────────────────────────────────────────────
    if selected == "Home":
        st.markdown("<div class='hero'><h1>Your parcels, on the move.</h1><p>Book a pickup, follow every milestone and know what happens next.</p><span class='hero-chip'>📍 12,000+ PIN codes &nbsp; · &nbsp; 🚚 Doorstep pickup &nbsp; · &nbsp; 🔔 Helpful updates</span></div>", unsafe_allow_html=True)
        left, right = st.columns([1.35, 1])
        with left:
            st.markdown("<div class='card'><div class='card-title'>Track a shipment</div><div class='card-sub'>Enter your DTDC consignment number to see the latest updates.</div></div>", unsafe_allow_html=True)
            with st.form("home_track"):
                number = st.text_input("Consignment number", value="D1234567890", placeholder="e.g. D1234567890")
                go = st.form_submit_button("Track shipment", type="primary", use_container_width=True)
            if go:
                st.session_state.track_number = number.strip().upper()
                st.session_state.pending_nav = "Track Shipment"
                st.rerun()
        with right:
            st.markdown("<div class='card'><div class='card-title'>Send a parcel</div><div class='card-sub'>Schedule a pickup from your doorstep in a few simple steps.</div></div>", unsafe_allow_html=True)
            if st.button("＋  Book a pickup", use_container_width=True, type="primary"):
                st.session_state.pending_nav = "Book a Pickup"; st.rerun()
            if st.button("View all shipments", use_container_width=True):
                st.session_state.pending_nav = "My Shipments"; st.rerun()
        # Delay notification toasts — compact inline cards with a working ✕ dismiss button
        delayed_shipments = [k for k, v in st.session_state.shipments.items() if v.get("status") == "Delayed"]
        active_toasts = [dk for dk in delayed_shipments if dk not in st.session_state.toast_dismissed]
        for dk in active_toasts:
            ds = st.session_state.shipments[dk]
            # Layout: notification content on the left, ✕ button on the far right
            _tcol_content, _tcol_btn = st.columns([10, 1])
            with _tcol_content:
                st.markdown(f"""<div style='background:#1C1C1E;color:#fff;border-radius:10px;
  padding:11px 14px;margin-bottom:4px;display:flex;align-items:flex-start;
  gap:10px;border-left:4px solid #FFC107;'>
  <div style='font-size:17px;line-height:1.4'>⚠️</div>
  <div style='flex:1'>
    <div style='font-size:11px;font-weight:700;color:#FFC107;text-transform:uppercase;letter-spacing:.07em'>Shipment Delayed</div>
    <div style='font-size:13px;font-weight:600;margin-top:3px'>{dk} &nbsp;·&nbsp; {ds["origin"]} → {ds["destination"]}</div>
    <div style='font-size:11px;color:#aaa;margin-top:2px'>{ds.get("overall_eta_label","")}</div>
  </div>
</div>""", unsafe_allow_html=True)
            with _tcol_btn:
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                if st.button("✕", key=f"toast_dismiss_{dk}", help="Dismiss this alert"):
                    st.session_state.toast_dismissed.add(dk)
                    st.rerun()

        st.markdown("<div class='card-title' style='margin:8px 0 12px'>Your recent shipments</div>", unsafe_allow_html=True)
        cols = st.columns(2)
        for col, key in zip(cols, list(st.session_state.shipments)[:2]):
            s = st.session_state.shipments[key]
            with col:
                status_badge = "status-delay" if s["status"] == "Delayed" else "status"
                st.markdown(f"<div class='card'><div style='display:flex;justify-content:space-between'><b style='color:{NAVY}'>{key}</b><span class='{status_badge}'>{s['status']}</span></div><div style='font-size:12px;color:{MUTED};margin-top:10px'>{s['origin']} → {s['destination']}</div><div style='font-size:12px;margin-top:10px'>Estimated delivery: <b>{s['eta']}</b></div></div>", unsafe_allow_html=True)

    # ── BOOK A PICKUP ─────────────────────────────────────────────────────────
    elif selected == "Book a Pickup":
        header("Book a doorstep pickup", "Tell us where and when to collect your parcel. A booking number is created when you submit.")
        left, right = st.columns([1.35, .8])
        with left:
            # Location: only triggered when user explicitly clicks the button
            if st.session_state.location_triggered:
                geo = location_component(triggered=True, key="mydtdc_location_component", default=None)
                if isinstance(geo, dict):
                    if geo.get("permission") == "granted":
                        st.session_state.location_permission_granted = True
                        st.session_state.location_triggered = False
                        # Store actual coordinates if returned
                        if geo.get("lat") and geo.get("lng"):
                            st.session_state.location_lat = geo["lat"]
                            st.session_state.location_lng = geo["lng"]
                        else:
                            # Demo fallback: Amul canteen, IIM Bangalore campus
                            st.session_state.location_lat = 12.9318
                            st.session_state.location_lng = 77.5962
                    elif geo.get("error"):
                        err = geo["error"]
                        if "declined" not in err.lower():
                            st.caption(f"Location note: {err}")
                        st.session_state.location_triggered = False
            else:
                location_component(triggered=False, key="mydtdc_location_component", default=None)

            # Show satellite map + ground-level photo so user can confirm the detected spot
            if st.session_state.get("location_permission_granted") and st.session_state.get("location_lat"):
                lat = st.session_state.location_lat
                lng = st.session_state.location_lng
                confirmed = st.session_state.get("location_confirmed", False)
                if not confirmed:
                    # Load ground-level campus photo from cache (read once per session)
                    _ground_b64 = _load_ground_photo()

                    sat_html = f"""
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<div style="font-family:Inter,sans-serif;font-size:13px;color:#102A43;font-weight:600;margin-bottom:8px">
  📍 Is this your pickup location? Confirm before proceeding.
</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
  <div>
    <div style="font-size:11px;color:#627D98;font-weight:600;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">🛰 Satellite view</div>
    <div id="satmap" style="height:220px;border-radius:10px;overflow:hidden;border:2px solid #2563EB;"></div>
  </div>
  <div>
    <div style="font-size:11px;color:#627D98;font-weight:600;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">📸 Ground view — what you see here</div>
    <div style="height:220px;border-radius:10px;overflow:hidden;border:2px solid #CBD5E0;background:#F4F7FA;display:flex;align-items:center;justify-content:center;">
      {'<img src="data:image/png;base64,' + _ground_b64 + '" style="width:100%;height:100%;object-fit:cover;" />' if _ground_b64 else '<span style="color:#627D98;font-size:12px;">Photo not available</span>'}
    </div>
    <div style="font-size:10px;color:#627D98;margin-top:4px;">IIM Bangalore campus · Hostel Block area</div>
  </div>
</div>
<script>
(function(){{
  var map = L.map('satmap', {{zoomControl:false}}).setView([{lat},{lng}], 19);
  L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
    {{maxZoom:20, attribution:'Tiles © Esri'}}
  ).addTo(map);
  var pin = L.divIcon({{
    html: '<div style="background:#D71920;color:white;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:14px;border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,.4)">📍</div>',
    iconSize:[28,28], iconAnchor:[14,14], className:''
  }});
  L.marker([{lat},{lng}], {{icon:pin}}).addTo(map);
}})();
</script>
<div style="font-size:11px;color:#627D98;margin-top:6px">Lat {lat:.5f} · Lng {lng:.5f} · Satellite imagery © Esri</div>
"""
                    components.html(sat_html, height=320)
                    if st.button("✓  Yes, this is my location — use it", type="primary", key="confirm_location"):
                        st.session_state.location_confirmed = True
                        st.rerun()
                    if st.button("✗  Wrong location — enter manually", key="reject_location"):
                        st.session_state.location_permission_granted = False
                        st.session_state.location_lat = None
                        st.session_state.location_lng = None
                        st.session_state.location_confirmed = False
                        st.rerun()
                else:
                    st.success(f"Location confirmed: Lat {lat:.5f}, Lng {lng:.5f}. Address prefilled as IIM Bangalore for this demo.")
            else:
                st.caption("The pickup address is prefilled as IIM Bangalore for this demo.")

            with st.form("pickup_form"):
                st.markdown("**Pickup details**")
                c1, c2 = st.columns(2)
                name = c1.text_input("Your name", placeholder="Full name")
                phone = c2.text_input("Mobile number", placeholder="10-digit mobile")
                st.markdown("**Pickup address**")

                # Live location button inside form via markdown note
                st.markdown(
                    "<div style='background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;padding:10px 14px;margin-bottom:10px;font-size:12px;color:#1E40AF'>"
                    "📍 <b>Use my live location</b> — click the button below the form to auto-fill coordinates. "
                    "You can also edit any field manually.</div>",
                    unsafe_allow_html=True,
                )
                address_c1, address_c2 = st.columns(2)
                house = address_c1.text_input("House / flat number", key="address_house", placeholder="e.g. H305")
                road = address_c2.text_input("Road / street", key="address_road", placeholder="Street or road name")
                area = st.text_input("Area / locality", key="address_area", placeholder="Neighbourhood, campus, landmark")
                address_c3, address_c4, address_c5 = st.columns([1.2, 1, 1])
                city = address_c3.text_input("City", key="address_city", placeholder="City")
                state = address_c4.text_input("State", key="address_state", placeholder="State")
                pincode = address_c5.text_input("PIN code", key="address_pincode", placeholder="6 digits", max_chars=6)
                st.markdown("**Person handing over the parcel**")
                c_col1, c_col2 = st.columns(2)
                collector_name = c_col1.text_input("Collector name", placeholder="Person who will hand over the parcel")
                collector_phone = c_col2.text_input("Collector mobile", placeholder="Their contact number")
                c3, c4 = st.columns(2)
                pickup_date = c3.date_input("Preferred date", min_value=date.today(), value=date.today() + timedelta(days=1))
                slot = c4.selectbox("Convenient time slot", ["9 AM – 12 PM","12 PM – 3 PM","3 PM – 6 PM"])
                st.markdown("**Parcel details**")
                c5, c6 = st.columns(2)
                contents = c5.selectbox("What are you sending?", ["Documents","Clothing","Electronics","Personal items","Other"])
                weight = c6.selectbox("Approx. weight", ["Up to 0.5 kg","0.5–2 kg","2–5 kg","More than 5 kg"])
                # Upfront all-in price estimate
                _price_map = {"Up to 0.5 kg": 99, "0.5–2 kg": 149, "2–5 kg": 249, "More than 5 kg": 349}
                _est_price = _price_map.get(weight, 99)
                st.markdown(f"""<div style='background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;padding:10px 16px;margin:6px 0 2px;display:flex;align-items:center;gap:12px'>
  <div style='font-size:22px'>💰</div>
  <div>
    <div style='font-size:11px;font-weight:700;color:#1E40AF;text-transform:uppercase;letter-spacing:0.06em'>Estimated price</div>
    <div style='font-size:20px;font-weight:800;color:#1E3A8A;margin-top:2px'>₹{_est_price}</div>
    <div style='font-size:11px;color:#3B82F6;margin-top:1px'>All-in · includes pickup, handling and standard delivery. No hidden charges.</div>
  </div>
</div>""", unsafe_allow_html=True)

                # Camera: only shown after user explicitly clicks the button
                st.markdown("**Location photo (optional)**")
                if st.session_state.show_camera:
                    photo = st.camera_input("Take a location photo", help="On mobile this opens the camera. The photo stays in this demo session.")
                    if st.form_submit_button("Hide camera", type="secondary"):
                        st.session_state.show_camera = False
                        st.rerun()
                else:
                    photo = None
                    st.caption("Add a photo to help the pickup partner find your location.")
                photo_upload = st.file_uploader("Or upload a location photo", type=["png","jpg","jpeg"], help="Demo only: this file is not stored in Supabase.")
                priority = st.checkbox("Priority pickup · request earliest available collection (₹99 premium)")
                note = st.text_input("Note for the pickup partner (optional)", placeholder="Gate, landmark, or access instructions")
                submitted = st.form_submit_button("Confirm pickup request", type="primary", use_container_width=True)

            # Buttons below the form (outside form context)
            loc_col, cam_col = st.columns(2)
            if loc_col.button("📍  Use my live location", key="use_live_location", use_container_width=True):
                st.session_state.location_triggered = True
                st.rerun()
            if cam_col.button("📷  Take a location photo", key="open_camera", use_container_width=True):
                st.session_state.show_camera = True
                st.rerun()

            if submitted:
                digits = "".join(ch for ch in phone if ch.isdigit())
                collector_digits = "".join(ch for ch in collector_phone if ch.isdigit())
                pincode_digits = "".join(ch for ch in pincode if ch.isdigit())
                address_parts = [house, road, area, city, state, pincode]
                address = ", ".join(part.strip() for part in address_parts if part.strip())
                if not name or len(digits) < 10 or not city or not state or len(pincode_digits) != 6 or not collector_name or len(collector_digits) < 10:
                    st.error("Enter your name and mobile, city, state, 6-digit PIN code, and the collector's name and valid mobile number.")
                else:
                    saved_photo = photo or photo_upload
                    photo_data = None
                    if saved_photo:
                        import base64
                        photo_data = base64.b64encode(saved_photo.getvalue()).decode("ascii")
                    record = {
                        "booking_id": "PU" + uuid.uuid4().hex[:8].upper(), "sender_name": name, "phone": phone,
                        "pickup_address": address, "house_number": house, "road": road, "area": area,
                        "city": city, "state": state, "pincode": pincode,
                        "collector_name": collector_name, "collector_phone": collector_phone,
                        "pickup_latitude": None, "pickup_longitude": None, "photo_data": photo_data,
                        "pickup_date": pickup_date.isoformat(), "time_slot": slot,
                        "contents": contents, "weight": weight, "priority": priority, "note": note,
                        "status": "Pickup request received", "created_at": datetime.now().isoformat(),
                    }
                    save_pickup(record)
                    st.session_state.last_pickup = record
                    # Save address for future quick-fill (avoid duplicates by pincode+house)
                    _new_addr = {"label": f"{area or city} ({pincode})", "house": house, "road": road, "area": area, "city": city, "state": state, "pincode": pincode}
                    _existing_keys = {(a["house"], a["pincode"]) for a in st.session_state.saved_addresses}
                    if (house, pincode) not in _existing_keys:
                        st.session_state.saved_addresses.append(_new_addr)
                    st.session_state.show_camera = False
                    st.session_state.location_confirmed = False
                    st.session_state.location_permission_granted = False
                    st.session_state.location_lat = None
                    st.session_state.location_lng = None
                    st.success(f"Pickup requested! Booking number: {record['booking_id']}.")
                    st.info(f"{pickup_date.strftime('%d %b %Y')} · {slot} · {'Priority pickup requested' if priority else 'Standard pickup'}")
                    st.session_state.pending_nav = "My Pickups"
                    st.rerun()

        with right:
            st.markdown("<div class='card'><div class='card-title'>Pickup, made clearer</div><div class='card-sub'>A simple flow from request to collection.</div><div class='feature-note'>✓ Start with IIM Bangalore as the demo address<br><br>✓ Click <b>Use my live location</b> in the address section when you need GPS<br><br>✓ Tap <b>Take a location photo</b> only if you want to add one<br><br>✓ Share who will hand over the parcel<br><br>✓ Follow progress in My Pickups</div></div>", unsafe_allow_html=True)
            if st.session_state.get("last_pickup"):
                p = st.session_state.last_pickup
                st.markdown(f"<div class='card'><div class='card-title'>Latest pickup</div><b>{p['booking_id']}</b><p><span class='status status-warn'>{p['status']}</span></p><small>{p['pickup_date']} · {p['time_slot']}</small></div>", unsafe_allow_html=True)

    # ── TRACK PICKUP ──────────────────────────────────────────────────────────
    elif selected == "Track Pickup":
        header("Track your pickup partner", "See where your pickup partner is and how far they are from your location.")
        pickup_id = st.session_state.get("track_pickup_id", "PU4A8B2C1D")
        p = next((x for x in st.session_state.pickup_requests if x.get("booking_id") == pickup_id), None)
        if not p and st.session_state.pickup_requests:
            p = st.session_state.pickup_requests[0]
        if p:
            col1, col2, col3 = st.columns(3)
            col1.markdown(f"<div class='kpi'><div class='kpi-label'>BOOKING</div><div class='kpi-value'>{p.get('booking_id','')}</div></div>", unsafe_allow_html=True)
            col2.markdown(f"<div class='kpi'><div class='kpi-label'>PICKUP PARTNER</div><div class='kpi-value'>{p.get('partner_name','Rahul M.')}</div></div>", unsafe_allow_html=True)
            col3.markdown(f"<div class='kpi'><div class='kpi-label'>ETA</div><div class='kpi-value'>~8 min · 1.8 km</div></div>", unsafe_allow_html=True)
            st.markdown("")
            mapcol, infocol = st.columns([1.4, 1])
            with mapcol:
                map_html = """
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<div id="pumap" style="height:300px;border-radius:14px;overflow:hidden;border:1px solid #E3EAF0;"></div>
<script>
var map=L.map('pumap').setView([12.9415,77.5942],14);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap'}).addTo(map);
var youIcon=L.divIcon({html:'<div style="background:#102A43;color:white;border-radius:50%;width:34px;height:34px;display:flex;align-items:center;justify-content:center;font-size:17px;border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,.35)">📍</div>',iconSize:[34,34],iconAnchor:[17,17],className:''});
var partnerIcon=L.divIcon({html:'<div style="background:#D71920;color:white;border-radius:50%;width:36px;height:36px;display:flex;align-items:center;justify-content:center;font-size:18px;border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,.35)">🚴</div>',iconSize:[36,36],iconAnchor:[18,18],className:''});
L.marker([12.9343,77.5953],{icon:youIcon}).addTo(map).bindPopup('<b>Your location</b><br>Main Gate, IIM Bangalore').openPopup();
L.marker([12.9490,77.5930],{icon:partnerIcon}).addTo(map).bindPopup('<b>Rahul M. — Pickup partner</b><br>~8 min away on Bannerghatta Road');
L.polyline([[12.9490,77.5930],[12.9450,77.5940],[12.9400,77.5950],[12.9343,77.5953]],{color:'#D71920',weight:3,dashArray:'6,6',opacity:0.7}).addTo(map);
</script>"""
                components.html(map_html, height=310)
            with infocol:
                st.markdown(f"<div class='card'><div class='card-title'>Partner details</div><p><b>Name:</b> {p.get('partner_name','Rahul M.')}<br><b>Slot:</b> {p.get('time_slot','9 AM – 12 PM')}<br><b>Date:</b> {p.get('pickup_date','')}</p><div class='feature-note'>The partner is tracking your address. Stay near the pickup location.</div></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='card'><div class='card-title'>Pickup address</div><p style='font-size:13px'>{p.get('pickup_address','')}</p></div>", unsafe_allow_html=True)
                if st.button("📞  Call pickup partner", key="call_pu_partner", use_container_width=True):
                    st.session_state.pu_call_placed = True
                if st.session_state.get("pu_call_placed"):
                    st.success("Demo call request ready: the live service would connect from your registered number using a masked relay. No call is placed by this prototype.")
            st.markdown("<div class='card-title' style='margin-top:14px;margin-bottom:10px'>Pickup journey</div>", unsafe_allow_html=True)
            stages = [("Pickup request received","Booking reference generated","done"),("DTDC confirmed","Slot confirmed","done"),("Partner assigned","Rahul M. assigned to your pickup","done"),("Partner on the way","Tracking live · ~8 min away","active"),("Parcel collected","Pending","future")]
            tl = "<div class='timeline'>"
            for title, sub, state in stages:
                cls = "event" if state in ("done","active") else "event future"
                tl += f"<div class='{cls}'><b{' style=\"color:#D71920\"' if state=='active' else ''}>{title}</b><small>{sub}</small></div>"
            tl += "</div>"
            st.markdown(tl, unsafe_allow_html=True)
            st.caption("Location shown is simulated for this usability demo. In the live product, the partner's device shares real-time GPS coordinates.")
        else:
            st.info("No active pickup to track. Book a pickup first.")
            if st.button("Book a pickup", type="primary"):
                st.session_state.pending_nav = "Book a Pickup"; st.rerun()

    # ── TRACK SHIPMENT ────────────────────────────────────────────────────────
    elif selected == "Track Shipment":
        header("Track your shipment", "Follow parcel scans and see the next expected step. Sample consignment numbers are in My Shipments.")
        c1, c2 = st.columns([1.2, 1])
        number = c1.text_input("Consignment number", value=st.session_state.get("track_number","D1234567890"), placeholder="Enter consignment number")
        with c2:
            st.write("")
            if st.button("Find shipment", type="primary", use_container_width=True):
                st.session_state.track_number = number.strip().upper()
        key = st.session_state.get("track_number", number.strip().upper())
        shipment = st.session_state.shipments.get(key)
        if shipment:
            cols = st.columns(3)
            for col, label, value in zip(cols, ["CURRENT STATUS","ESTIMATED DELIVERY","LAST UPDATED"],[shipment["status"],shipment["eta"],shipment["updated"]]):
                col.markdown(f"<div class='kpi'><div class='kpi-label'>{label}</div><div class='kpi-value'>{value}</div></div>", unsafe_allow_html=True)
            # Overall ETA banner — orange/red when delayed, navy otherwise
            overall_eta = shipment.get("overall_eta_label", f"Estimated delivery: {shipment['eta']}")
            is_delayed = shipment.get("status") == "Delayed"
            if is_delayed:
                st.markdown(f"""<div style='background:linear-gradient(135deg,#B45309 0%,#92400E 100%);border-radius:12px;padding:16px 20px;margin-bottom:16px;display:flex;align-items:center;gap:14px;border:1.5px solid #F59E0B'>
  <div style='font-size:28px'>⚠️</div>
  <div>
    <div style='color:#FDE68A;font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:2px'>Shipment Delayed</div>
    <div style='color:#fff;font-size:16px;font-weight:700'>{overall_eta}</div>
    <div style='color:#FDE68A;font-size:12px;margin-top:4px'>We apologise for the inconvenience. See timeline below for details.</div>
  </div>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div style='background:linear-gradient(135deg,{NAVY} 0%,#1a3a5c 100%);border-radius:12px;padding:16px 20px;margin-bottom:16px;display:flex;align-items:center;gap:14px'>
  <div style='font-size:28px'>📦</div>
  <div>
    <div style='color:#fff;font-size:11px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;opacity:0.7;margin-bottom:2px'>Final Delivery ETA</div>
    <div style='color:#fff;font-size:16px;font-weight:700'>{overall_eta}</div>
  </div>
</div>""", unsafe_allow_html=True)
            a, b = st.columns([1.2, .8])
            with a:
                def _event_html(e):
                    cls = "event" if e["done"] else "event future"
                    eta_line = f"<div style='font-size:11px;color:#D71920;font-weight:600;margin-top:3px'>🕐 {e['phase_eta']}</div>" if e.get("phase_eta") else ""
                    return f"<div class='{cls}'><b>{e['title']}</b><small>{e['place']} · {e['time']}</small>{eta_line}</div>"
                st.markdown(f"<div class='card'><div class='card-title'>Parcel journey</div><div class='card-sub'>{shipment['origin']} → {shipment['destination']}</div><div class='timeline'>"+"".join(_event_html(e) for e in shipment["events"])+"</div></div>", unsafe_allow_html=True)
            with b:
                st.markdown(f"<div class='card'><div class='card-title'>Delivery details</div><div class='card-sub'>Partner details appear here when available.</div><p><b>Delivery partner</b><br>{shipment['delivery_partner']}</p><div class='feature-note'>ETA is an estimate based on latest available shipment information.</div></div>", unsafe_allow_html=True)
                if shipment["status"] == "Out for delivery":
                    if st.button("📞  Call delivery partner", key="call_partner_"+key, use_container_width=True):
                        st.session_state[f"call_status_{key}"] = True
                    if st.session_state.get(f"call_status_{key}"):
                        st.success("Demo call request ready: the live service would connect from your registered number using a masked relay. No call is placed by this prototype.")
                with st.expander("Something doesn't look right?"):
                    issue = st.selectbox("Choose an issue", ["Marked delivered, but I did not receive it","Delivery attempt did not happen","Tracking has not updated","I need another kind of help"])
                    details = st.text_area("Add details", placeholder="Tell us what happened")
                    if st.button("Create support case"):
                        st.success(f"Case CS{uuid.uuid4().hex[:7].upper()} created for {key}. Shipment details are attached.")
        else:
            st.warning("Not found in demo data. Try D1234567890 or D9876543210.")

    # ── MY SHIPMENTS ──────────────────────────────────────────────────────────
    elif selected == "My Shipments":
        header("My shipments", "Your tracked parcels and recent pickup bookings.")
        for key, s in st.session_state.shipments.items():
            with st.container(border=True):
                a, b, c = st.columns([1.2, 1.1, .7])
                a.markdown(f"**{key}**  \n{s['origin']} → {s['destination']}")
                b.markdown(f"<span class='status'>{s['status']}</span><br><small>ETA: {s['eta']}</small>", unsafe_allow_html=True)
                if c.button("Track", key="track_"+key):
                    st.session_state.track_number = key; st.session_state.pending_nav = "Track Shipment"; st.rerun()
        if st.session_state.pickup_requests:
            st.markdown("<div class='card-title' style='margin-top:18px'>Pickup requests</div>", unsafe_allow_html=True)
            for p in st.session_state.pickup_requests:
                st.markdown(f"<div class='card'><b>{p['booking_id']}</b> &nbsp; <span class='status status-warn'>{p['status']}</span><div class='card-sub' style='margin:8px 0 0'>{p['pickup_address']} · {p['pickup_date']} · {p['time_slot']}</div></div>", unsafe_allow_html=True)

    # ── MY PICKUPS ────────────────────────────────────────────────────────────
    elif selected == "My Pickups":
        header("My pickups", "Check your pickup booking reference, selected slot, collector contact and request progress.")
        load_pickups()
        if not st.session_state.pickup_requests:
            st.info("No pickup requests yet. Use Book a Pickup to create your first request.")
            if st.button("Book a pickup", type="primary"):
                st.session_state.pending_nav = "Book a Pickup"; st.rerun()
        for p in st.session_state.pickup_requests:
            with st.container(border=True):
                a, b = st.columns([1.2, .8])
                status = p.get("status","Pickup request received")
                a.markdown(f"### {p.get('booking_id','Pickup request')}\n**{status}** · {p.get('pickup_date','')} · {p.get('time_slot','')}")
                b.markdown(f"**Pickup address**\n\n{p.get('pickup_address','Address not available')}\n\n**Person handing over**\n\n{p.get('collector_name','')} · {p.get('collector_phone','')}")
                stage_map = {"Pickup request received":0,"DTDC confirmed":1,"Pickup partner assigned":2,"Pickup partner on the way":3,"Parcel collected":4}
                cur = stage_map.get(status, 0)
                stages = [("Request received","Booking reference generated · "+str(p.get("created_at",""))[:16].replace("T"," ")),("DTDC confirmed","Slot and partner matching in progress"),("Pickup partner assigned","Partner details shared in app"),("Partner on the way","Track live location in Track Pickup"),("Parcel collected","Collection scan confirms handover")]
                tl = "<div class='timeline'>"
                for i, (title, sub) in enumerate(stages):
                    cls = "event" if i <= cur else "event future"
                    tl += f"<div class='{cls}'><b>{title}</b><small>{sub}</small></div>"
                tl += "</div>"
                st.markdown(tl, unsafe_allow_html=True)
                if status == "Pickup partner on the way":
                    st.markdown(f"""<div style='background:#FFF3E0;border:1.5px solid #FF8F00;border-radius:10px;padding:12px 16px;margin:10px 0;display:flex;align-items:center;gap:12px'>
  <div style='font-size:22px'>🛵</div>
  <div>
    <div style='font-size:11px;color:#E65100;font-weight:700;letter-spacing:0.06em;text-transform:uppercase'>Partner ETA</div>
    <div style='font-size:15px;font-weight:700;color:#BF360C'>Arriving in ~15 mins</div>
    <div style='font-size:11px;color:#795548;margin-top:2px'>Keep your parcel packed and ready at the pickup address</div>
  </div>
</div>""", unsafe_allow_html=True)
                    if st.button("📍  Track pickup partner", key="trackpu_"+p.get("booking_id",""), type="primary"):
                        st.session_state.track_pickup_id = p.get("booking_id"); st.session_state.pending_nav = "Track Pickup"; st.rerun()
                if p.get("photo_data"):
                    st.markdown(f"""
<div style='margin-top:8px'>
  <div style='font-size:12px;color:{MUTED};margin-bottom:4px'>📷 Item / location photo (taken at booking)</div>
  <img src="data:image/jpeg;base64,{p['photo_data']}" style="max-width:260px;height:140px;object-fit:cover;border-radius:10px;border:1px solid #E3EAF0" alt="Pickup photo"/>
</div>""", unsafe_allow_html=True)
                if p.get("priority"):
                    st.caption("Priority pickup requested · availability and price require confirmation by a real booking service.")
                # Reschedule / Cancel — only available for active (not collected) pickups
                bid = p.get("booking_id","")
                cancelled_key = f"pickup_cancelled_{bid}"
                reschedule_key = f"pickup_reschedule_open_{bid}"
                rescheduled_key = f"pickup_rescheduled_{bid}"
                if status not in ("Parcel collected","Cancelled") and not st.session_state.get(cancelled_key):
                    st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
                    act_col1, act_col2 = st.columns(2)
                    if act_col1.button("🗓  Reschedule", key=f"btn_reschedule_{bid}", use_container_width=True):
                        st.session_state[reschedule_key] = not st.session_state.get(reschedule_key, False)
                        st.rerun()
                    if act_col2.button("✖  Cancel pickup", key=f"btn_cancel_{bid}", use_container_width=True):
                        st.session_state[f"pickup_cancel_confirm_{bid}"] = True
                        st.rerun()
                    # Reschedule form
                    if st.session_state.get(reschedule_key) and not st.session_state.get(rescheduled_key):
                        with st.form(f"reschedule_form_{bid}"):
                            st.markdown("**Pick a new date and time slot**")
                            new_date = st.date_input("New pickup date", value=date.today()+timedelta(days=1), min_value=date.today()+timedelta(days=1), key=f"new_date_{bid}")
                            new_slot = st.selectbox("New time slot", ["9 AM – 12 PM","12 PM – 3 PM","3 PM – 6 PM"], key=f"new_slot_{bid}")
                            submitted = st.form_submit_button("Confirm reschedule", type="primary", use_container_width=True)
                            if submitted:
                                for pr in st.session_state.pickup_requests:
                                    if pr.get("booking_id") == bid:
                                        pr["pickup_date"] = new_date.isoformat()
                                        pr["time_slot"] = new_slot
                                        pr["status"] = "Pickup request received"
                                        break
                                st.session_state[rescheduled_key] = True
                                st.session_state[reschedule_key] = False
                                st.rerun()
                    if st.session_state.get(rescheduled_key):
                        st.success(f"Pickup {bid} rescheduled. DTDC will confirm the new slot within a few hours.")
                    # Cancel confirmation
                    if st.session_state.get(f"pickup_cancel_confirm_{bid}"):
                        st.warning(f"Are you sure you want to cancel pickup {bid}? This cannot be undone in this demo.")
                        yes_col, no_col = st.columns(2)
                        if yes_col.button("Yes, cancel it", key=f"confirm_yes_{bid}", type="primary", use_container_width=True):
                            for pr in st.session_state.pickup_requests:
                                if pr.get("booking_id") == bid:
                                    pr["status"] = "Cancelled"
                                    break
                            st.session_state[cancelled_key] = True
                            st.session_state[f"pickup_cancel_confirm_{bid}"] = False
                            st.rerun()
                        if no_col.button("No, keep it", key=f"confirm_no_{bid}", use_container_width=True):
                            st.session_state[f"pickup_cancel_confirm_{bid}"] = False
                            st.rerun()
                elif st.session_state.get(cancelled_key) or status == "Cancelled":
                    st.markdown(f"<div style='background:#FEE2E2;border-radius:8px;padding:10px 14px;margin-top:8px;font-size:13px;color:#991B1B;font-weight:600'>✖ Pickup cancelled. No partner will be assigned.</div>", unsafe_allow_html=True)
                    # One-tap rebook after cancellation
                    if st.button("🔄  Rebook this pickup", key=f"rebook_{bid}", use_container_width=True, type="primary"):
                        # Pre-fill address fields from the cancelled booking
                        for _fld, _val in [("address_house", p.get("house_number","")), ("address_road", p.get("road","")),
                                           ("address_area", p.get("area","")), ("address_city", p.get("city","")),
                                           ("address_state", p.get("state","")), ("address_pincode", p.get("pincode",""))]:
                            st.session_state[_fld] = _val
                        st.session_state.pending_nav = "Book a Pickup"
                        st.rerun()

    # ── WALLET ────────────────────────────────────────────────────────────────
    elif selected == "Wallet":
        header("DTDC Wallet", "A prototype wallet for eligible refunds, shipment credits and future bookings.")
        st.markdown(f"<div class='hero'><div style='font-size:12px;color:#D9E7F2'>AVAILABLE BALANCE</div><h1 style='margin-top:8px'>₹{st.session_state.wallet_balance:.0f}</h1><p>Use your balance toward an eligible booking.</p></div>", unsafe_allow_html=True)
        a, b = st.columns(2)
        with a:
            st.markdown("<div class='card'><div class='card-title'>Add demo credit</div><div class='card-sub'>Simulates adding funds; no payment is taken.</div></div>", unsafe_allow_html=True)
            credit = st.selectbox("Choose amount", [100, 250, 500])
            if st.button("Add demo credit", type="primary"):
                st.session_state.wallet_balance += credit; st.success(f"₹{credit} demo credit added."); st.rerun()
        with b:
            st.markdown("<div class='card'><div class='card-title'>Recent activity</div><div class='card-sub'>Concept only; not a real payment account.</div><div class='feature-note'>₹250 · Welcome credit<br><br>₹100 · Refund for D1234567890<br><br>−₹99 · Priority pickup PU8F3A1C2B</div></div>", unsafe_allow_html=True)

    # ── HELP & SUPPORT ────────────────────────────────────────────────────────
    elif selected == "Help & Support":
        # If user arrived from an order card, jump straight to chat section
        _jump_to_chat = bool(st.session_state.get("support_reference_auto",""))
        header("Help & Support", "Choose a topic or tap an active order below — no reference number needed.")
        ai_status = "GPT-5 nano is ready" if get_secret("OPENAI_API_KEY") and OpenAI else "Smart reply mode active · no API key needed"
        st.info(f"{ai_status}. The assistant uses only sample records from this prototype, not DTDC live systems.")

        # Active orders collapsible section
        active_orders_found = False
        order_ref_from_card = None

        all_shipments = list(st.session_state.shipments.items())
        all_pickups = st.session_state.pickup_requests

        # Contents icon fallback when no photo is attached
        CONTENTS_ICON = {"Documents":"📄","Clothing":"👕","Electronics":"📱","Personal items":"🎒","Other":"📦"}

        total_active = len(all_shipments) + len(all_pickups)
        with st.expander(f"📦  Your active orders ({total_active})", expanded=False):
         if all_shipments or all_pickups:
            active_orders_found = True
            total_orders = len(all_shipments) + len(all_pickups)
            order_cols = st.columns(min(2, total_orders))
            col_idx = 0

            for key, s in all_shipments:
                with order_cols[col_idx % len(order_cols)]:
                    icon = CONTENTS_ICON.get(s.get("contents",""), "📦")
                    # Shipments don't carry photos in demo data — show a large icon tile
                    st.markdown(f"""
<div class='order-summary-card'>
  <div style='display:flex;gap:10px;align-items:flex-start'>
    <div style='width:54px;height:54px;min-width:54px;border-radius:10px;background:#E8F4FF;display:flex;align-items:center;justify-content:center;font-size:26px;border:1px solid #BFDBFE'>{icon}</div>
    <div style='flex:1'>
      <div style='font-weight:700;color:{NAVY};font-size:13px'>{key}</div>
      <div style='font-size:11px;color:{MUTED};margin-top:2px'>{s['origin']} → {s['destination']}</div>
      <div style='margin-top:5px'><span class='status'>{s['status']}</span></div>
      <div style='font-size:11px;color:{MUTED};margin-top:4px'>ETA: {s['eta']}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)
                    if st.button(f"Get help for {key}", key=f"help_ship_{key}", use_container_width=True):
                        order_ref_from_card = key
                        st.session_state.support_reference_auto = key
                        st.rerun()
                col_idx += 1

            for p in all_pickups:   # ALL pickups — no cap
                bid = p.get("booking_id","")
                pstatus = p.get("status","")
                photo_data = p.get("photo_data")
                contents = p.get("contents","Other")
                icon = CONTENTS_ICON.get(contents, "📦")
                with order_cols[col_idx % len(order_cols)]:
                    if photo_data:
                        # Show the actual item/location photo the user took at booking time
                        st.markdown(f"""
<div class='order-summary-card'>
  <div style='font-weight:700;color:{NAVY};font-size:13px;margin-bottom:6px'>{bid}</div>
  <img src="data:image/jpeg;base64,{photo_data}" style="width:100%;height:90px;object-fit:cover;border-radius:8px;margin-bottom:7px;border:1px solid #BFDBFE" alt="Item photo"/>
  <div style='font-size:11px;color:{MUTED}'>{p.get("pickup_date","")} · {p.get("time_slot","")}</div>
  <div style='margin-top:5px'><span class='status status-warn'>{pstatus}</span></div>
  <div style='font-size:11px;color:{MUTED};margin-top:4px'>{contents} · {p.get("weight","")}</div>
</div>""", unsafe_allow_html=True)
                    else:
                        # No photo — show contents icon tile
                        st.markdown(f"""
<div class='order-summary-card'>
  <div style='display:flex;gap:10px;align-items:flex-start'>
    <div style='width:54px;height:54px;min-width:54px;border-radius:10px;background:#FFF5E5;display:flex;align-items:center;justify-content:center;font-size:26px;border:1px solid #FED7AA'>{icon}</div>
    <div style='flex:1'>
      <div style='font-weight:700;color:{NAVY};font-size:13px'>{bid}</div>
      <div style='font-size:11px;color:{MUTED};margin-top:2px'>{p.get("pickup_date","")} · {p.get("time_slot","")}</div>
      <div style='margin-top:5px'><span class='status status-warn'>{pstatus}</span></div>
      <div style='font-size:11px;color:{MUTED};margin-top:4px'>{contents} · {p.get("weight","")}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)
                    if st.button(f"Get help for {bid}", key=f"help_pu_{bid}", use_container_width=True):
                        order_ref_from_card = bid
                        st.session_state.support_reference_auto = bid
                        st.rerun()
                col_idx += 1
         else:
            st.caption("No active orders found in this session.")

        # Hardcode a stable topic so the chat doesn't reset on every render
        service = "Intracity"
        category = "General Information"
        topic = "General query"
        chat_topic = "DTDC Support"
        if st.session_state.get("active_chat_topic") != chat_topic:
            st.session_state.chat = []
            st.session_state.active_chat_topic = chat_topic
            st.session_state.pending_support_prompt = None

        st.markdown("#### Common questions")
        suggestions = ["Where is my shipment?", "How do I reschedule a pickup?", "What should I do next?"]
        question_cols = st.columns(min(3, len(suggestions)))
        for index, question in enumerate(suggestions):
            if question_cols[index % len(question_cols)].button(question, key=f"support_suggestion_{index}", use_container_width=True):
                st.session_state.pending_support_prompt = question
                st.rerun()

        # Anchor injected so JS can scroll here when arriving from an order card
        st.markdown('<a id="support-chat-anchor"></a>', unsafe_allow_html=True)
        if _jump_to_chat:
            st.components.v1.html("""<script>
            window.parent.document.getElementById('support-chat-anchor') &&
            window.parent.document.getElementById('support-chat-anchor').scrollIntoView({behavior:'smooth',block:'start'});
            </script>""", height=0)
        st.markdown("#### Chat with MyDTDC support")
        # Auto-fill reference if user tapped an order card
        auto_ref = st.session_state.get("support_reference_auto","")
        ref = st.text_input("Consignment or pickup reference (optional — or tap an order above)", value=auto_ref, key="support_reference", placeholder="e.g. D1234567890 or PUXXXXXXXX")
        if ref != auto_ref and auto_ref:
            st.session_state.support_reference_auto = ""

        _ref_upper = (ref or "").strip().upper()
        if _ref_upper:
            _s = st.session_state.shipments.get(_ref_upper)
            _p = next((x for x in st.session_state.pickup_requests if x.get("booking_id","").upper() == _ref_upper), None)
            if _s:
                st.markdown(f"<div class='card' style='margin-bottom:8px'><div style='display:flex;justify-content:space-between;align-items:center'><div><div class='card-title' style='font-size:14px'>{_ref_upper}</div><div style='font-size:12px;color:#627D98;margin-top:2px'>{_s['origin']} → {_s['destination']}</div></div><span class='status'>{_s['status']}</span></div><div style='margin-top:10px;font-size:12px;color:#627D98'>ETA: {_s['eta']} &nbsp;·&nbsp; Last updated: {_s['updated']}</div></div>", unsafe_allow_html=True)
                if st.button("📦  Track this shipment", key="sup_track_shipment", use_container_width=False):
                    st.session_state.track_number = _ref_upper; st.session_state.pending_nav = "Track Shipment"; st.rerun()
            elif _p:
                _pstatus = _p.get("status","Pickup request received")
                _pbadge = "status-warn" if "way" in _pstatus.lower() or "assigned" in _pstatus.lower() else "status"
                st.markdown(f"<div class='card' style='margin-bottom:8px'><div style='display:flex;justify-content:space-between;align-items:center'><div><div class='card-title' style='font-size:14px'>{_ref_upper}</div><div style='font-size:12px;color:#627D98;margin-top:2px'>{_p.get('pickup_address','')[:55]}…</div></div><span class='status {_pbadge}'>{_pstatus}</span></div><div style='margin-top:10px;font-size:12px;color:#627D98'>{_p.get('pickup_date','')} &nbsp;·&nbsp; {_p.get('time_slot','')} &nbsp;·&nbsp; {_p.get('contents','')}</div></div>", unsafe_allow_html=True)
                if _pstatus == "Pickup partner on the way":
                    if st.button("📍  Track pickup partner", key="sup_track_pickup", use_container_width=False):
                        st.session_state.track_pickup_id = _ref_upper; st.session_state.pending_nav = "Track Pickup"; st.rerun()
                else:
                    if st.button("📋  View pickup details", key="sup_view_pickup", use_container_width=False):
                        st.session_state.pending_nav = "My Pickups"; st.rerun()
            else:
                st.caption("Reference not found in demo data. The assistant will still try to answer your question.")

        if st.button("Start new conversation", key="support_new_chat"):
            st.session_state.chat = []
            st.session_state.pending_support_prompt = None
            st.rerun()

        def reply_to_support(question):
            previous = list(st.session_state.chat)
            st.session_state.chat.append(("user", question))
            context = support_record_context(ref)
            with st.spinner("MyDTDC support is preparing a reply…"):
                answer = support_answer(previous, question, service, chat_topic, context)
            st.session_state.chat.append(("assistant", answer))

        pending = st.session_state.get("pending_support_prompt")
        if pending:
            st.session_state.pending_support_prompt = None
            reply_to_support(pending)
        for role_msg, msg in st.session_state.chat:
            with st.chat_message(role_msg):
                st.write(msg)
        # Inline chat input — always visible in the page flow (no floating bar)
        with st.form("support_chat_form", clear_on_submit=True):
            inp_col, btn_col = st.columns([4, 1])
            user_msg = inp_col.text_input("Type your question", label_visibility="collapsed", placeholder="Type your question about this topic…", key="support_chat_input")
            send = btn_col.form_submit_button("Send", type="primary", use_container_width=True)
        if send and user_msg.strip():
            reply_to_support(user_msg.strip())
            st.rerun()

        with st.expander("Create a support request instead"):
            st.caption(f"Category: {chat_topic}")
            contact = st.text_input("Email or mobile number", key="case_contact")
            problem = st.text_area("Describe what happened", key="case_problem")
            if st.button("Submit support request", key="submit_support_case"):
                if not contact or not problem:
                    st.error("Add a contact method and describe the issue.")
                else:
                    st.success(f"Support request SR{uuid.uuid4().hex[:7].upper()} created in this demo session under {category}.")

    elif selected == "My Saved Addresses":
        header("My Saved Addresses", "Reuse a saved address to book your next pickup faster.")
        if not st.session_state.saved_addresses:
            st.markdown(f"""<div style='background:#F4F7FA;border-radius:12px;padding:32px 24px;text-align:center;color:{MUTED}'>
  <div style='font-size:40px;margin-bottom:10px'>📍</div>
  <div style='font-size:15px;font-weight:600;color:{INK};margin-bottom:6px'>No saved addresses yet</div>
  <div style='font-size:13px'>After you book a pickup, tick "Save this address" and it will appear here for one-tap reuse.</div>
</div>""", unsafe_allow_html=True)
        else:
            for _idx, _sa in enumerate(st.session_state.saved_addresses):
                _c1, _c2 = st.columns([5, 1])
                with _c1:
                    st.markdown(f"""<div style='background:#fff;border:1px solid #E3EAF0;border-radius:10px;padding:12px 16px;margin-bottom:8px'>
  <div style='font-weight:700;color:{NAVY};font-size:14px'>📍 {_sa['label']}</div>
  <div style='font-size:12px;color:{INK};margin-top:4px'>{_sa.get('house','')} {_sa.get('road','')}</div>
  <div style='font-size:12px;color:{MUTED}'>{_sa.get('area','')}, {_sa.get('city','')}, {_sa.get('state','')} — {_sa.get('pincode','')}</div>
</div>""", unsafe_allow_html=True)
                with _c2:
                    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                    if st.button("Book", key=f"saved_book_{_idx}", use_container_width=True, type="primary"):
                        for _fld in ("house","road","area","city","state","pincode"):
                            st.session_state[f"address_{_fld}"] = _sa.get(_fld, "")
                        st.session_state.pending_nav = "Book a Pickup"
                        st.rerun()
                    if st.button("Remove", key=f"saved_del_{_idx}", use_container_width=True):
                        st.session_state.saved_addresses.pop(_idx)
                        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ROLE: DELIVERY PARTNER
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state.app_role == "Delivery Partner":
    partner_pages = ["Deliveries Today", "Pickups Today"]
    if st.session_state.pending_nav in partner_pages:
        st.session_state.partner_nav = st.session_state.pending_nav
        st.session_state.pending_nav = None
    partner_selected = st.radio("Partner Navigation", partner_pages, horizontal=True, label_visibility="collapsed", key="partner_nav")

    # Shared partner header
    st.markdown("<div class='hero-partner'><h1>Good morning, Rahul 👋</h1><p>Here is your work list for today. Tap any order to open the map and contact the customer.</p></div>", unsafe_allow_html=True)

    # ── DELIVERIES TODAY ──────────────────────────────────────────────────────
    if partner_selected == "Deliveries Today":
        header("Deliveries Today", f"{len(st.session_state.partner_deliveries)} orders assigned · all heading to Bengaluru South zone")

        # Stale-status watchdog: visible to delivery partner only
        # Demo: D7777777777 is hardcoded as stale (last scan >48h ago)
        _stale_shipments = ["D7777777777"] if "D7777777777" in st.session_state.shipments else []
        _active_stale = [s for s in _stale_shipments if s not in st.session_state.stale_watchdog_dismissed]
        for _sk in _active_stale:
            _ss = st.session_state.shipments[_sk]
            st.markdown(f"""<div style='background:#FFF7ED;border:1.5px solid #FB923C;border-radius:10px;padding:12px 16px;margin-bottom:10px;display:flex;align-items:center;gap:12px'>
  <div style='font-size:20px'>🕒</div>
  <div style='flex:1'>
    <div style='font-size:11px;font-weight:700;color:#C2410C;text-transform:uppercase;letter-spacing:0.06em'>No scan in 48+ hours</div>
    <div style='font-size:13px;font-weight:600;color:#7C2D12;margin-top:2px'>{_sk} · {_ss["origin"]} → {_ss["destination"]}</div>
    <div style='font-size:11px;color:#9A3412;margin-top:1px'>Last status: {_ss.get("status","Unknown")}. Investigate and update scan immediately.</div>
  </div>
</div>""", unsafe_allow_html=True)
            _stale_col1, _stale_col2 = st.columns([1, 1])
            _stale_expand_key = f"stale_expanded_{_sk}"
            if _stale_col1.button(f"View {_sk}", key=f"stale_track_{_sk}", use_container_width=True):
                st.session_state[_stale_expand_key] = not st.session_state.get(_stale_expand_key, False)
                st.rerun()
            if _stale_col2.button("Dismiss", key=f"stale_dismiss_{_sk}", use_container_width=True):
                st.session_state.stale_watchdog_dismissed.add(_sk); st.rerun()
            # Inline shipment detail panel (toggled by View button)
            if st.session_state.get(_stale_expand_key):
                _journey = _ss.get("journey", [])
                _latest_scan = _journey[-1] if _journey else None
                _last_scan_loc = _latest_scan.get("location","Unknown") if _latest_scan else "Unknown"
                _last_scan_time = _latest_scan.get("time","Unknown") if _latest_scan else "Unknown"
                _last_scan_note = _latest_scan.get("note","") if _latest_scan else ""
                st.markdown(f"""<div style='background:#FFF;border:1.5px solid #E3EAF0;border-radius:10px;padding:16px;margin-bottom:12px'>
  <div style='font-size:13px;font-weight:700;color:{NAVY};margin-bottom:10px'>📋 Shipment details — {_sk}</div>
  <div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px'>
    <div><span style='color:{MUTED}'>Origin</span><br><b>{_ss.get("origin","")}</b></div>
    <div><span style='color:{MUTED}'>Destination</span><br><b>{_ss.get("destination","")}</b></div>
    <div><span style='color:{MUTED}'>Contents</span><br><b>{_ss.get("contents","")}</b></div>
    <div><span style='color:{MUTED}'>Weight</span><br><b>{_ss.get("weight","")}</b></div>
    <div><span style='color:{MUTED}'>Current status</span><br><b style='color:#D71920'>{_ss.get("status","")}</b></div>
    <div><span style='color:{MUTED}'>ETA</span><br><b>{_ss.get("eta","")}</b></div>
  </div>
  <div style='margin-top:12px;padding:10px;background:#FFF7ED;border-radius:8px;font-size:12px'>
    <div style='font-weight:700;color:#C2410C;margin-bottom:4px'>Last scan location</div>
    <div style='color:{INK}'>{_last_scan_loc} · {_last_scan_time}</div>
    {f"<div style='color:{MUTED};margin-top:2px'>{_last_scan_note}</div>" if _last_scan_note else ""}
  </div>
  <div style='margin-top:10px;font-size:12px;color:{MUTED}'>
    <b>Action required:</b> Locate the parcel at the last known hub and update the scan to unblock delivery.
  </div>
</div>""", unsafe_allow_html=True)

        for i, order in enumerate(st.session_state.partner_deliveries):
            oid = order["order_id"]
            done_key = f"delivery_done_{oid}"
            called_key = f"delivery_called_{oid}"
            expand_key = f"delivery_expanded_{oid}"

            if st.session_state.get(done_key):
                st.markdown(f"<div class='card' style='opacity:0.5'><span class='status'>Delivered ✓</span> &nbsp; <b>{oid}</b> — {order['recipient_area']}</div>", unsafe_allow_html=True)
                continue

            with st.expander(f"📦  {oid}  ·  {order['recipient_area']}  ·  {order['eta_window']}", expanded=st.session_state.get(expand_key, i == 0)):
                col_info, col_map = st.columns([1, 1.4])
                with col_info:
                    st.markdown(f"""
<div class='partner-order-card'>
  <div class='card-title'>{oid}</div>
  <div style='font-size:13px;margin-top:8px'>
    <b>Deliver to:</b> {order['recipient_area']}<br>
    <b>Contents:</b> {order['contents']}<br>
    <b>Weight:</b> {order['weight']}<br>
    <b>Window:</b> {order['eta_window']}<br>
    <b>Distance:</b> {order['distance_km']} km from your current location
  </div>
  <div style='margin-top:12px;padding:10px;background:#FFF0F0;border-radius:8px;font-size:12px;color:#8B0000'>
    🔒 Customer phone is not shown. Use the button below to connect.
  </div>
</div>""", unsafe_allow_html=True)
                    btn_col1, btn_col2 = st.columns(2)
                    if btn_col1.button("📞  Contact customer", key=f"contact_{oid}", use_container_width=True):
                        st.session_state[called_key] = True
                    if st.session_state.get(called_key):
                        st.success("Demo relay call initiated. In the live product, your registered number and the customer's number are both masked by the DTDC relay.")
                    # Verified delivery: photo proof flow
                    _photo_step_key = f"delivery_photo_step_{oid}"
                    _photo_data_key = f"delivery_photo_data_{oid}"
                    if not st.session_state.get(_photo_step_key):
                        if btn_col2.button("✅  Mark delivered", key=f"done_{oid}", use_container_width=True, type="primary"):
                            st.session_state[_photo_step_key] = True
                            st.rerun()
                    else:
                        st.markdown("<div style='background:#F0FFF4;border:1px solid #86EFAC;border-radius:8px;padding:10px 14px;margin-top:6px;font-size:12px;color:#166534'><b>📸 Photo proof required</b> — take or upload a photo showing the parcel handed over.</div>", unsafe_allow_html=True)
                        _proof_photo = st.file_uploader("Upload delivery photo", type=["png","jpg","jpeg"], key=f"proof_upload_{oid}", help="A photo confirms delivery for the customer's record.")
                        _cam_key = f"delivery_cam_{oid}"
                        if st.button("📷  Use camera instead", key=f"cam_btn_{oid}"):
                            st.session_state[_cam_key] = True
                            st.rerun()
                        if st.session_state.get(_cam_key):
                            _proof_photo = st.camera_input("Take delivery photo", key=f"cam_input_{oid}")
                        proof_col1, proof_col2 = st.columns(2)
                        if proof_col1.button("✅  Confirm delivery", key=f"confirm_delivered_{oid}", use_container_width=True, type="primary"):
                            if _proof_photo:
                                import base64 as _b64
                                st.session_state[_photo_data_key] = _b64.b64encode(_proof_photo.getvalue()).decode("ascii")
                            st.session_state[done_key] = True
                            st.session_state[_photo_step_key] = False
                            st.rerun()
                        if proof_col2.button("Back", key=f"cancel_proof_{oid}", use_container_width=True):
                            st.session_state[_photo_step_key] = False
                            st.rerun()
                with col_map:
                    map_code = f"""
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<div id="dmap_{oid}" style="height:220px;border-radius:12px;overflow:hidden;border:1px solid #E3EAF0;"></div>
<script>
(function(){{
  var map=L.map('dmap_{oid}').setView([{order['lat']},{order['lng']}],14);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{maxZoom:19,attribution:'© OpenStreetMap'}}).addTo(map);
  var destIcon=L.divIcon({{html:'<div style="background:#102A43;color:white;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-size:15px;border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,.3)">🏠</div>',iconSize:[32,32],iconAnchor:[16,16],className:''}});
  var youIcon=L.divIcon({{html:'<div style="background:#D71920;color:white;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-size:15px;border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,.3)">🚴</div>',iconSize:[32,32],iconAnchor:[16,16],className:''}});
  L.marker([{order['lat']},{order['lng']}],{{icon:destIcon}}).addTo(map).bindPopup('<b>Delivery address</b><br>{order["recipient_area"]}').openPopup();
  L.marker([12.9490,77.5930],{{icon:youIcon}}).addTo(map).bindPopup('<b>Your location (demo)</b>');
  L.polyline([[12.9490,77.5930],[{(order['lat']+12.9490)/2},{(order['lng']+77.5930)/2}],[{order['lat']},{order['lng']}]],{{color:'#D71920',weight:3,dashArray:'5,5',opacity:0.7}}).addTo(map);
}})();
</script>"""
                    components.html(map_code, height=230)
                    st.caption(f"Map is demo only. Navigate to: {order['recipient_area']}, Bengaluru.")

        completed = sum(1 for o in st.session_state.partner_deliveries if st.session_state.get(f"delivery_done_{o['order_id']}"))
        total = len(st.session_state.partner_deliveries)
        st.markdown(f"<div class='feature-note' style='margin-top:14px'>Progress: {completed} of {total} deliveries completed today.</div>", unsafe_allow_html=True)

    # ── PICKUPS TODAY ─────────────────────────────────────────────────────────
    elif partner_selected == "Pickups Today":
        # Merge user pickup_requests that are partner-assigned into the partner view
        PARTNER_ASSIGNED_STATUSES = {"Pickup partner assigned", "Pickup partner on the way"}
        _user_as_partner = []
        for _upr in st.session_state.pickup_requests:
            _ustatus = _upr.get("status","")
            if _ustatus in PARTNER_ASSIGNED_STATUSES or _ustatus not in {"Pickup request received","DTDC confirmed","Parcel collected","Cancelled"}:
                _user_as_partner.append({
                    "order_id": _upr.get("booking_id",""),
                    "sender_area": _upr.get("area","") or _upr.get("pickup_address","")[:40],
                    "sender_name": _upr.get("sender_name",""),
                    "weight": _upr.get("weight",""),
                    "contents": _upr.get("contents",""),
                    "lat": _upr.get("pickup_latitude") or 12.9343,
                    "lng": _upr.get("pickup_longitude") or 77.5953,
                    "slot": _upr.get("time_slot",""),
                    "status": _ustatus,
                    "distance_km": "0.0",
                    "note": _upr.get("note",""),
                    "photo_data": _upr.get("photo_data"),
                    "_from_user": True,
                })
        # User orders shown first, then static demo orders
        _all_partner_pickups = _user_as_partner + st.session_state.partner_pickups
        total_pu_count = len(_all_partner_pickups)
        header("Pickups Today", f"{total_pu_count} parcel{'s' if total_pu_count != 1 else ''} to collect · Bengaluru South zone")

        for i, order in enumerate(_all_partner_pickups):
            oid = order["order_id"]
            done_key = f"pickup_done_{oid}"
            called_key = f"pickup_called_{oid}"

            if st.session_state.get(done_key):
                st.markdown(f"<div class='card' style='opacity:0.5'><span class='status'>Collected ✓</span> &nbsp; <b>{oid}</b> — {order['sender_area']}</div>", unsafe_allow_html=True)
                continue

            # Tag user-linked orders with a special indicator
            _from_user = order.get("_from_user", False)
            _expander_label = f"{'🔗 ' if _from_user else ''}🧳  {oid}  ·  {order['sender_area']}  ·  {order['slot']}"
            with st.expander(_expander_label, expanded=i == 0):
                if _from_user:
                    st.markdown(f"<div style='background:#EFF6FF;border-radius:8px;padding:8px 12px;margin-bottom:8px;font-size:12px;color:#1D4ED8;font-weight:600'>🔗 Booked through MyDTDC app — customer-submitted order</div>", unsafe_allow_html=True)
                col_info, col_map = st.columns([1, 1.4])
                with col_info:
                    _photo_html = ""
                    if order.get("photo_data"):
                        _photo_html = f"<div style='margin-top:10px'><div style='font-size:11px;color:#627D98;font-weight:600;margin-bottom:4px'>📷 Item photo from sender</div><img src='data:image/jpeg;base64,{order['photo_data']}' style='width:100%;max-height:120px;object-fit:cover;border-radius:8px;border:1px solid #BFDBFE' alt='Item photo'/></div>"
                    st.markdown(f"""
<div class='partner-order-card'>
  <div class='card-title'>{oid}</div>
  <div style='font-size:13px;margin-top:8px'>
    <b>Collect from:</b> {order['sender_area']}<br>
    <b>Contents:</b> {order['contents']}<br>
    <b>Weight:</b> {order['weight']}<br>
    <b>Slot:</b> {order['slot']}<br>
    <b>Distance:</b> {order['distance_km']} km from your current location
  </div>
  {f"<div style='margin-top:8px;padding:8px;background:#FFFBEB;border-radius:8px;font-size:12px;color:#78350F'>📋 Note: {order['note']}</div>" if order.get('note') else ""}
  {_photo_html}
  <div style='margin-top:12px;padding:10px;background:#FFF0F0;border-radius:8px;font-size:12px;color:#8B0000'>
    🔒 Sender phone is not shown. Use the button below to connect.
  </div>
</div>""", unsafe_allow_html=True)
                    btn_col1, btn_col2 = st.columns(2)
                    if btn_col1.button("📞  Contact sender", key=f"contact_pu_{oid}", use_container_width=True):
                        st.session_state[called_key] = True
                    if st.session_state.get(called_key):
                        st.success("Demo relay call initiated. In the live product, both numbers are masked by the DTDC relay.")
                    if btn_col2.button("✅  Mark collected", key=f"done_pu_{oid}", use_container_width=True, type="primary"):
                        st.session_state[done_key] = True
                        st.rerun()
                with col_map:
                    map_code = f"""
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<div id="pmap_{oid}" style="height:220px;border-radius:12px;overflow:hidden;border:1px solid #E3EAF0;"></div>
<script>
(function(){{
  var map=L.map('pmap_{oid}').setView([{order['lat']},{order['lng']}],14);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{maxZoom:19,attribution:'© OpenStreetMap'}}).addTo(map);
  var srcIcon=L.divIcon({{html:'<div style="background:#102A43;color:white;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-size:15px;border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,.3)">📦</div>',iconSize:[32,32],iconAnchor:[16,16],className:''}});
  var youIcon=L.divIcon({{html:'<div style="background:#D71920;color:white;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-size:15px;border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,.3)">🚴</div>',iconSize:[32,32],iconAnchor:[16,16],className:''}});
  L.marker([{order['lat']},{order['lng']}],{{icon:srcIcon}}).addTo(map).bindPopup('<b>Pickup location</b><br>{order["sender_area"]}').openPopup();
  L.marker([12.9490,77.5930],{{icon:youIcon}}).addTo(map).bindPopup('<b>Your location (demo)</b>');
  L.polyline([[12.9490,77.5930],[{(order['lat']+12.9490)/2},{(order['lng']+77.5930)/2}],[{order['lat']},{order['lng']}]],{{color:'#D71920',weight:3,dashArray:'5,5',opacity:0.7}}).addTo(map);
}})();
</script>"""
                    components.html(map_code, height=230)
                    st.caption(f"Map is demo only. Navigate to: {order['sender_area']}, Bengaluru.")

        completed_pu = sum(1 for o in _all_partner_pickups if st.session_state.get(f"pickup_done_{o['order_id']}"))
        total_pu = len(_all_partner_pickups)
        st.markdown(f"<div class='feature-note' style='margin-top:14px'>Progress: {completed_pu} of {total_pu} pickups completed today.</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ROLE: FRANCHISEE
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state.app_role == "Franchisee":
    st.markdown("<div class='hero' style='background:linear-gradient(120deg,#1A472A,#2D6A4F)'><h1>DTDC Franchise Portal</h1><p>Manage your franchise operations, shipment volumes and partner assignments from one place.</p><span class='hero-chip'>🏢 Franchise management &nbsp; · &nbsp; 📊 Volume dashboard &nbsp; · &nbsp; 🤝 Partner assignment</span></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.markdown("<div class='kpi'><div class='kpi-label'>SHIPMENTS THIS MONTH</div><div class='kpi-value'>Coming soon</div></div>", unsafe_allow_html=True)
    col2.markdown("<div class='kpi'><div class='kpi-label'>ACTIVE DELIVERY PARTNERS</div><div class='kpi-value'>Coming soon</div></div>", unsafe_allow_html=True)
    col3.markdown("<div class='kpi'><div class='kpi-label'>PENDING PICKUPS</div><div class='kpi-value'>Coming soon</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    left_f, right_f = st.columns(2)
    with left_f:
        st.markdown(f"""
<div class='card'>
  <div class='card-title'>What the Franchise Portal will do</div>
  <div class='card-sub'>Planned features for the next build sprint</div>
  <div class='feature-note'>
    📦 <b>Order volume dashboard</b> — see all shipments booked under your franchise code, with daily and weekly trends<br><br>
    🚴 <b>Partner management</b> — assign delivery partners to zones, track their daily progress, and review performance<br><br>
    💰 <b>Revenue and billing</b> — view shipment earnings, pending payouts from DTDC, and monthly statements<br><br>
    🗂 <b>Bulk booking</b> — book multiple shipments at once for business clients, with volume pricing<br><br>
    🔔 <b>Escalation queue</b> — handle customer complaints routed to your franchise before they reach DTDC central
  </div>
</div>""", unsafe_allow_html=True)
    with right_f:
        st.markdown(f"""
<div class='card'>
  <div class='card-title'>Register your franchise interest</div>
  <div class='card-sub'>Leave your details and the DTDC franchise team will reach out.</div>
</div>""", unsafe_allow_html=True)
        with st.form("franchise_interest"):
            fname = st.text_input("Your name")
            fbusiness = st.text_input("Business or company name")
            fcity = st.text_input("City / location")
            fphone = st.text_input("Mobile number")
            submitted_f = st.form_submit_button("Express interest", type="primary", use_container_width=True)
        if submitted_f:
            if fname and fcity and fphone:
                st.success("Interest recorded. A DTDC franchise executive will contact you within 3 business days. This is a demo — no data is stored or transmitted.")
            else:
                st.error("Please fill in name, city and mobile number.")

# ── footer ────────────────────────────────────────────────────────────────────
st.markdown("<div class='footer'>MyDTDC concept prototype · Sample shipment information · No real booking, payment or delivery contact is initiated</div>", unsafe_allow_html=True)
