"""Defines URL patterns for SHEWROTE."""

from django.urls import path

from . import views
from shewrote.views import PersonVIAFSuggest

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

    # Receptions
    path('receptions/', views.receptions, name='receptions'),
    path('reception/<uuid:reception_id>/', views.reception, name='reception'),

    # VIAF API
    path('person_viaf_suggest', PersonVIAFSuggest.as_view(), name='person_viaf_suggest'),
]
