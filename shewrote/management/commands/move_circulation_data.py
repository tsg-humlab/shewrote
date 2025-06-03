import operator
from functools import reduce
from django.core.management.base import BaseCommand
from django.db.models import Q

from shewrote.models import (Reception, Circulation, AbstractReception, PersonReception, PersonCirculation,
                             WorkReception, WorkCirculation, EditionReception, EditionCirculation)


class Command(BaseCommand):
    help = "Move data from Reception to Circulation"
    strings_to_match = ['catalogue', 'presence']

    def add_arguments(self, parser):
        parser.add_argument(
            "--nwords",
            action="store",
            help="The number of words at the beginning of the reception title that should contain the strings to match.",
        )

    def handle_arguments(self, **options):
        n_words = options.get('nwords', None)
        if n_words and not n_words.isdigit():
            print('Argument --n-words should be a number.')
            exit(1)
        self.n_words = int(n_words) if n_words else None

    def match_string_to_first_n_words(self, string):
        words = [word.lower() for word in string.split()[:self.n_words]]
        strings_to_match = [string.lower() for string in self.strings_to_match]
        for string_to_match in strings_to_match:
            for word in words:
                if string_to_match in word:
                    return True
        return False

    def handle(self, *args, **options):
        self.handle_arguments(**options)

        reception_filter = reduce(operator.or_, (Q(title__icontains=string) for string in self.strings_to_match))
        receptions_to_move = (Reception.objects.filter(reception_filter)
                              .prefetch_related('personreception_set', 'workreception_set', 'editionreception_set'))
        fields_to_move = [field.name for field in AbstractReception._meta.fields]
        new_circulations = []
        new_personcirculations = []
        new_workcirculations = []
        new_editionscirculations = []
        reception_ids_to_delete = []
        for reception in receptions_to_move:
            if self.n_words and not self.match_string_to_first_n_words(reception.title):
                print(f'Unmatched reception: {reception.title} ({reception.id})')
                continue
            circulation = Circulation(**{field_name: getattr(reception, field_name) for field_name in fields_to_move})
            new_circulations.append(circulation)
            new_personcirculations.extend([
                PersonCirculation(circulation=circulation, person=person_reception.person, type=person_reception.type)
                for person_reception in reception.personreception_set.all()
            ])
            new_workcirculations.extend([
                WorkCirculation(circulation=circulation, work=work_reception.work, type=work_reception.type)
                for work_reception in reception.workreception_set.all()
            ])
            new_editionscirculations.extend([
                EditionCirculation(circulation=circulation, edition=edition_reception.edition, type=edition_reception.type)
                for edition_reception in reception.editionreception_set.all()
            ])
            reception_ids_to_delete.append(reception.id)

        print('Creating Circulations and related objects.')
        Circulation.objects.bulk_create(new_circulations)
        PersonCirculation.objects.bulk_create(new_personcirculations)
        WorkCirculation.objects.bulk_create(new_workcirculations)
        EditionCirculation.objects.bulk_create(new_editionscirculations)

        print('Deleting the following:')
        print(PersonReception.objects.filter(reception_id__in=reception_ids_to_delete).delete())
        print(WorkReception.objects.filter(reception_id__in=reception_ids_to_delete).delete())
        print(EditionReception.objects.filter(reception_id__in=reception_ids_to_delete).delete())
        print(Reception.objects.filter(id__in=reception_ids_to_delete).delete())
