import html
import re

import requests
from requests import Response

from django.utils import translation
from django.apps import apps
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q, OuterRef, Subquery, QuerySet, Count, Max, Min
from django.conf import settings
from django.contrib import messages

from .apps import ShewroteConfig
from .models import (Person, Work, Reception, WorkReception, PersonReception, Collective, Country, Place,
                     PersonPersonRelation, Edition, PersonCirculation)
from .forms import PersonForm, PersonSearchForm, ShortPersonForm, WorkForm, ChangesSearchForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from .models import Person, Work, Reception, WorkReception, Circulation, WorkCirculation
from .forms import PersonForm, ShortPersonForm, WorkForm, MergeUsersForm, WorkSearchForm, ReceptionSearchForm

from dal import autocomplete
from django.http import JsonResponse, Http404
from django.template.exceptions import TemplateDoesNotExist
from django.utils.html import escape
from apiconnectors.viafapi import ViafAPI
from easyaudit.models import CRUDEvent
from django_select2.views import AutoResponseView

from .wikidata_api import get_wikidata_statements, get_wikidata_label
from .utils import get_nested_object

from collections import OrderedDict

# Create your views here.
def index(request):
    """The home page for SHEWROTE."""
    return render(request, 'shewrote/index.html')


def pages(request, page):
    try:
        return render(request, f'shewrote/pages/{page}.html')
    except TemplateDoesNotExist:
        raise Http404


def get_int_slider_info(request, qs, field_name, search_field_names):
    min = qs.model.objects.aggregate(Min(field_name))[field_name+'__min']
    max = qs.model.objects.aggregate(Max(field_name))[field_name+'__max']

    start = request.GET.get(search_field_names[0], '') or min
    end = request.GET.get(search_field_names[1], '') or max

    print(start, end)

    is_checked = request.GET.get(field_name+'_checkbox', 'off') == 'on'
    if is_checked:
        qs = qs.filter(**{field_name+'__gte': start, field_name+'__lte': end})

    return qs, {'min': min, 'max': max, 'start': start, 'end': end, 'is_checked': is_checked}


class CountryAndPlaceAutocompleteView(AutoResponseView):
    page_size = 10

    country_qs = Country.objects.all()
    place_qs = Place.objects.all()

    def get(self, request, *args, **kwargs):
        term = request.GET.get('term', '')
        page = int(request.GET.get('page', 1))
        begin = (page - 1) * self.page_size / 2
        end = page * self.page_size / 2

        countries = ('country', self.country_qs.filter(modern_country__icontains=term).distinct()
                     .order_by('modern_country')[begin:end])
        places = ('place', self.place_qs.exclude(is_country=True, modern_country__isnull=False)
                  .filter(name__icontains=term).distinct()
                  .order_by('name')[begin:end])

        results: list = []
        for name, qs in [countries, places]:
            results.extend([
                {'id': f"{name}|{obj.pk}", 'text': f"{obj}{' ('+name+')' if name != 'place' else ''}" }
                for obj in qs
            ])

        more = True
        if countries[1].count() != self.page_size/2 and places[1].count() != self.page_size/2:
            more = False

        return JsonResponse({
            'results': results,
            'more': more
        })


class CountryAndPlaceAutocompleteViewForWorks(CountryAndPlaceAutocompleteView):
    page_size = 10

    country_qs = Country.objects.annotate(edition_count=Count('places__edition')).filter(edition_count__gt=0)
    place_qs = Place.objects.annotate(edition_count=Count('edition')).filter(edition_count__gt=0)


def get_country_or_place_q(filter, qs_filter_prefix: str) -> Q:
    if not filter:
        return Q()
    countries = [obj for obj in filter if isinstance(obj, Country)]
    places = [obj for obj in filter if isinstance(obj, Place)]
    return Q(**{qs_filter_prefix + '__in':places}) | Q(**{qs_filter_prefix+'__modern_country__in':countries})


def filter_persons_with_form(persons: QuerySet[Person], search_form: PersonSearchForm) -> QuerySet[Person]:
    """
    Filter Person objects using a valid instance of PersonSearchForm
    :param persons: a QuerySet of Persons to filter
    :param search_form: a valid instance of PersonSearchForm
    :return: a QuerySet of Person
    """
    if sex_filter := search_form.cleaned_data['sex']:
        persons = persons.filter(sex__in=sex_filter)

    country_or_place_of_birth_q = get_country_or_place_q(search_form.cleaned_data['country_or_place_of_birth'], 'place_of_birth')
    country_or_place_of_death_q = get_country_or_place_q(search_form.cleaned_data['country_or_place_of_death'], 'place_of_death')
    country_or_place_of_residence_q = get_country_or_place_q(search_form.cleaned_data['country_or_place_of_residence'], 'periodofresidence__place')
    persons = persons.filter(country_or_place_of_birth_q | country_or_place_of_death_q | country_or_place_of_residence_q)
        
    return persons


