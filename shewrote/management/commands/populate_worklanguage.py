import re
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

from shewrote.models import Work, Language, WorkLanguage


class Command(BaseCommand):
    help = "Create work language objects using the original_data"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        works = Work.objects.filter(**{'original_data__@relations__hasWorkLanguage__isnull': False})
        work_languages = []
        for work in works:
            ww_languages = work.original_data['@relations']['hasWorkLanguage']
            for ww_language in ww_languages:
                try:
                    sw_language = Language.objects.get(id=ww_language['id'])
                except ObjectDoesNotExist as e:
                    print(e)
                else:
                    work_languages.append(WorkLanguage(work=work, language=sw_language))
        WorkLanguage.objects.bulk_create(work_languages)
