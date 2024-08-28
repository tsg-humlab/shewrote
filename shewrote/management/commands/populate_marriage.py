import os
from datetime import datetime
from django.core.management.base import BaseCommand

from shewrote.models import Person, Marriage


class Command(BaseCommand):
    help = "Populate the Marriage objects using the original_data"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        persons = Person.objects.filter(original_data__isnull=False)\
                    .exclude(original_data='')\
                    .exclude(original_data__tempSpouse__isnull=True)\
                    .exclude(original_data__tempSpouse='') \
                    .values('id', 'original_data__tempSpouse')
        notes = f'Created by {os.path.basename(__file__)} on {datetime.now()}.'

        for person in persons:
            spouse = Person.objects.create(short_name=person['original_data__tempSpouse'])
            Marriage.objects.create(person_id=person['id'], spouse=spouse, notes=notes)
