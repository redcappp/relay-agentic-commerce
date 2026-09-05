import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./commerce.db")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
RAZORPAY_DASHBOARD_URL = os.getenv("RAZORPAY_DASHBOARD_URL", "")
PAYMENT_MODE = os.getenv("PAYMENT_MODE", "razorpay_test")
AUTONOMOUS_MODE_MAX_AMOUNT = float(os.getenv("AUTONOMOUS_MODE_MAX_AMOUNT", "5000"))
AUTONOMOUS_MODE_ALLOWED_CURRENCY = os.getenv("AUTONOMOUS_MODE_ALLOWED_CURRENCY", "INR")
AUTONOMOUS_MODE_ALLOWED_CATEGORIES = {x.strip() for x in os.getenv("AUTONOMOUS_MODE_ALLOWED_CATEGORIES", "headphones,electronics").split(",") if x.strip()}
