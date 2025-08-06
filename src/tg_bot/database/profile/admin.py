from sqladmin import ModelView

from database.profile.models import Profile


class ProfileAdmin(ModelView, model=Profile):
    column_list = (
        Profile.id, 
        Profile.user_id, 
        Profile.creation_date, 
        Profile.title, 
        Profile.birth_date, 
        Profile.birth_time, 
        Profile.birth_location_name, 
    )

    column_searchable_list = (
        Profile.id, 
        Profile.user_id, 
        Profile.title, 
        Profile.birth_date, 
        Profile.birth_time, 
        Profile.birth_location_name, 
    )

    column_sortable_list = (
        Profile.id, 
        Profile.user_id, 
        Profile.creation_date, 
        Profile.title, 
        Profile.birth_date, 
        Profile.birth_time, 
        Profile.birth_location_name, 
    )

    column_filters = (
        Profile.id, 
        Profile.user_id, 
        Profile.creation_date, 
        Profile.title, 
        Profile.birth_date, 
        Profile.birth_time, 
        Profile.birth_location_name, 
    )

    form_columns = (
        Profile.user_id, 
        Profile.title, 
        Profile.birth_date, 
        Profile.birth_time, 
        Profile.birth_location_name, 
    )

    column_labels = {
        'id': 'ID',
        'user_id': 'ID пользователя',
        'creation_date': 'Дата создания',
        'title': 'Название',
        'birth_date': 'Дата рождения',
        'birth_time': 'Время рождения',
        'birth_location_name': 'Название места рождения',
    }