import json
from django.contrib import admin
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter
from django_admin_inline_paginator_plus.admin import TabularInlinePaginated

from .models import (Country, Place, Person, Education, PersonEducation, Role, Profession, PersonProfession, Religion,
                     PersonReligion, Marriage, AlternativeName, PeriodOfResidence, CollectiveType, Collective,
                     PersonCollective, CollectivePlace, Genre, Language, Work, PersonWork, Edition, EditionLanguage,
                     PersonEdition, ReceptionSource, PersonReceptionSource, DocumentType, ReceptionType,
                     Reception, PersonReception, ReceptionLanguage, ReceptionGenre,
                     WorkReception, EditionReception, PersonPersonRelation, RelationType, WorkLanguage)


def pretty_json(self, instance, field_name):
    """Function to display pretty version of our data"""
    json_data = getattr(instance, field_name)
    json_string = json.dumps(json_data, ensure_ascii=False, indent=2) if json_data else ''
    formatter = HtmlFormatter(style='colorful')
    response = highlight(json_string, JsonLexer(), formatter)
    scroll_style = ".highlight { height: 20em; overflow: scroll; border: 1px solid lightgray; resize: both; min-width: 30em; } "
    style = "<style>" + scroll_style + formatter.get_style_defs() + "</style><br>"
    return mark_safe(style + response)


class PrettyOriginalDataMixin:
    def pretty_original_data(self, instance):
        return pretty_json(self, instance, 'original_data')

    pretty_original_data.short_description = 'Original data'


class NoDeleteRelatedMixin:
    """
    Mixin to remove the delete button (red x) from a related (FK or M2M) form field
    """
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        no_delete_fields = getattr(self, 'no_delete_fields', [f.name for f in self.model._meta.get_fields()
                                                              if f.many_to_one or f.one_to_one or f.many_to_many])
        for field_name in (no_delete_fields & form.base_fields.keys()):
                form.base_fields[field_name].widget.can_delete_related = False
        return form


class ReadOnlyInline(admin.TabularInline):
    max_num = 0
    can_delete = False
    show_change_link = True

    def get_readonly_fields(self, request, obj=None):
        return self.fields


class ShewroteModelAdmin(NoDeleteRelatedMixin, admin.ModelAdmin):
    pass


class PlaceInline(TabularInlinePaginated, ReadOnlyInline):
    model = Place
    fields = ["name"]
    pagination_key = 'place_inline'


@admin.register(Country)
class CountryAdmin(PrettyOriginalDataMixin, ShewroteModelAdmin):
    search_fields = ["modern_country"]
    inlines = [PlaceInline]


class PersonPlaceOfBirthInline(TabularInlinePaginated, ReadOnlyInline):
    model = Person
    fk_name = 'place_of_birth'
    fields = ['short_name', 'date_of_birth', 'place_of_death', 'date_of_death']
    verbose_name = "Person born in this place"
    verbose_name_plural = "Persons born in this place"
    pagination_key = 'person_placeofbirth_inline'


class PersonPlaceOfDeathInline(TabularInlinePaginated, ReadOnlyInline):
    model = Person
    fk_name = 'place_of_death'
    fields = ['short_name', 'place_of_birth', 'date_of_birth', 'date_of_death']
    verbose_name = "Person died in this place"
    verbose_name_plural = "Persons died in this place"
    pagination_key = 'person_placeofdeath_inline'


class PeriodsOfResidenceInline(TabularInlinePaginated, ReadOnlyInline):
    model = PeriodOfResidence
    fk_name = 'place'
    fields = ['person', 'start_year', 'end_year']
    verbose_name = 'Period of residence'
    verbose_name_plural = 'Periods of residence'
    pagination_key = 'periodofresidence_inline'


class CollectivePlaceInline(TabularInlinePaginated, ReadOnlyInline):
    model = CollectivePlace
    fk_name = 'place'
    fields = ['collective']
    pagination_key = 'collectiveplace_inline'


@admin.register(Place)
class PlaceAdmin(PrettyOriginalDataMixin, ShewroteModelAdmin):
    search_fields = ["name"]
    inlines = [PersonPlaceOfBirthInline, PersonPlaceOfDeathInline, PeriodsOfResidenceInline, CollectivePlaceInline]

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ('pretty_original_data',)
        else:
            return ()


class AlternativeNameInline(admin.TabularInline):
    model = AlternativeName
    fields = [
        "alternative_name",
        "start_year",
        "end_year",
        "notes"
    ]
    extra = 0


class CollectivePlaceInline(admin.TabularInline):
    model = CollectivePlace
    fields = ["collective", "place"]
    autocomplete_fields = ["collective", "place"]
    extra = 0
    verbose_name = "Place"


