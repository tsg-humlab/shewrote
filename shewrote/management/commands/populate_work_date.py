import re
from django.core.management.base import BaseCommand

from shewrote.models import Work


class Command(BaseCommand):
    help = "Populate the date_of_publication fields using the original_data"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.number_of_works_done = 0
        for work in Work.objects.filter(original_data__isnull=False):
            date_str = work.original_data.get('date', '')

            # Two years
            if (m := re.search(r'(?<!\d)(\d{4})\D+(\d{4})(?!\d)', date_str)) and m[1] and m[2]:
                self.save_work(work, date_str, m[1], m[2])

            # One year
            elif (m := re.search(r'(?<!\d)(\d{3,4})(?!\d)', date_str)) and m[1]:
                self.save_work(work, date_str, m[1], m[1])

            # No year
            else:
                self.save_work(work, date_str, None, None)

    def save_work(self, work, date_str, year_start, year_end):
        work.date_of_publication_start = year_start
        work.date_of_publication_end = year_end
        work.date_of_publication_text = date_str
        work.save()

        self.number_of_works_done += 1
        print(f'Number of works done: {self.number_of_works_done}', end='\r')