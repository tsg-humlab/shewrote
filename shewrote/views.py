from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q, OuterRef, Subquery, QuerySet
from django.conf import settings
from .models import (Person, Work, Reception, WorkReception, PersonReception, Collective, Country, Place,
                     PersonPersonRelation)
from .forms import PersonForm, PersonSearchForm, ShortPersonForm, WorkForm, ChangesSearchForm

from dal import autocomplete
from django.http import JsonResponse
from django.utils.html import escape
from apiconnectors.viafapi import ViafAPI
from easyaudit.models import CRUDEvent
from django_select2.views import AutoResponseView

from collections import OrderedDict

# Create your views here.
def index(request):
    """The home page for SHEWROTE."""
    return render(request, 'shewrote/index.html')


def get_year_slider_info(request, qs, field_name, search_field_names):
    year_min = (qs.model.objects.filter(**{field_name+'__isnull': False})
                      .order_by(field_name).first().normalised_date_of_birth)
    year_max = (qs.model.objects.filter(**{field_name+'__isnull': False})
                      .order_by('-'+field_name).first().normalised_date_of_birth)

    is_checked = request.GET.get(field_name+'_checkbox', 'off') == 'on'

    year_start = request.GET.get(search_field_names[0], '') or year_min
    if is_checked:
        qs = qs.filter(**{field_name+'__gte': year_start})

    year_end = request.GET.get(search_field_names[1], '') or year_max
    if is_checked:
        qs = qs.filter(**{field_name+'__lte': year_end})

    return qs, {'year_min': year_min, 'year_max': year_max, 'year_start': year_start, 'year_end': year_end,
                'is_checked': is_checked}


class CountryAndPlaceAutocompleteView(AutoResponseView):
    page_size = 10

    def get(self, request, *args, **kwargs):
        term = request.GET.get('term', '')
        page = int(request.GET.get('page', 1))
        begin = (page - 1) * self.page_size / 2
        end = page * self.page_size / 2

        countries = ('country', Country.objects.filter(modern_country__icontains=term).distinct()
                     .order_by('modern_country')[begin:end])
        places = ('place', Place.objects.filter(name__icontains=term).distinct()
                     .order_by('name')[begin:end])

        results: list = []
        for name, qs in [countries, places]:
            results.extend([
                {'id': f"{name}|{obj.pk}", 'text': f"{obj} ({name})" }
                for obj in qs
            ])

        more = True
        if countries[1].count() != self.page_size/2 and places[1].count() != self.page_size/2:
            more = False

        return JsonResponse({
            'results': results,
            'more': more
        })


def filter_persons_with_form(persons: QuerySet[Person], search_form: PersonSearchForm) -> QuerySet[Person]:
    """
    Filter Person objects using a valid instance of PersonSearchForm
    :param persons: a QuerySet of Persons to filter
    :param search_form: a valid instance of PersonSearchForm
    :return: a QuerySet of Person
    """
    if sex_filter := search_form.cleaned_data['sex']:
        persons = persons.filter(sex__in=sex_filter)

    if country_or_place_of_birth_filter := search_form.cleaned_data['country_or_place_of_birth']:
        countries = [obj for obj in country_or_place_of_birth_filter if isinstance(obj, Country)]
        places = [obj for obj in country_or_place_of_birth_filter if isinstance(obj, Place)]
        persons = persons.filter(Q(place_of_birth__in=places) | Q(place_of_birth__modern_country__in=countries))

    if country_or_place_of_death_filter := search_form.cleaned_data['country_or_place_of_death']:
        countries = [obj for obj in country_or_place_of_death_filter if isinstance(obj, Country)]
        places = [obj for obj in country_or_place_of_death_filter if isinstance(obj, Place)]
        persons = persons.filter(Q(place_of_death__in=places) | Q(place_of_death__modern_country__in=countries))
        
    return persons


