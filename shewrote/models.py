from django.db import models
from django.utils.translation import gettext_lazy as _


class Person(models.Model):
    """Represents a person."""

    class GenderChoices(models.TextChoices):
        FEMALE = "F", _("Female")
        MALE = "M", _("Male")
        UNKNOWN = "U", _("Unknown")

    class MaritalStatusChoices(models.TextChoices):
        UNMARRIED = "U", _("Unmarried")
        MARRIED = "M", _("Married")
        DIVORCED = "D", _("Divorced")
        WIDOWED = "W", _("Widowed")

    id = models.UUIDField(primary_key=True, editable=False)
    short_name = models.CharField(max_length=255)
    viaf_or_cerl_identifier = models.IntegerField()  # TODO ENUM DYNAMIC LINK, options?
    first_name = models.CharField(max_length=255)
    maiden_name = models.CharField(max_length=255)
    married_name = models.CharField(max_length=255, blank=True)  # VARCHAR (255) +, if multi needed, make it ManyToMany?
    alternative_name = models.CharField(max_length=255, blank=True)
    date_in_use_of_name = models.DateField(auto_now=False, auto_now_add=False, blank=True)
    date_of_birth = models.DateField(auto_now=False, auto_now_add=False)
    date_of_death = models.DateField(auto_now=False, auto_now_add=False)
    alternative_birth_date = models.DateField(auto_now=False, auto_now_add=False, blank=True)
    alternative_death_date = models.DateField(auto_now=False, auto_now_add=False, blank=True)
    flourishing = models.CharField(max_length=32)  # INT (start year – end year), don't think that is an INT
    sex = models.CharField(max_length=1, choices=GenderChoices.choices)
    alternative_name_gender = models.CharField(max_length=255, blank=True)
    place_of_birth = models.ForeignKey('Place', on_delete=models.CASCADE, related_name="+")
    place_of_death = models.ForeignKey('Place', on_delete=models.CASCADE, related_name="+")
    is_author_of = models.ManyToManyField(
        'Work',
        through="Authorship",
        through_fields=("person", "work"),
    ),
    professional_ecclesiastic_title = models.CharField(max_length=255, blank=True)
    aristocratic_title = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=255)  # TODO ENUM +, options?
    date_of_role = models.CharField(max_length=32)  # INT (start year – end year), don't think that is an INT
    place_of_residence = models.CharField(max_length=255)  # TODO ENUM +, options? Why not refer to Place?
    date_of_residence = models.CharField(max_length=32)  # INT (start year – end year), don't think that is an INT
    education = models.CharField(max_length=255)
    marital_status = models.CharField(max_length=1, choices=MaritalStatusChoices.choices)
    date_of_marital_status = models.CharField(max_length=32)  # INT (start year – end year), don't think that is an INT
    spouse = models.ManyToManyField("self")
    children = models.ManyToManyField("self")
    profession = models.CharField(max_length=255)  # TODO ENUM, options?
    religion = models.CharField(max_length=255)  # TODO ENUM, options?
    bibliography = models.TextField()
    related_to = models.ManyToManyField("self")
    publications = models.ManyToManyField(
        'Work',
        through="Publication",
        through_fields=("person", "work"),
    )
    notes = models.TextField()

    def __str__(self):
        """Return the name of the Person."""
        return self.short_name


class Collective(models.Model):
    """Represents a Collective with multiple Persons as members in multiple Places."""
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=255)  # TODO ENUM (not_null), what are the options?
    name = models.CharField(max_length=255)
    place = models.ManyToManyField('Place')
    dates_of_activity = models.CharField(max_length=32)  # INT +, but is it an INT?
    has_members = models.ManyToManyField(
        'Person',
        through="Membership",
        through_fields=("collective", "person"),
    )
    notes = models.TextField()

    def __str__(self):
        """Return the name of the Collective"""
        return self.name


class Work(models.Model):
    """Represent a Work by a Person that may have multiple Editions."""
    id = models.AutoField(primary_key=True)
    viaf_work = models.IntegerField()  # TODO ENUM DYNAMIC LINK, options?
    language = models.CharField(max_length=255)  # TODO ENUM +, options?
    related_persons = models.ManyToManyField(
        'Person',
        through="RelatedPersonWork",
        through_fields=("work", "person"),
    )
    person_role = models.CharField(max_length=255)  # TODO ENUM, options?
    notes = models.TextField()

    def __str__(self):
        """Returns the VIAF id for the work."""
        return self.viaf_work


class Edition(models.Model):
    """Represents an Edition of a Work published in a Place."""
    id = models.AutoField(primary_key=True)
    related_work = models.ForeignKey('Work', on_delete=models.CASCADE)
    publication_year = models.IntegerField()
    place_of_publication = models.ForeignKey('Place', on_delete=models.CASCADE)
    language = models.CharField(max_length=255)  # TODO ENUM, options?
    cerl_publisher = models.IntegerField(max_length=32)  # TODO ENUM DYNAMIC LINK, options?
    related_persons = models.ManyToManyField(
        'Person',
        through="RelatedPersonEdition",
        through_fields=("edition", "person"),
    )
    person_role = models.CharField(max_length=255)  # TODO ENUM, options?
    genre = models.CharField(max_length=255)  # TODO ENUM, options?
    cerl_publisher = models.IntegerField()  # TODO ENUM DYNAMIC LINK, options?
    url = models.CharField(max_length=255)
    notes = models.TextField()


class Place(models.Model):
    """Represents a Place in a country and its location in the world."""
    id = models.AutoField(primary_key=True)
    name_of_city = models.CharField(max_length=255)
    cerl_id = models.IntegerField()
    modern_country = models.CharField(max_length=255)  # TODO Make a dropdown list of modern countries.
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)


class Membership(models.Model):
    """Many-to-Many model connecting Person and Collective."""
    collective = models.ForeignKey(Collective, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)


class Authorship(models.Model):
    """Many-to-Many model connecting Person as author and Work."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    work = models.ForeignKey(Work, on_delete=models.CASCADE)


class Publication(models.Model):
    """Many-to-Many model connecting Person and Work as publication."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    work = models.ForeignKey(Work, on_delete=models.CASCADE)


class RelatedPersonWork(models.Model):
    """Many-to-Many model connecting a Work to related Persons."""
    work = models.ForeignKey(Work, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)


class RelatedPersonEdition(models.Model):
    """Many-to-Many model connecting an Edition to related Persons."""
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

