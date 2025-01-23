import uuid
from collections import defaultdict

from django.db import models
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from computedfields.models import ComputedFieldsModel, computed

from easyaudit.models import CRUDEvent

from shewrote.tools import date_of_x_text_to_int

# # # START Helper classes and functions # # #

class EasyAuditMixin:
    """Mixin to add EasyAudit methods"""
    def get_last_edit(self):
        """Returns a CRUDEvent of the last change of an object"""
        return CRUDEvent.objects.filter(object_id=self.id).latest('datetime')


def post_save_relation_creator(sender, relation_fields, other_fields=()):
    @receiver(post_save, sender=sender)
    def post_save_relation(sender, instance, created, **kwargs):
        """Create/update a/the symmetrical relation"""
        relation_fields_swapped = {
            relation_fields[0]: getattr(instance, relation_fields[1]),
            relation_fields[1]: getattr(instance, relation_fields[0]),
        }

        other_field_values = {field: getattr(instance, field) for field in other_fields}

        opposite_objects = sender.objects.filter(**relation_fields_swapped)
        if not opposite_objects.exists():
            sender.objects.create(**{**relation_fields_swapped, **other_field_values})
            return

        sender.objects.filter(id=opposite_objects[0].id).update(**other_field_values)

        # Delete superfluous objects
        sender.objects.filter(id__in=opposite_objects[1:].values_list('id', flat=True)).delete()

    return post_save_relation


def post_delete_relation_creator(sender, relation_fields):
    @receiver(post_delete, sender=sender)
    def post_delete_relation(sender, instance, **kwargs):
        """Delete the symmetrical relation"""
        relation_fields_swapped = {
            relation_fields[0]: getattr(instance, relation_fields[1]),
            relation_fields[1]: getattr(instance, relation_fields[0]),
        }
        sender.objects.filter(**relation_fields_swapped).delete()

    return post_delete_relation


# # # END Helper classes and functions # # #


