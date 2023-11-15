import uuid
from collections import defaultdict

from django.db import models
from django.utils.translation import gettext_lazy as _


class Country(models.Model):
    """Model representing a list of country names."""
    modern_country = models.CharField(max_length=255)
    alternative_country_name = models.CharField(max_length=255, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural = 'countries'

    def __str__(self):
        """Return the modern name of the country."""
        return self.modern_country


class Place(models.Model):
    """Represents a Place in a country and its location in the world."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, unique=True)
    cerl_id = models.IntegerField(blank=True, null=True)
    modern_country = models.ForeignKey(Country, models.SET_NULL, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True)
    original_data = models.JSONField(blank=True, null=True, editable=False)

    def __str__(self):
        """Return the Place name."""
        return self.name


class Person(models.Model):
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
    maiden_name = models.CharField(max_length=255, blank=True)
    date_of_birth = models.CharField(max_length=50, blank=True)
    date_of_death = models.CharField(max_length=50, blank=True)
    alternative_birth_date = models.CharField(max_length=50, blank=True)
    alternative_death_date = models.CharField(max_length=50, blank=True)
    flourishing_start = models.IntegerField(blank=True, null=True)
    flourishing_end = models.IntegerField(blank=True, null=True)
    sex = models.CharField(max_length=1, choices=GenderChoices.choices, blank=True)
    alternative_name_gender = models.CharField(max_length=1, choices=GenderChoices.choices, blank=True)
    place_of_birth = models.ForeignKey(Place, models.SET_NULL, blank=True, null=True, related_name="+")
    place_of_death = models.ForeignKey(Place, models.SET_NULL, blank=True, null=True, related_name="+")
    professional_ecclesiastic_title = models.CharField(max_length=255, blank=True)
    aristocratic_title = models.CharField(max_length=255, blank=True)
    education = models.CharField(max_length=255, blank=True)
    mother = models.ForeignKey("self", models.SET_NULL, null=True, blank=True, related_name="+")
    father = models.ForeignKey("self", models.SET_NULL, null=True, blank=True, related_name="+")
    bibliography = models.TextField(blank=True)
    related_to = models.ManyToManyField("self", blank=True)
    notes = models.TextField(blank=True)
    original_data = models.JSONField(blank=True, null=True, editable=False)

    def __str__(self):
        """Return the name of the Person."""
        return self.short_name

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
        return Work.objects.filter(personworkrole__person=self, personworkrole__role__name=role_name)


class Role(models.Model):
    """Model describing the roles a Person can have."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        """Return the name of the Role."""
        return self.name


class Profession(models.Model):
    """Model describing the profession of a Person."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

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


class Religion(models.Model):
    """Model describing the profession of a Person."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

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


class Marriage(models.Model):
    """Model defining the marital status of Person to a Spouse."""
    class MaritalStatusChoices(models.TextChoices):
        MARRIED = "M", _("Married")
        DIVORCED = "D", _("Divorced")
        WIDOWED = "W", _("Widowed")

    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="+")
    spouse = models.ForeignKey(Person, models.SET_NULL, null=True, blank=True)
    married_name = models.CharField(max_length=255, blank=True)
    marital_status = models.CharField(max_length=1, choices=MaritalStatusChoices.choices, blank=True)
    start_year = models.IntegerField(blank=True, null=True)
    end_year = models.IntegerField(blank=True, null=True)
    notes = models.CharField(max_length=255, blank=True)


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


class PeriodOfResidence(models.Model):
    """Model linking Person to Place over a period of time."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    start_year = models.IntegerField(blank=True, null=True)
    end_year = models.IntegerField(blank=True, null=True)
    notes = models.CharField(max_length=255, blank=True)


class TypeOfCollective(models.Model):
    """Model describing the different types of Collective that exist."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type_of_collective = models.CharField(max_length=255)

    def __str__(self):
        """Returns the name of the type of Collective."""
        return self.type_of_collective


class Collective(models.Model):
    """Represents a Collective with multiple Persons as members in multiple Places."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    type = models.ForeignKey(TypeOfCollective, models.SET_NULL, null=True, blank=True)
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

    def __str__(self):
        """Returns the name of the Collective."""
        return self.name


class PersonCollective(models.Model):
    """Many-to-Many model connecting Person and Collective."""
    collective = models.ForeignKey(Collective, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)


class CollectivePlace(models.Model):
    """Many-to-Many model connecting a Collective to its Places."""
    collective = models.ForeignKey(Collective, on_delete=models.CASCADE)
    place = models.ForeignKey(Place, on_delete=models.CASCADE)


class Genre(models.Model):
    """Model describing different genres."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        """Returns the name of the Genre."""
        return self.name


class Language(models.Model):
    """Model listing various languages."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        """Returns the name of the language."""
        return self.name


class Work(models.Model):
    """Represent a Work by a Person that may have multiple Editions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=1024)
    viaf_work = models.URLField(max_length=255, blank=True)
    related_persons = models.ManyToManyField(
        Person,
        through="PersonWorkRole",
        through_fields=("work", "person"),
        blank=True,
    )
    notes = models.TextField(blank=True)
    original_data = models.JSONField(blank=True, null=True, editable=False)

    def __str__(self):
        """Returns the title of the Work"""
        return self.title


