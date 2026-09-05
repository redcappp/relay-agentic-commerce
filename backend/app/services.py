import json, re, time, uuid, hashlib, hmac
from collections import defaultdict, deque
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .models import Merchant, Product, AgentEvent, BuyerRequest, Feedback, Order, WebhookEvent

class FixedWindowLimiter:
    def __init__(self, limit=20, seconds=60): self.limit, self.seconds, self.calls = limit, seconds, defaultdict(deque)
    def check(self, key):
        now=time.time(); q=self.calls[key]
        while q and q[0] < now-self.seconds: q.popleft()
        if len(q) >= self.limit: return False, max(1, int(self.seconds-(now-q[0])))
        q.append(now); return True, 0

buyer_limiter=FixedWindowLimiter(); seller_limiters={1:FixedWindowLimiter(), 2:FixedWindowLimiter()}
class TTLCache:
    def __init__(self, ttl=120): self.ttl=ttl; self.data={}
    def get(self, key):
        value=self.data.get(key)
        return value[0] if value and value[1]>time.time() else None
    def set(self,key,value): self.data[key]=(value,time.time()+self.ttl)
merchant_cache=TTLCache(300); product_cache=TTLCache(120)

def emit(db: Session, run_id, agent, component, event_type, status, message, metadata=None):
    event=AgentEvent(run_id=run_id, agent=agent, component=component, event_type=event_type, status=status, message=message, metadata_json=json.dumps(metadata or {}))
    db.add(event); db.commit(); db.refresh(event); return event

def event_dict(e): return {"id":e.id,"run_id":e.run_id,"timestamp":e.timestamp.isoformat(),"agent":e.agent,"component":e.component,"event_type":e.event_type,"status":e.status,"message":e.message,"metadata":json.loads(e.metadata_json)}

def parse_intent(prompt):
    p=prompt.lower(); category="headphones" if any(x in p for x in ["headphone","earphone","earbud"]) else "accessories" if any(x in p for x in ["accessor","stand","hub","case","charger","laptop"]) else "keyboard" if "keyboard" in p else "mouse" if "mouse" in p else "accessories"
    amount=re.search(r"(?:under|below|less than|₹|rs\.?)\s*([\d,]+)",p)
    max_price=float(amount.group(1).replace(",","")) if amount else None
    specs=[x for x in ("wireless","noise cancelling","anc","usb-c","laptop stand","case") if x in p]
    return {"category":category,"max_price":max_price,"specifications":specs}

def guard(prompt):
    bad=("ignore previous", "execute sql", "select *", "secret key", "bypass payment", "drop table")
    return not any(x in prompt.lower() for x in bad)

def product_dict(p, m, score=None):
    return {"id":p.id,"name":p.name,"merchant_id":m.id,"merchant":m.name,"price":p.price,"currency":"INR","category":p.category,"inventory":p.inventory,"available":p.inventory>0,"specifications":p.specs.split(","),"rating":p.rating,"score":score,"why_matched":"Matches your requested category, availability, and price constraints."}

# These tool functions are the only data access boundary for agents. Inputs are parsed/validated fields, never SQL.
def search_merchants_tool(db, category, run_id):
    key=f"merchant:{category}"; cached=merchant_cache.get(key)
    if cached is not None:
        emit(db,run_id,"buyer","merchant/category cache","CACHE_HIT","OK",f"Merchant/category cache hit for {category}"); return cached
    rows=db.execute(select(Merchant).join(Product).where(Product.category==category,Product.inventory>0).distinct()).scalars().all()
    result=[{"id":m.id,"name":m.name,"description":m.description,"accent":m.accent} for m in rows]; merchant_cache.set(key,result)
    emit(db,run_id,"buyer","merchant/category cache","CACHE_MISS","OK",f"Merchant/category cache miss; discovered {len(result)} merchants"); return result

def seller_query_tool(db, merchant_id, intent, run_id, force_limit=False):
    allowed, retry=seller_limiters[merchant_id].check(str(merchant_id)) if not force_limit else (False,60)
    merchant=db.get(Merchant,merchant_id)
    emit(db,run_id,merchant.name,"rate limiter","SELLER_RATE_LIMIT_CHECK","ALLOWED" if allowed else "BLOCKED", "Seller request accepted" if allowed else f"Seller limit reached; retry in {retry}s")
    if not allowed: return {"merchant":merchant.name,"products":[],"cache_hit":False,"error":"RATE_LIMITED"}
    key=f"{merchant_id}:{json.dumps(intent,sort_keys=True)}"; cached=product_cache.get(key)
    if cached is not None:
        emit(db,run_id,merchant.name,"product cache","SELLER_CACHE_HIT","OK","Seller product cache hit"); return {"merchant":merchant.name,"products":cached,"cache_hit":True}
    query=select(Product).where(Product.merchant_id==merchant_id,Product.category==intent['category'],Product.inventory>0)
    if intent['max_price']: query=query.where(Product.price<=intent['max_price'])
    # `query` is a SQLAlchemy 2.x Select, not a legacy Query.  Keep this
    # database access inside the seller tool boundary and materialise it via
    # the session so a seller failure cannot leak a broken result downstream.
    products=db.execute(query.order_by(Product.price)).scalars().all(); out=[]
    for p in products:
        spec_text=p.specs.lower()
        if all(s in spec_text or (s=="anc" and "noise cancelling" in spec_text) for s in intent['specifications']): out.append(product_dict(p,merchant))
    product_cache.set(key,out); emit(db,run_id,merchant.name,"product query tool","PRODUCT_DATABASE_QUERY","OK",f"Validated search_products returned {len(out)} products",intent)
    return {"merchant":merchant.name,"products":out,"cache_hit":False}

