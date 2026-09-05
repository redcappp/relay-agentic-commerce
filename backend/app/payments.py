"""Payment provider boundary.

All payment state transitions pass through this module.  The autonomous
provider deliberately models a test provider and emits the same capture /
webhook / verification events as the Razorpay path; it never touches a card.
"""
import hashlib
import hmac
import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET
from .models import Feedback, Order, Payment, Product
from .services import emit

def payment_dict(payment: Payment, order: Order):
    return {"order_id":order.id,"payment_id":payment.id,"status":order.status,
            "payment_status":payment.status,"verification_status":payment.verification_status,
            "source":"webhook" if payment.webhook_status=="PROCESSED" else "callback",
            "updated_at":(payment.verified_at or payment.created_at).isoformat()}

def create_payment(db: Session, order: Order, provider: str, run_id: str, provider_order_id: str | None = None):
    payment=Payment(id="pay_int_"+uuid.uuid4().hex[:18],order_id=order.id,provider=provider,provider_order_id=provider_order_id)
    order.status="PAYMENT_PENDING"; db.add(payment); db.commit(); db.refresh(payment)
    emit(db,run_id,"buyer","payment provider","PAYMENT_ORDER_CREATED","OK",f"{provider} payment order created",{"order_id":order.id,"payment_id":payment.id})
    return payment

def finalize_captured_payment(db: Session, payment: Payment, run_id: str, source: str):
    """Idempotent, authoritative transition from captured provider event to PAID."""
    order=db.get(Order,payment.order_id)
    if order is None: raise ValueError("Payment references an unknown order")
    if order.status=="PAID": return payment_dict(payment,order)
    payment.status="CAPTURED"; payment.verification_status="VERIFIED"; payment.webhook_status="PROCESSED" if source=="webhook" else payment.webhook_status; payment.verified_at=datetime.utcnow()
    emit(db,run_id,"buyer","payment provider","PAYMENT_CAPTURED","OK",f"Payment {payment.id} captured",{"source":source})
    product=db.get(Product,order.product_id)
    if product is None or product.inventory < 1:
        payment.status="FAILED"; payment.verification_status="FAILED"; order.status="FAILED"; db.commit()
        emit(db,run_id,"buyer","payment provider","ORDER_FAILED","BLOCKED","Payment could not finalize because inventory is unavailable")
        return payment_dict(payment,order)
    product.inventory-=1; order.status="PAID"; order.payment_id=payment.id
    purchased=db.execute(select(Feedback).where(Feedback.product_id==product.id,Feedback.event=="PURCHASED",Feedback.merchant_id==order.merchant_id).limit(1)).scalar_one_or_none()
    if purchased is None: db.add(Feedback(merchant_id=order.merchant_id,product_id=product.id,event="PURCHASED"))
    db.commit()
    emit(db,run_id,"buyer","payment verification","PAYMENT_SIGNATURE_VERIFIED","OK","Server-side payment verification completed")
    emit(db,run_id,"buyer","order","ORDER_PAID","OK",f"Order {order.id} is paid",{"payment_id":payment.id,"source":source})
    emit(db,run_id,"buyer","seller feedback","FEEDBACK_SENT","OK","Purchase feedback delivered to seller agent")
    return payment_dict(payment,order)

class RazorpayPaymentProvider:
    name="razorpay_test"
    def create_order(self, db: Session, order: Order, run_id: str):
        if not (RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET):
            raise ValueError("Razorpay Test credentials are not configured")
        import razorpay
        provider_order=razorpay.Client(auth=(RAZORPAY_KEY_ID,RAZORPAY_KEY_SECRET)).order.create({"amount":round(order.amount*100),"currency":"INR","receipt":order.id})
        payment=create_payment(db,order,self.name,run_id,provider_order["id"])
        emit(db,run_id,"buyer","razorpay checkout","PAYMENT_CHECKOUT_STARTED","OK","Razorpay Test checkout prepared")
        return payment, provider_order
    def verify_callback(self, db: Session, payment: Payment, razorpay_payment_id: str, signature: str, run_id: str):
        payload=f"{payment.provider_order_id}|{razorpay_payment_id}".encode()
        expected=hmac.new(RAZORPAY_KEY_SECRET.encode(),payload,hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected,signature): raise ValueError("Invalid Razorpay payment signature")
        payment.provider_payment_id=razorpay_payment_id; payment.status="AUTHORIZED"; payment.verification_status="SIGNATURE_VERIFIED"; db.commit()
        emit(db,run_id,"buyer","razorpay callback","PAYMENT_CALLBACK_RECEIVED","OK","Razorpay callback received")
        emit(db,run_id,"buyer","payment verification","PAYMENT_SIGNATURE_VERIFIED","OK","Razorpay callback signature verified; awaiting captured webhook")
        return payment
    def confirm_captured_payment(self, db: Session, payment: Payment, run_id: str):
        """Confirm a verified callback with Razorpay when a webhook is delayed.

        The callback signature proves the payment belongs to this order; this
        additional provider API lookup makes the capture status authoritative.
        A later signed webhook remains safe because finalization is idempotent.
        """
        if not payment.provider_payment_id:
            return payment_dict(payment, db.get(Order, payment.order_id))
        import razorpay
        provider_payment=razorpay.Client(auth=(RAZORPAY_KEY_ID,RAZORPAY_KEY_SECRET)).payment.fetch(payment.provider_payment_id)
        if provider_payment.get("status") != "captured":
            return payment_dict(payment, db.get(Order, payment.order_id))
        emit(db,run_id,"buyer","razorpay api","PAYMENT_CAPTURE_STATUS_CONFIRMED","OK","Razorpay API confirmed the payment is captured")
        return finalize_captured_payment(db,payment,run_id,"provider_api")

class DemoTestPaymentProvider:
    name="demo_autonomous"
    def process_test_payment(self, db: Session, order: Order, run_id: str):
        payment=create_payment(db,order,self.name,run_id,"order_test_"+uuid.uuid4().hex[:14])
        payment.provider_payment_id="pay_test_"+uuid.uuid4().hex[:14]; payment.status="AUTHORIZED"; db.commit()
        emit(db,run_id,"buyer","autonomous payment provider","AUTONOMOUS_PAYMENT_STARTED","OK","TEST MODE — no real money; autonomous test payment initiated")
        emit(db,run_id,"buyer","webhook","PAYMENT_WEBHOOK_RECEIVED","OK","Synthetic test-provider webhook received")
        emit(db,run_id,"buyer","webhook","PAYMENT_WEBHOOK_VERIFIED","OK","Synthetic test-provider webhook verified")
        result=finalize_captured_payment(db,payment,run_id,"webhook")
        emit(db,run_id,"buyer","autonomous payment provider","AUTONOMOUS_PAYMENT_COMPLETED","OK","Autonomous test payment completed")
        return result