class Country(models.Model):
    """Model representing a list of country names."""
    modern_country = models.CharField(max_length=255)
    alternative_country_name = models.CharField(max_length=255, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural = 'countries'
        ordering = ['modern_country']

    def __str__(self):
        """Return the modern name of the country."""
        return self.modern_country


class Place(models.Model):
    """Represents a Place in a country and its location in the world."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, unique=True)
    cerl_id = models.IntegerField(blank=True, null=True)
    modern_country = models.ForeignKey(Country, models.PROTECT, null=True, blank=True, related_name='places')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    original_data = models.JSONField(blank=True, null=True, editable=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        """Return the Place name."""
        return self.name


class Person(EasyAuditMixin, ComputedFieldsModel):
    """Represents a person."""

    class GenderChoices(models.TextChoices):
        FEMALE = "F", _("Female")
        MALE = "M", _("Male")
        OTHER = "O", _("Other")
        NOT_APPLICABLE = "N", _("Not Applicable")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    short_name = models.CharField(max_length=255)
    viaf_or_cerl = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    birth_name = models.CharField(max_length=255, blank=True)
    date_of_birth = models.CharField(max_length=50, blank=True)
    date_of_death = models.CharField(max_length=50, blank=True)
    alternative_birth_date = models.CharField(max_length=50, blank=True)
    alternative_death_date = models.CharField(max_length=50, blank=True)
    flourishing_start = models.CharField(max_length=255, blank=True, null=True)
    flourishing_end = models.CharField(max_length=255, blank=True, null=True)
    sex = models.CharField(max_length=1, choices=GenderChoices.choices, blank=True)
    alternative_name_gender = models.CharField(max_length=1, choices=GenderChoices.choices, blank=True)
    place_of_birth = models.ForeignKey(Place, models.PROTECT, blank=True, null=True, related_name="birthplace_of")
    place_of_death = models.ForeignKey(Place, models.SET_NULL, blank=True, null=True, related_name="+")
    professional_ecclesiastic_title = models.CharField(max_length=255, blank=True)
    aristocratic_title = models.CharField(max_length=255, blank=True)
    mother = models.ForeignKey("self", models.SET_NULL, null=True, blank=True, related_name="+")
    father = models.ForeignKey("self", models.SET_NULL, null=True, blank=True, related_name="+")
    bibliography = models.TextField(blank=True)
    related_to = models.ManyToManyField("self", blank=True, through="PersonPersonRelation",
                                        through_fields=('from_person', 'to_person'))
    notes = models.TextField(blank=True)
    original_data = models.JSONField(blank=True, null=True, editable=False)
    place_of_residence_notes = models.TextField(blank=True)

    @computed(models.SmallIntegerField(null=True), depends=[('self', ['date_of_birth'])])
    def normalised_date_of_birth(self):
        return date_of_x_text_to_int(self.date_of_birth)
    @computed(models.SmallIntegerField(null=True), depends=[('self', ['date_of_death'])])
    def normalised_date_of_death(self):
        return date_of_x_text_to_int(self.date_of_death)

    class Meta:
        indexes = [
            models.Index(fields=["normalised_date_of_birth"]),
            models.Index(fields=["normalised_date_of_death"])
        ]
        ordering = ['short_name']

    def __str__(self):
        """Return the name of the Person."""
        return self.short_name

    def get_absolute_url(self):
        return reverse("shewrote:person", kwargs={"person_id": self.pk})

    def get_children(self):
        if self.sex == Person.GenderChoices.FEMALE:
            return Person.objects.filter(mother=self).order_by('date_of_birth')
        elif self.sex == Person.GenderChoices.MALE:
            return Person.objects.filter(father=self).order_by('date_of_birth')

    def get_religions(self):
        return Religion.objects.filter(personreligion__person=self)

    def get_collectives(self):
        return Collective.objects.filter(personcollective__person=self)

    def get_works_for_role(self, role_name):
        return Work.objects.filter(personwork__person=self, personwork__role__name=role_name)

    def get_education(self):
        return Education.objects.filter(personeducation__person=self)

    def get_alternative_names(self):
        return AlternativeName.objects.filter(person=self)

    def get_marriages(self):
        return Marriage.objects.filter(person=self)

    def get_professions(self):
        return PersonProfession.objects.filter(person=self)

    def get_places_of_residence(self):
        return PeriodOfResidence.objects.filter(person=self)


class RelationType(models.Model):
    text = models.CharField(max_length=255, unique=True)
    reverse = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['text']

    def __str__(self):
        return self.text


@receiver(post_save, sender=RelationType)
def post_save_relation(sender, instance, created, **kwargs):
    reverse = instance.reverse
    if reverse and reverse.reverse != instance:
        reverse.reverse = instance
        reverse.save()


class PersonPersonRelation(models.Model):
    from_person = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="from_relations")
    to_person = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="to_relations")
    types = models.ManyToManyField(RelationType, blank=True)

    class Meta:
        unique_together = ['from_person', 'to_person']

    def __str__(self):
        return f'{self.from_person} is related to {self.to_person}'


@receiver(m2m_changed, sender=PersonPersonRelation.types.through)
def copy_types_to_reverse(sender, instance, **kwargs):
    reverse = PersonPersonRelation.objects.get(from_person=instance.to_person, to_person=instance.from_person)
    PersonPersonRelation.types.through.objects.filter(personpersonrelation=reverse).delete()
    types_for_reverse = []
    for type in instance.types.all():
        if type.reverse:
            types_for_reverse.append(PersonPersonRelation.types.through(personpersonrelation=reverse, relationtype=type.reverse))
        else:
            types_for_reverse.append(PersonPersonRelation.types.through(personpersonrelation=reverse, relationtype=type))
    PersonPersonRelation.types.through.objects.bulk_create(types_for_reverse)


post_save_personpersonrelation = post_save_relation_creator(PersonPersonRelation, ('from_person', 'to_person'))


post_delete_personpersonrelation = post_delete_relation_creator(PersonPersonRelation, ('from_person', 'to_person'))


class Education(models.Model):
    """Represents the type of Education a Person received."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        """Return the name of the Education."""
        return self.name


class PersonEducation(models.Model):
    """Model linking Person to Education."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    education = models.ForeignKey(Education, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.person.short_name}: {self.education.name.lower()}'


class Role(models.Model):
    """Model describing the roles a Person can have."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        """Return the name of the Role."""
        return self.name


class Profession(models.Model):
    """Model describing the profession of a Person."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        """Return the name of the Profession."""
        return self.name


class PersonProfession(models.Model):
    """Model linking a Person to a Profession during a period of time."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    profession = models.ForeignKey(Profession, models.SET_NULL, null=True)
    start_year = models.IntegerField(blank=True, null=True)
    end_year = models.IntegerField(blank=True, null=True)
    notes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f'{self.person.short_name} was {self.profession.name.lower()}'


class Religion(models.Model):
    """Model describing the profession of a Person."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        """Return the name of the Religion."""
        return self.name


class PersonReligion(models.Model):
    """Model linking a Person to a Profession during a period of time."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    religion = models.ForeignKey(Religion, models.SET_NULL, null=True)
    start_year = models.IntegerField(blank=True, null=True)
    end_year = models.IntegerField(blank=True, null=True)
    notes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f'{self.person.short_name} was {self.religion.name.lower()}'


class Marriage(models.Model):
    """Model defining the marital status of Person to a Spouse."""
    class MaritalStatusChoices(models.TextChoices):
        MARRIED = "M", _("Married")
        DIVORCED = "D", _("Divorced")
        WIDOWED = "W", _("Widowed")
        UNMARRIED = "U", _("Unmarried")
        LIVING_TOGETHER = "L", _("Living together")
        OTHER = "O", _("Other")

    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="+")
    spouse = models.ForeignKey(Person, models.SET_NULL, null=True, blank=True)
    married_name = models.CharField(max_length=255, blank=True)
    marital_status = models.CharField(max_length=1, choices=MaritalStatusChoices.choices, blank=True)
    start_year = models.IntegerField(blank=True, null=True)
    end_year = models.IntegerField(blank=True, null=True)
    notes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        marital_status = self.get_marital_status_display().lower()
        if self.marital_status == Marriage.MaritalStatusChoices.LIVING_TOGETHER[0]:
            return f'{self.person.short_name} and {self.spouse.short_name if self.spouse else "UNKNOWN"} were {marital_status}'
        if self.marital_status in (Marriage.MaritalStatusChoices.UNMARRIED[0]):
            return f'{self.person.short_name} was {marital_status}'
        if self.marital_status == Marriage.MaritalStatusChoices.OTHER[0]:
            return f'{self.person.short_name} and {self.spouse.short_name if self.spouse else "UNKNOWN"}: {marital_status}'
        return f'{self.person.short_name} {marital_status} {self.spouse.short_name if self.spouse else "UNKNOWN"}'


