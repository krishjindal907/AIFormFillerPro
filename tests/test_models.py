from models import User, Document, FormAnalysis, Feedback

def test_user_creation(test_app):
    with test_app.app_context():
        from models import db
        test_user = User.query.filter_by(email="test@example.com").first()
        assert test_user is not None
        assert test_user.name == "Test User"
        assert test_user.age == "30"

def test_profile_completion_calculation():
    # Model property test (Unit testing logic inside the class)
    
    # Empty user
    user1 = User()
    assert user1.profile_completion == 0
    
    # Partially filled user (2 fields out of 9)
    user2 = User(name="John Doe", phone="1234567890")
    # fields: name, phone, age, gender, address, profession, education, skills, preferences
    # 2 / 9 = 22.2% -> 22
    assert user2.profile_completion == 22
    
    # Fully filled user
    user3 = User(
        name="John", phone="123", age="25", gender="Male",
        address="123 Main", profession="Dev", education="BSc",
        skills="Python", preferences="Context"
    )
    assert user3.profile_completion == 100

def test_document_creation(test_app):
    with test_app.app_context():
        from models import db
        user = User.query.first()
        doc = Document(
            user_id=user.id,
            doc_type="Identity Card",
            filename="passport_scan.pdf",
            extracted_text="Extracted dummy text."
        )
        db.session.add(doc)
        db.session.commit()
        
        saved_doc = Document.query.first()
        assert saved_doc is not None
        assert saved_doc.doc_type == "Identity Card"
        assert saved_doc.user_ref == user
