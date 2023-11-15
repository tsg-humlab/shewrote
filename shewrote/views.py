from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from .models import Person
from .forms import PersonForm


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
        'is_creator_of_works': person.get_created_works("is creator of")
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

    context = {'person': entry, 'form': form}
    return render(request, 'shewrote/edit_person.html', context)

