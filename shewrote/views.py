from django.shortcuts import render, redirect
from .models import Person
from .forms import PersonForm


# Create your views here.
def index(request):
    """The home page for SHEWROTE."""
    return render(request, 'shewrote/index.html')


def persons(request):
    """Show all persons."""
    persons = Person.objects.order_by('short_name')
    context = {'persons': persons}
    return render(request, 'shewrote/persons.html', context)


def person(request, person_id):
    """Show a single person and all their details."""
    person = Person.objects.get(id=person_id)
    context = {'person': person}
    return render(request, 'shewrote/person.html', context)


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
