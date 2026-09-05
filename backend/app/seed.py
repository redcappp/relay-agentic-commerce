from sqlalchemy import select
from .models import Merchant, Product

CATALOGS = [
    ("TechNova", "Precision hardware, thoughtfully selected.", "#8b5cf6", [
      ("Sony WH-CH720N", "headphones", 4499, 18, "wireless,noise cancelling,35-hour battery", 4.5),
      ("JBL Tune 770NC", "headphones", 4999, 9, "wireless,noise cancelling,70-hour battery", 4.4),
      ("Logitech MX Master 3S", "mouse", 8995, 14, "wireless,ergonomic,usb-c", 4.7),
      ("Orbit Aluminum Laptop Stand", "accessories", 1499, 25, "laptop stand,aluminum,adjustable", 4.3),
      ("Nova 7-in-1 USB-C Hub", "accessories", 1899, 20, "usb-c,hdmi,ethernet", 4.2),
      ("SoundShell Travel Case", "accessories", 799, 31, "headphones case,hard shell", 4.2),
      ("Keychron K2", "keyboard", 7499, 10, "wireless,mechanical,bluetooth", 4.6),
      ("Sony WF-C700N", "headphones", 4790, 13, "wireless,earbuds,noise cancelling", 4.4),
      ("Aura Desk Light", "accessories", 1199, 12, "led,usb-c,adjustable", 4.1),
      ("PixelGuard Sleeve", "accessories", 899, 34, "laptop sleeve,water resistant", 4.2),
    ]),
    ("ElectroHub", "Everyday electronics with quick fulfillment.", "#22d3ee", [
      ("Sony WH-CH720N", "headphones", 4399, 22, "wireless,noise cancelling,35-hour battery", 4.5),
      ("boAt Nirvana 751 ANC", "headphones", 3999, 28, "wireless,noise cancelling,65-hour battery", 4.3),
      ("Anker Soundcore Q20i", "headphones", 4699, 16, "wireless,hybrid anc,40-hour battery", 4.4),
      ("LiftPro Laptop Stand", "accessories", 1299, 19, "laptop stand,foldable,aluminum", 4.2),
      ("Pulse Compact Keyboard", "keyboard", 2199, 21, "wireless,compact,bluetooth", 4.1),
      ("Glide Wireless Mouse", "mouse", 1099, 26, "wireless,silent,usb receiver", 4.1),
      ("CableCraft USB-C Hub", "accessories", 1699, 17, "usb-c,hdmi,card reader", 4.2),
      ("boAt Rockerz 450", "headphones", 1699, 40, "wireless,on-ear,15-hour battery", 4.1),
      ("CarryPod Headphone Case", "accessories", 649, 35, "headphones case,hard shell", 4.0),
      ("Anker 323 Charger", "accessories", 1399, 24, "usb-c,33w,fast charging", 4.4),
    ])]

def seed(db):
    if db.scalar(select(Merchant.id).limit(1)):
        return
    for name, desc, accent, products in CATALOGS:
        merchant = Merchant(name=name, description=desc, accent=accent); db.add(merchant); db.flush()
        for p in products:
            db.add(Product(merchant_id=merchant.id, name=p[0], category=p[1], price=p[2], inventory=p[3], specs=p[4], rating=p[5]))
    db.commit()
