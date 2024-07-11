from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import JsonResponse
from .models import Person, Work, Reception, WorkReception, PersonReception
from .forms import PersonForm, ShortPersonForm, WorkForm

from dal import autocomplete
from django.http import JsonResponse
from django.utils.html import escape
from apiconnectors.viafapi import ViafAPI

from collections import OrderedDict

# Create your views here.
def index(request):
    """The home page for SHEWROTE."""
    return render(request, 'shewrote/index.html')


def persons(request):
    """Show all persons."""
    persons = Person.objects.order_by('short_name')
    short_name_filter = request.GET.get("short_name", '')
    if short_name_filter:
        persons = persons.filter(short_name__icontains=short_name_filter)
    paginator = Paginator(persons, 25)
    page_number = request.GET.get("page")
    paginated_persons = paginator.get_page(page_number)
    context = {'persons': paginated_persons, 'count': persons.count(), 'short_name': short_name_filter}
    return render(request, 'shewrote/persons.html', context)


def person(request, person_id):
    """Show a single person and all their details."""
    person = Person.objects.get(id=person_id)

    person_receptions = PersonReception.objects.filter(reception__image__isnull=False, person=person)\
        .exclude(reception__image="")
    image = person_receptions.first().reception.image if person_receptions else None

    context = {
        'person': person,
        'is_creator_of': person.get_works_for_role("is creator of"),
        'has_biography': person.get_works_for_role("has biography"),
        'is_commented_on_in': person.get_works_for_role("is commented on in"),
        'is_mentioned_in': person.get_works_for_role("is mentioned in"),
        'is_referenced_in': person.get_works_for_role("is referenced in"),
        'image': image
    }
    return render(request, 'shewrote/person.html', context)


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

    return render(request, 'shewrote/reception.html', context)


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
    return render(request, 'shewrote/work.html', context)


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
