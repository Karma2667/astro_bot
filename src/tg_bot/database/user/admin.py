from sqladmin import ModelView
from database.user.models import Subscription, User

class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.user_id,
        User.name,
        User.locale,
        User.subscription,
        User.subscription_expiration_date,
        User.is_mail_subscribed,
        User.is_admin,  # Добавлено поле is_admin
    ]

    form_columns = [
        User.id,  # Только для отображения, не редактируется
        User.name,
        User.locale,
        User.subscription,
        User.subscription_expiration_date,
        User.is_mail_subscribed,
        User.is_admin,  # Редактируемый флаг администратора
    ]

    column_filters = [
        User.id,
        User.user_id,
        User.name,
        User.locale,
        User.subscription,
        User.subscription_expiration_date,
        User.is_mail_subscribed,
        User.is_admin,  # Фильтр по статусу админа
    ]

    column_sortable_list = [
        User.id,
        User.user_id,
        User.name,
        User.subscription_expiration_date,
    ]  # Добавлена сортировка

    column_labels = {
        User.id: "ID",
        User.user_id: "User ID",
        User.name: "Название",
        User.locale: "Язык",
        User.subscription: "Подписка",
        User.subscription_expiration_date: "Срок подписки",
        User.is_mail_subscribed: "Подписка на рассылку",
        User.is_admin: "Администратор",  # Добавлено название для is_admin
    }

    form_widget_args = {
        User.subscription: {"choices": (Subscription.FOREVER, Subscription.MONTHLY, Subscription.FREELY)},
        User.is_admin: {"type": "boolean"},  # Указываем, что это булево поле
        User.user_id: {"readonly": True},  # Делаем user_id неизменяемым
    }

    def is_accessible(self, request):
        # Проверка прав доступа (например, только для админов)
        from config import settings
        user_id = request.user.id if hasattr(request, "user") else None  # Адаптируй под твой механизм авторизации
        return user_id in settings.admin.ADMIN_IDS if user_id else False