from passlib.context import CryptContext
from shared.security import create_access_token

# Configure Passlib to use bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Mock Database for this example (replace with SQLAlchemy later)
# Structure: {email: {"id": int, "email": str, "hashed_password": str}}
fake_user_db = {}
user_id_counter = 1

class AuthService:
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def register_user(cls, user_data: dict) -> dict:
        global user_id_counter
        email = user_data["email"]
        
        if email in fake_user_db:
            raise ValueError("Email already registered")
            
        hashed_password = cls.get_password_hash(user_data["password"])
        
        new_user = {
            "id": user_id_counter,
            "email": email,
            "hashed_password": hashed_password
        }
        fake_user_db[email] = new_user
        user_id_counter += 1
        
        return new_user

    @classmethod
    def authenticate_user(cls, user_data: dict) -> str:
        email = user_data["email"]
        password = user_data["password"]
        
        user = fake_user_db.get(email)
        if not user or not cls.verify_password(password, user["hashed_password"]):
            raise ValueError("Invalid credentials")
            
        # Generate the JWT using our shared security package
        # We pass the user ID as the 'sub' (subject)
        access_token = create_access_token(data={"sub": str(user["id"])})
        return access_token