def persons(request):
    """Show all persons."""
    persons = Person.objects.all()

    order_by_options = OrderedDict([
        ('short_name', 'Short name'),
        ('-reception_count', ('Reception count (persons)', True)),
        ('-reception_count_incl_works', ('Reception count (persons and works)', True)),
    ])
    persons, order_by_context = order_queryset(persons, request.GET.dict(), order_by_options,
                                               '-reception_count_incl_works', ['short_name'])

    short_name_filter = request.GET.get("short_name", '')
    if short_name_filter:
        short_name_q = Q()
        for word in short_name_filter.split():
            short_name_q &= Q(short_name__unaccent__icontains=word)
        alternative_name_q = Q()
        for word in short_name_filter.split():
            alternative_name_q &= Q(alternativename__alternative_name__unaccent__icontains=word)
        persons = persons.filter(short_name_q | alternative_name_q).distinct()

    search_form = PersonSearchForm(request.GET)
    if search_form.is_valid():
        persons = filter_persons_with_form(persons, search_form)

    persons, birth_year_slider_info = get_int_slider_info(request, persons, 'normalised_date_of_birth',
                                                           ['birth_year_start', 'birth_year_end'])

    persons, death_year_slider_info = get_int_slider_info(request, persons, 'normalised_date_of_death',
                                                           ['death_year_start', 'death_year_end'])

    receptions = (Reception.objects.filter(personreception__person_id=OuterRef('pk'), image__isnull=False,
                                           personreception__type__type_of_reception=settings.PORTRAIT_TYPE)
                  .exclude(image='').values('image'))
    persons = persons.annotate(image=Subquery(receptions[:1]))

    persons = persons.prefetch_related('alternativename_set', 'place_of_birth', 'place_of_death')

    paginator = Paginator(persons, 25)
    page_number = request.GET.get("page")
    paginated_persons = paginator.get_page(page_number)
    context = {'persons': paginated_persons, 'count': paginator.count, 'short_name': short_name_filter,
               'birth_year_slider_info': birth_year_slider_info,
               'death_year_slider_info': death_year_slider_info,
               'search_form': search_form} | order_by_context
    return render(request, 'shewrote/persons.html', context)


def person(request, person_id):
    """Show a single person and all their details."""
    person = Person.objects.get(id=person_id)
    person_receptions = (PersonReception.objects.filter(person=person)
                         .prefetch_related('type', 'reception__is_same_as_work__personwork_set'))
    person_receptions_with_image = (person_receptions.filter(reception__image__isnull=False,
                                                             type__type_of_reception=settings.PORTRAIT_TYPE)
                                    .exclude(reception__image=""))
    reception_with_image = person_receptions_with_image.first().reception if person_receptions_with_image else None
    
    person_circulations = (PersonCirculation.objects.filter(person=person).prefetch_related('type'))
    relations = PersonPersonRelation.objects.filter(from_person=person)

    context = {
        'person': person,
        'is_creator_of': person.get_works_for_role("is creator of",
                count_relations=['workreception__reception', 'workcirculation__circulation'])
            .order_by('date_of_publication_start'),
        'is_editor_of': person.get_works_for_role("is editor of",
                count_relations=['workreception__reception', 'workcirculation__circulation'])
            .order_by('date_of_publication_start'),
        'is_copyist_of': person.get_works_for_role("is copyist of",
                count_relations=['workreception__reception', 'workcirculation__circulation'])
            .order_by('date_of_publication_start'),
        'is_illustrator_of': person.get_works_for_role("is illustrator of",
                count_relations=['workreception__reception', 'workcirculation__circulation'])
            .order_by('date_of_publication_start'),
        'is_translator_of': person.get_works_for_role("is translator of",
                count_relations=['workreception__reception', 'workcirculation__circulation'])
            .order_by('date_of_publication_start'),
        'has_biography': person.get_works_for_role("has biography"),
        'is_commented_on_in': person.get_works_for_role("is commented on in"),
        'is_mentioned_in': person.get_works_for_role("is mentioned in"),
        'is_referenced_in': person.get_works_for_role("is referenced in"),
        'reception_with_image': reception_with_image,
        'relations': relations,
        'person_receptions': person_receptions.order_by('reception__date_of_reception'),
        'person_circulations': person_circulations.order_by('circulation__date_of_reception')
    }
    return render(request, 'shewrote/person_details.html', context)


