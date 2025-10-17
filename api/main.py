"""
FastAPI backend for Translation Order Management
Minimal viable version - CRUD + calendar feed + webhook endpoint
"""
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from icalendar import Calendar, Event
import logging
from pydantic import BaseModel
import os

# Database setup
DATABASE_URL = "postgresql://tmorder:change_me_in_production@db:5432/tmorder"
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
    reminder_sent_24h = Column(Boolean, default=False)
    reminder_sent_6h = Column(Boolean, default=False)
    reminder_sent_2h = Column(Boolean, default=False)
    reminder_sent_due = Column(Boolean, default=False)
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


# Do not wrap `app` here; we'll wrap it after routes are defined so decorators
# bind to the FastAPI instance. The actual wrap is applied at the end of this
# module to avoid breaking decorator usage.

# Ensure logging configuration prints INFO-level logs to stdout
logging.basicConfig(level=logging.INFO)

# simple middleware to avoid proxy caching interfering with development
# @app.middleware("http")
# async def add_no_cache_header(request: Request, call_next):
#     response = await call_next(request)
#     # prevent intermediate proxies from caching responses during debugging
#     response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
#     return response


# Temporary request-logging middleware for proxy debugging
# @app.middleware("http")
# async def log_incoming_request(request: Request, call_next):
#     # Log method and path
#     try:
#         path = request.url.path
#     except Exception:
#         path = 'unknown'
#     headers_of_interest = [
#         'host', 'x-forwarded-for', 'x-forwarded-host', 'x-forwarded-proto', 'via', 'user-agent'
#     ]
#     hdrs = {h: request.headers.get(h) for h in headers_of_interest}
#     # Also print raw_path from ASGI scope for exact forwarded bytes
#     raw_path = request.scope.get('raw_path')
#     try:
#         raw_path_display = raw_path.decode('utf-8') if isinstance(raw_path, (bytes, bytearray)) else str(raw_path)
#     except Exception:
#         raw_path_display = str(raw_path)
#     msg = f"DEBUG-INCOMING: {request.method} {path} raw={raw_path_display} headers={hdrs}"
#     print(msg, flush=True)
#     logging.info(msg)

#     response = await call_next(request)

#     # Log response status and length
#     try:
#         length = response.headers.get('content-length')
#     except Exception:
#         length = None
#     resp_msg = f"DEBUG-RESPONSE: {request.method} {path} status={response.status_code} content-length={length}"
#     print(resp_msg, flush=True)
#     logging.info(resp_msg)
#     return response

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
    print(f"Creating order: {order}")
    db_order = Order(**order.model_dump())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    print(f"Order created with ID: {db_order.id}")
    return db_order

@app.get("/api/orders", response_model=list[OrderResponse])
def list_orders(
    status: str | None = None,
    db: Session = Depends(get_db),
    request: Request = None
):
    """List all orders, optionally filtered by status"""
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    results = query.all()
    # log for debugging: how many rows the DB returned and requester address
    try:
        client_addr = request.client.host if request and request.client else 'unknown'
    except Exception:
        client_addr = 'unknown'
    logging.info(f"list_orders: returned {len(results)} rows; remote={client_addr}")
    return results


@app.get("/api/orders/undelivered", response_model=list[OrderResponse])
def list_undelivered_orders(db: Session = Depends(get_db), request: Request = None):
    """List all undelivered orders with deadlines"""
    query = db.query(Order).filter(Order.status != "delivered").order_by(Order.deadline_at)
    results = query.all()
    try:
        client_addr = request.client.host if request and request.client else 'unknown'
    except Exception:
        client_addr = 'unknown'
    logging.info(f"list_undelivered_orders: returned {len(results)} rows; remote={client_addr}")
    return results


@app.get("/api/orders/undelivered/{client_name}", response_model=list[OrderResponse])
def list_undelivered_orders_by_client(client_name: str, db: Session = Depends(get_db), request: Request = None):
    """List undelivered orders for a specific client"""
    query = db.query(Order).filter(Order.status != "delivered", Order.customer_name == client_name).order_by(Order.deadline_at)
    results = query.all()
    try:
        client_addr = request.client.host if request and request.client else 'unknown'
    except Exception:
        client_addr = 'unknown'
    logging.info(f"list_undelivered_orders_by_client: client={client_name}, returned {len(results)} rows; remote={client_addr}")
    return results