def persons(request):
    """Show all persons."""
    persons = Person.objects.order_by('short_name')
    short_name_filter = request.GET.get("short_name", '')
    if short_name_filter:
        persons = persons.filter(
            Q(short_name__icontains=short_name_filter)
            | Q(alternativename__alternative_name__icontains=short_name_filter)
        ).distinct()

    search_form = PersonSearchForm(request.GET)
    if search_form.is_valid():
        persons = filter_persons_with_form(persons, search_form)

    persons, birth_year_slider_info = get_year_slider_info(request, persons, 'normalised_date_of_birth',
                                                           ['birth_year_start', 'birth_year_end'])

    persons, death_year_slider_info = get_year_slider_info(request, persons, 'normalised_date_of_death',
                                                           ['death_year_start', 'death_year_end'])

    receptions = Reception.objects.filter(personreception__person_id=OuterRef('pk'), image__isnull=False)\
        .exclude(image='').values('image')
    persons = persons.annotate(image=Subquery(receptions[:1]))

    persons = persons.prefetch_related('alternativename_set', 'place_of_birth', 'place_of_death')

    paginator = Paginator(persons, 25)
    page_number = request.GET.get("page")
    paginated_persons = paginator.get_page(page_number)
    context = {'persons': paginated_persons, 'count': paginator.count, 'short_name': short_name_filter,
               'birth_year_slider_info': birth_year_slider_info,
               'death_year_slider_info': death_year_slider_info,
               'search_form': search_form}
    return render(request, 'shewrote/persons.html', context)


def person(request, person_id):
    """Show a single person and all their details."""
    person = Person.objects.get(id=person_id)

    person_receptions = PersonReception.objects.filter(person=person)
    person_receptions_with_image = person_receptions.filter(reception__image__isnull=False).exclude(reception__image="")
    reception_with_image = person_receptions_with_image.first().reception if person_receptions else None
    image = person_receptions.first().reception.image if person_receptions else None

    relations = PersonPersonRelation.objects.filter(from_person=person)

    context = {
        'person': person,
        'is_creator_of': person.get_works_for_role("is creator of").order_by('date_of_publication_start'),
        'has_biography': person.get_works_for_role("has biography"),
        'is_commented_on_in': person.get_works_for_role("is commented on in"),
        'is_mentioned_in': person.get_works_for_role("is mentioned in"),
        'is_referenced_in': person.get_works_for_role("is referenced in"),
        'reception_with_image': reception_with_image,
        'relations': relations,
        'person_receptions': person_receptions.order_by('reception__date_of_reception')
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
        collectives = collectives.filter(name__icontains=name_filter).distinct()
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


def receptions(request):
    receptions = Reception.objects.prefetch_related(
        'place_of_reception',
        'workreception_set',
        'workreception_set__work',
        'workreception_set__type',
    )
    title_filter = request.GET.get('title', '')
    if title_filter:
        receptions = receptions.filter(title__icontains=title_filter)
    paginator = Paginator(receptions, 25)
    page_number = request.GET.get('page')
    paginated_receptions = paginator.get_page(page_number)
    context = {'receptions': paginated_receptions, 'count': paginator.count, 'title': title_filter}
    return render(request, 'shewrote/receptions.html', context)


def reception(request, reception_id):
    reception = get_object_or_404(Reception.objects.select_related('part_of_work', 'document_type'), id=reception_id)

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


def works(request):
    """Show all works."""
    works = Work.objects.prefetch_related("personwork_set__person", "personwork_set__role")

    get_params = request.GET.dict()
    order_by = get_params.pop('order_by', 'date_of_publication_start')
    works = works.order_by(F(order_by).asc(nulls_last=True))

    order_by_options = OrderedDict([
        ('title', 'Title'),
        ('date_of_publication_start', 'Publication date'),
    ])
    current_order_by_label = order_by_options[order_by]
    get_params_str = '&'.join(
        f'{key}={value}' for key, value in get_params.items()
    )

    title_filter = request.GET.get("title", '')
    if title_filter:
        works = works.filter(title__icontains=title_filter)

    paginator = Paginator(works, 25)
    page_number = request.GET.get("page")
    paginated_works = paginator.get_page(page_number)

    context = {'works': paginated_works, 'count': works.count(), 'title': title_filter, 'order_by': order_by,
               'order_by_options': order_by_options, 'current_order_by_label': current_order_by_label,
               'get_params': get_params_str}

    return render(request, 'shewrote/works.html', context)


def work(request, work_id):
    """Show a single work and all its details."""
    work = Work.objects.prefetch_related("personwork_set__person", "personwork_set__role").get(id=work_id)
    work_receptions = WorkReception.objects.filter(work=work).prefetch_related('reception', 'type')\
        .order_by('reception__date_of_reception')
    context = {
        'work': work,
        'workreceptions': work_receptions,
    }
    return render(request, 'shewrote/work_details.html', context)


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
    return render(request, 'shewrote/editions.html', {})


def circulation(request):
    return render(request, 'shewrote/circulation.html', {})


@login_required
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