@login_required
def new_person(request):
    """Add a new person."""
    if request.method != 'POST':
        # No data submitted, create a blank form
        form = PersonForm()
    else:
        # Process the POST data
        form = PersonForm(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('shewrote:persons')

    # Display a blank or invalid form
    context = {'form': form}
    return render(request, 'shewrote/new_person.html', context)


@login_required
def short_new_person(request):
    """Add a new person."""
    if request.method != 'POST':
        # No data submitted, create a blank form
        form = ShortPersonForm()
    else:
        # Process the POST data
        form = PersonForm(data=request.POST)
        if form.is_valid():
            object = form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                data = {
                    'pk': object.pk,
                    'short_name': object.short_name,
                }
                return JsonResponse(data)
            return redirect('shewrote:persons')

    # Display a blank or invalid form
    context = {'form': form}
    return render(request, 'shewrote/new_person.html', context)



@login_required
def edit_person(request, person_id):
    """Edit an existing person."""
    entry = Person.objects.get(id=person_id)

    if request.method != 'POST':
        # Initial request, pre-fill form with the current person.
        form = PersonForm(instance=entry)
    else:
        # POST data submitted; process data.
        form = PersonForm(instance=entry, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('shewrote:person', person_id=entry.id)

    context = {
        'person': entry,
        'form': form,
        'addanother_person_form': ShortPersonForm()
    }
    return render(request, 'shewrote/edit_person.html', context)


def collectives(request):
    """Show all persons."""
    collectives = Collective.objects.order_by('name')
    name_filter = request.GET.get("name", '')
    if name_filter:
        collectives = collectives.filter(name__unaccent__icontains=name_filter).distinct()
    paginator = Paginator(collectives, 25)
    page_number = request.GET.get("page")
    paginated_collectives = paginator.get_page(page_number)
    context = {'collectives': paginated_collectives, 'count': collectives.count(), 'name': name_filter}
    return render(request, 'shewrote/collectives.html', context)


def collective(request, collective_id):
    """Show a single collective and all its details."""
    collective = Collective.objects.get(id=collective_id)
    context = {
        'collective': collective,
    }
    return render(request, 'shewrote/collective_details.html', context)


def order_queryset(qs: QuerySet, get_params: dict, order_by_options: OrderedDict, default_option: str,
                   secondary_order_bys: list=None) \
        -> tuple[QuerySet, dict]:
    """
    Orders the given Queryset and returns it with a dict containing context variables to be used in the template
    :param qs: QuerySet to order
    :param get_params: parameters in the GET request
    :param order_by_options: options the user can choose from
    :param default_option: the default option if none is selected
    :return: ordered QuerySet and a dict with context variables
    """
    order_by: str = get_params.pop('order_by', default_option)
    if order_by not in order_by_options.keys():
        order_by = default_option
    order_by_option = order_by_options[order_by]

    # Get Queryset annotate function if there is one
    order_by_annotate_field = None
    if isinstance(order_by_option, tuple):
        current_order_by_label, show_order_by_annotate_field = order_by_option
        if show_order_by_annotate_field:
            order_by_annotate_field = order_by[1:] if order_by.startswith('-') else order_by
    else:
        current_order_by_label: str = order_by_option

    for option, label in order_by_options.items():
        if isinstance(label, tuple):
            label = label[0]
            order_by_options[option] = label

    secondary_order_bys = secondary_order_bys if secondary_order_bys is not None else []
    if order_by.startswith('-'):
        qs: QuerySet = qs.order_by(F(order_by[1:]).desc(nulls_last=True), *secondary_order_bys)
    else:
        qs: QuerySet = qs.order_by(F(order_by).asc(nulls_last=True), *secondary_order_bys)

    get_params_str: str = '&'.join( f'{key}={value}' for key, value in get_params.items())
    return qs, {'order_by': order_by, 'order_by_options': order_by_options,
                'current_order_by_label': current_order_by_label, 'get_params': get_params_str,
                'order_by_annotate_field': order_by_annotate_field}


def filter_receptions_with_form(receptions: QuerySet[Work], search_form: WorkSearchForm) -> QuerySet[Work]:
    if title_filter := search_form.cleaned_data['title']:
        receptions = receptions.filter(title__unaccent__icontains=title_filter)

    if received_works_filter := search_form.cleaned_data['received_works']:
        receptions = receptions.filter(received_works__in=received_works_filter)

    if received_persons_filter := search_form.cleaned_data['received_persons']:
        receptions = receptions.filter(received_persons__in=received_persons_filter)

    if persons_receiving_filter := search_form.cleaned_data['persons_receiving']:
        receptions = receptions.filter(is_same_as_work__personwork__role__name='is creator of',
                                       is_same_as_work__related_persons__in=persons_receiving_filter)

    if receiving_persons_gender_filter := search_form.cleaned_data['receiving_persons_gender']:
        receptions = receptions.filter(is_same_as_work__personwork__role__name='is creator of',
                                       is_same_as_work__related_persons__sex__in=receiving_persons_gender_filter)

    if type_filter := search_form.cleaned_data['type']:
        receptions = receptions.filter(personreception__type__in=type_filter)

    if country_or_place_of_original_publication_filter := search_form.cleaned_data['country_or_place_of_original_publication']:
        country_or_place_of_original_publication_q = get_country_or_place_q(
            country_or_place_of_original_publication_filter,
            'workreception__work__edition__place_of_publication'
        )
        receptions = receptions.filter(country_or_place_of_original_publication_q)

    if country_or_place_of_reception_filter := search_form.cleaned_data['country_or_place_of_reception']:
        country_or_place_of_reception_q = get_country_or_place_q(
            country_or_place_of_reception_filter,
            'place_of_reception'
        )
        receptions = receptions.filter(country_or_place_of_reception_q)

    if language_filter := search_form.cleaned_data['language']:
        receptions = receptions.filter(language_of_reception__in=language_filter)

    if genre_filter := search_form.cleaned_data['genre']:
        receptions = receptions.filter(reception_genre__in=genre_filter)

    if notes_filter := search_form.cleaned_data['notes']:
        receptions = receptions.filter(notes__icontains=notes_filter)
    return receptions


def receptions(request):
    receptions = Reception.objects.prefetch_related(
        'place_of_reception',
        'workreception_set',
        'workreception_set__work',
        'workreception_set__work__related_persons',
        'workreception_set__type',
        'is_same_as_work',
        'personreception_set'
    )

    order_by_options = OrderedDict([
        ('title', 'Title'),
        ('date_of_reception', 'Date of reception'),
    ])
    receptions, ordering_context = order_queryset(receptions, request.GET.dict(), order_by_options, 'date_of_reception')

    search_form = ReceptionSearchForm(request.GET)
    if search_form.is_valid():
        receptions = filter_receptions_with_form(receptions, search_form)

    receptions, date_of_reception_slider_info = get_int_slider_info(request, receptions, 'date_of_reception',
                                                              ['date_of_reception_start',
                                                               'date_of_reception_end'])

    paginator = Paginator(receptions, 25)
    page_number = request.GET.get('page')
    paginated_receptions = paginator.get_page(page_number)
    context = {'receptions': paginated_receptions,
               'count': paginator.count,
               'search_form': search_form,
               'date_of_reception_slider_info': date_of_reception_slider_info
               } | ordering_context
    return render(request, 'shewrote/receptions.html', context)


def reception(request, reception_id):
    reception = get_object_or_404(Reception.objects.select_related('is_same_as_work', 'document_type'), id=reception_id)

    work_receptions = WorkReception.objects.filter(reception=reception).prefetch_related(
        'work',
        'work__related_persons',
        'type'
    )
    person_receptions = reception.personreception_set.all()

    context = {
        'reception': reception,
        'personreceptions': person_receptions,
        'workreceptions': work_receptions,
    }

    return render(request, 'shewrote/reception_details.html', context)


def work_reception_count_annotate(qs):
    return qs.annotate(reception_count=Count('workreception__reception', distinct=True))


def circulations(request):
    circulations = Circulation.objects.prefetch_related(
        'place_of_reception',
        'workcirculation_set',
        'workcirculation_set__work',
        'workcirculation_set__work__related_persons',
        'workcirculation_set__type',
        'personcirculation_set'
    )
    title_filter = request.GET.get('title', '')
    if title_filter:
        circulations = circulations.filter(title__unaccent__icontains=title_filter)

    order_by_options = OrderedDict([
        ('title', 'Title'),
        ('date_of_reception', 'Date of reception'),
    ])
    circulations, ordering_context = order_queryset(circulations, request.GET.dict(), order_by_options, 'date_of_reception')

    paginator = Paginator(circulations, 25)
    page_number = request.GET.get('page')
    paginated_circulations = paginator.get_page(page_number)
    context = {'circulations': paginated_circulations, 'count': paginator.count, 'title': title_filter} | ordering_context
    return render(request, 'shewrote/circulations.html', context)


def circulation(request, circulation_id):
    circulation = get_object_or_404(Circulation.objects.select_related('document_type'), id=circulation_id)

    work_circulations = WorkCirculation.objects.filter(circulation=circulation).prefetch_related(
        'work',
        'work__related_persons',
        'type'
    )
    person_circulations = circulation.personcirculation_set.all()

    context = {
        'circulation': circulation,
        'personcirculations': person_circulations,
        'workcirculations': work_circulations,
    }

    return render(request, 'shewrote/circulation_details.html', context)


def filter_works_with_form(works: QuerySet[Work], search_form: WorkSearchForm) -> QuerySet[Work]:
    if title_filter := search_form.cleaned_data['title']:
        works = works.filter(title__unaccent__icontains=title_filter)

    if author_filter := search_form.cleaned_data['author']:
        works = works.filter(personwork__role__name='is creator of', related_persons__in=author_filter)

    if author_gender_filter := search_form.cleaned_data['author_gender']:
        works = works.filter(personwork__role__name='is creator of', related_persons__sex__in=author_gender_filter)

    if country_or_place_of_publication_filter := search_form.cleaned_data['country_or_place_of_publication']:
        country_or_place_of_publication_q = get_country_or_place_q(
            country_or_place_of_publication_filter,
            'edition__place_of_publication'
        )
        works = works.filter(country_or_place_of_publication_q)

    if language_filter := search_form.cleaned_data['language']:
        works = works.filter(languages__in=language_filter)

    if genre_filter := search_form.cleaned_data['genre']:
        works = works.filter(edition__genre__in=genre_filter)

    if notes_filter := search_form.cleaned_data['notes']:
        works = works.filter(notes__icontains=notes_filter)
    return works


def works_list(request, base_qs, extra_context={}):
    """Show all works."""
    works = base_qs.prefetch_related("personwork_set__person", "personwork_set__role")

    order_by_options = OrderedDict([
        ('title', 'Title'),
        ('date_of_publication_start', 'Publication date'),
        ('-reception_count', ('Reception count', work_reception_count_annotate)),
    ])
    works, ordering_context = order_queryset(works, request.GET.dict(), order_by_options, '-reception_count')

    search_form = WorkSearchForm(request.GET)
    if search_form.is_valid():
        works = filter_works_with_form(works, search_form)

    works, publication_year_slider_info = get_int_slider_info(request, works, 'date_of_publication_start',
                                                              ['date_of_publication_start_start', 'date_of_publication_start_end'])

    paginator = Paginator(works, 25)
    page_number = request.GET.get("page")
    paginated_works = paginator.get_page(page_number)

    context = {'works': paginated_works,
               'count': paginator.count,
               'search_form': search_form,
               'publication_year_slider_info': publication_year_slider_info
              } | ordering_context | extra_context

    return render(request, 'shewrote/works.html', context)


def works(request):
    return works_list(request, base_qs=Work.work_objects.all())


def sources(request):
    return works_list(request, base_qs=Work.source_objects.all(),
                      extra_context={'heading': "sources", 'details_path_name': 'shewrote:source'})


def work(request, work_id):
    """Show a single work and all its details."""
    work = Work.objects.prefetch_related("personwork_set__person", "personwork_set__role").get(id=work_id)
    editions = Edition.objects.filter(related_work=work).order_by('publication_year_start')
    work_receptions = WorkReception.objects.filter(work=work).prefetch_related('reception', 'type')\
        .order_by('reception__date_of_reception')
    receptions_in_work = (Reception.objects.filter(Q(is_same_as_work=work) | Q(part_of_work=work))
                          .order_by('date_of_reception').prefetch_related('received_works', 'received_persons'))
    work_circulations = WorkCirculation.objects.filter(work=work).prefetch_related('circulation', 'type')\
        .order_by('circulation__date_of_reception')
    context = {
        'work': work,
        'editions': editions,
        'workreceptions': work_receptions,
        'receptions_in_work': receptions_in_work,
        'workcirculations': work_circulations,
    }
    return render(request, 'shewrote/work_details.html', context)


@login_required
def work_info(request, work_id):
    work = get_object_or_404(Work, id=work_id)
    return JsonResponse({'title': work.title, 'date_of_publication': work.date_of_publication_start})


@login_required
def new_work(request):
    """Add a new work."""
    if request.method != 'POST':
        # No data submitted, create a blank form
        form = WorkForm()
    else:
        # Process the POST data
        form = WorkForm(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('shewrote:works')

    # Display a blank or invalid form
    context = {'form': form}
    return render(request, 'shewrote/new_work.html', context)


@login_required
def edit_work(request, work_id):
    """Edit an existing work."""
    entry = Work.objects.get(id=work_id)

    if request.method != 'POST':
        # Initial request, pre-fill form with the current person.
        form = WorkForm(instance=entry)
    else:
        # POST data submitted; process data.
        form = WorkForm(instance=entry, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('shewrote:work', work_id=entry.id)

    context = {
        'work': entry,
        'form': form,
    }
    return render(request, 'shewrote/edit_work.html', context)


def editions(request):
    works = Work.objects.filter(edition__isnull=False)\
                        .annotate(edition_count=Count('edition'))\
                        .prefetch_related('personwork_set')

    title_filter = request.GET.get('title', '')
    if title_filter:
        works = works.filter(title__unaccent__icontains=title_filter)

    order_by_options = OrderedDict([
        ('-edition_count', 'Edition count'),
        ('date_of_publication_start', 'Date'),
    ])
    works, ordering_context = order_queryset(works, request.GET.dict(), order_by_options, '-edition_count')

    paginator = Paginator(works, 25)
    page_number = request.GET.get('page')
    paginated_works = paginator.get_page(page_number)
    context = {'works': paginated_works, 'count': paginator.count, 'title': title_filter} | ordering_context
    return render(request, 'shewrote/editions.html', context)


def work_edition(request, work_id):
    work = get_object_or_404(Work, pk=work_id)
    editions = Edition.objects.filter(related_work=work)
    context = {
        'work': work,
        'editions': editions
    }
    return render(request, 'shewrote/work_edition_details.html', context)


def edition(request, edition_id):
    edition = get_object_or_404(Edition, pk=edition_id)
    context = {
        'edition': edition
    }
    return render(request, 'shewrote/edition_details.html', context)


def list_of_changes(request, content_type_id, object_id):
    crudevents = CRUDEvent.objects.filter(object_id=object_id, content_type_id=content_type_id)
    return render(request, 'shewrote/components/list_of_changes.html', {'crudevents': crudevents})


@login_required
def changes(request):
    form = ChangesSearchForm(data=request.GET)
    user = form.cleaned_data['user'] if form.is_valid() and form.cleaned_data['user'] else request.user

    crud_events = CRUDEvent.objects.filter(user=user, content_type__app_label="shewrote")\
                   .order_by('-datetime').prefetch_related('content_type')

    paginator = Paginator(crud_events, 25)
    page_number = request.GET.get("page")
    paginated_crud_events = paginator.get_page(page_number)
    context = {'crudevents': paginated_crud_events, 'count': paginator.count,
               'selected_user': user,
               'admin_path': settings.ADMIN_URL_NAME,
               'form': form}

    return render(request, 'shewrote/changes.html', context)


from dal import autocomplete
from django.contrib.auth import get_user_model


class UserAutocompleteView(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = get_user_model().objects.all()

        if self.q:
            qs = qs.filter(username__icontains=self.q)

        return qs


class VIAFSuggest(autocomplete.Select2ListView):
    def get(self, request, *args, **kwargs):
        return self.find_viaf(self.q)

    @staticmethod
    def find_viaf(q, discard_viaf_ids=set(), json_output=True, cql_relation='cql.any'):
        viaf = ViafAPI()
        viaf_result_raw = viaf.search('%s = "%s"' % (cql_relation, q)) or []
        viaf_result = [dict(
            id=item.uri,
            id_number=item.viaf_id,
            text=escape(item.label),
            nametype=item.nametype,
            class_name="viaf_api",
            external_url=item.uri,
            clean_text=escape(item.label)
        ) for item in viaf_result_raw if item.viaf_id not in discard_viaf_ids]

        if json_output:
            return JsonResponse({
                'results': viaf_result
            })
        else:
            return viaf_result


class PersonVIAFSuggest(autocomplete.Select2ListView):
    def get(self, request, *args, **kwargs):
        viaf_result = VIAFSuggest.find_viaf(self.q, json_output=False, cql_relation='local.personalNames')

        return JsonResponse({'results': viaf_result})


class WorkVIAFSuggest(autocomplete.Select2ListView):
    def get(self, request, *args, **kwargs):
        viaf_result = VIAFSuggest.find_viaf(self.q, json_output=False, cql_relation='local.uniformTitleWorks')

        return JsonResponse({'results': viaf_result})


@staff_member_required
@user_passes_test(lambda u: u.is_superuser)
def merge_users(request):
    template = 'shewrote/merge_users.html'

    if request.method != 'POST':
        return render(request, template, {'form': MergeUsersForm()})

    form = MergeUsersForm(request.POST)
    if not form.is_valid():
        return render(request, template, {'form': form})

    active_user = form.cleaned_data['active_user']
    inactive_users = form.cleaned_data['inactive_users']
    update_count = 0
    for inactive_user in inactive_users:
        update_count += CRUDEvent.objects.filter(user=inactive_user).update(user_id=active_user.id)
    message_level =  messages.SUCCESS if update_count else messages.INFO
    messages.add_message(request, message_level,f"{update_count} CRUD events were re-linked to {active_user}.")

    return render(request, template, {'form': MergeUsersForm()})


def get_wikidata_label_translations(api_id, field_name):
    field_values = {}
    for language_code, _ in settings.LANGUAGES:
        response = requests.get(settings.WIKIDATA_LABEL_URL.format(api_id, language_code),
                                headers={'accept': 'application/json',
                                         'Authorization': f'Bearer {settings.WIKIDATA_API_KEY}'})
        if response.status_code == requests.codes.ok:
            field_values[field_name] = response.json()
    return field_values


def get_wikidata_label_for_property(data, property, language='en'):
    id = get_nested_object(data, ('statements', property, 0, 'value', 'content'), None)
    if not id:
        return ''
    resp = requests.get(settings.WIKIDATA_LABEL_URL.format(id, language),
                        headers={'accept': 'application/json',
                                 'Authorization': f'Bearer {settings.WIKIDATA_API_KEY}'})
    return resp.json() if resp.status_code == requests.codes.ok else ''


def get_or_create_object_from_wikidata_id(wikidata_id, property, model):
    if data := get_wikidata_statements(wikidata_id):
        return get_option_from_wikidata_property(data, property, model).get('id', None)
    return None


# Which field holds the name value of the model:
name_field_names = {Country: 'modern_country', Place: 'name'}


def create_object_from_wikidata_id(model, wikidata_id):
    if model not in name_field_names.keys():
        return None
    field_values = get_wikidata_label_translations(wikidata_id, name_field_names[model])
    field_values['wikidata_id'] = wikidata_id
    if model == Place and (data := get_wikidata_statements(wikidata_id)):
        field_values['latitude'] = round(get_nested_object(data, ('statements', 'P625', 0, 'value', 'content', 'latitude')), 6)
        field_values['longitude'] = round(get_nested_object(data, ('statements', 'P625', 0, 'value', 'content', 'longitude')), 6)
        field_values['modern_country_id'] = get_or_create_object_from_wikidata_id(wikidata_id, 'P17', Country)
    return model.objects.create(**field_values)


def get_option_from_wikidata_property(data, property, model):
    wikidata_id = get_nested_object(data, ('statements', property, 0, 'value', 'content'), None)
    if not wikidata_id:
        return {}
    label = get_wikidata_label_for_property(data, property)
    if obj := model.objects.filter(Q(wikidata_id=wikidata_id) | Q(**{name_field_names[model]: label})).first():
        return {'text': str(obj), 'id': obj.pk}
    if obj := create_object_from_wikidata_id(model, wikidata_id):
        return {'text': str(obj), 'id': obj.pk}
    return {}


def request_wikidata_suggest(term: str, page: int=1, limit: int=10) -> Response:
    api_key = settings.WIKIDATA_API_KEY
    language_code = translation.get_language()
    offset = (page - 1) * limit

    return requests.get(settings.WIKIDATA_SUGGEST_URL,
                        params={'q': term, 'language': language_code, 'limit': limit, 'offset': offset},
                        headers={'accept': 'application/json', 'Authorization': f'Bearer {api_key}'})


class WikidataSuggestView(AutoResponseView):
    def get(self, request, *args, **kwargs):
        term = request.GET.get('term', '')
        page = request.GET.get('page', '1')
        page = int(page) if page.isdigit() else 1
        limit = 10
        response = request_wikidata_suggest(term, page, limit)

        if response.status_code != requests.codes.ok:
            return JsonResponse({'results': {}, 'more': False})

        results = [
            {'id': html.escape(item['id']), 'text': self.render_text(item)}
            for item in response.json().get('results', [])
        ]

        return JsonResponse({
            'results': results,
            'more': len(results) >= limit
        })

    @staticmethod
    def render_text(item):
        id = html.escape(item['id'])
        label = html.escape(item['display-label']['value'])
        description = html.escape(item['description']['value'] if item['description'] else '')
        return f"""
            <div>
                <b>{label}</b>
                <span style='color: dimgray; margin-left: auto; margin-right: 0'>{id}</span>
                <br/>
                <small>{description}</small>
            </div>
        """


class FillFieldsView(AutoResponseView):
    def get(self, request, fill_field_name, *args, **kwargs):
        method = f'get_{fill_field_name}_fillfield_response'
        if hasattr(self, method) and callable(getattr(self, method)):
            return JsonResponse(getattr(self, method)(request))
        return JsonResponse({})

    @staticmethod
    def get_country_wikidata_fillfield_response(request):
        api_id = request.GET.get('api_id', "")
        field_values = get_wikidata_label_translations(api_id, "modern_country")
        return field_values

    @staticmethod
    def get_place_wikidata_fillfield_response(request):
        api_id = request.GET.get('api_id', "")
        field_values = get_wikidata_label_translations(api_id, "name")

        if data := get_wikidata_statements(api_id):
            field_values['modern_country'] = get_option_from_wikidata_property(data, 'P17', Country)
            field_values['latitude'] = round(get_nested_object(data, ('statements', 'P625', 0, 'value', 'content', 'latitude')), 6)
            field_values['longitude'] = round(get_nested_object(data, ('statements', 'P625', 0, 'value', 'content', 'longitude')), 6)

        return field_values

    @staticmethod
    def get_person_wikidata_fillfield_response(request):
        api_id = request.GET.get('api_id', "")
        field_values = {}
        if data := get_wikidata_statements(api_id):
            field_values['short_name'] = get_wikidata_label(api_id)
            field_values['first_name'] = get_wikidata_label_for_property(data, 'P735')
            field_values['birth_name'] = get_wikidata_label_for_property(data, 'P1477')

            date_of_birth = get_nested_object(data, ('statements', 'P569', 0, 'value', 'content', 'time', slice(1, 11)), '')
            field_values['date_of_birth'] = next(iter(re.findall(r"^(\d{4})", date_of_birth)), '')
            field_values['alternative_birth_date'] = date_of_birth
            date_of_death = get_nested_object(data, ('statements', 'P570', 0, 'value', 'content', 'time', slice(1, 11)), '')
            field_values['date_of_death'] = next(iter(re.findall(r"^(\d{4})", date_of_death)), '')
            field_values['alternative_death_date'] = date_of_death

            sex = get_wikidata_label_for_property(data, 'P21')
            field_values['sex'] = getattr(Person.GenderChoices, sex.upper()).value \
                                    if sex and hasattr(Person.GenderChoices, sex.upper()) else None

            # place_of_{birth,death} fields cannot be used because, while the application language is English,
            # the name of places are not always in English, e.g.
            # - Den Haag (Dutch) vs The Hague (see https://www.wikidata.org/wiki/Q36600)
            # - Köln (German) vs Cologne (see https://www.wikidata.org/wiki/Q365)
            # field_values['place_of_birth'] = get_option_from_wikidata_property(data, 'P19', Place)
            # field_values['place_of_death'] = get_option_from_wikidata_property(data, 'P20', Place)

        return {k:v for k,v in field_values.items() if v}  # Leave out items with empty values


class ObjectExistsWikidataView(AutoResponseView):
    """Returns whether an object exists given the model name and Wikidata ID"""
    def get(self, request, model_name, wikidata_id):
        model = apps.get_model(app_label=ShewroteConfig.name, model_name=model_name)
        return JsonResponse({
            'exists': model.objects.filter(wikidata_id=wikidata_id).exists()
        })
