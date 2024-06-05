from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import (Country, Place, Person, Education, PersonEducation, Role, Profession, PersonProfession, Religion,
                     PersonReligion, Marriage, AlternativeName, PeriodOfResidence, CollectiveType, Collective,
                     PersonCollective, CollectivePlace, Genre, Language, Work, PersonWork, Edition, EditionLanguage,
                     PersonEdition, ReceptionSource, PersonReceptionSource, DocumentType, ReceptionType,
                     Reception, PersonReception, ReceptionReceptionType, ReceptionLanguage, ReceptionGenre,
                     WorkReception, EditionReception)

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


class PersonWorkInline(admin.TabularInline):
    model = PersonWork
    fields = [
        "person",
        "role",
        "work",
        "start_year",
        "end_year",
        "notes"
    ]
    extra = 0
    autocomplete_fields = ['work', 'person']


class PersonWorkInlineFromPersons(PersonWorkInline):
    verbose_name = "Work"


class PersonWorkInlineFromWorks(PersonWorkInline):
    verbose_name = "Person"


class PersonReceptionInline(admin.TabularInline):
    model = PersonReception
    fields = [
        "person",
        "role",
        "reception",
    ]
    autocomplete_fields = ['person', 'reception', 'role']
    extra = 0


class PersonReceptionInlineFromPerson(PersonReceptionInline):
    verbose_name = "Reception"


class PersonReceptionInlineFromReception(PersonReceptionInline):
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
    autocomplete_fields = ["collective"]
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
                           ("date_of_birth", "place_of_birth"), ("date_of_death", "place_of_death"),
                           "notes"],
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
               PersonWorkInlineFromPersons, PersonCollectiveInline, PersonReceptionInlineFromPerson]

    def view_on_site_link(self, obj):
        icon = '<img src="/static/admin/img/icon-viewlink.svg" alt="View on site" title="View on site">'
        return mark_safe(f'<a href="{obj.get_absolute_url()}">{icon}</i></a>')

admin.site.register(Education)


@admin.register(PersonEducation)
class PersonEducationAdmin(admin.ModelAdmin):
    autocomplete_fields = ['person']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(Profession)
class ProfessionAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(PersonProfession)
class PersonProfessionAdmin(admin.ModelAdmin):
    autocomplete_fields = ['person', 'profession']


admin.site.register(Religion)


@admin.register(PersonReligion)
class PersonReligionAdmin(admin.ModelAdmin):
    autocomplete_fields = ['person']

@admin.register(Marriage)
class MarriageAdmin(admin.ModelAdmin):
    autocomplete_fields = ['person', 'spouse']

@admin.register(AlternativeName)
class AlternativeNameAdmin(admin.ModelAdmin):
    autocomplete_fields = ['person']


@admin.register(PeriodOfResidence)
class PeriodOfResidenceAdmin(admin.ModelAdmin):
    search_fields = ['person__short_name', 'place__name']
    autocomplete_fields = ['person', 'place']


admin.site.register(CollectiveType)


@admin.register(Collective)
class CollectiveAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(PersonCollective)
class PersonCollectiveAdmin(admin.ModelAdmin):
    autocomplete_fields = ['person', 'collective']


admin.site.register(CollectivePlace)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    search_fields = ['name']


admin.site.register(Language)


class EditionInline(admin.StackedInline):
    model = Edition
    extra = 0
    autocomplete_fields = ['related_work', 'place_of_publication', 'genre']


class WorkReceptionInline(admin.TabularInline):
    model = WorkReception
    extra = 0
    fields = ['reception', 'type', 'work']
    autocomplete_fields = ['work', 'reception']


class WorkReceptionInlineFromWork(WorkReceptionInline):
    verbose_name = 'Reception'


class WorkReceptionInlineFromReception(WorkReceptionInline):
    verbose_name = 'Work'


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ['title', 'viaf_link']
    search_fields = ['title']

    inlines = [PersonWorkInlineFromWorks, EditionInline, WorkReceptionInlineFromWork]

    def viaf_link(self, obj):
        return mark_safe(f'<a href="{obj.viaf_work}">{obj.viaf_work}</a>')


@admin.register(PersonWork)
class PersonWorkRoleAdmin(admin.ModelAdmin):
    list_display = ["person", "role", "work"]
    list_display_links = ["person", "role", "work"]
    search_fields = ["person__short_name", "role__name", "work__title"]
    autocomplete_fields = ['work', 'person']


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    autocomplete_fields = ['related_work', 'place_of_publication', 'genre']


admin.site.register(EditionLanguage)
admin.site.register(PersonEdition)


@admin.register(ReceptionSource)
class ReceptionSourceAdmin(admin.ModelAdmin):
    search_fields = ['title_work']
    autocomplete_fields = ['work', 'part_of']


admin.site.register(PersonReceptionSource)


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    search_fields = ['type_of_document']


admin.site.register(ReceptionType)


class ReceptionReceptionTypeInline(admin.TabularInline):
    model = ReceptionReceptionType
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
    inlines = [PersonReceptionInlineFromReception, WorkReceptionInlineFromReception, ReceptionReceptionTypeInline, ReceptionLanguageInline,
               ReceptionGenreInline]


@admin.register(PersonReception)
class PersonReception(admin.ModelAdmin):
    search_fields = []
    autocomplete_fields = ['person', 'reception']


admin.site.register(ReceptionReceptionType)
admin.site.register(ReceptionLanguage)
admin.site.register(ReceptionGenre)