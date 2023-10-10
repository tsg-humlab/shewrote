import sys
import json
import requests
import re
from django.core.management.base import BaseCommand
from shewrote.models import Genre, Religion, Profession, Language, TypeOfCollective, Collective, Work, Place, Person, \
    PeriodOfResidence


ww_collections = [
    "wwlanguages",
    "wwkeywords",
    "wwcollectives",
    "wwdocuments",
    "wwlocations",
    "wwpersons",
]

objects_path = '/domain/{}?withRelations=true&rows={}&start={}'


class Command(BaseCommand):
    help = "Import data from the WomenWriters database"

    def add_arguments(self, parser):
        parser.add_argument("base_url", nargs=1)
        parser.add_argument("collections", nargs='*')

        parser.add_argument(
            "--limited",
            action="store_true",
            help="Import a limited number",
        )

    def handle(self, *args, **options):
        self.limited = options.get('limited', False)

        base_url = options['base_url'][0]
        self.objects_url = base_url + objects_path

        collections = options['collections']
        if not collections:
            collections = ww_collections

        for collection in collections:
            self.import_collection(collection)

    def import_collection(self, collection):
        print(f"Importing {collection}...")

        rows, start = 1000, 0
        objects = self.get_objects(collection, rows, start)
        all_objects = objects
        if not self.limited:
            while objects is not None and len(objects) == rows:
                start += rows
                objects = self.get_objects(collection, rows, start)
                all_objects.extend(objects)

        self.create_shewrote_objects(collection, all_objects)

    def get_objects(self, collection, rows=1000, start=0):
        print(f"Request for {rows} rows...")
        url = self.objects_url.format(collection, rows, start)
        response = requests.get(url, timeout=60)
        if response.status_code == requests.codes.ok:
            return response.json()

        print(f"Could not get objects from {url}: {response.status_code}.", file=sys.stderr)
        return None

    def create_shewrote_objects(self, collection, objects):
        create_for = f'create_for_{collection}'
        if hasattr(self, create_for) and callable(func := getattr(self, create_for)):
            func(objects)

    ##### Methods to process each WomenWriters entity #####

    def create_for_wwlanguages(self, languages):
        print(f"Processing {len(languages)} wwlanguage...")

        for language in languages:
            uuid = language["_id"]
            name = language["name"]

            obj, created = Language.objects.get_or_create(language=name)  # TODO add uuid
            # print(obj.language, created)

    def create_for_wwkeywords(self, keywords):
        print(f"Processing {len(keywords)} wwkeywords...")

        for keyword in keywords:
            uuid = keyword["_id"]
            value = keyword["value"]
            relation_names = set(keyword["@relations"].keys())

            if "isGenreOf" in relation_names:
                obj, created = Genre.objects.get_or_create(genre=value)  # TODO add uuid
                # print(obj.genre, created)
            if "isReligionOf" in relation_names:
                obj, created = Religion.objects.get_or_create(religion=value)  # TODO add uuidO
                # print(obj.religion, created)
            if "isProfessionOf" in relation_names:
                obj, created = Profession.objects.get_or_create(profession=value)  # TODO add uuid
                # print(obj.profession, created)

    def create_for_wwcollectives(self, collectives):
        print(f"Processing {len(collectives)} collectives...")

        for collective in collectives:
            uuid = collective["_id"]
            name = collective["name"]
            type = collective["type"]

            type_of_collective, created = TypeOfCollective.objects.get_or_create(type_of_collective=type)

            obj, created = Collective.objects.get_or_create(id=uuid, name=name, type=type_of_collective,
                                                            start_year=0, end_year=0,
                                                            original_data=json.dumps(collective))

    def create_for_wwdocuments(self, documents):
        print(f"Processing {len(documents)} documents...")

        for document in documents:
            if document["documentType"] == "WORK":
                uuid = document["_id"]
                title = document["title"]

                genre = None
                genre_relations = document["@relations"].get("hasGenre", None)
                if genre_relations:
                    genre = Genre.objects.get(genre=genre_relations[0]["displayName"])  # TODO add uuid

                obj, created = Work.objects.get_or_create(id=uuid, title=title, genre=genre,
                                                          original_data=json.dumps(document))

                # Add languages
                language_relations = document["@relations"].get("hasWorkLanguage", None)
                if language_relations:
                    for language_relation in language_relations:
                        language = Language.objects.get(language=language_relation["displayName"])  # TODO add uuid
                        obj.language.add(language)

    def create_for_wwlocations(self, locations):
        print(f"Processing {len(locations)} locations...")

        for location in locations:
            uuid = location["_id"]
            name = location["name"]

            obj, created = Place.objects.get_or_create(id=uuid, name_of_city=name,
                                                       cerl_id=-1, latitude=-1.0, longitude=-1.0, # TODO remove when possible
                                                       original_data=json.dumps(location))

            # Add collectives
            collective_locations = location["@relations"].get("isLocationOf", [])
            for collective_location in collective_locations:
                uuid = collective_location["id"]
                collective = Collective.objects.get(id=uuid)
                collective.place.add(obj)


    def extract_names(self, person, name_type):
        if person['names']:
            components = person['names'][0]['components']
            filtered_components = filter(lambda component: component['type'] == name_type, components)
            return " ".join([component['value'] for component in filtered_components])
        return ''


    def transform_to_date(self, date):
        # TODO remove default '-01-01' when possible
        if not date:
            return '0001-01-01'
        if re.search('^\d{4}-\d\d-\d\d$', date): # YYYY-MM-DD
            return date
        if re.search('^\d{4}$', date): # YYYY
            return date + "-01-01"
        if re.search('^\d\d-\d\d-\d{4}$', date): # DD-MM-YYYY
            day, month, year = date.split('-')
            return f'{year}-{month}-{day}'
        return '0001-01-01'

    def create_for_wwpersons(self, persons):
        print(f"Processing {len(persons)} persons...")

        gender_choices = {
            'FEMALE': "F",
            'MALE': "M",
            'UNKNOWN': "O",
            'NOT_APPLICABLE': "N"
        }

        for person in persons:
            uuid = person["_id"]
            short_name = person.get('tempName', '')
            sex = gender_choices[person['gender']]
            forenames = self.extract_names(person, "FORENAME")
            surnames = self.extract_names(person, "SURNAME")
            # print(first_names, " | ", maiden_name)

            date_of_birth = self.transform_to_date(person.get('birthDate'))
            date_of_death = self.transform_to_date(person.get('deathDate'))

            # See whether this person already exists
            existing_person = Person.objects.filter(id=uuid)
            if existing_person:
                print(f"WARNING - A person object with id {uuid} already exists in the database.")
                continue

            obj, created = Person.objects.get_or_create(id=uuid, short_name=short_name, first_name=forenames,
                                                        maiden_name=surnames, date_of_birth=date_of_birth,
                                                        date_of_death=date_of_death,
                                                        alternative_birth_date='0001-01-01',
                                                        alternative_death_date='0001-01-01',
                                                        flourishing_start=-1, flourishing_end=-1, sex=sex,
                                                        alternative_name_gender='', professional_ecclesiastic_title='',
                                                        aristocratic_title='', education='', bibliography='',
                                                        original_data='')
            
            self.add_person_relations(person, obj)

    def add_person_relations(self, person, obj):
            birth_place = person["@relations"].get("hasBirthPlace", None)
            if birth_place:
                obj.place_of_birth = Place.objects.get(id=birth_place[0]["id"])
                obj.save()

            death_place = person["@relations"].get("hasDeathPlace", None)
            if death_place:
                obj.place_of_death = Place.objects.get(id=death_place[0]["id"])
                obj.save()

            residence_locations = person["@relations"].get("hasResidenceLocation", None)
            if residence_locations:
                for residence_location in residence_locations:
                    place = Place.objects.get(id=residence_location["id"])
                    PeriodOfResidence.objects.create(person=obj, place=place, start_year=-1, end_year=-1, notes='')