class GameServiceError(Exception):
    """Базовая ошибка игрового сервиса."""


class NoActiveGameSessionError(GameServiceError):
    """У пользователя нет активной игровой сессии."""


class QuestionAlreadyAnsweredError(GameServiceError):
    """На этот пример уже был дан ответ."""


class QuestionDoesNotBelongToUserError(GameServiceError):
    """Пример не принадлежит текущему пользователю."""


class ActiveQuestionNotFoundError(GameServiceError):
    """В активной сессии отсутствует текущий пример."""