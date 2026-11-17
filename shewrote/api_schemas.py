from typing import Annotated

from ninja import ModelSchema, FilterSchema, FilterLookup
from pydantic import Field

from shewrote.models import Place, Person, Role, PersonWork, Work


class PlaceSchema(ModelSchema):
    class Meta:
        model = Place
        fields = ["id", "name"]


class PersonSchema(ModelSchema):
    place_of_birth: PlaceSchema
    place_of_death: PlaceSchema
    url: str = Field(..., alias="get_absolute_url")

    class Meta:
        model = Person
        fields = ["id", "short_name", "sex", "place_of_birth", "year_of_birth", "place_of_death", "year_of_death"]


class PersonFilterSchema(FilterSchema):
    search: Annotated[
        str | None,
        FilterLookup(["short_name__icontains", "first_name__icontains", "birth_name__icontains"]),
    ] = None


class CompactPersonSchema(ModelSchema):
    url: str = Field(..., alias="get_absolute_url")

    class Meta:
        model = Person
        fields = ["id", "short_name", "sex", "year_of_birth", "year_of_death"]


class RoleSchema(ModelSchema):
    class Meta:
        model = Role
        fields = ["id", "name"]


class PersonWorkSchema(ModelSchema):
    person: CompactPersonSchema
    role: RoleSchema

    class Meta:
        model = PersonWork
        fields = ["person", "role"]


class WorkSchema(ModelSchema):
    related_persons: list[PersonWorkSchema] = Field(..., alias="personwork_set")
    date_of_publication: str = Field(..., alias="date_of_publication_text")
    url: str = Field(..., alias="get_absolute_url")

    class Meta:
        model = Work
        fields = ["id", "title"]


class WorkFilterSchema(FilterSchema):
    search: Annotated[str | None, FilterLookup(["title__icontains"]),] = None
