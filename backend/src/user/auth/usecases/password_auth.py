from uuid import uuid4

from redis.asyncio import Redis

from loggers import get_logger
from src.core.database.uow import ApplicationUnitOfWork, RepositoryProtocol
from src.core.errors.enums import ErrorCode
from src.core.errors.exceptions import PermissionDeniedException, UnauthorizedException
from src.core.schemas import TokenModel
from src.core.utils.security import verify_password
from src.user.auth.schemas import PasswordAuthResponse, PasswordLoginRequest
from src.user.auth.security import create_access_token, create_refresh_token
from src.user.schemas import UserProfileViewModel

logger = get_logger(__name__)


class PasswordAuthUseCase:
    """Authenticate an existing user with a login + password pair."""

    def __init__(
        self,
        uow: ApplicationUnitOfWork[RepositoryProtocol],
        redis_client: Redis,
    ) -> None:
        self.uow = uow
        self.redis_client = redis_client

    async def execute(self, data: PasswordLoginRequest) -> PasswordAuthResponse:
        """
        Validates the login/password pair and returns a token pair on success.

        Args:
            data: The login and password submitted by the client.

        Returns:
            PasswordAuthResponse: Access/refresh tokens and the user profile.

        Raises:
            UnauthorizedException: If credentials are wrong or the user has no password set.
            PermissionDeniedException: If the user account is inactive.
        """
        invalid_exc = UnauthorizedException(ErrorCode.AUTH_INVALID_CREDENTIALS)

        async with self.uow as uow:
            user = await uow.users.get_single(uow.session, login=data.login)

            if not user or not user.password_hash:
                raise invalid_exc

            is_valid = await verify_password(data.password, user.password_hash)
            if not is_valid:
                raise invalid_exc

            if not user.is_active:
                raise PermissionDeniedException(ErrorCode.USER_BLOCKED)

            token_data = {"sub": str(user.id)}
            session_id = str(uuid4())
            family = str(uuid4())

            access_token = await create_access_token(
                token_data, redis_client=self.redis_client, session_id=session_id
            )
            refresh_token = await create_refresh_token(
                token_data,
                redis_client=self.redis_client,
                session_id=session_id,
                family=family,
            )

            await uow.commit()

            logger.info(f"User authenticated via password: {user.id}")

            return PasswordAuthResponse(
                tokens=TokenModel(
                    access_token=access_token, refresh_token=refresh_token
                ),
                user=UserProfileViewModel.model_validate(user),
            )
