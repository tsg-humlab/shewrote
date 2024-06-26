import sys
import os
import json
import requests
import re
import pickle
import pathlib
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from shewrote.models import Genre, Religion, Profession, Language, CollectiveType, Collective, Work, Place, Person, \
    PeriodOfResidence, PersonCollective, PersonReligion, PersonWork, Role, AlternativeName, Education, \
    PersonEducation


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

    def __init__(self):
        self.places = {}

    def add_arguments(self, parser):
        parser.add_argument("base_url", nargs=1)
        parser.add_argument("collections", nargs='*')

        parser.add_argument(
            "--limited",
            action="store_true",
            help="Import a limited number",
        )

        parser.add_argument(
            "--pickle",
            action="store",
            help="A path for the pickled data to load data from file or dump the downloaded data to a file.",
        )

    def handle(self, *args, **options):
        self.limited = options.get('limited', False)
        self.pickle = options.get('pickle', None)

        base_url = options['base_url'][0]
        self.objects_url = base_url + objects_path

        collections = options['collections']
        if not collections:
            collections = ww_collections

        for collection in collections:
            collection_data = self.get_collection_data(collection)
            self.create_shewrote_objects(collection, collection_data)

    def get_collection_data(self, collection):
        """
        Get the WomenWriters data either from the API or from a pickled file
        :param collection:
        :return: collection data
        """
        if not self.pickle:
            return self.import_collection(collection)

        pickle_file = pathlib.Path(self.pickle) / (collection+".pkl")

        # Load data from file
        if os.path.isfile(pickle_file):
            with open(pickle_file, "rb") as f:
                return pickle.load(f)

        # Import data and dump to file
        collection_data = self.import_collection(collection)
        with open(pickle_file, "wb") as f:
            pickle.dump(collection_data, f)
        return collection_data

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

        return all_objects

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
            if Language.objects.filter(id=uuid).exists():
                print(f"WARNING - A language object with id {uuid} already exists in the database.")
                continue

            name = language["name"]
            Language.objects.create(id=uuid, name=name)

    def create_for_wwkeywords(self, keywords):
        print(f"Processing {len(keywords)} wwkeywords...")

        for keyword in keywords:
            uuid = keyword["_id"]
            value = keyword["value"]
            relation_names = set(keyword["@relations"].keys())

            try:
                if "isGenreOf" in relation_names:
                    obj, created = Genre.objects.get_or_create(id=uuid, name=value)
                    # print(obj.genre, created)
                if "isReligionOf" in relation_names:
                    obj, created = Religion.objects.get_or_create(id=uuid, name=value)
                    # print(obj.religion, created)
                if "isProfessionOf" in relation_names:
                    obj, created = Profession.objects.get_or_create(id=uuid, name=value)
                    # print(obj.profession, created)
                if "isEducationOf" in relation_names:
                    obj, created = Education.objects.get_or_create(id=uuid, name=value)
                    # print(obj.profession, created)
            except IntegrityError as ie:
                print(f"Keyword with id {uuid} was not imported due to this error: {ie}")

    def create_for_wwcollectives(self, collectives):
        print(f"Processing {len(collectives)} collectives...")

        new_collectives = {}

        for collective in collectives:
            uuid = collective["_id"]
            if uuid in new_collectives.keys():
                print(f"WARNING - A Collective object with id {uuid} already exists in the database.")
                continue

            name = collective["name"]
            type = collective["type"]

            type_of_collective, created = CollectiveType.objects.get_or_create(type_of_collective=type)

            new_collectives[uuid] = Collective(id=uuid, name=name, type=type_of_collective,
                                               original_data=collective)

        Collective.objects.bulk_create(new_collectives.values())

    def create_for_wwdocuments(self, documents):
        print(f"Processing {len(documents)} documents...")

        self.works = {}

        for document in documents:
            if document["documentType"] != "WORK":
                continue

            uuid = document["_id"]
            if uuid in self.works.keys():
                print(f"WARNING - A work object with id {uuid} already exists in the database.")
                continue

            title = document["title"]

            # genre = None
            # genre_relations = document["@relations"].get("hasGenre", None)
            # if genre_relations:
            #     genre = Genre.objects.get(id=uuid, name=genre_relations[0]["displayName"])

            self.works[uuid] = Work(id=uuid, title=title, original_data=document)

            # Add languages
            # language_relations = document["@relations"].get("hasWorkLanguage", None)
            # if language_relations:
            #     for language_relation in language_relations:
            #         language = Language.objects.get(id=language_relation["id"])
            #         obj.language.add(language)

        Work.objects.bulk_create(self.works.values())

    def create_for_wwlocations(self, locations):
        print(f"Processing {len(locations)} locations...")

        places = {}
        names = set()

        for location in locations:
            uuid = location["_id"]
            name = location["name"]

            if name in names:
                print(f"WARNING - A place object with name {name} already exists in the database. Using id {uuid} as name")
                name = uuid

            if uuid in places.keys():
                print(f"WARNING - A place object with id {uuid} already exists in the database.")
                continue

            places[uuid] = Place(id=uuid, name=name, cerl_id=-1,
                                 latitude=-1.0, longitude=-1.0, # TODO remove when possible
                                 original_data=location)
            names.add(name)

        Place.objects.bulk_create(places.values())

        for obj in places.values():
            # Add collectives
            collective_locations = location["@relations"].get("isLocationOf", [])
            for collective_location in collective_locations:
                uuid = collective_location["id"]
                collective = Collective.objects.get(id=uuid)
                collective.place.add(obj)

        self.places = places

    def get_place(self, uuid):
        if uuid in self.places.keys():
            return self.places[uuid]

        try:
            place = Place.objects.get(id=uuid)
            self.places[place.id] = place
        except IntegrityError:
            place = None
        return place

    def extract_names(self, person, name_type):
        if person['names']:
            components = person['names'][0]['components']
            filtered_components = filter(lambda component: component['type'] == name_type, components)
            return " ".join([component['value'] for component in filtered_components])
        return ''

    def create_for_wwpersons(self, persons):
        print(f"Processing {len(persons)} persons...")

        gender_choices = {
            'FEMALE': "F",
            'MALE': "M",
            'UNKNOWN': "O",
            'NOT_APPLICABLE': "N"
        }

        self.new_persons = {}

        for person in persons:
            uuid = person["_id"]
            if uuid in self.new_persons.keys():
                print(f"WARNING - A person object with id {uuid} already exists in the database.")
                continue

            short_name = person.get('@displayName', '')
            if not short_name:
                short_name = person.get('tempName', '')
            sex = gender_choices[person['gender']]
            forenames = self.extract_names(person, "FORENAME")
            surnames = self.extract_names(person, "SURNAME")
            
            birth_place = person["@relations"].get("hasBirthPlace", None)
            place_of_birth = self.get_place(birth_place[0]["id"]) if birth_place else None
            death_place = person["@relations"].get("hasDeathPlace", None)
            place_of_death = self.get_place(death_place[0]["id"]) if death_place else None

            self.new_persons[uuid] = Person(id=uuid, short_name=short_name, first_name=forenames, maiden_name=surnames,
                                            date_of_birth=person.get('birthDate', ''),
                                            date_of_death=person.get('deathDate', ''),
                                            place_of_birth=place_of_birth, place_of_death=place_of_death,
                                            alternative_birth_date='', alternative_death_date='', sex=sex,
                                            alternative_name_gender='', professional_ecclesiastic_title='',
                                            aristocratic_title='', bibliography='',
                                            original_data=person)

        self.bulk_create_persons_and_relations(persons)

    def bulk_create_persons_and_relations(self, persons):
        # Bulk create Persons and relations
        for person in persons:
            self.add_parents(person)

        Person.objects.bulk_create(self.new_persons.values())
        PeriodOfResidence.objects.bulk_create(self.get_periodofresidences(persons))
        PersonCollective.objects.bulk_create(self.get_personcollectives(persons))
        PersonReligion.objects.bulk_create(self.get_personreligions(persons))
        PersonWork.objects.bulk_create(self.get_personwork(persons))
        PersonEducation.objects.bulk_create(self.get_personeducations(persons))
        AlternativeName.objects.bulk_create(self.get_alternativenames(persons))

    def get_periodofresidences(self, persons):
        new_periodofresidences = []
        for person in persons:
            residence_locations = person["@relations"].get("hasResidenceLocation", [])
            new_periodofresidences.extend([PeriodOfResidence(person_id=person["_id"], place_id=residence_location["id"], notes='')
                    for residence_location in residence_locations])
        return new_periodofresidences

    def get_personcollectives(self, persons):
        new_personcollectives = []
        for person in persons:
            collectives = person["@relations"].get("isMemberOf", [])
            new_personcollectives.extend([PersonCollective(person_id=person["_id"], collective_id=collective["id"])
                                          for collective in collectives])
        return new_personcollectives

    def get_personreligions(self, persons):
        new_personreligions = []
        for person in persons:
            religions = person["@relations"].get("hasReligion", [])
            new_personreligions.extend([PersonReligion(person_id=person["_id"], religion_id=religion["id"], notes='')
                                        for religion in religions])
        return new_personreligions

    def get_personwork(self, persons):
        new_personworks = []
        for person in persons:
            roles = [
                ("isCreatorOf", "is creator of"),
                ("isPersonReferencedIn", "is referenced in"),
                ("isPersonQuotedIn", "is quoted in"),
                ("hasObituary", "has obituary"),
                ("isPersonMentionedIn", "is mentioned in"),
                ("isPersonListedOn", "is listed on"),
                ("isPersonAwarded", "is awarded"),
                ("isDedicatedPersonOf", "is dedidicated person of"),
                ("isPersonCommentedOnIn", "is commented on in"),
                ("hasBiography", "has biography"),
            ]

            for old_role, new_role in roles:
                role, created = Role.objects.get_or_create(name=new_role)
                works = person["@relations"].get(old_role, [])
                new_personworks.extend([PersonWork(person_id=person["_id"], work_id=work["id"], role=role)
                                        for work in works if work["id"] in self.works.keys()])
        return new_personworks

    def add_parents(self, person):
        new_person = self.new_persons[person["_id"]]
        parents = person["@relations"].get("isChildOf", [])
        for parent in parents:
            new_parent = self.new_persons[parent["id"]]
            if new_parent.sex == Person.GenderChoices.FEMALE:
                new_person.mother_id = new_parent.id
            elif new_parent.sex == Person.GenderChoices.MALE:
                new_person.father_id = new_parent.id

    def get_personeducations(self, persons):
        personeducations = []
        for person in persons:
            personeducations.extend([PersonEducation(person_id=person["_id"], education_id=education["id"])
                                     for education in person["@relations"].get("hasEducation", [])])
        return personeducations

    def get_alternativenames(self, persons):
        new_alternativenames = []
        for person in persons:
            pseudonyms = person["@relations"].get("hasPseudonym", [])
            new_alternativenames.extend([AlternativeName(person_id=person["_id"], alternative_name=pseudonym["displayName"])
                    for pseudonym in pseudonyms])
        return new_alternativenames
