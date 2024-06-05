from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Person, Reception
from .forms import PersonForm, ShortPersonForm

from dal import autocomplete
from django.http import JsonResponse
from django.utils.html import escape
from apiconnectors.viafapi import ViafAPI


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
    context = {
        'person': person,
        'is_creator_of': person.get_works_for_role("is creator of"),
        'has_biography': person.get_works_for_role("has biography"),
        'is_commented_on_in': person.get_works_for_role("is commented on in"),
        'is_mentioned_in': person.get_works_for_role("is mentioned in"),
        'is_referenced_in': person.get_works_for_role("is referenced in")
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
    receptions = Reception.objects.all()
    title_filter = request.GET.get('title', '')
    if title_filter:
        receptions = receptions.filter(title__icontains=title_filter)
    paginator = Paginator(receptions, 25)
    page_number = request.GET.get('page')
    paginated_receptions = paginator.get_page(page_number)
    context = {'receptions': paginated_receptions, 'count': receptions.count(), 'title': title_filter}
    return render(request, 'shewrote/receptions.html', context)


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
