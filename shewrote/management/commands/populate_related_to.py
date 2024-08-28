import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

from shewrote.models import Person, Marriage


class Command(BaseCommand):
    help = "Populate the Person.related_to using the original_data"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        persons = Person.objects.filter(original_data__isnull=False)\
                    .exclude(original_data='')\
                    .exclude(**{'original_data__@relations__isRelatedTo__isnull': True})

        for person in persons:
            for relation in person.original_data['@relations']['isRelatedTo']:
                try:
                    related_person = Person.objects.get(id=relation['id'])
                except ObjectDoesNotExist as e:
                    pass
                else:
                    if not person.related_to.contains(related_person):
                        person.related_to.add(related_person)