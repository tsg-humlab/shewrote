import json
import re
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from shewrote.models import ReceptionType, Reception, ReceptionReceptionType, Work, Place, Person, \
    PersonReception, DocumentType


def get_obj_or_none(klass, **kwargs):
    try:
        obj = klass.objects.get(**kwargs)
    except (ObjectDoesNotExist, MultipleObjectsReturned) as e:
        print(f'kwargs: {kwargs}')
        print(e)
        return None
    else:
        return obj


class Command(BaseCommand):
    help = "Import data from the WomenWriters database"

    def add_arguments(self, parser):
        parser.add_argument("filename", nargs=1)

    def handle(self, *args, **options):
        self.filename = options.get('filename', False)[0]
        with open(self.filename) as receptions_file:
            data = json.load(receptions_file)
            receptions = {}
            person_receptions = []
            reception_type_names = dict(ReceptionType.objects.values_list('type_of_reception', 'id'))
            reception_types = []
            reception_reception_types = {}


            for doc in data['response']['docs']:

                received_person = get_obj_or_none(Person, id=doc["person_id_s"])
                if not received_person:
                    print(f"Source Person with id {doc['person_id_s']} not found")
                    continue

                part_of_work = get_obj_or_none(Work, id=doc["reception_id_s"])
                if not part_of_work:
                    print(f"Reception Work with id {doc['reception_id_s']} not found")
                    continue

                publication_location = doc.get("publishLocation_ss", [])
                if publication_location:
                    publication_location = publication_location[0][:255]
                try:
                    place_of_reception = Place.objects.get(name=publication_location)
                except ObjectDoesNotExist as e:
                    place_of_reception = None

                document_type, created = DocumentType.objects.get_or_create(type_of_document=doc.get("documentType_s", ""))

                if title_list := doc["title_t"]:
                    title = title_list[0]
                else:
                    title = doc["displayName_s"]
                if not (reception := receptions.get(doc["reception_id_s"], None)):
                    reception = Reception(
                        id = doc["id"],
                        # source = reception_source,
                        title = title,
                        part_of_work = part_of_work,
                        place_of_reception = place_of_reception,
                        date_of_reception = doc.get("date_i", 0),
                        document_type = document_type,
                        notes = doc.get("notes_t", ''),
                        original_data = json.dumps(doc)
                    )
                    receptions[doc["reception_id_s"]] = reception

                type_of_reception = re.sub(r"(?<=[a-zA-Z])(?=[A-Z])", " ", doc['relationType_s']).lower()
                reception_type_id = reception_type_names.get(type_of_reception, None)
                if not reception_type_id:
                    reception_type = ReceptionType(type_of_reception=type_of_reception)
                    reception_types.append(reception_type)
                    reception_type_id = reception_type.id
                    reception_type_names[type_of_reception] = reception_type_id

                reception_reception_type_key = (reception.id, reception_type_id)
                if reception_reception_type_key not in reception_reception_types.keys():
                    reception_reception_types[reception_reception_type_key] = \
                        ReceptionReceptionType(reception=reception, type_id=reception_type_id)

                person_reception = PersonReception(
                    person = received_person,
                    reception = reception,
                    type_id = reception_type_id
                )
                person_receptions.append(person_reception)

                print(f'Receptions: {len(receptions)}', end='\r')

                if len(receptions) >= 256:
                    ReceptionType.objects.bulk_create(reception_types)
                    Reception.objects.bulk_create(receptions.values())
                    PersonReception.objects.bulk_create(person_receptions)
                    ReceptionReceptionType.objects.bulk_create(reception_reception_types.values())
                    receptions = {}
                    person_receptions = []
                    reception_type_names = dict(ReceptionType.objects.values_list('type_of_reception', 'id'))
                    reception_types = []
                    reception_reception_types = {}
                    print("")

            ReceptionType.objects.bulk_create(reception_types)
            Reception.objects.bulk_create(receptions.values())
            PersonReception.objects.bulk_create(person_receptions)
            ReceptionReceptionType.objects.bulk_create(reception_reception_types.values())
