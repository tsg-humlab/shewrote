from django import forms
from django.urls import reverse_lazy
from django_select2.forms import ModelSelect2Widget, ModelSelect2MultipleWidget
from apiconnectors.widgets import ApiSelectWidget
from django.utils.safestring import SafeString

from .models import Person, Place


class AddAnotherWidget(ModelSelect2Widget):
    def render(self, name, value, attrs=None, renderer=None):
        output = super(AddAnotherWidget, self).render(name, value, attrs=attrs, renderer=renderer)
        print(output)
        output += """<a href="#" data-bs-toggle="modal" data-bs-target="#addanotherModal">
                    <span data-toggle="tooltip" data-original-title="Add another" title="New">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-plus-circle" viewBox="0 0 16 16">
                    <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14m0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16"/>
                    <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4"/>
                    </svg>
                    </span>
                    </a>"""
        return SafeString(output)


class PersonForm(forms.ModelForm):
    suggest_select_ids = ['person_viaf_suggest']
    class Meta:
        model = Person
        fields = [
            'short_name', 'viaf_or_cerl', 'first_name', 'maiden_name', 'date_of_birth', 'date_of_death',
            'alternative_birth_date', 'alternative_death_date', 'flourishing_start', 'flourishing_end', 'sex',
            'alternative_name_gender', 'place_of_birth', 'place_of_death', 'professional_ecclesiastic_title',
            'aristocratic_title', 'mother', 'father', 'bibliography', 'related_to', 'notes',
        ]
        labels = {
            'short_name': 'Short name',
            'viaf_or_cerl': 'VIAF',
            'first_name': 'First name',
            'maiden_name': 'Maiden name',
            'date_of_birth': 'Date of birth',
            'date_of_death': 'Date of death',
            'alternative_birth_date': 'Alt. birth date',
            'alternative_death_date': 'Alt. death date',
            'flourishing_start': 'Flourishing start',
            'flourishing_end': 'Flourishing end',
            'sex': 'Gender',
            'alternative_name_gender': 'Alt. gender',
            'place_of_birth': 'Birth place',
            'place_of_death': 'Death place',
            'professional_ecclesiastic_title': 'Ecclesiastic title',
            'aristocratic_title': 'Aristocratic title',
            'mother': 'Mother',
            'father': 'Father',
            'bibliography': 'Bibliography',
            'related_to': 'Related to',
            'notes': 'Notes',
        }

        widgets = {
            'viaf_or_cerl': ApiSelectWidget(
                url=reverse_lazy('shewrote:person_viaf_suggest'),
                attrs={'data-html': True,
                       'data-placeholder': "Search for a person"}
            ),
            'bibliography': forms.Textarea(attrs={'cols': 80}),
            'notes': forms.Textarea(attrs={'cols': 80}),
            'place_of_birth': ModelSelect2Widget(model=Place, search_fields=['name__icontains'],
                                                     attrs={'data-placeholder': "Select a place"}),
            'place_of_death': ModelSelect2Widget(model=Place, search_fields=['name__icontains'],
                                                     attrs={'data-placeholder': "Select a place"}),
            'mother': AddAnotherWidget(model=Person, search_fields=['short_name__icontains'],
                                       attrs={'data-placeholder': "Select a person"}),
            'father': AddAnotherWidget(model=Person, search_fields=['short_name__icontains'],
                                       attrs={'data-placeholder': "Select a person"}),
            'related_to': ModelSelect2MultipleWidget(model=Person, search_fields=['short_name__icontains'],
                                                     attrs={'data-placeholder': "Select multiple persons"})
        }

    class Media:
        js = (
            'js/viaf_select.js',
        )

class ShortPersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = [
            'short_name', 'first_name', 'maiden_name', 'date_of_birth', 'date_of_death',
            'sex', 'notes',
        ]
        labels = {
            'short_name': 'Short name',
            'first_name': 'First name',
            'maiden_name': 'Maiden name',
            'date_of_birth': 'Date of birth',
            'date_of_death': 'Date of death',
            'sex': 'Gender',
            'notes': 'Notes',
        }

        widgets = {
            'notes': forms.Textarea(attrs={'cols': 80, 'rows': 5}),
        }
