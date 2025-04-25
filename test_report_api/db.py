from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def init_app(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{Config.DATABASE}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress warning
    db.init_app(app)

# Define models (replace with your actual models)
class TestReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(255))
    part_number = db.Column(db.String(255))
    date = db.Column(db.DateTime)
    result = db.Column(db.String(50))

    def __repr__(self):
        return f"<TestReport {self.serial_number}>"

class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('test_report.id'))
    name = db.Column(db.String(255))
    result_value = db.Column(db.Float)
    status = db.Column(db.String(50))
    unit_of_measure = db.Column(db.String(50))

    report = db.relationship("TestReport", back_populates="measurements")

    def __repr__(self):
        return f"<Measurement {self.name}>"

TestReport.measurements = db.relationship("Measurement", back_populates="report")