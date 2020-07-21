from django.test import TestCase

# Create your tests here.
class IndexTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        pass

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