class PersonWorkRole(models.Model):
    """Many-to-Many model connecting Persons, Works, and their Roles."""
    work = models.ForeignKey(Work, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, models.SET_NULL, null=True, blank=True)
    start_year = models.IntegerField(blank=True, null=True)
    end_year = models.IntegerField(blank=True, null=True)
    notes = models.CharField(max_length=255, blank=True)


class Edition(models.Model):
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
        through="PersonEditionRole",
        through_fields=("edition", "person"),
        blank=True,
    )
    genre = models.ForeignKey(Genre, models.SET_NULL, null=True, blank=True)
    url = models.URLField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    original_data = models.JSONField(blank=True, null=True, editable=False)


class EditionLanguage(models.Model):
    """Model linking an Edition to its Language(s)."""
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, models.SET_NULL, null=True)


class PersonEditionRole(models.Model):
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
        through="PersonReceptionSourceRole",
        through_fields=("reception_source", "person"),
        blank=True,
    )
    shelfmark = models.CharField(max_length=255, blank=True)
    reference = models.TextField(blank=True)
    date = models.DateField(blank=True, null=True)
    url = models.URLField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    original_Data = models.JSONField(blank=True, null=True, editable=False)

    def __str__(self):
        """Returns the title of the Reception Source."""
        return self.title_work


class PersonReceptionSourceRole(models.Model):
    """Many-to-Many model connecting an Edition to related Persons."""
    reception_source = models.ForeignKey(ReceptionSource, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, models.SET_NULL, null=True, blank=True)


class TypeOfDocument(models.Model):
    """Defines the Type of document that can exist for a Reception."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type_of_document = models.CharField(max_length=255)

    def __str__(self):
        """Returns the name of the Type of Document."""
        return self.type_of_document


class TypeOfReception(models.Model):
    """This model defines the different types of Reception that can occur."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type_of_reception = models.CharField(max_length=255)

    def __str__(self):
        """Returns the name of the Type of Reception."""
        return self.type_of_reception


class Reception(models.Model):
    """Model defining a Reception of a Work by a Source in a Place."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.ManyToManyField(
        Person,
        through="PersonReceptionRole",
        through_fields=("reception", "person"),
    )
    source = models.ForeignKey(ReceptionSource, models.SET_NULL, null=True, blank=True)
    title = models.TextField(blank=True)
    part_of_work = models.ForeignKey(Work, models.SET_NULL, null=True, blank=True)
    reference = models.TextField(blank=True)
    place_of_reception = models.ForeignKey(Place, models.SET_NULL, null=True, blank=True)
    date_of_reception = models.IntegerField(blank=True)
    quotation_reception = models.TextField(blank=True)
    document_type = models.ForeignKey(TypeOfDocument, models.SET_NULL, null=True, blank=True)
    url = models.URLField(max_length=255, blank=True)
    reception_type = models.ManyToManyField(
        TypeOfReception,
        through="ReceptionType",
        through_fields=("reception", "type"),
        blank=True,
    )
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
    original_data = models.JSONField(blank=True, null=True, editable=False)

    def __str__(self):
        """Returns the title of the Reception."""
        return self.title


class PersonReceptionRole(models.Model):
    """Defines the Role of a Person related to a Reception."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    reception = models.ForeignKey(Reception, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, models.SET_NULL, null=True, blank=True)


class ReceptionType(models.Model):
    """Model linking a Reception to its Type."""
    reception = models.ForeignKey(Reception, on_delete=models.CASCADE)
    type = models.ForeignKey(TypeOfReception, models.SET_NULL, null=True)


class ReceptionLanguage(models.Model):
    """Model linking a Reception to the Language it was written in."""
    reception = models.ForeignKey(Reception, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, models.SET_NULL, null=True)


class ReceptionGenre(models.Model):
    """This model links a Reception to a Genre."""
    reception = models.ForeignKey(Reception, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, models.SET_NULL, null=True)