@app.get("/api/orders/delivered", response_model=list[OrderResponse])
def list_delivered_orders(db: Session = Depends(get_db), request: Request = None):
    """List all delivered orders with delivery timestamps"""
    query = db.query(Order).filter(Order.status == "delivered").order_by(Order.updated_at.desc())
    results = query.all()
    try:
        client_addr = request.client.host if request and request.client else 'unknown'
    except Exception:
        client_addr = 'unknown'
    logging.info(f"list_delivered_orders: returned {len(results)} rows; remote={client_addr}")
    return results


@app.get("/api/orders/delivered/{client_name}", response_model=list[OrderResponse])
def list_delivered_orders_by_client(client_name: str, db: Session = Depends(get_db), request: Request = None):
    """List delivered orders for a specific client"""
    query = db.query(Order).filter(Order.status == "delivered", Order.customer_name == client_name).order_by(Order.updated_at.desc())
    results = query.all()
    try:
        client_addr = request.client.host if request and request.client else 'unknown'
    except Exception:
        client_addr = 'unknown'
    logging.info(f"list_delivered_orders_by_client: client={client_name}, returned {len(results)} rows; remote={client_addr}")
    return results


@app.put("/api/orders/{order_id}/deliver", response_model=OrderResponse)
def deliver_order(order_id: int, db: Session = Depends(get_db), request: Request = None):
    """Mark an order as delivered"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status == "delivered":
        raise HTTPException(status_code=400, detail="Order is already delivered")
    
    order.status = "delivered"
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    
    try:
        client_addr = request.client.host if request and request.client else 'unknown'
    except Exception:
        client_addr = 'unknown'
    logging.info(f"deliver_order: order_id={order_id}, customer={order.customer_name}, remote={client_addr}")
    return order


@app.put("/api/orders/{order_id}", response_model=OrderResponse)
def update_order(order_id: int, order_update: OrderUpdate, db: Session = Depends(get_db), request: Request = None):
    """Update an existing order"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Update only provided fields
    update_data = order_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    
    try:
        client_addr = request.client.host if request and request.client else 'unknown'
    except Exception:
        client_addr = 'unknown'
    logging.info(f"update_order: order_id={order_id}, updated_fields={list(update_data.keys())}, remote={client_addr}")
    return order


# @app.get("/api/debug/orders_count")
# def debug_orders_count(db: Session = Depends(get_db)):
#     """Debug endpoint: return total orders and last created timestamp to help diagnose proxy issues."""
#     total = db.query(Order).count()
#     last = db.query(Order).order_by(Order.created_at.desc()).first()
#     return {
#         "count": total,
#         "last": {
#             "id": last.id,
#             "created_at": last.created_at.isoformat()
#         } if last else None
#     }


# @app.get("/api/debug/headers")
# def debug_headers(request: Request):
#     """Debug endpoint: echo request headers and remote client address.

#     Use this from the outside (via Caddy) to see which headers and
#     forwarded addresses the proxy is sending to the API. This is a
#     temporary debugging aid and should be removed or restricted later.
#     """
#     try:
#         client_addr = request.client.host if request.client else None
#     except Exception:
#         client_addr = None

#     # Copy headers into a plain dict for JSON serialization
#     headers = {k: v for k, v in request.headers.items()}
#     return {"client": client_addr, "headers": headers}


# Backwards-compatibility routes: some proxies may strip the leading /api when
# forwarding requests. Provide duplicate endpoints without the /api prefix so
# proxied requests still reach the same handlers while we fix the proxy.
# @app.get("/debug/headers")
# def debug_headers_no_prefix(request: Request):
#     return debug_headers(request)


# @app.get("/api/debug/catch/{rest:path}")
# def debug_catchall(rest: str, request: Request):
#     """Catch-all debug endpoint to report the exact path and headers received.

#     Example: /api/debug/catch/some/path -> returns {'path': '/api/debug/catch/some/path', ...}
#     """
#     try:
#         client_addr = request.client.host if request.client else None
#     except Exception:
#         client_addr = None
#     headers = {k: v for k, v in request.headers.items()}
#     return {"client": client_addr, "received_path": request.url.path, "headers": headers, "rest": rest}


