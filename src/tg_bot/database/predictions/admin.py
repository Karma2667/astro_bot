from sqladmin import ModelView

from database.predictions.models import Prediction, PredictionType


class PredictionAdmin(ModelView, model=Prediction):
    column_list = [
        "id",
        "profile_id",
        "prediction_type",
        "recognition_str",
        "expiration_time"
    ]

    column_searchable_list = [
        "id",
        "profile_id",
        "prediction_type",
        "recognition_str",
        "expiration_time",
    ]

    column_filters = [
        "id",
        "profile_id",
        "prediction_type",
        "recognition_str",
        "expiration_time",
    ]

    form_excluded_columns = [
        "id",
    ]

    column_sortable_list = [
        "id",
        "profile_id",
        "prediction_type",
        "recognition_str",
        "expiration_time",
    ]

    column_labels = {
        "id": "ID",
        "profile_id": "ID профиля",
        "prediction_type": "Тип предсказания",
        "recognition_str": "Строка распознавания",
        "expiration_time": "Время истечения",
    }

    form_widget_args = {
        "prediction_type": {
            "choices": [
                (PredictionType.HOROSCOPE, PredictionType.HOROSCOPE.value),
            ]
        }
    }
