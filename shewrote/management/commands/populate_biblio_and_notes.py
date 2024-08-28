import re
from django.core.management.base import BaseCommand

from shewrote.models import Person


class Command(BaseCommand):
    help = "Populate the bibliography and notes fields using the original_data"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.number_of_persons_done = 0
        persons = Person.objects.filter(original_data__isnull=False).exclude(original_data='')

        for person in persons:
            bibliography = person.original_data.get('bibliography', '')
            person.bibliography += f'\n\n{bibliography}' if bibliography and person.bibliography else bibliography

            notes = person.original_data.get('notes', '')
            person.notes += f'\n\n{notes}' if notes and person.notes else notes

            self.number_of_persons_done +=1
            print(f'Number of persons done: {self.number_of_persons_done}', end='\r')

        Person.objects.bulk_update(persons, ['bibliography', 'notes'], batch_size=1000)