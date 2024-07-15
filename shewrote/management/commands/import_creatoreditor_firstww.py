import sqlite3
from contextlib import closing
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import make_aware
from easyaudit.models import CRUDEvent
from shewrote.models import Work, Person


class Command(BaseCommand):
    help = "Import creator/editor data from the first WomenWriters database"

    def add_arguments(self, parser):
        parser.add_argument("sqlite_filename", nargs=1, type=str, help="file path of the SQLite database")

    def handle(self, *args, **options):
        sqlite_filename = options.get('sqlite_filename', '')[0]
        if not sqlite_filename:
            return

        with closing(sqlite3.connect(sqlite_filename)) as connection:
            connection.row_factory = sqlite3.Row
            with closing(connection.cursor()) as cursor:
                sw_users = self.create_users(cursor)

                sw_works = {
                    work[1]: str(work[0]) for work in
                    Work.objects.filter(original_data__tempOldId__isnull=False)
                        .values_list('id', 'original_data__tempOldId')
                }
                self.import_changes(cursor, sw_users, sw_works, ContentType.objects.get_for_model(Work),
                                    ['receptions', 'works'])

                sw_persons = {
                    person[1]: str(person[0]) for person in
                    Person.objects.filter(original_data__tempOldId__isnull=False)
                        .values_list('id', 'original_data__tempOldId')
                }
                self.import_changes(cursor, sw_users, sw_persons, ContentType.objects.get_for_model(Person),
                                    ['authors'])

    @staticmethod
    def import_changes(cursor, sw_users, sw_objects, content_type, ww1_object_names):
        """
        Import the change from the first WomenWriters database
        :param cursor: SQLite cursor
        :param sw_users: newly created users
        :param sw_objects: all tempOldId and id data from Work and Person objects
        :param content_type: content type for CRUDEvent
        :param ww1_object_names: object names for SELECTing change events from first WomenWriters
        :return: None
        """
        object_names = ', '.join([f"'{name}'" for name in ww1_object_names])
        ww1_changes = cursor.execute(
            "SELECT object_name, object_id, changetype, user_id, created_at FROM changes "
            f"WHERE object_name in ({object_names})"
        )

        event_types = {
            'update': CRUDEvent.UPDATE,
            'create': CRUDEvent.CREATE,
            'delete': CRUDEvent.DELETE,
        }

        crud_events = []
        for ww1_change in ww1_changes:
            tempOldId = f'{ww1_change["object_name"]}/{ww1_change["object_id"]}'
            if object_id := sw_objects.get(tempOldId, ''):
                crud_events.append(CRUDEvent(
                    event_type=event_types[ww1_change['changetype']],
                    object_id=object_id,
                    content_type=content_type,
                    user=sw_users[ww1_change['user_id']],
                    datetime=make_aware(datetime.fromtimestamp(ww1_change['created_at'] / 1000))
                ))
            else:
                print(f'Not found: {tempOldId}')
        CRUDEvent.objects.bulk_create(crud_events, batch_size=10_000)

    @staticmethod
    def create_users(cursor):
        """
        Create inactive users that correspond with the users from the first WomenWriters
        :param cursor: SQLite cursor
        :return: dict of new users identified by the id from the first WomenWriters
        """
        ww1_group, created = Group.objects.get_or_create(name="ww1_group")
        ww1_users = cursor.execute("SELECT id, name, username, email, created_at FROM users").fetchall()
        sw_users = {}
        for ww1_user in ww1_users:
            names = ww1_user['name'].split(maxsplit=1)
            first_name = last_name = ''
            if len(names) == 1:
                last_name = names[0]
            elif len(names) == 2:
                first_name, last_name = names

            email = ww1_user['email'] if ww1_user['email'] else ''

            sw_user, created = User.objects.get_or_create(
                username=ww1_user['username'],
                first_name=first_name,
                last_name=last_name,
                email=email,
                is_staff=False,
                is_active=False,
                is_superuser=False,
                date_joined=make_aware(datetime.fromtimestamp(ww1_user['created_at'] / 1000))
            )
            sw_user.groups.add(ww1_group)

            sw_users[ww1_user['id']] = sw_user

        return sw_users

