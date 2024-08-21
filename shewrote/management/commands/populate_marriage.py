import os
from datetime import datetime
from django.core.management.base import BaseCommand

from shewrote.models import Person, Marriage


class Command(BaseCommand):
    help = "Populate the Marriage objects using the original_data"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.number_of_persons_done = 0
        persons = Person.objects.filter(original_data__isnull=False).exclude(original_data='')
        notes = f'Created by {os.path.basename(__file__)} on {datetime.now()}.'

        for person in persons:
            spouse_name = person.original_data.get('tempSpouse', '')
            spouse = Person.objects.create(short_name=spouse_name)
            Marriage.objects.create(person=person, spouse=spouse, notes=notes)
