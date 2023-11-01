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
    # Page for editing an existing person
    path('edit_person/<uuid:person_id>/', views.edit_person, name='edit_person'),
]
