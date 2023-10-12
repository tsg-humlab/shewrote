from django import forms

from .models import Person


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = [
            'short_name', 'viaf_or_cerl', 'first_name', 'maiden_name', 'date_of_birth', 'date_of_death',
            'alternative_birth_date', 'alternative_death_date', 'flourishing_start', 'flourishing_end', 'sex',
            'alternative_name_gender', 'place_of_birth', 'place_of_death', 'professional_ecclesiastic_title',
            'aristocratic_title', 'education', 'mother', 'father', 'bibliography', 'related_to', 'notes',
        ]
        labels = {
            'short_name': 'Short name',
            'viaf_or_cerl': 'VIAF or CERL',
            'first_name': 'First name',
            'maiden_name': 'Maiden name',
            'date_of_birth': 'Date of birth',
            'date_of_death': 'Date of death',
            'alternative_birth_date': 'Alt. birth date',
            'alternative_death_date': 'Alt. death date',
            'flourishing_start': 'Flourishing start',
            'flourishing_end': 'Flourishing end',
            'sex': 'Gender',
            'alternative_name_gender': 'Alt. gender name',
            'place_of_birth': 'Place of birth',
            'place_of_death': 'Place of death',
            'professional_ecclesiastic_title': 'Prof. ecclesiastic title',
            'aristocratic_title': 'Aristocratic title',
            'education': 'Education',
            'mother': 'Mother',
            'father': 'Father',
            'bibliography': 'Bibliography',
            'related_to': 'Related to',
            'notes': 'Notes',
        }

        widgets = {
            'bibliography': forms.Textarea(attrs={'cols': 80}),
            'notes': forms.Textarea(attrs={'cols': 80}),
        }