# @app.get("/debug/catch/{rest:path}")
# def debug_catchall_no_prefix(rest: str, request: Request):
#     return debug_catchall(rest, request)

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
    """Check for orders needing deadline reminders at different intervals"""
    now = datetime.utcnow()
    
    reminders = []
    
    # Check for 24h reminders
    reminder_24h_window_start = now + timedelta(hours=23, minutes=45)  # 24h ±15min
    reminder_24h_window_end = now + timedelta(hours=24, minutes=15)
    orders_24h = db.query(Order).filter(
        Order.deadline_at.between(reminder_24h_window_start, reminder_24h_window_end),
        Order.reminder_sent_24h == False,
        Order.status != "delivered",
        Order.status != "cancelled"
    ).all()
    for order in orders_24h:
        reminders.append({
            "id": order.id,
            "customer_name": order.customer_name,
            "deadline_at": order.deadline_at,
            "reminder_type": "24h",
            "message": f"⏰ **24 Hours Reminder**\nOrder #{order.id} for {order.customer_name}\nTopic: {order.topic or 'N/A'}\nDeadline: {order.deadline_at.strftime('%Y-%m-%d %H:%M UTC')}"
        })
    
    # Check for 6h reminders
    reminder_6h_window_start = now + timedelta(hours=5, minutes=45)  # 6h ±15min
    reminder_6h_window_end = now + timedelta(hours=6, minutes=15)
    orders_6h = db.query(Order).filter(
        Order.deadline_at.between(reminder_6h_window_start, reminder_6h_window_end),
        Order.reminder_sent_6h == False,
        Order.status != "delivered",
        Order.status != "cancelled"
    ).all()
    for order in orders_6h:
        reminders.append({
            "id": order.id,
            "customer_name": order.customer_name,
            "deadline_at": order.deadline_at,
            "reminder_type": "6h",
            "message": f"🚨 **6 Hours Reminder**\nOrder #{order.id} for {order.customer_name}\nTopic: {order.topic or 'N/A'}\nDeadline: {order.deadline_at.strftime('%Y-%m-%d %H:%M UTC')}"
        })
    
    # Check for 2h reminders
    reminder_2h_window_start = now + timedelta(hours=1, minutes=45)  # 2h ±15min
    reminder_2h_window_end = now + timedelta(hours=2, minutes=15)
    orders_2h = db.query(Order).filter(
        Order.deadline_at.between(reminder_2h_window_start, reminder_2h_window_end),
        Order.reminder_sent_2h == False,
        Order.status != "delivered",
        Order.status != "cancelled"
    ).all()
    for order in orders_2h:
        reminders.append({
            "id": order.id,
            "customer_name": order.customer_name,
            "deadline_at": order.deadline_at,
            "reminder_type": "2h",
            "message": f"⚠️ **2 Hours Reminder**\nOrder #{order.id} for {order.customer_name}\nTopic: {order.topic or 'N/A'}\nDeadline: {order.deadline_at.strftime('%Y-%m-%d %H:%M UTC')}"
        })
    
    # Check for due reminders (at deadline)
    reminder_due_window_start = now - timedelta(minutes=15)  # Within 15min of deadline
    reminder_due_window_end = now + timedelta(minutes=15)
    orders_due = db.query(Order).filter(
        Order.deadline_at.between(reminder_due_window_start, reminder_due_window_end),
        Order.reminder_sent_due == False,
        Order.status != "delivered",
        Order.status != "cancelled"
    ).all()
    for order in orders_due:
        reminders.append({
            "id": order.id,
            "customer_name": order.customer_name,
            "deadline_at": order.deadline_at,
            "reminder_type": "due",
            "message": f"🚨 **DEADLINE REACHED**\nOrder #{order.id} for {order.customer_name}\nTopic: {order.topic or 'N/A'}\nDeadline: {order.deadline_at.strftime('%Y-%m-%d %H:%M UTC')}"
        })
    
    return reminders

@app.post("/api/orders/{order_id}/mark-reminder-sent")
def mark_reminder_sent(order_id: int, reminder_type: str = "24h", db: Session = Depends(get_db)):
    """Mark specific reminder type as sent for an order"""
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if reminder_type == "24h":
        db_order.reminder_sent_24h = True
    elif reminder_type == "6h":
        db_order.reminder_sent_6h = True
    elif reminder_type == "2h":
        db_order.reminder_sent_2h = True
    elif reminder_type == "due":
        db_order.reminder_sent_due = True
    
    db.commit()
    return {"status": "updated"}


# Finally, wrap the FastAPI app with the ASGI raw logger so the ASGI-level
# logger executes before routing. This must happen after route definitions
# so decorators like @app.get/@app.post are bound to the original FastAPI app.
# try:
#     # `app` is currently the FastAPI instance; replace it with the wrapped ASGI app
#     import types
#     if not isinstance(app, ASGIRawLogger):
#         app = ASGIRawLogger(app)  # type: ignore
# except Exception as e:
#     print(f"Failed to wrap ASGI logger: {e}", flush=True)