def run_search(db, prompt, force_failure=False):
    run_id=str(uuid.uuid4()); db.add(BuyerRequest(id=run_id,prompt=prompt)); db.commit()
    emit(db,run_id,"buyer","buyer agent","BUYER_REQUEST","OK","Buyer request received")
    allowed,retry=buyer_limiter.check("buyer")
    emit(db,run_id,"buyer","rate limiter","BUYER_RATE_LIMIT_CHECK","ALLOWED" if allowed else "BLOCKED", "Buyer request accepted" if allowed else f"Request blocked. Retry in {retry}s")
    if not allowed: return {"run_id":run_id,"error":"RATE_LIMITED","message":f"Buyer rate limit reached. Try again in {retry} seconds.","products":[]}
    ok=guard(prompt); emit(db,run_id,"buyer","guardrails","GUARDRAIL_CHECK","ALLOWED" if ok else "BLOCKED", "Request is within permitted commerce operations." if ok else "Prompt attempts a restricted operation.")
    if not ok:return {"run_id":run_id,"error":"GUARDRAIL_BLOCKED","message":"Direct database access is not an available agent capability. Database selection must occur through approved tools.","products":[]}
    intent=parse_intent(prompt); emit(db,run_id,"buyer","tool selector","TOOL_SELECTED","OK","Selected search_merchants and request_seller_products",intent)
    merchants=search_merchants_tool(db,intent['category'],run_id); emit(db,run_id,"buyer","merchant discovery","MERCHANT_SEARCH","OK",f"Selected {', '.join(x['name'] for x in merchants)}")
    responses=[]
    for m in merchants:
        emit(db,run_id,"buyer","seller gateway","SELLER_REQUEST","OK",f"Requesting catalog from {m['name']}",intent)
        responses.append(seller_query_tool(db,m['id'],intent,run_id,force_failure and m['id']==1))
    products=[p for r in responses for p in r['products']]
    for p in products:
        p['score']=round((10 if p['inventory']>0 else 0)+(6 if p['rating']>=4.4 else 3)+(5000-p['price'])/1000,2); db.add(Feedback(merchant_id=p['merchant_id'],product_id=p['id'],event="IMPRESSION"))
    products.sort(key=lambda p:(-p['score'],p['price'])); db.commit()
    unavailable=[r['merchant'] for r in responses if r.get('error')]
    if unavailable:
        for merchant in unavailable:
            emit(db,run_id,merchant,"rate limiter","SELLER_RATE_LIMITED","BLOCKED",f"{merchant} was rate limited")
        emit(db,run_id,"buyer","seller fallback","FALLBACK_SELLER_USED","DEGRADED",f"{', '.join(unavailable)} temporarily unavailable; continued with remaining seller.")
    emit(db,run_id,"buyer","ranking","PRODUCT_RANKING","OK",f"Ranked {len(products)} matching products from {len(merchants)-len(unavailable)} sellers")
    return {"run_id":run_id,"intent":intent,"products":products,"seller_responses":responses,"message":f"Found {len(products)} matching products from {len(merchants)-len(unavailable)} merchant agents."}

def report(db, merchant_id):
    merchant=db.get(Merchant,merchant_id); products=db.scalars(select(Product).where(Product.merchant_id==merchant_id)).all(); ids=[p.id for p in products]
    def count(event): return db.scalar(select(func.count()).select_from(Feedback).where(Feedback.merchant_id==merchant_id,Feedback.event==event)) or 0
    impressions,selections,purchases=count("IMPRESSION"),count("SELECTED"),count("PURCHASED")
    revenue=db.scalar(select(func.coalesce(func.sum(Order.amount),0)).where(Order.merchant_id==merchant_id,Order.status=="PAID")) or 0
    top=products[0].name if products else "—"
    return {"merchant":merchant.name,"requests":impressions,"products_returned":impressions,"selected":selections,"orders":purchases,"revenue":revenue,"conversion":round(purchases/selections*100,1) if selections else 0,"top_product":top,"cache_hit_rate":0,"recommendation":f"Keep {top} well stocked; it is the current catalog leader."}

def verify_webhook(raw, signature, secret): return bool(secret) and hmac.compare_digest(hmac.new(secret.encode(),raw,"sha256").hexdigest(),signature or "")
