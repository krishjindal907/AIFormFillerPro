import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(150), default='')
    phone = db.Column(db.String(50), default='')
    age = db.Column(db.String(50), default='')
    profile_pic = db.Column(db.String(255), default='')
    gender = db.Column(db.String(50), default='')
    address = db.Column(db.Text, default='')
    father_name = db.Column(db.String(150), default='')
    mother_name = db.Column(db.String(150), default='')
    profession = db.Column(db.String(150), default='')
    education = db.Column(db.String(150), default='')
    skills = db.Column(db.Text, default='') 
    preferences = db.Column(db.Text, default='')
    
    analyzed_forms = db.relationship('FormAnalysis', backref='user', lazy=True)
    feedbacks = db.relationship('Feedback', backref='user', lazy=True)

    @property
    def profile_completion(self):
        fields = [self.name, self.phone, self.age, self.gender, self.address, self.profession, self.education, self.skills, self.preferences]
        filled = sum(1 for f in fields if f and str(f).strip())
        return int((filled / len(fields)) * 100)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doc_type = db.Column(db.String(100), nullable=False) # e.g., 'Aadhar Card', 'PAN Card', 'Marksheet', 'Generic'
    filename = db.Column(db.String(255), nullable=False)
    extracted_text = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_ref = db.relationship('User', backref=db.backref('documents', lazy=True))

class FormAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_url = db.Column(db.String(500), nullable=True) # url or generic 'custom_html'
    form_html_snapshot = db.Column(db.Text, nullable=False) # sanitized structural representation
    fields_detected = db.Column(db.Integer, default=0)
    matched_fields = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    form_analysis_id = db.Column(db.Integer, db.ForeignKey('form_analysis.id'), nullable=False)
    is_accurate = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
