def get_calendar_data_for_month(year: int, month: int, supervisor_tag: str) -> dict:
    """

    :param year:
    :param month:
    :param supervisor_tag:
    :return:
    """
    # Возвращает структуру вида:
    # {
    #   "2025-11-22": {"shifts": [shift_id, ...], "leaves": {"@user": "vacation"}}
    # }
    # Только для сотрудников, подчинённых supervisor_tag