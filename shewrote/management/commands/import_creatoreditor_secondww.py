import sqlite3
from contextlib import closing
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import make_aware
from easyaudit.models import CRUDEvent
from shewrote.models import Work, Person, Place, Collective, Edition, Reception


class Command(BaseCommand):
    help = "Import creator/editor data from the second WomenWriters database"
    _new_users = {}
    _crud_events = []
    _crud_events_datetime = []

    def handle(self, *args, **options):
        self.create_events(Person)
        self.create_events(Work)
        self.create_events(Place)
        self.create_events(Collective)
        self.create_events(Edition)

        print(f'Number of new users: {len(self._new_users)}, number of new CRUD events: {len(self._crud_events)}')

        User.objects.bulk_create(self._new_users.values())
        CRUDEvent.objects.bulk_create(self._crud_events)

        # At this point datetime values are equal to datetime.now.
        # The next bit is to get the correct datetime values in the database.
        for index, datetime in enumerate(self._crud_events_datetime):
            self._crud_events[index].datetime = datetime
        CRUDEvent.objects.bulk_update(self._crud_events, ['datetime'], batch_size=1000)

    def create_events(self, cls):
        print("Creating events for", cls.__name__)
        content_type = ContentType.objects.get_for_model(cls)
        for obj in cls.objects.exclude(original_data=None).exclude(original_data=''):
            # Created
            created_info = self.get_original_event_info(obj, '^created')
            if created_info and created_info['timestamp'] and created_info['username']:
                self.create_event(created_info, obj, content_type, CRUDEvent.CREATE)

            # Modified
            modified_info = self.get_original_event_info(obj, '^modified')
            if (modified_info and modified_info['timestamp'] and modified_info['username']
                    and modified_info['timestamp'] != created_info.get('timestamp', None)):
                self.create_event(modified_info, obj, content_type, CRUDEvent.UPDATE)

    @staticmethod
    def get_original_event_info(obj, field_name):
        event = obj.original_data.get(field_name, None)
        if event:
            return {
                'timestamp': event.get('timeStamp', None),
                'username': event.get('username', '') or event.get('userId', '')
            }

    def create_event(self, event_info, obj, content_type, crud_event_type):
        # User
        username = event_info['username']
        user = User.objects.filter(username=username).first() or self._new_users.get(username, None)
        if user is None:
            first_name, last_name = self.get_first_and_last_name(username)
            user = User(
                username=username, first_name=first_name, last_name=last_name,
                is_staff=False, is_active=False, is_superuser=False
            )
            self._new_users[username] = user

        # Event
        self._crud_events.append(CRUDEvent(
            event_type=crud_event_type,
            object_id=obj.id,
            content_type=content_type,
            user=user,
            object_repr=str(obj)
        ))
        self._crud_events_datetime.append(make_aware(datetime.fromtimestamp(event_info['timestamp'] / 1000)))

    @staticmethod
    def get_first_and_last_name(username):
        if "," in username:
            last_name, first_name = username.split(",", maxsplit=1)
        elif " " in username:
            first_name, last_name = username.split(maxsplit=1)
        else:
            first_name, last_name = ('', username)
        return first_name.strip(), last_name.strip()
