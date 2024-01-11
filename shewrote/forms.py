from django import forms
from django_select2.forms import ModelSelect2Widget, ModelSelect2MultipleWidget

from .models import Person, Place, Education, PersonEducation


class PersonForm(forms.ModelForm):
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
            'bibliography': forms.Textarea(attrs={'cols': 80}),
            'notes': forms.Textarea(attrs={'cols': 80}),
            'place_of_birth': ModelSelect2Widget(model=Place, search_fields=['name__icontains'],
                                                     attrs={'data-placeholder': "Select a place"}),
            'place_of_death': ModelSelect2Widget(model=Place, search_fields=['name__icontains'],
                                                     attrs={'data-placeholder': "Select a place"}),
            'mother': ModelSelect2Widget(model=Person, search_fields=['short_name__icontains'],
                                                     attrs={'data-placeholder': "Select a person"}),
            'father': ModelSelect2Widget(model=Person, search_fields=['short_name__icontains'],
                                                     attrs={'data-placeholder': "Select a person"}),
            'related_to': ModelSelect2MultipleWidget(model=Person, search_fields=['short_name__icontains'],
                                                     attrs={'data-placeholder': "Select multiple persons"})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_personeducation_field()

    def add_personeducation_field(self):
        personeducations = forms.ModelMultipleChoiceField(
            label="Education",
            widget=ModelSelect2MultipleWidget(
                model=Education,
                search_fields=['name'],
                attrs={"data-minimum-input-length": 0,}
            ),
            queryset=Education.objects.all(),
            required=False,
            initial=Education.objects.filter(personeducation__person=self.instance)
        )
        self.fields['personeducation'] = personeducations

    def save_personeducations(self):
        educations_in_form = self.cleaned_data['personeducation']
        existing_educations = Education.objects.filter(personeducation__person=self.instance)

        # Delete Educations that were removed in the form
        educations_to_delete = existing_educations.exclude(pk__in=educations_in_form.values_list('pk', flat=True))
        for education in educations_to_delete:
            PersonEducation.objects.get(person=self.instance, education=education).delete()

        # Save Educations that were added in the form
        new_educations = educations_in_form.exclude(pk__in=existing_educations.values_list('pk', flat=True))
        for education in new_educations:
            PersonEducation(person=self.instance, education=education).save()

    def save(self, commit=True):
        self.instance = super(PersonForm, self).save(commit=commit)
        if commit:
            self.save_personeducations()

        return self.instance
