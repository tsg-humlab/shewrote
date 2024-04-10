from django.contrib import admin
from django.utils.safestring import mark_safe
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


class PersonReceptionRoleInline(admin.TabularInline):
    model = PersonReceptionRole
    fields = [
        "person",
        "role",
        "reception",
    ]
    autocomplete_fields = ['person', 'reception', 'role']
    extra = 0


class PersonReceptionRoleInlineFromPerson(PersonReceptionRoleInline):
    verbose_name = "Reception"


class PersonReceptionRoleInlineFromReception(PersonReceptionRoleInline):
    verbose_name = "Person"


class PersonProfessionInline(admin.TabularInline):
    model = PersonProfession
    fields = ["person", "profession", "start_year", "end_year", "notes"]
    extra = 0
    verbose_name = "Profession"


class PersonEducationInline(admin.TabularInline):
    model = PersonEducation
    fields = ["person", "education"]
    extra = 0
    verbose_name = "Education"


class PersonReligionInline(admin.TabularInline):
    model = PersonReligion
    fields = ["person", "religion", "start_year", "end_year", "notes"]
    extra = 0
    verbose_name = "Religion"


class PersonCollectiveInline(admin.TabularInline):
    model = PersonCollective
    fields = ["person", "collective"]
    extra = 0
    verbose_name = "Collective"


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ["short_name", "first_name", "maiden_name", "sex", "date_of_birth", "place_of_birth",
                    "date_of_death", "place_of_death", "notes", 'view_on_site_link']
    search_fields = ['short_name']
    ordering = ['short_name']
    list_filter = ["sex", "place_of_birth__modern_country__modern_country"]
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
                "fields": [("short_name", "viaf_or_cerl"), ("first_name", "maiden_name",),
                           ("date_of_birth", "place_of_birth"), ("date_of_death", "place_of_death")],
            },
        ),
        (
            "Relations",
            {
                # "classes": ("collapse",),
                "fields": [("mother", "father"), "related_to"]
            }
        ),
        (
            "Professional",
            {
                # "classes": ("collapse",),
                "fields": [("aristocratic_title", "professional_ecclesiastic_title"), ("flourishing_start",
                           "flourishing_end"), "bibliography"]
            }
        )
    ]
    inlines = [PersonEducationInline, PersonProfessionInline, PersonReligionInline,
               AlternativeNameInline, PeriodsOfResidenceInline,
               PersonWorkRoleInline, PersonCollectiveInline, PersonReceptionRoleInlineFromPerson]

    def view_on_site_link(self, obj):
        icon = '<img src="/static/admin/img/icon-viewlink.svg" alt="View on site" title="View on site">'
        return mark_safe(f'<a href="{obj.get_absolute_url()}">{icon}</i></a>')

admin.site.register(Education)
admin.site.register(PersonEducation)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    search_fields = ['name']


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


@admin.register(ReceptionSource)
class ReceptionSourceAdmin(admin.ModelAdmin):
    search_fields = ['title_work']
    autocomplete_fields = ['work', 'part_of']


admin.site.register(PersonReceptionSourceRole)


@admin.register(TypeOfDocument)
class TypeOfDocumentAdmin(admin.ModelAdmin):
    search_fields = ['type_of_document']


admin.site.register(TypeOfReception)


class ReceptionTypeInline(admin.TabularInline):
    model = ReceptionType
    fields = ["reception", "type"]
    extra = 0
    verbose_name = "Type"


class ReceptionLanguageInline(admin.TabularInline):
    model = ReceptionLanguage
    fields = ["reception", "language"]
    extra = 0
    verbose_name = "Language"


class ReceptionGenreInline(admin.TabularInline):
    model = ReceptionGenre
    fields = ["reception", "genre"]
    extra = 0
    verbose_name = "Genre"


@admin.register(Reception)
class ReceptionAdmin(admin.ModelAdmin):
    list_display = ['title', 'reference']
    list_display_links = ['title', 'reference']
    search_fields = ['title', 'reference']
    autocomplete_fields = [
        'source',
        'part_of_work',
        'place_of_reception',
        'document_type',
    ]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    ("title", "source", "part_of_work", "reference"),
                    "document_type",
                    ("place_of_reception", "date_of_reception"),
                    ("quotation_reception", "url", "viaf_work"),
                    "notes"
                ],
            },
        ),
    ]
    inlines = [PersonReceptionRoleInlineFromReception, ReceptionTypeInline, ReceptionLanguageInline,
               ReceptionGenreInline]


@admin.register(PersonReceptionRole)
class PersonReceptionRole(admin.ModelAdmin):
    search_fields = []


admin.site.register(ReceptionType)
admin.site.register(ReceptionLanguage)
admin.site.register(ReceptionGenre)