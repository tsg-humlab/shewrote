from django.contrib import admin
from .models import (Country, Place, Person, Education, PersonEducation, Role, Profession, PersonProfession, Religion,
                     PersonReligion, Marriage, AlternativeName, PeriodOfResidence, TypeOfCollective, Collective,
                     PersonCollective, CollectivePlace, Genre, Language, Work, PersonWorkRole, Edition, EditionLanguage,
                     PersonEditionRole, ReceptionSource, PersonReceptionSourceRole, TypeOfDocument, TypeOfReception,
                     Reception, PersonReceptionRole, ReceptionType, ReceptionLanguage, ReceptionGenre)

admin.site.register(Country)


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    search_fields = ["name"]


class AlternativeNameInline(admin.TabularInline):
    model = AlternativeName
    fields = [
        "alternative_name",
        "start_year",
        "end_year",
        "notes"
    ]
    extra = 0


class PeriodsOfResidenceInline(admin.TabularInline):
    model = PeriodOfResidence
    fields = [
        "place",
        "start_year",
        "end_year",
        "notes"
    ]
    extra = 0
    autocomplete_fields = ['place']
    verbose_name = "Lived in"
    verbose_name_plural = "Lived in"


class PersonWorkRoleInline(admin.TabularInline):
    model = PersonWorkRole
    fields = [
        "role",
        "work",
        "start_year",
        "end_year",
        "notes"
    ]
    extra = 0
    autocomplete_fields = ['work', 'person']
    verbose_name = "Work"


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    search_fields = ['short_name']
    ordering = ['short_name']
    autocomplete_fields = [
        "place_of_birth",
        "place_of_death",
        "mother",
        "father",
        "related_to",
    ]
    fieldsets = [
        (
            None,
            {
                "fields": ["short_name", "viaf_or_cerl", "first_name", "maiden_name",
                           "date_of_birth", "place_of_birth", "date_of_death", "place_of_death"]
            },
        ),
        (
            "Relations",
            {
                # "classes": ("collapse",),
                "fields": ["mother", "father", "related_to"]
            }
        ),
        (
            "Professional",
            {
                # "classes": ("collapse",),
                "fields": ["professional_ecclesiastic_title", "aristocratic_title", "flourishing_start",
                           "flourishing_end", "bibliography"]
            }
        )
    ]
    inlines = [AlternativeNameInline, PeriodsOfResidenceInline, PersonWorkRoleInline]

admin.site.register(Education)
admin.site.register(PersonEducation)
admin.site.register(Role)
admin.site.register(Profession)
admin.site.register(PersonProfession)
admin.site.register(Religion)
admin.site.register(PersonReligion)

@admin.register(Marriage)
class MarriageAdmin(admin.ModelAdmin):
    autocomplete_fields = ['person', 'spouse']

admin.site.register(AlternativeName)

@admin.register(PeriodOfResidence)
class PeriodOfResidenceAdmin(admin.ModelAdmin):
    search_fields = ['person__short_name', 'place__name']
    autocomplete_fields = ['person']

admin.site.register(TypeOfCollective)
admin.site.register(Collective)
admin.site.register(PersonCollective)
admin.site.register(CollectivePlace)
admin.site.register(Genre)
admin.site.register(Language)


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    search_fields = ['title']


@admin.register(PersonWorkRole)
class PersonWorkRoleAdmin(admin.ModelAdmin):
    list_display = ["person", "role", "work"]
    list_display_links = ["person", "role", "work"]
    search_fields = ["person__short_name", "role__name", "work__title"]
    autocomplete_fields = ['work', 'person']


admin.site.register(Edition)
admin.site.register(EditionLanguage)
admin.site.register(PersonEditionRole)
admin.site.register(ReceptionSource)
admin.site.register(PersonReceptionSourceRole)
admin.site.register(TypeOfDocument)
admin.site.register(TypeOfReception)
admin.site.register(Reception)
admin.site.register(PersonReceptionRole)
admin.site.register(ReceptionType)
admin.site.register(ReceptionLanguage)
admin.site.register(ReceptionGenre)