@receiver(post_save, sender=Marriage)
def post_save_marriage(sender, instance, created, **kwargs):
    """Create/update a/the symmetrical relation"""
    field_values = {
        'married_name': instance.married_name,
        'marital_status': instance.marital_status,
        'start_year': instance.start_year,
        'end_year': instance.end_year,
        'notes': instance.notes
    }
    
    marriages = sender.objects.filter(person=instance.spouse, spouse=instance.person)
    if not marriages:
        sender.objects.create(person=instance.spouse, spouse=instance.person, **field_values)
        return

    # Delete superfluous marriage objects
    if len(marriages) > 1:
        Marriage.objects.filter(id__in=[marriage.id for marriage in marriages[1:]]).delete()

    sender.objects.filter(id=marriages[0].id).update(**field_values)


@receiver(post_delete, sender=Marriage)
def post_delete_marriage(sender, instance, **kwargs):
    """Delete the symmetrical relation"""
    sender.objects.filter(person=instance.spouse, spouse=instance.person).delete()


class AlternativeName(models.Model):
    """Model describing name variations and periods they were in use."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    alternative_name = models.CharField(max_length=255)
    start_year = models.IntegerField(blank=True, null=True)
    end_year = models.IntegerField(blank=True, null=True)
    notes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        """Return the Alternative Name for a Person during a period."""
        return self.alternative_name


class   PeriodOfResidence(models.Model):
    """Model linking Person to Place over a period of time."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    start_year = models.IntegerField(blank=True, null=True)
    end_year = models.IntegerField(blank=True, null=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural = "periods of residence"

    def __str__(self):
        from_string = f"from {self.start_year}" if self.start_year else ""
        until_string = f" until {self.end_year}" if self.end_year else ""
        return f"{self.person} lived in {self.place}{from_string}{until_string}"


class CollectiveType(models.Model):
    """Model describing the different types of Collective that exist."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type_of_collective = models.CharField(max_length=255)

    class Meta:
        ordering = ['type_of_collective']

    def __str__(self):
        """Returns the name of the type of Collective."""
        return self.type_of_collective


class Collective(models.Model):
    """Represents a Collective with multiple Persons as members in multiple Places."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    type = models.ForeignKey(CollectiveType, models.SET_NULL, null=True, blank=True)
    place = models.ManyToManyField(
        Place,
        through="CollectivePlace",
        through_fields=("collective", "place"),
        blank=True,
    )
    start_year = models.IntegerField(blank=True, null=True)
    end_year = models.IntegerField(blank=True, null=True)
    has_members = models.ManyToManyField(
        Person,
        through="PersonCollective",
        through_fields=("collective", "person"),
        blank=True,
    )
    notes = models.TextField(blank=True)
    original_data = models.JSONField(blank=True, null=True, editable=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        """Returns the name of the Collective."""
        return self.name


class PersonCollective(models.Model):
    """Many-to-Many model connecting Person and Collective."""
    collective = models.ForeignKey(Collective, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.person.short_name} was member of {self.collective.name}'


class CollectivePlace(models.Model):
    """Many-to-Many model connecting a Collective to its Places."""
    collective = models.ForeignKey(Collective, on_delete=models.CASCADE)
    place = models.ForeignKey(Place, on_delete=models.CASCADE)


class Genre(models.Model):
    """Model describing different genres."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        """Returns the name of the Genre."""
        return self.name


class Language(models.Model):
    """Model listing various languages."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        """Returns the name of the language."""
        return self.name


class IsNotSourceWorkManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(**{'original_data__@relations__isDocumentSourceOf__isnull': False})


class IsSourceWorkManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(**{'original_data__@relations__isDocumentSourceOf__isnull': False})


class Work(EasyAuditMixin, models.Model):
    """Represent a Work by a Person that may have multiple Editions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=1024)
    date_of_publication_start = models.IntegerField(blank=True, null=True)
    date_of_publication_end = models.IntegerField(blank=True, null=True)
    date_of_publication_text = models.CharField(max_length=128, blank=True)
    viaf_work = models.URLField(max_length=255, blank=True)
    related_persons = models.ManyToManyField(
        Person,
        through="PersonWork",
        through_fields=("work", "person"),
        blank=True,
    )
    languages = models.ManyToManyField(
        Language,
        through="WorkLanguage",
        through_fields=("work", "language"),
        blank=True,
    )
    notes = models.TextField(blank=True)
    original_data = models.JSONField(blank=True, null=True, editable=False)

    objects = models.Manager()
    work_objects = IsNotSourceWorkManager()
    source_objects = IsSourceWorkManager()

    class Meta:
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["date_of_publication_start"]),
            models.Index(fields=["date_of_publication_end"]),
        ]
        ordering = ['title']

    def __str__(self):
        """Returns the title of the Work"""
        return self.title

    def get_creators(self):
        return Person.objects.filter(personwork__work=self, personwork__role__name="is creator of")

    def get_persons_for_work(self):
        return Person.objects.filter(personwork__work=self)

    def get_role_for_person(self):
        return Role.objects.filter(personwork__work=self)

    def get_date_of_publication_string(self):
        if self.date_of_publication_start and self.date_of_publication_end\
            and self.date_of_publication_start != self.date_of_publication_end:
            return f'{self.date_of_publication_start} - {self.date_of_publication_end}'

        if self.date_of_publication_start:
            return str(self.date_of_publication_start)

        return self.date_of_publication_text



