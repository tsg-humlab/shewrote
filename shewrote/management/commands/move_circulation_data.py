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
        pass

    def handle(self, *args, **options):
        reception_filter = reduce(operator.or_, (Q(title__icontains=string) for string in self.strings_to_match))
        receptions_to_move = (Reception.objects.filter(reception_filter)
                              .prefetch_related('personreception_set', 'workreception_set', 'editionreception_set'))
        fields_to_move = [field.name for field in AbstractReception._meta.fields]
        new_circulations = []
        new_personcirculations = []
        new_workcirculations = []
        new_editionscirculations = []
        for reception in receptions_to_move:
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

        print('Creating Circulations and related objects.')
        Circulation.objects.bulk_create(new_circulations)
        PersonCirculation.objects.bulk_create(new_personcirculations)
        WorkCirculation.objects.bulk_create(new_workcirculations)
        EditionCirculation.objects.bulk_create(new_editionscirculations)

        print('Deleting the following:')
        print(PersonReception.objects.filter(reception__in=receptions_to_move).delete())
        print(WorkReception.objects.filter(reception__in=receptions_to_move).delete())
        print(EditionReception.objects.filter(reception__in=receptions_to_move).delete())
        print(receptions_to_move.delete())
