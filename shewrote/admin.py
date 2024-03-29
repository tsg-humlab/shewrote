from django.contrib import admin
from .models import (Country, Place, Person, Education, PersonEducation, Role, Profession, PersonProfession, Religion,
                     PersonReligion, Marriage, AlternativeName, PeriodOfResidence, TypeOfCollective, Collective,
                     PersonCollective, CollectivePlace, Genre, Language, Work, PersonWorkRole, Edition, EditionLanguage,
                     PersonEditionRole, ReceptionSource, PersonReceptionSourceRole, TypeOfDocument, TypeOfReception,
                     Reception, PersonReceptionRole, ReceptionType, ReceptionLanguage, ReceptionGenre)

admin.site.register(Country)
admin.site.register(Place)

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    search_fields = ['short_name']
    ordering = ['short_name']

admin.site.register(Education)
admin.site.register(PersonEducation)
admin.site.register(Role)
admin.site.register(Profession)
admin.site.register(PersonProfession)
admin.site.register(Religion)
admin.site.register(PersonReligion)

@admin.register(Marriage)
class MarriageAdmin(admin.ModelAdmin):
    autocomplete_fields = ['person', 'spouse']

admin.site.register(AlternativeName)

@admin.register(PeriodOfResidence)
class PeriodOfResidenceAdmin(admin.ModelAdmin):
    search_fields = ['person__short_name', 'place__name']
    autocomplete_fields = ['person']

admin.site.register(TypeOfCollective)
admin.site.register(Collective)
admin.site.register(PersonCollective)
admin.site.register(CollectivePlace)
admin.site.register(Genre)
admin.site.register(Language)
admin.site.register(Work)
admin.site.register(PersonWorkRole)
admin.site.register(Edition)
admin.site.register(EditionLanguage)
admin.site.register(PersonEditionRole)
admin.site.register(ReceptionSource)
admin.site.register(PersonReceptionSourceRole)
admin.site.register(TypeOfDocument)
admin.site.register(TypeOfReception)
admin.site.register(Reception)
admin.site.register(PersonReceptionRole)
admin.site.register(ReceptionType)
admin.site.register(ReceptionLanguage)
admin.site.register(ReceptionGenre)