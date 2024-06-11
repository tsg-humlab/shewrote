"""Defines URL patterns for SHEWROTE."""

from django.urls import path

from . import views
from shewrote.views import PersonVIAFSuggest, WorkVIAFSuggest

app_name = 'shewrote'
urlpatterns = [
    # Home page
    path('', views.index, name='index'),
    # Page that shows all persons
    path('persons/', views.persons, name='persons'),
    # Detail page for a single person
    path('persons/<uuid:person_id>/', views.person, name='person'),
    # Page for adding a new person
    path('new_person/', views.new_person, name='new_person'),
    # Page for adding a new person (short version)
    path('short_new_person/', views.short_new_person, name='short_new_person'),
    # Page for editing an existing person
    path('edit_person/<uuid:person_id>/', views.edit_person, name='edit_person'),
    # Page that shows all works
    path('works/', views.works, name='works'),
    # Detail page for a single work
    path('works/<uuid:work_id>/', views.work, name='work'),
    # Page for adding a new work
    path('new_work/', views.new_work, name='new_work'),
    # Page for editing an existing work
    path('edit_work/<uuid:work_id>/', views.edit_work, name='edit_work'),

    # Receptions
    path('receptions/', views.receptions, name='receptions'),
    path('reception/<uuid:reception_id>/', views.reception, name='reception'),

    # VIAF API Persons
    path('person_viaf_suggest', PersonVIAFSuggest.as_view(), name='person_viaf_suggest'),
    # VIAF API Works
    path('work_viaf_suggest', WorkVIAFSuggest.as_view(), name='work_viaf_suggest'),
]
