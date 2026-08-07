class QuestionGenerationError(Exception):
    """
    Не удалось сформировать пример,
    соответствующий настройкам пользователя.
    """


class OperationDisabledError(
    QuestionGenerationError
):
    """
    Выбранное математическое действие отключено.
    """


class NoEnabledOperationsError(
    QuestionGenerationError
):
    """
    В смешанном режиме не осталось доступных действий.
    """


class InvalidGenerationSettingsError(
    QuestionGenerationError
):
    """
    Настройки генерации противоречат друг другу.
    """