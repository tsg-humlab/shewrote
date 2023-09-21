import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class Country(models.Model):
    """Model representing a list of country names."""
    modern_country = models.CharField(max_length=255)
    alternative_country_name = models.CharField(max_length=255, blank=True)
    notes = models.CharField(max_length=255, blank=True)


class Place(models.Model):
    """Represents a Place in a country and its location in the world."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name_of_city = models.CharField(max_length=255, blank=True)
    cerl_id = models.IntegerField(blank=True)
    modern_country = models.ForeignKey(Country, models.SET_NULL, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True)
    original_data = models.JSONField(blank=True)


class Person(models.Model):
    """Represents a person."""

    class GenderChoices(models.TextChoices):
        FEMALE = "F", _("Female")
        MALE = "M", _("Male")
        OTHER = "O", _("Other")
        NOT_APPLICABLE = "N", _("Not Applicable")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    short_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255, blank=True)
    maiden_name = models.CharField(max_length=255, blank=True)
    married_name = models.CharField(max_length=255, blank=True)  # TODO VARCHAR (255) +
    date_of_birth = models.DateField(blank=True)
    date_of_death = models.DateField(blank=True)
    alternative_birth_date = models.DateField(blank=True)
    alternative_death_date = models.DateField(blank=True)
    flourishing_start = models.IntegerField(blank=True)
    flourishing_end = models.IntegerField(blank=True)
    sex = models.CharField(max_length=1, choices=GenderChoices.choices, blank=True)
    alternative_name_gender = models.CharField(max_length=1, choices=GenderChoices.choices, blank=True)
    place_of_birth = models.ForeignKey(Place, models.SET_NULL, blank=True, null=True, related_name="+")
    place_of_death = models.ForeignKey(Place, models.SET_NULL, blank=True, null=True, related_name="+")
    professional_ecclesiastic_title = models.CharField(max_length=255, blank=True)
    aristocratic_title = models.CharField(max_length=255, blank=True)
    education = models.CharField(max_length=255, blank=True)
    bibliography = models.TextField(blank=True)
    related_to = models.ManyToManyField("self", blank=True)
    notes = models.TextField(blank=True)
    original_data = models.JSONField(blank=True)

    def __str__(self):
        """Return the name of the Person."""
        return self.short_name


class PersonViafOrCerl(models.Model):
    """Model containing VIAF or CERL related to Person."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    viaf = models.CharField(max_length=255, blank=True)
    cerl = models.CharField(max_length=255, blank=True)
    notes = models.CharField(max_length=255, blank=True)


class Role(models.Model):
    """Model describing the roles a Person can have."""
    role = models.CharField(max_length=255)


class PersonRole(models.Model):
    """Model describing the Role a Person had during a certain period."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, models.SET_NULL, null=True)
    start_year = models.IntegerField(blank=True)
    end_year = models.IntegerField(blank=True)
    notes = models.CharField(max_length=255, blank=True)


class Profession(models.Model):
    """Model describing the profession of a Person."""
    profession = models.CharField(max_length=255)


class PersonProfession(models.Model):
    """Model linking a Person to a Profession during a period of time."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    profession = models.ForeignKey(Profession, models.SET_NULL, null=True)
    start_year = models.IntegerField(blank=True)
    end_year = models.IntegerField(blank=True)
    notes = models.CharField(max_length=255, blank=True)


class Religion(models.Model):
    """Model describing the profession of a Person."""
    religion = models.CharField(max_length=255)


