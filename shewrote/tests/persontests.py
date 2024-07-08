from django.test import TestCase
from shewrote.models import Person


class ChildrenTestCase(TestCase):
    def setUp(self):
        self.person_without_children = Person.objects.create(short_name="person_without_children")

        self.mother_with_1_child = Person.objects.create(short_name="mother_with_1_child", sex=Person.GenderChoices.FEMALE)
        self.father_with_2_children = Person.objects.create(short_name="father_with_2_children", sex=Person.GenderChoices.MALE)
        self.child1 = Person.objects.create(short_name="child1", father=self.father_with_2_children)
        self.child2 = Person.objects.create(short_name="child2", father=self.father_with_2_children, mother=self.mother_with_1_child)

    def test_person_has_no_children(self):
        person_without_children = Person.objects.get(short_name="person_without_children")
        children = person_without_children.get_children()
        self.assertFalse(children)  # no children found

    def test_person_has_children(self):
        """Persons that have chrildren are correctly identified"""
        mother_with_1_child = Person.objects.get(short_name="mother_with_1_child")
        children = mother_with_1_child.get_children()
        self.assertEqual(children.count(), 1)

        father_with_2_children = Person.objects.get(short_name="father_with_2_children")
        children = father_with_2_children.get_children()
        self.assertEqual(children.count(), 2)
