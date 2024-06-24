import re
from django.core.management.base import BaseCommand

from shewrote.models import Work


class Command(BaseCommand):
    help = "Populate the date_of_publication fields using the original_data"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.number_of_works_done = 0
        for work in Work.objects.all():
            date_str = work.original_data.get('date', '')
            # XX-XX-XXXX
            m = re.search(r'\d\d\-\d\d\-(\d\d\d\d)', date_str)
            if m and m[1]:
                self.save_work(work, date_str, m[1])
                continue

            m = re.search(r'\d\d\d\d', date_str)
            if m and m[0]:
                self.save_work(work, date_str, m[0])
                continue

            self.save_work(work, date_str, None)

    def save_work(self, work, date_str, year):
        work.date_of_publication_start = year
        work.date_of_publication_end = year
        work.date_of_publication_text = date_str
        work.save()

        self.number_of_works_done += 1
        print(f'Number of works done: {self.number_of_works_done}', end='\r')