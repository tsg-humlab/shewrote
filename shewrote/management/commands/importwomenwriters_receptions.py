import json
import re
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from shewrote.models import ReceptionType, Reception, ReceptionSource, ReceptionReceptionType, Work, Place, Person, \
    PersonReception, PersonReceptionSource, WorkReception, DocumentType


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
            # reception_sources = []
            person_reception_source_roles = []
            receptions = {}
            work_receptions = []
            person_reception_roles = []
            reception_type_names = dict(ReceptionType.objects.values_list('type_of_reception', 'id'))
            reception_types = []
            reception_reception_types = []


            for doc in data['response']['docs']:
                # print(
                #     doc["id"],
                #     doc["displayName_s"],
                #     f'({doc["reception_id_s"]})',
                #     doc["relationType_s"],
                #     doc["document_displayName_s"],
                #     f'({doc["document_id_s"]})',
                # )

                received_work = get_obj_or_none(Work, id=doc["document_id_s"])
                if not received_work:
                    print(f"Source Work with id {doc['document_id_s']} not found")
                    continue

                part_of_work = get_obj_or_none(Work, id=doc["reception_id_s"])
                if not part_of_work:
                    print(f"Reception Work with id {doc['reception_id_s']} not found")
                    continue

                # reception_source = ReceptionSource(
                #     id = uuid.uuid4(),
                #     work = received_work,
                #     title_work = doc["document_displayName_s"],
                #     notes = doc.get("document_notes_t", ''),
                # )
                # reception_sources.append(reception_source)

                # document_author_names = []
                # for element in  doc.get("document_authorName_ss", []):
                #     document_author_names.extend(element.split(", "))
                # for document_author_name in document_author_names:
                #     if person := get_obj_or_none(Person, short_name=document_author_name):
                #         person_reception_source_roles.append(
                #             PersonReceptionSource(person=person, reception_source=reception_source)
                #         )

                publication_location = doc.get("publishLocation_ss", [])
                if publication_location:
                    publication_location[0][:255]
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

                # author_names = []
                # for element in doc.get("authorName_ss", []):
                #     author_names.extend(element.split(", "))
                # for author_name in author_names:
                #     person = get_obj_or_none(Person, short_name=author_name)
                #     if person:
                #         # reception.person.add(person)
                #         person_reception_roles.append(PersonReception(person=person, reception=reception))

                type_of_reception = re.sub(r"(?<=[a-zA-Z])(?=[A-Z])", " ", doc['relationType_s']).lower()
                reception_type_id = reception_type_names.get(type_of_reception, None)
                if not reception_type_id:
                    reception_type = ReceptionType(type_of_reception=type_of_reception)
                    reception_types.append(reception_type)
                    reception_type_id = reception_type.id
                    reception_type_names[type_of_reception] = reception_type_id
                reception_reception_types.append(ReceptionReceptionType(reception=reception, type_id=reception_type_id))

                work_reception = WorkReception(
                    work = received_work,
                    reception = reception,
                    type = reception_type
                )
                work_receptions.append(work_reception)

                print(f'Receptions: {len(receptions)}', end='\r')

            ReceptionType.objects.bulk_create(reception_types)
            Reception.objects.bulk_create(receptions.values())
            WorkReception.objects.bulk_create(work_receptions)
            # PersonReception.objects.bulk_create(person_reception_roles)
            ReceptionReceptionType.objects.bulk_create(reception_reception_types)
