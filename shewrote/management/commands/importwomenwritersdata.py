import sys
import json
import requests
from django.core.management.base import BaseCommand
from shewrote.models import Genre, Religion, Profession, Language, TypeOfCollective, Collective, Work


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

    def handle(self, *args, **options):
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

            obj, created = Collective.objects.get_or_create(name=name, type=type_of_collective,
                                                            start_year=0, end_year=0,
                                                            original_data=json.dumps(collective))  # TODO add uuid

    def create_for_wwdocuments(self, documents):
        print(f"Processing {len(documents)} documents...")

        for document in documents:
            if document["documentType"] == "WORK":
                uuid = document["_id"]
                title = document["title"]

                genre = None
                genre_relations = document["@relations"].get("hasGenre", None)
                if genre_relations:
                    genre = Genre.objects.get(genre=genre_relations[0]["displayName"]) # TODO this should be the '_id' uuid

                obj, created = Work.objects.get_or_create(title=title, genre=genre,
                                                          original_data=json.dumps(document)) # TODO add uuid

                language_relations = document["@relations"].get("hasWorkLanguage", None)
                if language_relations:
                    for language_relation in language_relations:
                        language = Language.objects.get(language=language_relation["displayName"]) # TODO this should be the '_id' uuid
                        obj.language.add(language)

                # TODO isPublishedBy and isStoredAt relations to wwcollectives

