from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()


class Customer(db.Model):
    __tablename__ = "customers"

    id         = db.Column(db.String(20),  primary_key=True)
    name       = db.Column(db.String(255), nullable=False)
    email      = db.Column(db.String(255), nullable=False, unique=True)
    contact    = db.Column(db.String(50),  nullable=False)
    passport   = db.Column(db.String(100), nullable=False)
    registered = db.Column(db.String(20),  nullable=False)

    def to_dict(self):
        return {
            "id":         self.id,
            "name":       self.name,
            "email":      self.email,
            "contact":    self.contact,
            "passport":   self.passport,
            "registered": self.registered,
        }


class Booking(db.Model):
    __tablename__ = "bookings"

    id             = db.Column(db.String(20),  primary_key=True)
    customer_id    = db.Column(db.String(20),  nullable=True)
    passenger_name = db.Column(db.String(255), nullable=False)
    flight         = db.Column(db.String(50),  nullable=False)
    route          = db.Column(db.String(255), nullable=False)
    departure      = db.Column(db.String(50),  nullable=False)
    seat           = db.Column(db.String(10),  nullable=False)
    seat_class     = db.Column(db.String(50),  nullable=False)
    service        = db.Column(db.String(100), nullable=False)
    bags           = db.Column(db.String(5),   nullable=False)
    status         = db.Column(db.String(50),  nullable=False, default="Confirmed")
    date_booked    = db.Column(db.String(20),  nullable=False)

    def to_dict(self):
        return {
            "id":             self.id,
            "customer_id":    self.customer_id or "GUEST",
            "passenger_name": self.passenger_name,
            "flight":         self.flight,
            "route":          self.route,
            "departure":      self.departure,
            "seat":           self.seat,
            "seat_class":     self.seat_class,
            "service":        self.service,
            "bags":           self.bags,
            "status":         self.status,
            "date_booked":    self.date_booked,
        }