class MarriageInline(admin.TabularInline):
    model = Marriage
    fk_name = "person"
    fields = ["marital_status", "person", "spouse", "married_name", "start_year", "end_year", "notes"]
    extra = 0
    autocomplete_fields = ["person", "spouse"]


class PersonPersonRelationInline(admin.TabularInline):
    model = PersonPersonRelation
    fk_name = "from_person"
    fields = ["from_person", "types", "to_person"]
    extra = 0
    autocomplete_fields = ["from_person", "types", "to_person"]
    verbose_name = "Relation"


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
        "type",
        "reception",
    ]
    autocomplete_fields = ['person', 'reception', 'type']
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


class ChildrenOfInline(TabularInlinePaginated, ReadOnlyInline):
    model = Person
    fields = ['short_name', 'place_of_birth', 'date_of_birth', 'place_of_death', 'date_of_death']
    verbose_name = "Child"
    verbose_name_plural = "Children"
    pagination_key = 'childrenof_inline'

    def __init__(self, *args, **kwargs):
        self.fk_name = kwargs.pop('fk_name')
        super().__init__(*args, **kwargs)


@admin.register(Person)
class PersonAdmin(PrettyOriginalDataMixin, ShewroteModelAdmin):
    list_display = ["short_name", "first_name", "birth_name", "sex", "date_of_birth", "place_of_birth",
                    "date_of_death", "place_of_death", "notes", 'view_on_site_link']
    search_fields = ['short_name']
    ordering = ['short_name']
    list_filter = ["sex", "place_of_birth__modern_country__modern_country"]
    autocomplete_fields = [
        "place_of_birth",
        "place_of_death",
        "mother",
        "father",
    ]
    inlines = [MarriageInline, PersonPersonRelationInline,
               PersonEducationInline, PersonProfessionInline, PersonReligionInline,
               AlternativeNameInline, PeriodsOfResidenceInline,
               PersonWorkInlineFromPersons, PersonCollectiveInline, PersonReceptionInlineFromPerson]

    def get_inline_instances(self, request, obj=None):
        inline_instances = [inline(self.model, self.admin_site) for inline in self.inlines]
        if obj.sex == Person.GenderChoices.FEMALE:
            inline_instances.append(ChildrenOfInline(self.model, self.admin_site, fk_name='mother'))
        elif obj.sex == Person.GenderChoices.MALE:
            inline_instances.append(ChildrenOfInline(self.model, self.admin_site, fk_name='father'))
        return inline_instances

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (
                None,
                {
                    "fields": [("short_name", "viaf_or_cerl"),
                               ("first_name", "birth_name",),
                               ("date_of_birth", "place_of_birth"),
                               ("date_of_death", "place_of_death"),
                               "notes"],
                },
            ),
            (
                "Parents", {"fields": [("mother", "father")]}
            ),
            (
                "Professional",
                {
                    "fields": [("aristocratic_title", "professional_ecclesiastic_title"),
                               ("flourishing_start", "flourishing_end"),
                               "bibliography"]
                }
            )
        ]
        if request.user.is_superuser:
            fieldsets[0][1]['fields'].append('pretty_original_data')
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ('pretty_original_data',)
        else:
            return ()

    def view_on_site_link(self, obj):
        icon = '<img src="/static/admin/img/icon-viewlink.svg" alt="View on site" title="View on site">'
        return mark_safe(f'<a href="{obj.get_absolute_url()}">{icon}</i></a>')


admin.site.register(Education)


@admin.register(PersonEducation)
class PersonEducationAdmin(ShewroteModelAdmin):
    autocomplete_fields = ['person']


@admin.register(Role)
class RoleAdmin(ShewroteModelAdmin):
    search_fields = ['name']


@admin.register(Profession)
class ProfessionAdmin(ShewroteModelAdmin):
    search_fields = ['name']


@admin.register(PersonProfession)
class PersonProfessionAdmin(ShewroteModelAdmin):
    autocomplete_fields = ['person', 'profession']


admin.site.register(Religion)


@admin.register(PersonReligion)
class PersonReligionAdmin(ShewroteModelAdmin):
    autocomplete_fields = ['person']


@admin.register(Marriage)
class MarriageAdmin(ShewroteModelAdmin):
    autocomplete_fields = ['person', 'spouse']


@admin.register(PersonPersonRelation)
class PersonPersonRelation(ShewroteModelAdmin):
    fields = ['from_person', 'types', 'to_person']
    autocomplete_fields = ['from_person', 'types', 'to_person']


@admin.register(RelationType)
class RelationType(ShewroteModelAdmin):
    autocomplete_fields = ['reverse']
    search_fields = ['text']


