import jwt
from config import Config

class AuthService:
    def get_mock_token(self, user_id="mock_user_123", tier="paid"): # Default to 'paid' for full features
        """Generates a mock JWT token for development with a specified tier."""
        payload = {"user_id": user_id, "tier": tier}
        token = jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")
        return token

    def validate_token(self, token):
        """Validates a JWT token. Returns the full payload or None."""
        # --- THIS BLOCK IS NOW CORRECT ---
        try:
            # The code to be "tried" is now correctly indented under the try block.
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

# Singleton instance
auth_service = AuthService()