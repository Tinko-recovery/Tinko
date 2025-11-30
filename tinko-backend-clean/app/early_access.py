import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from supabase import create_client, Client

router = APIRouter()

# --- SUPABASE INIT ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise Exception("❌ Supabase ENV variables missing")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# --- SENDGRID ENV ---
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "contact@tinko.in")
ALERT_EMAIL = FROM_EMAIL  # receives signup alerts

if not SENDGRID_API_KEY:
    raise Exception("❌ SENDGRID_API_KEY missing in environment")


class EarlyAccessRequest(BaseModel):
    email: str
    company: str | None = None


@router.post("/signup")
async def early_access_signup(data: EarlyAccessRequest):
    """
    1. Save signup in Supabase
    2. Email alert to Tinko team
    3. Thank-you email to customer
    """

    # --------------------------------
    # 1️⃣ Save user to Supabase
    # --------------------------------
    try:
        supabase.table("early_access").insert({
            "email": data.email,
            "company": data.company
        }).execute()
    except Exception as e:
        print("Supabase DB Error:", e)
        raise HTTPException(status_code=500, detail="Could not save user")

    # --------------------------------
    # Prepare SendGrid client
    # --------------------------------
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SendGrid init failed: {e}")

    # --------------------------------
    # 2️⃣ Send alert email to YOU
    # --------------------------------
    alert_html = f"""
        <h2>🚀 New Early Access Signup</h2>
        <p><b>Email:</b> {data.email}</p>
        <p><b>Company:</b> {data.company or 'Not Provided'}</p>
    """

    alert_msg = Mail(
        from_email=FROM_EMAIL,
        to_emails=ALERT_EMAIL,
        subject="New Early Access Signup",
        html_content=alert_html
    )

    try:
        sg.send(alert_msg)
    except Exception as e:
        print("SendGrid Alert Error:", e)

    # --------------------------------
    # 3️⃣ Send thank-you email to USER
    # --------------------------------
    user_html = f"""
        <div style="font-family:Arial;padding:20px;">
            <h2 style="color:#DE6B06;">Welcome to Tinko!</h2>
            <p>Hi there,</p>
            <p>Thank you for joining the early access waitlist.</p>
            <p>We will notify you the moment Tinko is ready.</p>
            <br>
            <p>— Team Tinko<br>The Moment That Matters — Saved.</p>
        </div>
    """

    user_msg = Mail(
        from_email=FROM_EMAIL,
        to_emails=data.email,
        subject="You're on the Tinko Early Access List 🎉",
        html_content=user_html
    )

    try:
        sg.send(user_msg)
    except Exception as e:
        print("SendGrid Customer Email Error:", e)

    return {"message": "Signup completed"}


# --------------------------------
# OPTIONAL — TEST EMAIL ENDPOINT
# --------------------------------
@router.get("/test-email")
async def test_email():
    """Send a test email to verify SendGrid setup."""
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        msg = Mail(
            from_email=FROM_EMAIL,
            to_emails=ALERT_EMAIL,
            subject="Tinko Test Email",
            html_content="<strong>This is a test email from the Tinko backend.</strong>"
        )
        sg.send(msg)
        return {"status": "ok", "detail": "Test email sent"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
