"""
FastAPI backend for Translation Order Management
Minimal viable version - CRUD + calendar feed + webhook endpoint
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from icalendar import Calendar, Event
from pydantic import BaseModel
import os

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://tmorder:change_me@db:5432/tmorder")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(255), nullable=False)
    source_lang = Column(String(10), nullable=False)
    target_lang = Column(String(10), nullable=False)
    word_count = Column(Integer)
    topic = Column(Text)
    deadline_at = Column(DateTime, nullable=False)
    status = Column(String(50), default="pending")
    reminder_sent = Column(Boolean, default=False)
    telegram_user_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Pydantic schemas
class OrderCreate(BaseModel):
    customer_name: str
    source_lang: str
    target_lang: str
    word_count: int | None = None
    topic: str | None = None
    deadline_at: datetime
    telegram_user_id: int | None = None

class OrderUpdate(BaseModel):
    customer_name: str | None = None
    source_lang: str | None = None
    target_lang: str | None = None
    word_count: int | None = None
    topic: str | None = None
    deadline_at: datetime | None = None
    status: str | None = None

class OrderResponse(BaseModel):
    id: int
    customer_name: str
    source_lang: str
    target_lang: str
    word_count: int | None
    topic: str | None
    deadline_at: datetime
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# FastAPI app
app = FastAPI(title="TM-Order API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy"}

@app.post("/api/orders", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """Create new translation order"""
    db_order = Order(**order.model_dump())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@app.get("/api/orders", response_model=list[OrderResponse])
def list_orders(
    status: str | None = None,
    db: Session = Depends(get_db)
):
    """List all orders, optionally filtered by status"""
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    return query.order_by(Order.deadline_at).all()

@app.get("/api/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get single order by ID"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.put("/api/orders/{order_id}", response_model=OrderResponse)
def update_order(order_id: int, order: OrderUpdate, db: Session = Depends(get_db)):
    """Update existing order"""
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    for key, value in order.model_dump(exclude_unset=True).items():
        setattr(db_order, key, value)
    
    db.commit()
    db.refresh(db_order)
    return db_order

@app.get("/calendar/ics")
def get_calendar_feed(
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """Generate iCalendar feed of all deadlines"""
    expected_token = os.getenv("SECRET_CALENDAR_TOKEN", "change_me")
    if token != expected_token:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    cal = Calendar()
    cal.add('prodid', '-//TM-Order Calendar//EN')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'Translation Deadlines')
    
    orders = db.query(Order).filter(Order.status != "delivered").all()
    
    for order in orders:
        event = Event()
        event.add('summary', f"#{order.id} {order.customer_name} {order.source_lang}→{order.target_lang}")
        event.add('dtstart', order.deadline_at.date())
        event.add('dtend', order.deadline_at.date())
        event.add('description', f"Topic: {order.topic or 'N/A'}\\nWords: {order.word_count or 'N/A'}")
        event.add('uid', f"tmorder-{order.id}@localhost")
        cal.add_component(event)
    
    return Response(content=cal.to_ical(), media_type="text/calendar")

@app.post("/bot/webhook")
async def telegram_webhook(update: dict):
    """Telegram webhook endpoint - placeholder for bot integration"""
    # Bot service will handle actual logic
    return {"status": "received"}

@app.get("/api/orders/check-reminders")
def check_reminders(db: Session = Depends(get_db)):
    """Check for orders needing deadline reminders (called by bot background job)"""
    now = datetime.utcnow()
    reminder_window = now + timedelta(hours=24)
    
    orders = db.query(Order).filter(
        Order.deadline_at <= reminder_window,
        Order.deadline_at > now,
        Order.reminder_sent == False,
        Order.status != "delivered"
    ).all()
    
    return [{"id": o.id, "customer_name": o.customer_name, "deadline_at": o.deadline_at} for o in orders]

@app.post("/api/orders/{order_id}/mark-reminder-sent")
def mark_reminder_sent(order_id: int, db: Session = Depends(get_db)):
    """Mark reminder as sent for an order"""
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    db_order.reminder_sent = True
    db.commit()
    return {"status": "updated"}
