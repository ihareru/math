from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(
        self,
        email=None,
        phone=None,
        password=None,
        **extra_fields,
    ):
        if not email and not phone:
            raise ValueError(
                "Необходимо указать email или номер телефона."
            )

        if email:
            email = self.normalize_email(email).lower()

        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(
            email=email,
            phone=phone,
            **extra_fields,
        )

        user.set_password(password)
        user.full_clean(exclude=["password"])
        user.save(using=self._db)

        return user

    def create_superuser(
            self,
            email=None,
            phone=None,
            password=None,
            **extra_fields,
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(
                "Суперпользователь должен иметь is_staff=True."
            )

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(
                "Суперпользователь должен иметь is_superuser=True."
            )

        if email:
            extra_fields.setdefault(
                "registration_method",
                self.model.RegistrationMethod.EMAIL,
            )
            extra_fields.setdefault(
                "email_verified",
                True,
            )
        elif phone:
            extra_fields.setdefault(
                "registration_method",
                self.model.RegistrationMethod.PHONE,
            )
            extra_fields.setdefault(
                "phone_verified",
                True,
            )

        return self.create_user(
            email=email,
            phone=phone,
            password=password,
            **extra_fields,
        )