class PersonWork(models.Model):
    """Many-to-Many model connecting Persons, Works, and their Roles."""
    work = models.ForeignKey(Work, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, models.SET_NULL, null=True, blank=True)
    start_year = models.IntegerField(blank=True, null=True)
    end_year = models.IntegerField(blank=True, null=True)
    notes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f'{self.person} {self.role} {self.work}'


class WorkLanguage(models.Model):
    """Model linking an Edition to its Language(s)."""
    work = models.ForeignKey(Work, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, models.SET_NULL, null=True)


class Edition(EasyAuditMixin, models.Model):
    """Represents an Edition of a Work published in a Place."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    related_work = models.ForeignKey(Work, on_delete=models.CASCADE)
    publication_year = models.IntegerField(blank=True, null=True)
    place_of_publication = models.ForeignKey(Place, models.SET_NULL, null=True, blank=True)
    language = models.ManyToManyField(
        Language,
        through="EditionLanguage",
        through_fields=("edition", "language"),
        blank=True,
    )
    cerl_publisher = models.CharField(max_length=255, blank=True)
    related_persons = models.ManyToManyField(
        Person,
        through="PersonEdition",
        through_fields=("edition", "person"),
        blank=True,
    )
    genre = models.ForeignKey(Genre, models.SET_NULL, null=True, blank=True)
    url = models.URLField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    original_data = models.JSONField(blank=True, null=True, editable=False)

    def __str__(self):
        place_of_publication = f' in {self.place_of_publication}' if self.publication_year else ''
        cerl_publisher = f' by {self.cerl_publisher}' if self.cerl_publisher else ''
        publication_year = f' in {self.publication_year}' if self.publication_year else ''
        return f'{self.related_work} is published {place_of_publication}{cerl_publisher }{publication_year}'


class EditionLanguage(models.Model):
    """Model linking an Edition to its Language(s)."""
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, models.SET_NULL, null=True)


class PersonEdition(models.Model):
    """Many-to-Many model connecting an Edition to related Persons."""
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, models.SET_NULL, null=True, blank=True)


class ReceptionSource(models.Model):
    """Defines the Source of a Reception."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work = models.ForeignKey(Work, models.SET_NULL, blank=True, null=True, related_name="+")
    part_of = models.ForeignKey(Work, models.SET_NULL, blank=True, null=True, related_name="+")
    title_work = models.CharField(max_length=255, blank=True)
    related_persons = models.ManyToManyField(
        Person,
        through="PersonReceptionSource",
        through_fields=("reception_source", "person"),
        blank=True,
    )
    shelfmark = models.CharField(max_length=255, blank=True)
    reference = models.TextField(blank=True)
    date = models.DateField(blank=True, null=True)
    url = models.URLField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    original_Data = models.JSONField(blank=True, null=True, editable=False)

    class Meta:
        ordering = ['title_work']

    def __str__(self):
        """Returns the title of the Reception Source."""
        return self.title_work


