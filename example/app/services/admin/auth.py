import jwt
from fastapi import HTTPException, status

from example.app.schemas.admin.user import CurrentUser

from example.common.config import get_settings



class AuthService:
    def __init__(self):
        self.settings = get_settings()


    def get_authorized_user(self, authorization:str | None, *roles:str) -> CurrentUser:

        current_user = self._get_current_user(authorization)
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="用户访问无权限")
        return current_user

    def _get_current_user(self, authorization:str | None) -> CurrentUser:

        access_token = self._extract_token(authorization)
        current_user = self._decode_access_token(access_token)
        return current_user

    def _extract_token(self, authorization:str | None) -> str:

        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="该用户未认证")
        return authorization.split(" ", 1)[1]


    def _decode_access_token(self, access_token:str) -> CurrentUser:

        payload = jwt.decode(access_token, self.settings.jwt_secret, algorithms=[self.settings.jwt_algorithm])
        return CurrentUser.model_validate(payload)

    def encode_access_token(self, current_user: CurrentUser) -> str:
        return jwt.encode(current_user.model_dump(), self.settings.jwt_secret, algorithm=self.settings.jwt_algorithm)



