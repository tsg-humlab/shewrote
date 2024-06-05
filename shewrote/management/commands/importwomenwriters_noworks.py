import os
import pickle
import pathlib
from django.core.management.base import BaseCommand
from shewrote.models import Work, Person, PersonWork, Role

person_work_roles = [
    ("commentsOnPerson", "is commented on in"),
    ("isAwardForPerson", "is awarded"),
    ("isBiographyOf", "has biography"),
    ("isCreatedBy", "is creator of"),
    ("isDedicatedTo", "is dedidicated person of"),
    ("isObituaryOf", "has obituary"),
    ("listsPerson", "is listed on"),
    ("mentionsPerson", "is mentioned in"),
    ("quotesPerson", "is quoted in"),
    ("referencesPerson", "is referenced in"),
]

objects_path = '/domain/{}?withRelations=true&rows={}&start={}'


class Command(BaseCommand):
    help = "Import data from the WomenWriters database"

    def __init__(self):
        self.places = {}

    def add_arguments(self, parser):
        parser.add_argument("base_url", nargs=1)

        parser.add_argument(
            "--pickle",
            action="store",
            help="A path for the pickled data to load data from file or dump the downloaded data to a file.",
        )

    def handle(self, *args, **options):
        self.pickle = options.get('pickle', None)

        base_url = options['base_url'][0]
        self.objects_url = base_url + objects_path

        collection_data = self.get_collection_data("wwdocuments")
        self.create_for_wwdocuments(collection_data)

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

    def create_for_wwdocuments(self, documents):
        print(f"Processing {len(documents)} documents...")

        works = {}
        work_ids_in_db = set([str(id) for id in Work.objects.all().values_list('id', flat=True)])
        new_personworks = []
        person_ids_in_db = set([str(id) for id in Person.objects.all().values_list('id', flat=True)])
        new_roles = []
        roles_in_db = dict([(role.name, role.id) for role in Role.objects.all()])

        for document in documents:
            if document["documentType"] == "WORK":
                continue

            uuid = document["_id"]
            if uuid in works.keys() or uuid in work_ids_in_db:
                print(f"WARNING - A work object with id {uuid} already exists in the database.")
                continue

            title = document.get("title", 'NO TITLE IN WOMENWRITERS OBJECT')
            work = Work(id=uuid, title=title, original_data=document)
            works[uuid] = work

            for old_role, new_role in person_work_roles:
                if not (role_id := roles_in_db.get(new_role, None)):
                    role = Role(name=new_role)
                    new_roles.append(role)
                    role_id = role.id
                persons = document["@relations"].get(old_role, [])
                new_personworks.extend([
                    PersonWork(person_id=person["id"], work_id=uuid, role_id=role_id)
                    for person in persons if person["id"] in person_ids_in_db
                ])

            print(f'Works: {len(works)} - Roles: {len(new_roles)} - PersonWorks: {len(new_personworks)}', end='\r')

        Work.objects.bulk_create(works.values())
        Role.objects.bulk_create(new_roles)
        PersonWork.objects.bulk_create(new_personworks)