class PersonReceptionSource(models.Model):
    """Many-to-Many model connecting an Edition to related Persons."""
    reception_source = models.ForeignKey(ReceptionSource, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, models.SET_NULL, null=True, blank=True)


class DocumentType(models.Model):
    """Defines the Type of document that can exist for a Reception."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type_of_document = models.CharField(max_length=255)

    class Meta:
        ordering = ['type_of_document']

    def __str__(self):
        """Returns the name of the Type of Document."""
        return self.type_of_document


class ReceptionType(models.Model):
    """This model defines the different types of Reception that can occur."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type_of_reception = models.CharField(max_length=255)

    class Meta:
        ordering = ['type_of_reception']

    def __str__(self):
        """Returns the name of the Type of Reception."""
        return self.type_of_reception


class Reception(EasyAuditMixin, models.Model):
    """Model defining a Reception of a Work by a Source in a Place."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    received_persons = models.ManyToManyField(
        Person,
        through="PersonReception",
        through_fields=("reception", "person"),
    )
    received_works = models.ManyToManyField(
        Work,
        through="WorkReception",
        through_fields=("reception", "work"),
    )
    received_editions = models.ManyToManyField(
        Edition,
        through="EditionReception",
        through_fields=("reception", "edition"),
    )
    source = models.ForeignKey(ReceptionSource, models.SET_NULL, null=True, blank=True)
    title = models.TextField(blank=True)
    is_same_as_work = models.ForeignKey(Work, models.SET_NULL, null=True, blank=True, related_name="+", verbose_name="is same as work")
    part_of_work = models.ForeignKey(Work, models.SET_NULL, null=True, blank=True, related_name="+")
    reference = models.TextField(blank=True)
    place_of_reception = models.ForeignKey(Place, models.SET_NULL, null=True, blank=True)
    date_of_reception = models.IntegerField(blank=True, null=True)
    quotation_reception = models.TextField(blank=True)
    document_type = models.ForeignKey(DocumentType, models.SET_NULL, null=True, blank=True)
    url = models.URLField(max_length=255, blank=True)
    language_of_reception = models.ManyToManyField(
        Language,
        through="ReceptionLanguage",
        through_fields=("reception", "language"),
        blank=True,
    )
    reception_genre = models.ManyToManyField(
        Genre,
        through="ReceptionGenre",
        through_fields=("reception", "genre"),
        blank=True,
    )
    viaf_work = models.URLField(max_length=255, blank=True)
    image = models.ImageField
    notes = models.TextField(blank=True)
    image = models.ImageField(upload_to="reception", null=True, blank=True)
    original_data = models.JSONField(blank=True, null=True, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["date_of_reception"])
        ]
        ordering = ['title']

    def __str__(self):
        """Returns the title of the Reception."""
        return self.title


class PersonReception(models.Model):
    """Defines the Role of a Person related to a Reception."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    reception = models.ForeignKey(Reception, on_delete=models.CASCADE)
    type = models.ForeignKey(ReceptionType, models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.reception.title} {self.type or "receives"} {self.person.short_name}'


class WorkReception(models.Model):
    work = models.ForeignKey(Work, on_delete=models.CASCADE)
    reception = models.ForeignKey(Reception, on_delete=models.CASCADE)
    type = models.ForeignKey(ReceptionType, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'{self.reception} {self.type} {self.work}'


class EditionReception(models.Model):
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE)
    reception = models.ForeignKey(Reception, on_delete=models.CASCADE)
    type = models.ForeignKey(ReceptionType, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'{self.reception} is reception of edition {self.edition}'


class ReceptionLanguage(models.Model):
    """Model linking a Reception to the Language it was written in."""
    reception = models.ForeignKey(Reception, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, models.SET_NULL, null=True)


class ReceptionGenre(models.Model):
    """This model links a Reception to a Genre."""
    reception = models.ForeignKey(Reception, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, models.SET_NULL, null=True)