@admin.register(AlternativeName)
class AlternativeNameAdmin(ShewroteModelAdmin):
    autocomplete_fields = ['person']


@admin.register(PeriodOfResidence)
class PeriodOfResidenceAdmin(ShewroteModelAdmin):
    search_fields = ['person__short_name', 'place__name']
    autocomplete_fields = ['person', 'place']


admin.site.register(CollectiveType)


@admin.register(Collective)
class CollectiveAdmin(PrettyOriginalDataMixin, ShewroteModelAdmin):
    search_fields = ["name"]
    inlines = [CollectivePlaceInline]

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ('pretty_original_data',)
        else:
            return ()


@admin.register(PersonCollective)
class PersonCollectiveAdmin(ShewroteModelAdmin):
    autocomplete_fields = ['person', 'collective']


admin.site.register(CollectivePlace)


@admin.register(Genre)
class GenreAdmin(ShewroteModelAdmin):
    search_fields = ['name']


@admin.register(Language)
class LanguageAdmin(ShewroteModelAdmin):
    search_fields = ['name']


class EditionInline(admin.StackedInline):
    model = Edition
    extra = 0
    autocomplete_fields = ['related_work', 'place_of_publication', 'genre']


class WorkLanguageInline(admin.TabularInline):
    model = WorkLanguage
    extra = 0
    fields = ['work', 'language']
    autocomplete_fields = ['language']


class WorkReceptionInline(admin.TabularInline):
    model = WorkReception
    extra = 0
    fields = ['reception', 'type', 'work']
    autocomplete_fields = ['work', 'reception']


class WorkReceptionInlineFromWork(WorkReceptionInline):
    verbose_name = 'Reception'


class WorkReceptionInlineFromReception(WorkReceptionInline):
    verbose_name = 'Received work'


@admin.register(Work)
class WorkAdmin(PrettyOriginalDataMixin, ShewroteModelAdmin):
    list_display = ['title', 'viaf_link']
    search_fields = ['title']

    inlines = [WorkLanguageInline, PersonWorkInlineFromWorks, EditionInline, WorkReceptionInlineFromWork]

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ('pretty_original_data',)
        else:
            return ()

    def viaf_link(self, obj):
        return mark_safe(f'<a href="{obj.viaf_work}">{obj.viaf_work}</a>')


@admin.register(PersonWork)
class PersonWorkAdmin(ShewroteModelAdmin):
    list_display = ["person", "role", "work"]
    list_display_links = ["person", "role", "work"]
    search_fields = ["person__short_name", "role__name", "work__title"]
    autocomplete_fields = ['work', 'person']


@admin.register(Edition)
class EditionAdmin(ShewroteModelAdmin):
    search_fields = ['related_work__title']
    autocomplete_fields = ['related_work', 'place_of_publication', 'genre']


admin.site.register(EditionLanguage)


@admin.register(PersonEdition)
class PersonEditionAdmin(ShewroteModelAdmin):
    autocomplete_fields = ['person', 'edition', 'role']


@admin.register(ReceptionSource)
class ReceptionSourceAdmin(ShewroteModelAdmin):
    search_fields = ['title_work']
    autocomplete_fields = ['work', 'part_of']


admin.site.register(PersonReceptionSource)


@admin.register(DocumentType)
class DocumentTypeAdmin(ShewroteModelAdmin):
    search_fields = ['type_of_document']


@admin.register(ReceptionType)
class ReceptionTypeAdmin(ShewroteModelAdmin):
    search_fields = ['type_of_reception']


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
class ReceptionAdmin(PrettyOriginalDataMixin, ShewroteModelAdmin):
    list_display = ['title', 'reference']
    list_display_links = ['title', 'reference']
    search_fields = ['title', 'reference']
    autocomplete_fields = [
        'source',
        'is_same_as_work',
        'part_of_work',
        'place_of_reception',
        'document_type',
    ]
    inlines = [PersonReceptionInlineFromReception, WorkReceptionInlineFromReception, ReceptionLanguageInline,
               ReceptionGenreInline]

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (
                None,
                {
                    "fields": [
                        "title",
                        ("source", "is_same_as_work", "part_of_work"),
                        "reference",
                        "document_type",
                        ("place_of_reception", "date_of_reception"),
                        ("quotation_reception", "url", "viaf_work"),
                        "image",
                        "notes",
                    ],
                },
            ),
        ]
        if request.user.is_superuser:
            fieldsets[0][1]['fields'].append('pretty_original_data')
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ('pretty_original_data',)
        else:
            return ()


@admin.register(PersonReception)
class PersonReception(ShewroteModelAdmin):
    search_fields = []
    autocomplete_fields = ['person', 'reception']


admin.site.register(ReceptionLanguage)
admin.site.register(ReceptionGenre)
