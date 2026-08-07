class CheatActivationError(Exception):
    """
    Базовая ошибка активации чит-кода.
    """


class CheatCodeNotFoundError(CheatActivationError):
    """
    Код не существует.
    """


class CheatCodeInactiveError(CheatActivationError):
    """
    Код отключён администратором.
    """


class CheatCodeNotStartedError(CheatActivationError):
    """
    Период активации кода ещё не начался.
    """


class CheatCodeExpiredError(CheatActivationError):
    """
    Период активации кода закончился.
    """


class CheatGlobalLimitReachedError(
    CheatActivationError
):
    """
    Достигнут общий лимит активаций.
    """


class CheatUserLimitReachedError(
    CheatActivationError
):
    """
    Пользователь исчерпал свой лимит.
    """


class CheatHasNoRewardsError(CheatActivationError):
    """
    У кода не настроено ни одной награды.
    """