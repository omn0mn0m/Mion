from django.test import TestCase

from awc.forms import CreateChallengeForm, AddExistingSubmissionForm

from awc.models import Challenge

# Create your tests here.
class CreateChallengeFormTest(TestCase):
    def test_thread_id_field_label(self):
        form = CreateChallengeForm()
        self.assertTrue(form.fields['thread_id'].label == None or form.fields['thread_id'].label == 'thread id')

    def test_thread_id_is_negative(self):
        form = CreateChallengeForm(data={'thread_id': -1,
                                         'category': Challenge.GENRE,
                                         'challenge_code': 'Filler'})
        self.assertFalse(form.is_valid())

    def test_thread_id_is_zero(self):
        form = CreateChallengeForm(data={'thread_id': 0,
                                         'category': Challenge.GENRE,
                                         'challenge_code': 'Filler'})
        self.assertFalse(form.is_valid())

    def test_thread_id_valid(self):
        form = CreateChallengeForm(data={'thread_id': 1,
                                         'category': Challenge.GENRE,
                                         'challenge_code': 'Filler'})
        self.assertTrue(form.is_valid())

    def test_category_field_label(self):
        form = CreateChallengeForm()
        self.assertTrue(form.fields['category'].label == None or form.fields['category'].label == 'category')

    def test_challenge_code_field_label(self):
        form = CreateChallengeForm()
        self.assertTrue(form.fields['challenge_code'].label == None or form.fields['challenge_code'].label == 'challenge code')

class AddExistingSubmissionFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        challenge = Challenge.objects.create(name="Beginner's Challenge",
                                             thread_id=4448,
                                             category=Challenge.TIER,
                                             extra='')
        
    def test_challenge_field_label(self):
        form = AddExistingSubmissionForm()
        self.assertTrue(form.fields['challenge'].label == None or form.fields['challenge'].label == 'challenge')

    def test_comment_id_field_label(self):
        form = AddExistingSubmissionForm()
        self.assertTrue(form.fields['comment_id'].label == None or form.fields['comment_id'].label == 'comment id')

    def test_comment_id_is_negative(self):
        challenge = Challenge.objects.get(name="Beginner's Challenge")
        form = AddExistingSubmissionForm(data={'comment_id': -1,
                                               'challenge': challenge.pk})
        self.assertFalse(form.is_valid())

    def test_comment_id_is_zero(self):
        challenge = Challenge.objects.get(name="Beginner's Challenge")
        form = AddExistingSubmissionForm(data={'comment_id': 0,
                                               'challenge': challenge.pk})
        self.assertFalse(form.is_valid())

    def test_comment_id_valid(self):
        challenge = Challenge.objects.get(name="Beginner's Challenge")
        form = AddExistingSubmissionForm(data={'comment_id': 1,
                                               'challenge': challenge.pk})
        self.assertTrue(form.is_valid())
