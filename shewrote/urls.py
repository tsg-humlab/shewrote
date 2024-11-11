"""Defines URL patterns for SHEWROTE."""

from django.urls import path

from . import views

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
    # Page that shows all collectives
    path('collectives/', views.collectives, name='collectives'),
    # Detail page for a single collective
    path('collectives/<uuid:collective_id>/', views.collective, name='collective'),
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

    # Editions
    path('editions/', views.editions, name='editions'),

    # Editions
    path('circulation/', views.circulation, name='circulation'),

    # AutoResponse
    path(r'countryplaceautoresponse/', views.CountryAndPlaceAutocompleteView.as_view(), name='countryplaceautoresponse'),

    # List of changes
    path('list_of_changes/<int:content_type_id>/<uuid:object_id>/', views.list_of_changes, name='list_of_changes'),
    path('changes/', views.changes, name='changes'),
    path('user_autocomplete/', views.UserAutocompleteView.as_view(), name='user_autocomplete'),

    # VIAF API Persons
    path('person_viaf_suggest', views.PersonVIAFSuggest.as_view(), name='person_viaf_suggest'),
    # VIAF API Works
    path('work_viaf_suggest', views.WorkVIAFSuggest.as_view(), name='work_viaf_suggest'),
]
