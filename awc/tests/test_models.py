from django.test import TestCase

from awc.models import Challenge, Requirement, User, Submission

# Create your tests here.
class ChallengeModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
        beginners_challenge = Challenge.objects.create(name="Beginner's Challenge",
                                 thread_id=4448,
                                 category=Challenge.TIER,
                                 extra='')
        intermediate_challenge = Challenge.objects.create(name="Intermediate Challenge",
                                 thread_id=5027,
                                 category=Challenge.TIER,
                                 extra='')
        intermediate_challenge.prerequisites.add(beginners_challenge)

    def setUp(self):
        # Run once for every test method to setup clean data
        pass

    def test_name_label(self):
        challenge = Challenge.objects.get(name="Intermediate Challenge")
        field_label = challenge._meta.get_field('name').verbose_name
        self.assertEquals(field_label, 'name')

    def test_thread_id_label(self):
        challenge = Challenge.objects.get(name="Intermediate Challenge")
        field_label = challenge._meta.get_field('thread_id').verbose_name
        self.assertEquals(field_label, 'thread id')

    def test_category_label(self):
        challenge = Challenge.objects.get(name="Intermediate Challenge")
        field_label = challenge._meta.get_field('category').verbose_name
        self.assertEquals(field_label, 'category')

    def test_extra_label(self):
        challenge = Challenge.objects.get(name="Intermediate Challenge")
        field_label = challenge._meta.get_field('extra').verbose_name
        self.assertEquals(field_label, 'extra')

    def test_prerequisites_label(self):
        challenge = Challenge.objects.get(name="Intermediate Challenge")
        field_label = challenge._meta.get_field('prerequisites').verbose_name
        self.assertEquals(field_label, 'prerequisites')

    def test_name_max_length(self):
        challenge = Challenge.objects.get(name="Intermediate Challenge")
        max_length = challenge._meta.get_field('name').max_length
        self.assertEquals(max_length, 50)

    def test_category_max_length(self):
        challenge = Challenge.objects.get(name="Intermediate Challenge")
        max_length = challenge._meta.get_field('category').max_length
        self.assertEquals(max_length, 3)

    def test_challenge_name_is_name(self):
        challenge = Challenge.objects.get(name="Intermediate Challenge")
        expected_object_name = f'{challenge.name}'
        self.assertEquals(expected_object_name, str(challenge))

class RequirementModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
        beginners_challenge = Challenge.objects.create(name="Beginner's Challenge",
                                                       thread_id=4448,
                                                       category=Challenge.TIER,
                                                       extra='')
        requirement_1 = Requirement.objects.create(challenge=beginners_challenge,
                                                   number=1,
                                                   mode=Requirement.DEFAULT,
                                                   text="Watch an anime from the recently reviewed section of AniList",
                                                   extra="~!Screenshot: img(https://imgur.com/00000.png)!~",
                                                   extra_newline=True,
                                                   bonus=False)

    def setUp(self):
        # Run once for every test method to setup clean data
        pass

    def test_challenge_label(self):
        requirement = Requirement.objects.get(number=1)
        field_label = requirement._meta.get_field('challenge').verbose_name
        self.assertEquals(field_label, 'challenge')

    def test_number_label(self):
        requirement = Requirement.objects.get(number=1)
        field_label = requirement._meta.get_field('number').verbose_name
        self.assertEquals(field_label, 'number')

    def test_mode_label(self):
        requirement = Requirement.objects.get(number=1)
        field_label = requirement._meta.get_field('mode').verbose_name
        self.assertEquals(field_label, 'mode')

    def test_text_label(self):
        requirement = Requirement.objects.get(number=1)
        field_label = requirement._meta.get_field('text').verbose_name
        self.assertEquals(field_label, 'text')

    def test_extra_label(self):
        requirement = Requirement.objects.get(number=1)
        field_label = requirement._meta.get_field('extra').verbose_name
        self.assertEquals(field_label, 'extra')

    def test_extra_newline_label(self):
        requirement = Requirement.objects.get(number=1)
        field_label = requirement._meta.get_field('extra_newline').verbose_name
        self.assertEquals(field_label, 'extra newline')

    def test_bonus_label(self):
        requirement = Requirement.objects.get(number=1)
        field_label = requirement._meta.get_field('bonus').verbose_name
        self.assertEquals(field_label, 'bonus')

    def test_mode_max_length(self):
        requirement = Requirement.objects.get(number=1)
        max_length = requirement._meta.get_field('mode').max_length
        self.assertEquals(max_length, 1)

    def test_text_max_length(self):
        requirement = Requirement.objects.get(number=1)
        max_length = requirement._meta.get_field('text').max_length
        self.assertEquals(max_length, 250)

    def test_requirement_name_is_requirement_number(self):
        requirement = Requirement.objects.get(number=1)
        expected_object_name = f'{requirement.challenge} Requirement {requirement.number}'
        self.assertEquals(expected_object_name, str(requirement))

class UserModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
        user = User.objects.create(name='omn0mn0m',
                    user_id=403743,
                    avatar_url='https://s4.anilist.co/file/anilistcdn/user/avatar/medium/b403743-wCOMiEI2vm8i.png',
                    is_admin=True)

    def setUp(self):
        # Run once for every test method to setup clean data
        pass

    def test_name_label(self):
        user = User.objects.get(name='omn0mn0m')
        field_label = user._meta.get_field('name').verbose_name
        self.assertEquals(field_label, 'name')

    def test_user_id_label(self):
        user = User.objects.get(name='omn0mn0m')
        field_label = user._meta.get_field('user_id').verbose_name
        self.assertEquals(field_label, 'user id')

    def test_avatar_url_label(self):
        user = User.objects.get(name='omn0mn0m')
        field_label = user._meta.get_field('avatar_url').verbose_name
        self.assertEquals(field_label, 'avatar url')

    def test_is_admin_label(self):
        user = User.objects.get(name='omn0mn0m')
        field_label = user._meta.get_field('is_admin').verbose_name
        self.assertEquals(field_label, 'is admin')

    def test_name_max_length(self):
        user = User.objects.get(name='omn0mn0m')
        max_length = user._meta.get_field('name').max_length
        self.assertEquals(max_length, 50)

    def test_avatar_url_max_length(self):
        user = User.objects.get(name='omn0mn0m')
        max_length = user._meta.get_field('avatar_url').max_length
        self.assertEquals(max_length, 200)

    def test_user_name_is_name(self):
        user = User.objects.get(name='omn0mn0m')
        expected_object_name = f'{user.name}'
        self.assertEquals(expected_object_name, str(user))

class SubmissionModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
        challenge = Challenge.objects.create(name="Beginner's Challenge",
                                 thread_id=4448,
                                 category=Challenge.TIER,
                                 extra='')
        user = User.objects.create(name='omn0mn0m',
                                   user_id=403743,
                                   avatar_url='https://s4.anilist.co/file/anilistcdn/user/avatar/medium/b403743-wCOMiEI2vm8i.png',
                                   is_admin = True)
        submission = Submission.objects.create(user=user,
                                               challenge=challenge,
                                               thread_id=4448,
                                               comment_id=261096)

    def setUp(self):
        # Run once for every test method to setup clean data
        pass

    def test_user_label(self):
        submission = Submission.objects.get(comment_id=261096)
        field_label = submission._meta.get_field('user').verbose_name
        self.assertEquals(field_label, 'user')

    def test_challenge_label(self):
        submission = Submission.objects.get(comment_id=261096)
        field_label = submission._meta.get_field('challenge').verbose_name
        self.assertEquals(field_label, 'challenge')

    def test_thread_id_label(self):
        submission = Submission.objects.get(comment_id=261096)
        field_label = submission._meta.get_field('thread_id').verbose_name
        self.assertEquals(field_label, 'thread id')

    def test_comment_id_label(self):
        submission = Submission.objects.get(comment_id=261096)
        field_label = submission._meta.get_field('comment_id').verbose_name
        self.assertEquals(field_label, 'comment id')

    def test_submission_comment_id_label(self):
        submission = Submission.objects.get(comment_id=261096)
        field_label = submission._meta.get_field('submission_comment_id').verbose_name
        self.assertEquals(field_label, 'submission comment id')

    def test_submission_name_is_challenge_name(self):
        submission = Submission.objects.get(comment_id=261096)
        expected_object_name = f'{submission.challenge.name} Submission'
        self.assertEquals(expected_object_name, str(submission))
