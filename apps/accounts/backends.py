from django.contrib.auth.backends import ModelBackend

from .models import User


class EmailBackend(ModelBackend):
    def authenticate(
        self,
        request,
        username=None,
        password=None,
        identifier=None,
        **kwargs,
    ):
        email = identifier or username

        if not email or not password:
            return None

        email = email.strip().lower()

        user = (
            User.objects
            .filter(email__iexact=email)
            .first()
        )

        if user is None:
            # Выполняем хеширование фиктивного пароля,
            # чтобы уменьшить различие во времени ответа.
            User().set_password(password)
            return None

        if (
            user.check_password(password)
            and self.user_can_authenticate(user)
        ):
            return user

        return None