import json

import requests
from dataclasses import dataclass, astuple

from django.db.models import Q
from django.utils import html
from django.db import models
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.html import html_safe
from django.conf import settings
from django.urls import reverse
from django.utils import translation
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter
from django_admin_inline_paginator_plus.admin import TabularInlinePaginated
from django_select2.forms import HeavySelect2Widget

from .models import (Country, Place, Person, Education, PersonEducation, Role, Profession, PersonProfession, Religion,
                     PersonReligion, Marriage, AlternativeName, PeriodOfResidence, CollectiveType, Collective,
                     PersonCollective, CollectivePlace, Genre, Language, Work, PersonWork, Edition, EditionLanguage,
                     PersonEdition, DocumentType, ReceptionType,
                     Reception, PersonReception, ReceptionLanguage, ReceptionGenre,
                     WorkReception, EditionReception, PersonPersonRelation, RelationType, WorkLanguage, Circulation,
                     PersonCirculation, WorkCirculation, EditionCirculation, CirculationSource, CirculationSourceType,
                     PersonCirculationSource, PersonCirculationSourceRole)


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
    Mixin to remove the delete button (red x) from a related (FK or M2M) form field.
    Can be used for both XxxAdmin and XxxInline classes.
    """
    def _set_can_x_related(self, form, switches={}):
        relation_fields = [f.name for f in self.model._meta.get_fields()
                           if f.many_to_one or f.one_to_one or f.many_to_many]
        for field_name in (relation_fields & form.base_fields.keys()):
            for switch, value in switches.items():
                if hasattr(form.base_fields[field_name].widget, switch):
                    setattr(form.base_fields[field_name].widget, switch, value)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        self._set_can_x_related(form, {'can_delete_related': False})
        return form

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        self._set_can_x_related(formset.form, {'can_delete_related': False})
        return formset


@dataclass
class ApiInfo:
    obj: object
    model: models.Model
    model_field_name: str
    url_template: str
    api_name: str
    fill_field_name: str


class ApiSelectWidget(HeavySelect2Widget):
    css_class_name = 'django-select2 django-select2-apilink'
    js = 'js/apilink.js'

    def __init__(self, *args, **kwargs):
        self.api_info = kwargs.pop('api_info', None)
        super().__init__(*args, **kwargs)

    def render(self, *args, **kwargs):
        output =  super().render(*args, **kwargs)
        obj, model, model_field_name, url_template, api_name, fill_field_name = astuple(self.api_info)
        api_id, display_style = ("", "display: none") if not obj or not getattr(obj, model_field_name, None) \
                                else (html.escape(getattr(obj, model_field_name)), "")

        return output + mark_safe(f"""
            <div id='api_block_{model_field_name}' style="margin: 4px 0 0 10px;{display_style}">
                <a id="apilink_{model_field_name}" href="{url_template.format(api_id)}" target="_blank"
                 href_base="{url_template[:-2]}">
                    Show on {api_name}
                </a>
                <button class="button fill-button" id="fillbutton_{model_field_name}" data-fill-field-name="{fill_field_name}" 
                type="button">Fill in</button>
            </div>
            <div id='api_object_exists_{model_field_name}' style="display: none;" data-django-model="{model.__name__}">
                <p style="color: red; margin: .4em 1em 0em 1em">A {model.__name__} with this Wikidata ID already exists.</p>
            </div>
            <script src="{settings.STATIC_URL}{self.js}"></script>
        """)


class WikidataMixin:
    class Media:
        css = {
            'all': ('css/admin/wikidata_id.css', 'admin/css/vendor/select2/select2.css')
        }

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        api_info = ApiInfo(obj, self.model, 'wikidata_id', settings.WIKIDATA_URL, 'Wikidata',
                           fill_field_name=self.fill_field_name)

        if not obj:
            form.base_fields['wikidata_id'].widget = ApiSelectWidget(data_view='shewrote:wikidata', api_info=api_info)
            return form

        language_code = translation.get_language()
        api_key = settings.WIKIDATA_API_KEY
        response = requests.get(settings.WIKIDATA_LABEL_URL.format(obj.wikidata_id, language_code),
                                headers={'accept': 'application/json', 'Authorization': f'Bearer {api_key}',
                                         'User-Agent': 'https://shewrote.rich.ru.nl/'})
        text = f"""
            <div>
                <b>{str(response.json())}</b>
                <span style='color: dimgray; margin-left: auto; margin-right: 0'>{obj.wikidata_id}</span>
            </div>
        """

        form.base_fields['wikidata_id'].widget = ApiSelectWidget(data_view='shewrote:wikidata', api_info=api_info,
                                                                 choices=[(obj.wikidata_id, text)])
        return form

    def wikidata_link(self, obj):
        wikidata_id = html.escape(obj.wikidata_id)
        return mark_safe(f'<a href="https://www.wikidata.org/wiki/{wikidata_id}">{wikidata_id}</a>')


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
class CountryAdmin(WikidataMixin, PrettyOriginalDataMixin, ShewroteModelAdmin):
    search_fields = ["modern_country"]
    inlines = [PlaceInline]
    fill_field_name = 'country_wikidata'


class PersonPlaceOfBirthInline(TabularInlinePaginated, ReadOnlyInline):
    model = Person
    fk_name = 'place_of_birth'
    fields = ['short_name', 'year_of_birth', 'place_of_death', 'year_of_death']
    verbose_name = "Person born in this place"
    verbose_name_plural = "Persons born in this place"
    pagination_key = 'person_placeofbirth_inline'


class PersonPlaceOfDeathInline(TabularInlinePaginated, ReadOnlyInline):
    model = Person
    fk_name = 'place_of_death'
    fields = ['short_name', 'place_of_birth', 'year_of_birth', 'year_of_death']
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


class ReadOnlyCollectivePlaceInline(TabularInlinePaginated, ReadOnlyInline):
    model = CollectivePlace
    fk_name = 'place'
    fields = ['collective']
    pagination_key = 'collectiveplace_inline'
    verbose_name = 'Collective'


class ReadOnlyEditionPlaceInline(TabularInlinePaginated, ReadOnlyInline):
    model = Edition
    fields = ['related_work', 'place_of_publication', 'publication_year_start', 'publication_year_end']
    pagination_key = 'editionplace_inline'


@admin.register(Place)
class PlaceAdmin(WikidataMixin, PrettyOriginalDataMixin, ShewroteModelAdmin):
    search_fields = ["name"]
    inlines = [PersonPlaceOfBirthInline, PersonPlaceOfDeathInline, PeriodsOfResidenceInline,
               ReadOnlyCollectivePlaceInline, ReadOnlyEditionPlaceInline]
    autocomplete_fields = ['modern_country']
    fill_field_name = 'place_wikidata'
    exclude = ['cerl_id']

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


class CollectivePlaceInline(NoDeleteRelatedMixin, admin.TabularInline):
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


class PeriodsOfResidenceInline(NoDeleteRelatedMixin, admin.TabularInline):
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


class PersonWorkInline(NoDeleteRelatedMixin, admin.TabularInline):
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


class PersonReceptionInline(NoDeleteRelatedMixin, admin.TabularInline):
    model = PersonReception
    fields = [
        "person",
        "type",
        "reception",
    ]
    autocomplete_fields = ['person', 'reception', 'type']
    extra = 0


class PersonReceptionInlineFromPerson(PersonReceptionInline):
    verbose_name = "Reception of Person"
    verbose_name_plural = "Receptions of Person"


class PersonReceptionInlineFromReception(PersonReceptionInline):
    verbose_name = "Person"


class PersonCirculationInline(NoDeleteRelatedMixin, admin.TabularInline):
    model = PersonCirculation
    fields = [
        "person",
        "type",
        "circulation",
    ]
    autocomplete_fields = ['person', 'circulation', 'type']
    extra = 0


class PersonCirculationInlineFromPerson(PersonCirculationInline):
    verbose_name = "Circulation"


class PersonCirculationInlineFromCirculation(PersonCirculationInline):
    verbose_name = "Person"


class PersonProfessionInline(NoDeleteRelatedMixin, admin.TabularInline):
    model = PersonProfession
    fields = ["person", "profession", "start_year", "end_year", "notes"]
    extra = 0
    verbose_name = "Profession"


class PersonEducationInline(NoDeleteRelatedMixin, admin.TabularInline):
    model = PersonEducation
    fields = ["person", "education"]
    extra = 0
    verbose_name = "Education"


class PersonReligionInline(NoDeleteRelatedMixin, admin.TabularInline):
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
    fields = ['short_name', 'place_of_birth', 'year_of_birth', 'place_of_death', 'year_of_death']
    verbose_name = "Child"
    verbose_name_plural = "Children"
    pagination_key = 'childrenof_inline'

    def __init__(self, *args, **kwargs):
        self.fk_name = kwargs.pop('fk_name')
        super().__init__(*args, **kwargs)


@admin.register(Person)
class PersonAdmin(WikidataMixin, PrettyOriginalDataMixin, ShewroteModelAdmin):
    list_display = ["short_name", "first_name", "birth_name", "sex", "year_of_birth", "place_of_birth",
                    "year_of_death", "place_of_death", 'view_on_site_link']
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
               PersonWorkInlineFromPersons, PersonCollectiveInline,
               PersonReceptionInlineFromPerson, PersonCirculationInlineFromPerson]
    fill_field_name = 'person_wikidata'

    def get_inline_instances(self, request, obj=None):
        inline_instances = [inline(self.model, self.admin_site) for inline in self.inlines]
        if not obj:
            return inline_instances
        if obj.sex == Person.GenderChoices.FEMALE:
            return inline_instances + [ChildrenOfInline(self.model, self.admin_site, fk_name='mother')]
        if obj.sex == Person.GenderChoices.MALE:
            return inline_instances + [ChildrenOfInline(self.model, self.admin_site, fk_name='father')]
        return inline_instances

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (
                None,
                {
                    "fields": ["wikidata_id",
                               ("short_name", "viaf_or_cerl"),
                               ("first_name", "birth_name",),
                               "sex",
                               ("year_of_birth", "alternative_birth_date", "place_of_birth"),
                               ("year_of_death", "alternative_death_date", "place_of_death"),
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

    def get_search_results(self, request, queryset, search_term):
        short_name_q = Q()
        for word in search_term.split():
            short_name_q &= Q(short_name__unaccent__icontains=word)
        alternative_name_q = Q()
        for word in search_term.split():
            alternative_name_q &= Q(alternativename__alternative_name__unaccent__icontains=word)
        queryset = queryset.filter(short_name_q | alternative_name_q).distinct()
        return queryset, False


admin.site.register(Education)


@admin.register(PersonEducation)
class PersonEducationAdmin(ShewroteModelAdmin):
    autocomplete_fields = ['person']


class ReadOnlyPersonWorkRoleInline(TabularInlinePaginated, ReadOnlyInline):
    model = PersonWork
    fields = ['person', 'work']
    pagination_key = 'personworkrole_inline'
    verbose_name = 'Person work'


class ReadOnlyPersonEditionRoleInline(TabularInlinePaginated, ReadOnlyInline):
    model = PersonEdition
    fields = ['person', 'edition']
    pagination_key = 'personedition_inline'
    verbose_name = 'Person edition'


@admin.register(Role)
class RoleAdmin(ShewroteModelAdmin):
    search_fields = ['name']
    inlines = [ReadOnlyPersonWorkRoleInline, ReadOnlyPersonEditionRoleInline]


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


class PersonCollectiveInline(TabularInlinePaginated, ReadOnlyInline):
    model = PersonCollective
    fields = ['person']
    pagination_key = 'person_collective_inline'
    verbose_name = 'Person'


@admin.register(Collective)
class CollectiveAdmin(PrettyOriginalDataMixin, ShewroteModelAdmin):
    search_fields = ["name"]
    inlines = [CollectivePlaceInline, PersonCollectiveInline]

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ('pretty_original_data',)
        else:
            return ()


@admin.register(PersonCollective)
class PersonCollectiveAdmin(ShewroteModelAdmin):
    autocomplete_fields = ['person', 'collective']


@admin.register(CollectivePlace)
class CollectivePlaceAdmin(ShewroteModelAdmin):
    pass


class ReadOnlyEditionGenreInline(TabularInlinePaginated, ReadOnlyInline):
    model = Edition
    fields = ['related_work', 'place_of_publication', 'publication_year_start', 'publication_year_end']
    pagination_key = 'readonly_editiongenre_inline'
    verbose_name = 'edition'


@admin.register(Genre)
class GenreAdmin(ShewroteModelAdmin):
    search_fields = ['name']
    inlines = [ReadOnlyEditionGenreInline]


class ReadOnlyWorkLanguageInline(TabularInlinePaginated, ReadOnlyInline):
    model = WorkLanguage
    fields = ['work']
    pagination_key = 'readonly_worklanguage_inline'
    verbose_name = 'work'


class ReadOnlyEditionLanguageInline(TabularInlinePaginated, ReadOnlyInline):
    model = EditionLanguage
    fields = ['edition']
    pagination_key = 'readonly_editionlanguage_inline'
    verbose_name = 'edition'


class ReadOnlyReceptionLanguageInline(TabularInlinePaginated, ReadOnlyInline):
    model = ReceptionLanguage
    fields = ['reception']
    pagination_key = 'readonly_receptionlanguage_inline'
    verbose_name = 'reception'


@admin.register(Language)
class LanguageAdmin(ShewroteModelAdmin):
    search_fields = ['name']
    inlines = [ReadOnlyWorkLanguageInline, ReadOnlyEditionLanguageInline, ReadOnlyReceptionLanguageInline]


class EditionInline(NoDeleteRelatedMixin, admin.StackedInline):
    model = Edition
    extra = 0
    autocomplete_fields = ['related_work', 'place_of_publication', 'genre']


class WorkLanguageInline(NoDeleteRelatedMixin, admin.TabularInline):
    model = WorkLanguage
    extra = 0
    fields = ['work', 'language']
    autocomplete_fields = ['language']


class WorkReceptionInline(NoDeleteRelatedMixin, admin.TabularInline):
    model = WorkReception
    extra = 0
    fields = ['reception', 'type', 'work']
    autocomplete_fields = ['work', 'reception']


class WorkReceptionInlineFromWork(WorkReceptionInline):
    verbose_name = 'Reception'


class WorkReceptionInlineFromReception(WorkReceptionInline):
    verbose_name = 'Received work'


class WorkCirculationInline(NoDeleteRelatedMixin, admin.TabularInline):
    model = WorkCirculation
    extra = 0
    fields = ['circulation', 'type', 'work']
    autocomplete_fields = ['work', 'circulation']


class WorkCirculationInlineFromWork(WorkCirculationInline):
    verbose_name = 'Circulation'


class WorkCirculationInlineFromCirculation(WorkCirculationInline):
    verbose_name = 'Received work'


@admin.register(Work)
class WorkAdmin(PrettyOriginalDataMixin, ShewroteModelAdmin):
    list_display = ['title', 'viaf_link']
    search_fields = ['title']

    inlines = [WorkLanguageInline, PersonWorkInlineFromWorks, EditionInline,
               WorkReceptionInlineFromWork, WorkCirculationInlineFromWork]

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


class PersonEditionInline(TabularInlinePaginated):
    model = PersonEdition
    fields = ['person', 'edition', 'role']
    autocomplete_fields = ['person']


@admin.register(Edition)
class EditionAdmin(ShewroteModelAdmin):
    search_fields = ['related_work__title']
    autocomplete_fields = ['related_work', 'place_of_publication', 'genre']
    inlines = [PersonEditionInline]


admin.site.register(EditionLanguage)


@admin.register(PersonEdition)
class PersonEditionAdmin(ShewroteModelAdmin):
    autocomplete_fields = ['person', 'edition', 'role']


@admin.register(DocumentType)
class DocumentTypeAdmin(ShewroteModelAdmin):
    search_fields = ['type_of_document']


class ReadOnlyPersonReceptionInline(TabularInlinePaginated, ReadOnlyInline):
    model = PersonReception
    fields = ['reception', 'person']
    pagination_key = 'personreception_inline'
    verbose_name = 'Person reception'


class ReadOnlyWorkReceptionInline(TabularInlinePaginated, ReadOnlyInline):
    model = WorkReception
    fields = ['reception', 'work']
    pagination_key = 'workreception_inline'
    verbose_name = 'Work reception'


class ReadOnlyEditionReceptionInline(TabularInlinePaginated, ReadOnlyInline):
    model = EditionReception
    fields = ['reception', 'edition']
    pagination_key = 'editionreception_inline'
    verbose_name = 'Edition reception'


@admin.register(ReceptionType)
class ReceptionTypeAdmin(ShewroteModelAdmin):
    search_fields = ['type_of_reception']
    inlines = [ReadOnlyPersonReceptionInline, ReadOnlyWorkReceptionInline, ReadOnlyEditionReceptionInline]


class ReceptionLanguageInline(NoDeleteRelatedMixin, admin.TabularInline):
    model = ReceptionLanguage
    fields = ["reception", "language"]
    extra = 0
    verbose_name = "Language"


class ReceptionGenreInline(NoDeleteRelatedMixin, admin.TabularInline):
    model = ReceptionGenre
    fields = ["reception", "genre"]
    extra = 0
    verbose_name = "Genre"


@html_safe
class FillReceptionJSPath:
    def __str__(self):
        uuid_dummy = '00000000-0000-0000-0000-000000000000'
        work_info_url = reverse('shewrote:work_info', args=[uuid_dummy])
        return f"""
        <script>
            var uuid_dummy = '{uuid_dummy}';
            var work_info_url = "{work_info_url}";
        </script>
        <script src="{settings.STATIC_URL}js/fill_reception.js" defer></script>
        """


@admin.register(Reception)
class ReceptionAdmin(PrettyOriginalDataMixin, ShewroteModelAdmin):
    list_display = ['title', 'reference']
    list_display_links = ['title', 'reference']
    search_fields = ['title', 'reference']
    autocomplete_fields = [
        'is_same_as_work',
        'part_of_work',
        'place_of_reception',
        'document_type',
    ]
    inlines = [PersonReceptionInlineFromReception, WorkReceptionInlineFromReception, ReceptionLanguageInline,
               ReceptionGenreInline]

    class Media:
        js = [FillReceptionJSPath()]

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (
                None,
                {
                    "fields": [
                        ("is_same_as_work", "part_of_work"),
                        "title",
                        "reference",
                        "document_type",
                        ("place_of_reception", "date_of_reception"),
                        ("quotation", "url", "viaf_work"),
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


@admin.register(CirculationSourceType)
class CirculationSourceTypeAdmin(ShewroteModelAdmin):
    search_fields = ["name"]


@admin.register(PersonCirculationSourceRole)
class PersonCirculationSourceRoleAdmin(ShewroteModelAdmin):
    search_fields = ["name"]


class PersonCirculationSourceInline(admin.TabularInline):
    model = PersonCirculationSource
    fields = ["person", "circulation_source", "role"]
    autocomplete_fields = ["person", "role"]
    extra = 0
    verbose_name = "Person"


@admin.register(CirculationSource)
class CirculationSourceAdmin(ShewroteModelAdmin):
    search_fields = ["full_title"]
    autocomplete_fields = ["type", "country_of_publication"]
    inlines = [PersonCirculationSourceInline]


@admin.register(Circulation)
class CirculationAdmin(PrettyOriginalDataMixin, ShewroteModelAdmin):
    list_display = ['title', 'reference']
    list_display_links = ['title', 'reference']
    search_fields = ['title', 'reference']
    autocomplete_fields = [
        'place_of_reception',
        'document_type',
        'source',
    ]
    inlines = [PersonCirculationInlineFromCirculation, WorkCirculationInlineFromCirculation]

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (
                None,
                {
                    "fields": [
                        "title",
                        "shelf_mark",
                        "reference",
                        "document_type",
                        ("place_of_reception", "date_of_reception"),
                        ("quotation", "url", "viaf_work"),
                        "image",
                        "source",
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

