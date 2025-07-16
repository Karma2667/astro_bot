import gettext

from config import settings

def get_translation(msgid: str, locale: str = settings.locales.DEFAULT_LOCALE):
    localedir = settings.locales.LOCALE_PATH
    domain = settings.locales.I18N_DOMAIN
    
    lang = gettext.translation(domain, localedir, languages=[locale], fallback=True)
    return lang.gettext(msgid)


# Command for compiling files: pybabel compile -f -d <translations-directory>
