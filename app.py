from __future__ import annotations

import os
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

st.set_page_config(page_title="MyDTDC | Ship with confidence", page_icon="📦", layout="wide", initial_sidebar_state="collapsed")
location_component = components.declare_component("mydtdc_location", path=str(Path(__file__).parent / "location_component"))
NAVY, RED, PALE, INK, MUTED = "#102A43", "#D71920", "#F4F7FA", "#243B53", "#627D98"
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{{font-family:Inter,system-ui,sans-serif;color:{INK}}}.stApp{{background:{PALE}}}[data-testid="stHeader"]{{background:transparent}}
.block-container{{max-width:1160px;padding-top:1.15rem;padding-bottom:3rem}}.brandbar{{background:white;border:1px solid #E3EAF0;border-radius:16px;padding:14px 20px;display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;box-shadow:0 3px 14px #102a4308}}
.brand{{display:flex;gap:12px;align-items:center}}.brandmark{{height:42px;width:42px;display:grid;place-items:center;border-radius:12px;background:{RED};color:white;font-size:21px}}.brandname{{color:{NAVY};font-weight:800;font-size:20px;letter-spacing:-.5px}}.brandtag{{color:{MUTED};font-size:11px;margin-top:2px}}.demo-pill{{border-radius:999px;background:#FFF3E8;color:#9A4D00;padding:7px 11px;font-size:11px;font-weight:700}}
.hero{{background:linear-gradient(120deg,#102A43,#174B73);color:#fff;border-radius:20px;padding:28px 30px;margin-bottom:18px}}.hero h1{{font-size:30px;line-height:1.15;margin:0 0 8px;letter-spacing:-.8px;color:white}}.hero p{{margin:0;color:#D9E7F2;font-size:14px}}.hero-chip{{display:inline-block;margin-top:16px;border:1px solid #ffffff42;border-radius:999px;padding:7px 11px;font-size:11px;color:#EFF6FB}}
.card{{background:white;border:1px solid #E3EAF0;border-radius:16px;padding:19px;box-shadow:0 3px 14px #102a4308;margin-bottom:14px}}.card-title{{font-weight:750;color:{NAVY};font-size:16px;margin-bottom:4px}}.card-sub{{color:{MUTED};font-size:12px;margin-bottom:14px}}.kpi{{background:white;border:1px solid #E3EAF0;border-radius:14px;padding:15px}}.kpi-label{{color:{MUTED};font-size:11px}}.kpi-value{{color:{NAVY};font-size:18px;font-weight:750;margin-top:4px}}
.status{{display:inline-block;background:#E8F7EF;color:#16794B;border-radius:999px;padding:5px 9px;font-size:11px;font-weight:700}}.status-warn{{background:#FFF5E5;color:#9A6400}}.timeline{{border-left:2px solid #D9E2EC;margin:10px 0 8px 8px;padding-left:19px}}.event{{position:relative;padding:1px 0 17px}}.event:before{{content:"";width:10px;height:10px;border-radius:50%;background:#2F855A;border:2px solid white;position:absolute;left:-25px;top:4px;box-shadow:0 0 0 1px #2F855A}}.event.future:before{{background:white;box-shadow:0 0 0 1px #9FB3C8}}.event b{{color:{NAVY};font-size:13px}}.event small{{display:block;color:{MUTED};margin-top:3px;font-size:11px}}.feature-note{{color:{MUTED};font-size:11px;padding:10px 12px;background:#F4F7FA;border-radius:10px}}
div.stButton>button{{border-radius:10px;font-weight:650}}div[data-testid="stForm"]{{background:white;border:1px solid #E3EAF0;padding:18px;border-radius:15px}}.footer{{text-align:center;color:#829AB1;font-size:11px;padding:16px 0 2px}}@media(max-width:700px){{.hero h1{{font-size:24px}}.hero{{padding:22px}}.brandbar{{padding:12px 14px}}}}
</style>""", unsafe_allow_html=True)

def get_db():
    # Streamlit raises StreamlitSecretNotFoundError when no secrets file exists,
    # so check for its presence before reading optional Supabase settings.
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

@st.cache_resource()
def db():
    return get_db()

def sample_shipments():
    today = date.today()
    return {
        "D1234567890": {"consignment_no":"D1234567890","recipient":"Aarav Mehta","origin":"Bengaluru, Karnataka","destination":"Mumbai, Maharashtra","status":"In transit","eta":(today+timedelta(days=2)).isoformat(),"updated":datetime.now().strftime("%d %b, %I:%M %p"),"events":[{"title":"Shipment picked up","place":"Indiranagar, Bengaluru","time":"Today, 10:42 AM","done":True},{"title":"Arrived at Bengaluru hub","place":"Bengaluru, Karnataka","time":"Today, 02:15 PM","done":True},{"title":"In transit to destination","place":"Next scan pending","time":"On the way","done":False},{"title":"Out for delivery","place":"Mumbai, Maharashtra","time":"Estimated delivery day","done":False}],"delivery_partner":"Will be shared when out for delivery"},
        "D9876543210": {"consignment_no":"D9876543210","recipient":"Demo Receiver","origin":"Delhi, NCR","destination":"Pune, Maharashtra","status":"Out for delivery","eta":today.isoformat(),"updated":datetime.now().strftime("%d %b, %I:%M %p"),"events":[{"title":"Shipment picked up","place":"Connaught Place, Delhi","time":"Yesterday, 09:10 AM","done":True},{"title":"Arrived at Pune hub","place":"Pune, Maharashtra","time":"Today, 06:20 AM","done":True},{"title":"Out for delivery","place":"Pune, Maharashtra","time":"Today, 09:05 AM","done":True},{"title":"Delivered","place":"Your delivery address","time":"Pending","done":False}],"delivery_partner":"Rohit • 98••• ••42"}
    }

if "shipments" not in st.session_state: st.session_state.shipments = sample_shipments()
if "pickup_requests" not in st.session_state: st.session_state.pickup_requests = []
if "wallet_balance" not in st.session_state: st.session_state.wallet_balance = 250
if "chat" not in st.session_state: st.session_state.chat = []
if "nav" not in st.session_state: st.session_state.nav = "Home"
if "pending_nav" not in st.session_state: st.session_state.pending_nav = None
if "location_refresh" not in st.session_state: st.session_state.location_refresh = 0
if "pickup_requests_loaded" not in st.session_state: st.session_state.pickup_requests_loaded = False
if "pickup_address" not in st.session_state: st.session_state.pickup_address = ""
if "pickup_call_requested" not in st.session_state: st.session_state.pickup_call_requested = set()
geo = location_component(refresh=st.session_state.location_refresh, key="mydtdc_location_component", default=None)
if isinstance(geo, dict) and geo.get("latitude") is not None and geo.get("longitude") is not None:
    st.session_state.device_location = {"latitude": geo["latitude"], "longitude": geo["longitude"], "accuracy": geo.get("accuracy")}
    if not st.session_state.pickup_address:
        st.session_state.pickup_address = f"Current device location ({geo['latitude']:.5f}, {geo['longitude']:.5f}) — please add street / PIN code"
client = db()
backend = "Supabase connected" if client else "Demo mode · session data"
st.markdown(f"<div class='brandbar'><div class='brand'><div class='brandmark'>D</div><div><div class='brandname'>MyDTDC</div><div class='brandtag'>Ship with confidence</div></div></div><div class='demo-pill'>{backend}</div></div>",unsafe_allow_html=True)
pages=["Home","Book a Pickup","Track Shipment","My Shipments","My Pickups","Wallet","Help & Support"]
if st.session_state.pending_nav in pages:
    st.session_state.nav = st.session_state.pending_nav
    st.session_state.pending_nav = None
selected=st.radio("Navigation",pages,horizontal=True,label_visibility="collapsed",key="nav")

def save_pickup(record):
    st.session_state.pickup_requests.insert(0,record)
    if client:
        try:
            db_record={k:v for k,v in record.items() if k not in {"photo_data","location_accuracy"}}
            client.table("pickup_requests").insert(db_record).execute()
        except Exception as exc: st.info(f"Saved for this session. Supabase write did not complete: {exc}")

def load_pickups():
    if client and not st.session_state.pickup_requests_loaded:
        try:
            rows=client.table("pickup_requests").select("*").order("created_at",desc=True).limit(50).execute().data or []
            known={p.get("booking_id") for p in st.session_state.pickup_requests}
            st.session_state.pickup_requests.extend(p for p in rows if p.get("booking_id") not in known)
        except Exception as exc:
            st.info(f"Showing pickup requests from this session. Could not load saved requests: {exc}")
        st.session_state.pickup_requests_loaded=True

def support_answer(history, prompt):
    api_key=get_secret("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return "The live support assistant is not connected yet. You can still create a support case below; for this demo I can guide you through pickup booking and shipment tracking."
    try:
        client_ai=OpenAI(api_key=api_key, timeout=25.0, max_retries=1)
        conversation=[{"role":"system","content":"You are MyDTDC support in a student concept prototype. Give concise, empathetic, practical answers about pickup booking, parcel tracking, ETAs and delivery issues. Never claim to access live DTDC systems or change a booking. Do not invent tracking events, prices, policies, phone numbers, or promises. If the user needs action or the answer is uncertain, offer the in-app support-case form. Explain that shown tracking data is sample/demo data. Do not ask for full payment details, passwords or OTPs."}]
        conversation.extend({"role":role,"content":text} for role,text in history[-10:])
        conversation.append({"role":"user","content":prompt})
        response=client_ai.responses.create(model="gpt-5-nano",input=conversation,max_output_tokens=250)
        answer=(response.output_text or "I couldn't prepare a response. Please create a support case below.").strip()
        return answer
    except Exception as exc:
        return f"I couldn't reach the support assistant just now. Please try again or create a support case below. (Assistant error: {type(exc).__name__})"

def header(title,subtitle):
    st.markdown(f"<div class='card-title' style='font-size:23px'>{title}</div><div class='card-sub'>{subtitle}</div>",unsafe_allow_html=True)

if selected=="Home":
    st.markdown("<div class='hero'><h1>Your parcels, on the move.</h1><p>Book a pickup, follow every milestone and know what happens next.</p><span class='hero-chip'>📍 12,000+ PIN codes &nbsp; · &nbsp; 🚚 Doorstep pickup &nbsp; · &nbsp; 🔔 Helpful updates</span></div>",unsafe_allow_html=True)
    left,right=st.columns([1.35,1])
    with left:
        st.markdown("<div class='card'><div class='card-title'>Track a shipment</div><div class='card-sub'>Enter your DTDC consignment number to see the latest updates.</div></div>",unsafe_allow_html=True)
        with st.form("home_track"):
            number=st.text_input("Consignment number",value="D1234567890",placeholder="e.g. D1234567890")
            go=st.form_submit_button("Track shipment",type="primary",use_container_width=True)
        if go: st.session_state.track_number=number.strip().upper();st.session_state.pending_nav="Track Shipment";st.rerun()
    with right:
        st.markdown("<div class='card'><div class='card-title'>Send a parcel</div><div class='card-sub'>Schedule a pickup from your doorstep in a few simple steps.</div></div>",unsafe_allow_html=True)
        if st.button("＋  Book a pickup",use_container_width=True,type="primary"): st.session_state.pending_nav="Book a Pickup";st.rerun()
        if st.button("View all shipments",use_container_width=True): st.session_state.pending_nav="My Shipments";st.rerun()
    st.markdown("<div class='card-title' style='margin:8px 0 12px'>Your recent shipments</div>",unsafe_allow_html=True)
    cols=st.columns(2)
    for col,key in zip(cols,list(st.session_state.shipments)[:2]):
        s=st.session_state.shipments[key]
        with col: st.markdown(f"<div class='card'><div style='display:flex;justify-content:space-between'><b style='color:{NAVY}'>{key}</b><span class='status'>{s['status']}</span></div><div style='font-size:12px;color:{MUTED};margin-top:10px'>{s['origin']} → {s['destination']}</div><div style='font-size:12px;margin-top:10px'>Estimated delivery: <b>{s['eta']}</b></div></div>",unsafe_allow_html=True)

elif selected=="Book a Pickup":
    header("Book a doorstep pickup","Tell us where and when to collect your parcel. A booking number is created when you submit.")
    left,right=st.columns([1.35,.8])
    with left:
        geo_error=geo.get("error") if isinstance(geo,dict) else None
        if geo_error and geo_error!="Location permission was declined.": st.caption(geo_error)
        if st.session_state.get("device_location"):
            coords=st.session_state.device_location
            st.caption(f"Current device location detected (±{coords.get('accuracy',0):.0f} m). Please confirm the street address and PIN code.")
        if st.button("↻  Use my current location",key="refresh_pickup_location"):
            st.session_state.location_refresh+=1
            st.rerun()
        with st.form("pickup_form"):
            st.markdown("**Pickup details**")
            c1,c2=st.columns(2);name=c1.text_input("Your name",placeholder="Full name");phone=c2.text_input("Mobile number",placeholder="10-digit mobile")
            address=st.text_area("Pickup address (edit or complete your detected location)",value=st.session_state.pickup_address,placeholder="House / street, area, city, PIN code")
            st.markdown("**Person handing over the parcel**")
            c_collector1,c_collector2=st.columns(2)
            collector_name=c_collector1.text_input("Collector name",placeholder="Person who will hand over the parcel")
            collector_phone=c_collector2.text_input("Collector mobile",placeholder="Their contact number")
            c3,c4=st.columns(2);pickup_date=c3.date_input("Preferred date",min_value=date.today(),value=date.today()+timedelta(days=1));slot=c4.selectbox("Convenient time slot",["9 AM – 12 PM","12 PM – 3 PM","3 PM – 6 PM"])
            st.markdown("**Parcel details**")
            c5,c6=st.columns(2);contents=c5.selectbox("What are you sending?",["Documents","Clothing","Electronics","Personal items","Other"]);weight=c6.selectbox("Approx. weight",["Up to 0.5 kg","0.5–2 kg","2–5 kg","More than 5 kg"])
            photo=st.camera_input("Take a location photo (optional)",help="On mobile this opens the camera. The photo stays in this demo session.")
            photo_upload=st.file_uploader("Or upload a location photo",type=["png","jpg","jpeg"],help="Demo only: this file is not stored in Supabase.")
            priority=st.checkbox("Priority pickup · request earliest available collection (demo premium ₹99)")
            note=st.text_input("Note for the pickup partner (optional)",placeholder="Gate, landmark, or access instructions")
            submitted=st.form_submit_button("Confirm pickup request",type="primary",use_container_width=True)
        if submitted:
            digits="".join(ch for ch in phone if ch.isdigit())
            collector_digits="".join(ch for ch in collector_phone if ch.isdigit())
            if not name or len(digits)<10 or not address or not collector_name or len(collector_digits)<10: st.error("Enter your name and mobile, complete the pickup address, and add the collector’s name and valid mobile number.")
            else:
                saved_photo=photo or photo_upload
                photo_data=None
                if saved_photo:
                    import base64
                    photo_data=base64.b64encode(saved_photo.getvalue()).decode("ascii")
                coords=st.session_state.get("device_location",{})
                record={"booking_id":"PU"+uuid.uuid4().hex[:8].upper(),"sender_name":name,"phone":phone,"pickup_address":address,"collector_name":collector_name,"collector_phone":collector_phone,"pickup_latitude":coords.get("latitude"),"pickup_longitude":coords.get("longitude"),"location_accuracy":coords.get("accuracy"),"photo_data":photo_data,"pickup_date":pickup_date.isoformat(),"time_slot":slot,"contents":contents,"weight":weight,"priority":priority,"note":note,"status":"Pickup request received","created_at":datetime.now().isoformat()}
                save_pickup(record);st.session_state.last_pickup=record;st.success(f"Pickup requested! Booking number: {record['booking_id']}.")
                st.info(f"{pickup_date.strftime('%d %b %Y')} · {slot} · {'Priority pickup requested' if priority else 'Standard pickup'}")
                st.session_state.pending_nav="My Pickups"
                st.rerun()
    with right:
        st.markdown("<div class='card'><div class='card-title'>Pickup, made clearer</div><div class='card-sub'>A simple flow from request to collection.</div><div class='feature-note'>✓ Start with your device location<br><br>✓ Choose an address and pickup slot<br><br>✓ Add a photo or landmark<br><br>✓ Share who will hand over the parcel<br><br>✓ Follow progress in My Pickups</div></div>",unsafe_allow_html=True)
        if st.session_state.get("last_pickup"):
            p=st.session_state.last_pickup;st.markdown(f"<div class='card'><div class='card-title'>Latest pickup</div><b>{p['booking_id']}</b><p><span class='status status-warn'>{p['status']}</span></p><small>{p['pickup_date']} · {p['time_slot']}</small></div>",unsafe_allow_html=True)

elif selected=="Track Shipment":
    header("Track your shipment","Follow parcel scans and see the next expected step. Sample consignment numbers are in My Shipments.")
    c1,c2=st.columns([1.2,1]);number=c1.text_input("Consignment number",value=st.session_state.get("track_number","D1234567890"),placeholder="Enter consignment number")
    with c2:
        st.write("")
        if st.button("Find shipment",type="primary",use_container_width=True): st.session_state.track_number=number.strip().upper()
    key=st.session_state.get("track_number",number.strip().upper());shipment=st.session_state.shipments.get(key)
    if shipment:
        cols=st.columns(3)
        for col,label,value in zip(cols,["CURRENT STATUS","ESTIMATED DELIVERY","LAST UPDATED"],[shipment["status"],shipment["eta"],shipment["updated"]]): col.markdown(f"<div class='kpi'><div class='kpi-label'>{label}</div><div class='kpi-value'>{value}</div></div>",unsafe_allow_html=True)
        a,b=st.columns([1.2,.8])
        with a: st.markdown(f"<div class='card'><div class='card-title'>Parcel journey</div><div class='card-sub'>{shipment['origin']} → {shipment['destination']}</div><div class='timeline'>"+"".join(f"<div class='event {' ' if e['done'] else 'future'}'><b>{e['title']}</b><small>{e['place']} · {e['time']}</small></div>" for e in shipment["events"])+"</div></div>",unsafe_allow_html=True)
        with b:
            st.markdown(f"<div class='card'><div class='card-title'>Delivery details</div><div class='card-sub'>Partner details appear here when available.</div><p><b>Delivery partner</b><br>{shipment['delivery_partner']}</p><div class='feature-note'>ETA is an estimate based on latest available shipment information.</div></div>",unsafe_allow_html=True)
            if shipment["status"]=="Out for delivery":
                if st.button("📞  Call delivery partner",key="call_partner_"+key,use_container_width=True):
                    st.session_state[f"call_status_{key}"]=True
                if st.session_state.get(f"call_status_{key}"):
                    st.success("Demo call request ready: the live service would connect from your registered number using a masked relay. No call is placed by this prototype.")
            with st.expander("Something doesn't look right?"):
                issue=st.selectbox("Choose an issue",["Marked delivered, but I did not receive it","Delivery attempt did not happen","Tracking has not updated","I need another kind of help"]);details=st.text_area("Add details",placeholder="Tell us what happened")
                if st.button("Create support case"): st.success(f"Case CS{uuid.uuid4().hex[:7].upper()} created for {key}. Shipment details are attached.")
    else: st.warning("Not found in demo data. Try D1234567890 or D9876543210.")

elif selected=="My Shipments":
    header("My shipments","Your tracked parcels and recent pickup bookings.")
    for key,s in st.session_state.shipments.items():
        with st.container(border=True):
            a,b,c=st.columns([1.2,1.1,.7]);a.markdown(f"**{key}**  \n{s['origin']} → {s['destination']}");b.markdown(f"<span class='status'>{s['status']}</span><br><small>ETA: {s['eta']}</small>",unsafe_allow_html=True)
            if c.button("Track",key="track_"+key): st.session_state.track_number=key;st.session_state.pending_nav="Track Shipment";st.rerun()
    if st.session_state.pickup_requests:
        st.markdown("<div class='card-title' style='margin-top:18px'>Pickup requests</div>",unsafe_allow_html=True)
        for p in st.session_state.pickup_requests: st.markdown(f"<div class='card'><b>{p['booking_id']}</b> &nbsp; <span class='status status-warn'>{p['status']}</span><div class='card-sub' style='margin:8px 0 0'>{p['pickup_address']} · {p['pickup_date']} · {p['time_slot']}</div></div>",unsafe_allow_html=True)

elif selected=="My Pickups":
    header("My pickups","Check your pickup booking reference, selected slot, collector contact and request progress.")
    load_pickups()
    if not st.session_state.pickup_requests:
        st.info("No pickup requests yet. Use Book a Pickup to create your first request.")
        if st.button("Book a pickup",type="primary"):
            st.session_state.pending_nav="Book a Pickup";st.rerun()
    for p in st.session_state.pickup_requests:
        with st.container(border=True):
            a,b=st.columns([1.2,.8])
            a.markdown(f"### {p.get('booking_id','Pickup request')}\n**{p.get('status','Pickup request received')}** · {p.get('pickup_date','')} · {p.get('time_slot','')}")
            b.markdown(f"**Pickup address**\n\n{p.get('pickup_address','Address not available')}\n\n**Person handing over**\n\n{p.get('collector_name','')} · {p.get('collector_phone','')}")
            st.markdown("<div class='timeline'><div class='event'><b>Request received</b><small>Booking reference generated · "+str(p.get("created_at",""))[:16].replace("T"," ")+"</small></div><div class='event future'><b>Pickup confirmation</b><small>Pending DTDC confirmation</small></div><div class='event future'><b>Pickup partner assigned</b><small>Partner and call option appear when assigned</small></div><div class='event future'><b>Parcel collected</b><small>Collection scan will confirm handover</small></div></div>",unsafe_allow_html=True)
            if p.get("photo_data"):
                import base64
                st.image(base64.b64decode(p["photo_data"]),caption="Pickup location photo · demo session only",width=280)
            if p.get("priority"):
                st.caption("Priority pickup requested · availability and price require confirmation by a real booking service.")

elif selected=="Wallet":
    header("DTDC Wallet","A prototype wallet for eligible refunds, shipment credits and future bookings.")
    st.markdown(f"<div class='hero'><div style='font-size:12px;color:#D9E7F2'>AVAILABLE BALANCE · DEMO</div><h1 style='margin-top:8px'>₹{st.session_state.wallet_balance:.0f}</h1><p>Use your balance toward an eligible booking.</p></div>",unsafe_allow_html=True)
    a,b=st.columns(2)
    with a:
        st.markdown("<div class='card'><div class='card-title'>Add demo credit</div><div class='card-sub'>Simulates adding funds; no payment is taken.</div></div>",unsafe_allow_html=True);credit=st.selectbox("Choose amount",[100,250,500])
        if st.button("Add demo credit",type="primary"): st.session_state.wallet_balance+=credit;st.success(f"₹{credit} demo credit added.");st.rerun()
    with b: st.markdown("<div class='card'><div class='card-title'>Recent activity</div><div class='card-sub'>Concept only; not a real payment account.</div><div class='feature-note'>₹250 · Welcome demo credit<br><br>Refund status and wallet terms need definition before launch.</div></div>",unsafe_allow_html=True)

elif selected=="Help & Support":
    header("How can we help?","Get a quick answer or create a case with shipment details attached.")
    ai_status="GPT-5 nano connected" if get_secret("OPENAI_API_KEY") and OpenAI else "Demo mode · add OPENAI_API_KEY for GPT-5 nano"
    st.markdown(f"<div class='feature-note'>Support assistant · {ai_status}. It cannot view live DTDC systems; shipment updates in this prototype are sample data. Create a support case if it cannot resolve your question.</div>",unsafe_allow_html=True)
    for role,msg in st.session_state.chat:
        with st.chat_message(role): st.write(msg)
    prompt=st.chat_input("Ask about a shipment, pickup, or delivery")
    if prompt:
        answer=support_answer(st.session_state.chat,prompt)
        st.session_state.chat.append(("user",prompt))
        st.session_state.chat.append(("assistant",answer));st.rerun()
    with st.expander("Create a support case"):
        contact=st.text_input("Email or mobile number");problem=st.text_area("What do you need help with?")
        if st.button("Submit support case"):
            if not contact or not problem: st.error("Add a contact method and describe the issue.")
            else: st.success(f"Support case SC{uuid.uuid4().hex[:7].upper()} created in this demo session.")

st.markdown("<div class='footer'>MyDTDC concept prototype · Sample shipment information · No real booking, payment or delivery contact is initiated</div>",unsafe_allow_html=True)

