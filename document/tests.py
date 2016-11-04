from django.test import TestCase

from document.models import Category


class TestExample(TestCase):
    """ Example test case """

    def test_example(self):
        """ Example test """
        self.assertEqual(1, 1)
        self.assertTrue(True)
        self.assertFalse(False)


class TestCategory(TestCase):

    def test_create_category(self):
        category, created = Category.objects.get_or_create(name='Test Category Name')
        self.assertEqual(category.slug, 'test-category-name')
