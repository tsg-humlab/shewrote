from django import forms
from django.urls import reverse_lazy
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django_select2.forms import (ModelSelect2Widget, ModelSelect2MultipleWidget, Select2MultipleWidget,
                                  HeavySelect2MultipleWidget)
from apiconnectors.widgets import ApiSelectWidget
from django.utils.safestring import SafeString
from dal import autocomplete
from easyaudit.models import CRUDEvent

import functools

from .models import Person, Place, Education, PersonEducation, PeriodOfResidence, Work, Marriage, Religion


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
            'short_name', 'viaf_or_cerl', 'first_name', 'birth_name', 'date_of_birth', 'date_of_death',
            'alternative_birth_date', 'alternative_death_date', 'flourishing_start', 'flourishing_end', 'sex',
            'alternative_name_gender', 'place_of_birth', 'place_of_death', 'professional_ecclesiastic_title',
            'aristocratic_title', 'mother', 'father', 'bibliography', 'related_to', 'notes', 'place_of_residence_notes'
        ]
        labels = {
            'short_name': 'Short name',
            'viaf_or_cerl': 'VIAF',
            'first_name': 'First name',
            'birth_name': 'Birth name',
            'date_of_birth': 'Date of birth',
            'date_of_death': 'Date of death',
            'alternative_birth_date': 'Birth date Notes',
            'alternative_death_date': 'Death date Notes',
            'flourishing_start': 'Flourishing start',
            'flourishing_end': 'Flourishing end',
            'sex': 'Sex',
            'alternative_name_gender': 'Alt. gender',
            'place_of_birth': 'Birth place',
            'place_of_death': 'Death place',
            'professional_ecclesiastic_title': 'Professional or ecclesiastical title',
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_personeducation_field()
        self.add_periodsofresidence_field()

        # Set the order to accomodate the fields added above
        self.order_fields(field_order=[
            'short_name', 'viaf_or_cerl', 'first_name', 'birth_name', 'date_of_birth', 'date_of_death',
            'alternative_birth_date', 'alternative_death_date', 'flourishing_start', 'flourishing_end', 'sex',
            'alternative_name_gender', 'place_of_birth', 'place_of_death', 'professional_ecclesiastic_title',
            'aristocratic_title', 'mother', 'father', 'bibliography', 'related_to', 'notes',
            'personeducation', 'periodofresidence', 'place_of_residence_notes'
        ])

    def add_personeducation_field(self):
        personeducations = forms.ModelMultipleChoiceField(
            label="Education",
            widget=ModelSelect2MultipleWidget(
                model=Education,
                search_fields=['name__icontains'],
                attrs={"data-minimum-input-length": 0,}
            ),
            queryset=Education.objects.all(),
            required=False,
            initial=Education.objects.filter(personeducation__person=self.instance)
        )
        self.fields['personeducation'] = personeducations

    def add_periodsofresidence_field(self):
        periodsofresidence = forms.ModelMultipleChoiceField(
            label="Lived in",
            widget=ModelSelect2MultipleWidget(
                model=Place,
                search_fields=['name__icontains'],
                attrs={"data-minimum-input-length": 0,}
            ),
            queryset=Place.objects.all(),
            required=False,
            initial=Place.objects.filter(periodofresidence__person=self.instance).distinct()
        )
        self.fields['periodofresidence'] = periodsofresidence

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

    def save_periodsofresidence(self):
        places_in_form = self.cleaned_data['periodofresidence']
        existing_places = Place.objects.filter(periodofresidence__person=self.instance)

        # Delete Places that were removed in the form
        places_to_delete = existing_places.exclude(pk__in=places_in_form.values_list('pk', flat=True))
        for place in places_to_delete:
            PeriodOfResidence.objects.filter(person=self.instance, place=place).delete()

        # Save Places that were added in the form
        new_places = places_in_form.exclude(pk__in=existing_places.values_list('pk', flat=True))
        for place in new_places:
            PeriodOfResidence(person=self.instance, place=place).save()

    def save(self, commit=True):
        self.instance = super(PersonForm, self).save(commit=commit)
        if commit:
            self.save_personeducations()
            self.save_periodsofresidence()

        return self.instance


class CountryOrPlaceField(forms.MultipleChoiceField):
    def to_python(self, value):
        objects = []
        for country_or_place in value:
            obj = self.get_country_or_place_instance(country_or_place)
            objects.append(obj)
        return objects

    @staticmethod
    @functools.lru_cache
    def get_country_or_place_instance(country_or_place):
        if '|' not in country_or_place:
            raise ValidationError("Invalid value: %(value)s", code="invalid",
                                  params={"value": f'{country_or_place}'})
        model_name, pk = country_or_place.split('|', 1)
        if model_name not in ['country', 'place']:
            raise ValidationError("Invalid model name: %(value)s", code="invalid",
                                  params={"value": f"{model_name} with id {pk}"})
        model = apps.get_model('shewrote', model_name.capitalize())
        try:
            obj = model.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise ValidationError("Invalid id: %(value)s", code="invalid",
                                  params={"value": f"{model.__name__} with id {pk}"})
        return obj

    def validate(self, value):
        # Validation is done in method 'to_python'
        pass


class PersonSearchForm(forms.Form):
    sex = forms.MultipleChoiceField(widget=Select2MultipleWidget(choices=Person.GenderChoices.choices,
                                                                 attrs={'data-placeholder': "Select one or more genders",
                                                                        'style': "width: 100%"}),
                                    choices=Person.GenderChoices.choices,
                                    required=False)

    country_or_place_of_birth = CountryOrPlaceField(
        widget=HeavySelect2MultipleWidget(
            attrs={'data-placeholder': "Select multiple"},
            data_view='shewrote:countryplaceautoresponse'
        ),
        required=False
    )

    country_or_place_of_death = CountryOrPlaceField(
        widget=HeavySelect2MultipleWidget(
            attrs={'data-placeholder': "Select multiple"},
            data_view='shewrote:countryplaceautoresponse'
        ),
        required=False
    )

    country_or_place_of_residence = CountryOrPlaceField(
        widget=HeavySelect2MultipleWidget(
            attrs={'data-placeholder': "Select multiple"},
            data_view='shewrote:countryplaceautoresponse'
        ),
        required=False
    )

    marital_status = forms.MultipleChoiceField(
        widget=Select2MultipleWidget(choices=Marriage.MaritalStatusChoices.choices,
                                     attrs={'data-placeholder': "Select multiple",
                                            'style': "width: 100%"}),
        choices=Marriage.MaritalStatusChoices.choices,
        required=False
    )

    religion = forms.ModelMultipleChoiceField(
        widget=ModelSelect2MultipleWidget(model=Religion, search_fields=['name__icontains'],
                                          attrs={'data-placeholder': "Select multiple",
                                                 'data-minimum-input-length': 0,
                                                 'style': "width: 100%"}),
        queryset=Religion.objects.all(),
        required=False
    )

    education = forms.ModelMultipleChoiceField(
        widget=ModelSelect2MultipleWidget(model=Education, search_fields=['name__icontains'],
                                          attrs={'data-placeholder': "Select multiple",
                                                 'data-minimum-input-length': 0,
                                                 'style': "width: 100%"}),
        queryset=Education.objects.all(),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in ['country_or_place_of_birth', 'country_or_place_of_death', 'country_or_place_of_residence']:
            field = self.fields[field_name]
            field.choices = []
            for country_or_place_string in self.data.getlist(field_name):
                try:
                    obj = CountryOrPlaceField.get_country_or_place_instance(country_or_place_string)
                except ValidationError as e:
                    # Errors are handled in an is_valid() call
                    pass
                else:
                    field.choices.append((f'{obj.__class__.__name__.lower()}|{obj.pk}',
                                          f'{obj} ({obj.__class__.__name__.lower()})'))


class ShortPersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = [
            'short_name', 'first_name', 'birth_name', 'date_of_birth', 'date_of_death',
            'sex', 'notes',
        ]
        labels = {
            'short_name': 'Short name',
            'first_name': 'First name',
            'birth_name': 'Birth name',
            'date_of_birth': 'Date of birth',
            'date_of_death': 'Date of death',
            'sex': 'Sex',
            'notes': 'Notes',
        }

        widgets = {
            'notes': forms.Textarea(attrs={'cols': 80, 'rows': 5}),
        }


class WorkForm(forms.ModelForm):
    class Meta:
        model = Work
        fields = ['title', 'viaf_work', 'notes']
        labels = {
            'title': 'Title',
            'viaf_work': 'VIAF',
            'notes': 'Notes',
        }

        widgets = {
            'viaf_work': ApiSelectWidget(
                url=reverse_lazy('shewrote:work_viaf_suggest'),
                attrs={'data-html': True,
                       'data-placeholder': "Search for a work"}
            ),
            'notes': forms.Textarea(attrs={'cols': 80}),
        }


class ChangesSearchForm(forms.ModelForm):
    class Meta:
        model = CRUDEvent
        fields = ['user']
        labels = {
            'user': ''
        }
        widgets = {
            'user': autocomplete.ModelSelect2(url='shewrote:user_autocomplete',
                                              attrs={'data-theme': 'bootstrap-5',
                                                     'data-placeholder': "Change user",
                                                     'onchange': 'this.form.submit();'}),
        }

    class Media:
        css = {
            'screen': ['css/select2-bootstrap-5-theme.min.css'],
        }

