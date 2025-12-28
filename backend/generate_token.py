def generate_token():
    from src.core.config import get_settings
    settings = get_settings()
    settings.database_url = "postgresql://ntufar@localhost:5432/fna_development"
    
    from src.database.connection import init_database
    init_database()
    
    from src.database.connection import SessionLocal
    from src.models.user import User
    from src.core.security import auth_manager
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "ntufar@example.com").first()
        if not user:
            print("User not found")
            return
        
        user_data = {
            "id": str(user.id),
            "email": user.email,
            "subscription_tier": user.subscription_tier
        }
        token = auth_manager.create_access_token(user_data)
        print(token)
    finally:
        db.close()

if __name__ == "__main__":
    generate_token()
