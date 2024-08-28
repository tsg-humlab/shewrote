import os
from datetime import datetime
from django.core.management.base import BaseCommand

from shewrote.models import Person, AlternativeName


class Command(BaseCommand):
    help = "Populate the AlternativeName objects using the original_data"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.number_of_persons_done = 0
        persons = Person.objects.filter(original_data__isnull=False).exclude(original_data='')

        alternative_names = []
        notes = f'Created by {os.path.basename(__file__)} on {datetime.now()}.'

        for person in persons:
            names = person.original_data.get('names', [])[1:]

            for name in names:
                alternative_name = " ".join(component['value'] for component in name['components'])

                alternative_names.append(AlternativeName(
                    person=person,
                    alternative_name = alternative_name,
                    notes=notes
                ))

        AlternativeName.objects.bulk_create(alternative_names, batch_size=1000)