class PersonReligion(models.Model):
    """Model linking a Person to a Profession during a period of time."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    religion = models.ForeignKey(Religion, models.SET_NULL, null=True)
    start_year = models.IntegerField(blank=True)
    end_year = models.IntegerField(blank=True)
    notes = models.CharField(max_length=255, blank=True)


class Marriage(models.Model):
    """Model defining the marital status of Person to a Spouse."""
    class MaritalStatusChoices(models.TextChoices):
        UNMARRIED = "U", _("Unmarried")
        MARRIED = "M", _("Married")
        DIVORCED = "D", _("Divorced")
        WIDOWED = "W", _("Widowed")

    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="+")
    spouse = models.ForeignKey(Person, models.SET_NULL, null=True, blank=True)
    marital_status = models.CharField(max_length=1, choices=MaritalStatusChoices.choices, blank=True)
    start_year = models.IntegerField(blank=True)
    end_year = models.IntegerField(blank=True)
    notes = models.CharField(max_length=255, blank=True)


class Child(models.Model):
    """Model linking a Child to its parent(s) as Persons."""
    child = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="+")
    mother = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="+")
    father = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="+")
    notes = models.CharField(max_length=255, blank=True)


class AlternativeName(models.Model):
    """"Model describing name variations and periods they were in use."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    alternative_name = models.CharField(max_length=255)
    start_year = models.IntegerField(blank=True)
    end_year = models.IntegerField(blank=True)
    notes = models.CharField(max_length=255, blank=True)


class PeriodOfResidence(models.Model):
    """Model linking Person to Place over a period of time."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    start_year = models.IntegerField(blank=True)
    end_year = models.IntegerField(blank=True)
    notes = models.CharField(max_length=255, blank=True)


class TypeOfCollective(models.Model):
    """Model describing the different types of Collective that exist."""
    type_of_collective = models.CharField(max_length=255)


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
    start_year = models.IntegerField(blank=True)
    end_year = models.IntegerField(blank=True)
    has_members = models.ManyToManyField(
        Person,
        through="PersonCollective",
        through_fields=("collective", "person"),
        blank=True,
    )
    notes = models.TextField(blank=True)
    original_data = models.JSONField(blank=True)

    def __str__(self):
        """Return the name of the Collective"""
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
    genre = models.CharField(max_length=255)


class Language(models.Model):
    """Model listing various languages."""
    language = models.CharField(max_length=255)


class Work(models.Model):
    """Represent a Work by a Person that may have multiple Editions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    viaf_work = models.IntegerField(blank=True)  # TODO DYNAMIC LINK
    related_persons = models.ManyToManyField(
        Person,
        through="PersonWork",
        through_fields=("work", "person"),
        blank=True,
    )
    person_role = models.CharField(max_length=255, blank=True)  # TODO ENUM, options?
    genre = models.ForeignKey(Genre, models.SET_NULL, null=True, blank=True)
    language = models.ManyToManyField(
        Language,
        through="WorkLanguage",
        through_fields=("work", "language"),
        blank=True,
    )
    notes = models.TextField(blank=True)
    original_data = models.JSONField(blank=True)

    def __str__(self):
        """Return the title of the Work"""
        return self.title


class PersonWork(models.Model):
    """Many-to-Many model connecting Persons and Works."""
    work = models.ForeignKey(Work, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)


class WorkLanguage(models.Model):
    """Model linking a Work to the Language it was written in."""
    work = models.ForeignKey(Work, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, models.SET_NULL, null=True)


class Edition(models.Model):
    """Represents an Edition of a Work published in a Place."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    related_work = models.ForeignKey(Work, on_delete=models.CASCADE)
    publication_year = models.IntegerField(blank=True)
    place_of_publication = models.ForeignKey(Place, models.SET_NULL, null=True, blank=True)
    language = models.ForeignKey(Language, models.SET_NULL, null=True, blank=True)
    cerl_publisher = models.CharField(max_length=255, blank=True)
    related_persons = models.ManyToManyField(
        Person,
        through="PersonEdition",
        through_fields=("edition", "person"),
        blank=True,
    )
    person_role = models.CharField(max_length=255, blank=True)  # TODO ENUM, options?
    genre = models.ForeignKey(Genre, models.SET_NULL, null=True, blank=True)
    url = models.URLField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    original_data = models.JSONField(blank=True)


class PersonEdition(models.Model):
    """Many-to-Many model connecting an Edition to related Persons."""
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
