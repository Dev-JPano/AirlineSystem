from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from models import db, Customer, Booking
from datetime import date
from functools import wraps
import os, re
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "skylink_secret_2026")

# ── Database (Supabase PostgreSQL via SQLAlchemy) ──────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "")
# SQLAlchemy requires 'postgresql://' not 'postgres://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

app.config["SQLALCHEMY_DATABASE_URI"]        = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"]      = {
    "pool_pre_ping": True,
    "pool_recycle":  300,
    "connect_args":  {"sslmode": "require"},
}

db.init_app(app)

# Create tables if they don't exist (idempotent on first run)
with app.app_context():
    db.create_all()

# ── Constants ─────────────────────────────────────────────────────────────────
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "skylink2026")


# ── ID helpers ────────────────────────────────────────────────────────────────
def next_customer_id():
    last = Customer.query.order_by(Customer.id.desc()).all()
    if not last:
        return "CUST-001"
    nums = []
    for c in last:
        try:
            nums.append(int(c.id.split("-")[-1]))
        except ValueError:
            pass
    return f"CUST-{(max(nums) + 1):03d}" if nums else "CUST-001"


def next_booking_id():
    last = Booking.query.order_by(Booking.id.desc()).all()
    if not last:
        return "BK-001"
    nums = []
    for b in last:
        try:
            nums.append(int(b.id.split("-")[-1]))
        except ValueError:
            pass
    return f"BK-{(max(nums) + 1):03d}" if nums else "BK-001"


# ── Auth decorator ────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Page Routes ───────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/booking")
def booking():
    return render_template("booking.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        if u == ADMIN_USER and p == ADMIN_PASS:
            session["admin"] = True
            return redirect(url_for("dashboard"))
        error = "Invalid credentials. Please try again."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    total_customers = Customer.query.count()
    total_bookings  = Booking.query.count()
    confirmed   = Booking.query.filter_by(status="Confirmed").count()
    processing  = Booking.query.filter_by(status="Processing").count()
    completed   = Booking.query.filter_by(status="Completed").count()
    cancelled   = Booking.query.filter_by(status="Cancelled").count()
    return render_template("dashboard.html",
        total_customers=total_customers,
        total_bookings=total_bookings,
        confirmed=confirmed,
        processing=processing,
        completed=completed,
        cancelled=cancelled,
    )

@app.route("/customers")
@login_required
def customers():
    return render_template("customers.html")

@app.route("/bookings")
@login_required
def bookings():
    return render_template("bookings.html")


# ── API: Customers ────────────────────────────────────────────────────────────
@app.route("/api/customers", methods=["GET"])
def api_get_customers():
    customers = Customer.query.order_by(Customer.id).all()
    return jsonify([c.to_dict() for c in customers])


@app.route("/api/customers", methods=["POST"])
def api_add_customer():
    body = request.get_json()
    name     = (body.get("name",     "") or "").strip()
    email    = (body.get("email",    "") or "").strip()
    contact  = (body.get("contact",  "") or "").strip()
    passport = (body.get("passport", "") or "").strip()

    if not all([name, email, contact, passport]):
        return jsonify({"error": "All fields are required."}), 400
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"error": "Invalid email format."}), 400
    if Customer.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered."}), 409

    cid = next_customer_id()
    cust = Customer(
        id=cid, name=name, email=email,
        contact=contact, passport=passport,
        registered=date.today().strftime("%Y-%m-%d"),
    )
    db.session.add(cust)
    db.session.commit()
    return jsonify({"success": True, "id": cid}), 201


@app.route("/api/customers/<cid>", methods=["PUT"])
@login_required
def api_update_customer(cid):
    body = request.get_json()
    cust = Customer.query.get(cid)
    if not cust:
        return jsonify({"error": "Customer not found."}), 404
    for field in ["name", "email", "contact", "passport"]:
        if field in body:
            setattr(cust, field, body[field].strip())
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/customers/<cid>", methods=["DELETE"])
@login_required
def api_delete_customer(cid):
    cust = Customer.query.get(cid)
    if not cust:
        return jsonify({"error": "Customer not found."}), 404
    db.session.delete(cust)
    db.session.commit()
    return jsonify({"success": True})


# ── API: Bookings ─────────────────────────────────────────────────────────────
@app.route("/api/bookings", methods=["GET"])
def api_get_bookings():
    bookings = Booking.query.order_by(Booking.id).all()
    return jsonify([b.to_dict() for b in bookings])


@app.route("/api/bookings", methods=["POST"])
def api_add_booking():
    body = request.get_json()
    required = ["passenger_name", "flight", "route", "departure",
                "seat", "seat_class", "service", "bags"]
    for field in required:
        if not (body.get(field) or "").strip():
            return jsonify({"error": f"Field '{field}' is required."}), 400

    bid = next_booking_id()
    bk = Booking(
        id=bid,
        customer_id=body.get("customer_id", "GUEST") or "GUEST",
        passenger_name=body["passenger_name"].strip(),
        flight=body["flight"].strip(),
        route=body["route"].strip(),
        departure=body["departure"].strip(),
        seat=body["seat"].strip(),
        seat_class=body["seat_class"].strip(),
        service=body["service"].strip(),
        bags=body["bags"].strip(),
        status="Confirmed",
        date_booked=date.today().strftime("%Y-%m-%d"),
    )
    db.session.add(bk)
    db.session.commit()
    return jsonify({"success": True, "id": bid}), 201


@app.route("/api/bookings/<bid>", methods=["PUT"])
@login_required
def api_update_booking(bid):
    body = request.get_json()
    bk = Booking.query.get(bid)
    if not bk:
        return jsonify({"error": "Booking not found."}), 404
    for field in ["status", "seat", "bags", "service"]:
        if field in body:
            setattr(bk, field, body[field].strip())
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/bookings/<bid>", methods=["DELETE"])
@login_required
def api_delete_booking(bid):
    bk = Booking.query.get(bid)
    if not bk:
        return jsonify({"error": "Booking not found."}), 404
    db.session.delete(bk)
    db.session.commit()
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True)
