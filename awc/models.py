from django.db import models

from core.models import User

# Challenge Defaults Models
class Challenge(models.Model):
    GENRE = 'GEN'
    TIMED = 'TIM'
    TIER = 'TIE'
    COLLECTION = 'COL'
    CLASSIC = 'CLA'
    PUZZLE = 'PUZ'
    SPECIAL = 'SPE'

    CATEGORY_CHOICES = [
        (GENRE, 'Genre'),
        (TIMED, 'Timed'),
        (TIER, 'Tier'),
        (COLLECTION, 'Collection'),
        (CLASSIC, 'Classic'),
        (PUZZLE, 'Puzzle'),
        (SPECIAL, 'Special'),
    ]
    
    name = models.CharField(max_length=50)
    thread_id = models.IntegerField()
    category = models.CharField(
        max_length = 3,
        choices = CATEGORY_CHOICES,
        default = TIMED,
    )
    extra = models.TextField(blank=True, default='')

    prerequisites = models.ManyToManyField('self', symmetrical=False)

    allows_up_to_date = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Requirement(models.Model):
    # Difficulty mode stuff
    DEFAULT = 'D'
    EASY = 'E'
    NORMAL = 'N'
    HARD = 'H'
    BONUS = 'B'

    MODE_CHOICES = [
        (DEFAULT, 'Default'),
        (EASY, 'Easy'),
        (NORMAL, 'Normal'),
        (HARD, 'Hard'),
        (BONUS, 'Bonus'),
    ]

    # Completed status stuff (doesn't get saved in database)
    NOT_COMPLETED = 'O'
    COMPLETED = 'X'
    UP_TO_DATE = 'U'

    COMPLETED_STATUS_CHOICES = [
        (NOT_COMPLETED, 'Not Completed'),
        (COMPLETED, 'Completed'),
        (UP_TO_DATE, 'Up-to-date')
    ]

    # Fields
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)

    number = models.IntegerField()
    mode = models.CharField(
        max_length = 1,
        choices = MODE_CHOICES,
        default = DEFAULT,
    )
    text = models.CharField(max_length=250)
    extra = models.TextField(blank=True, default='')
    extra_newline = models.BooleanField(default=False)

    bonus = models.BooleanField(default=False)

    # For challenges that require a specific anime
    anime_title = models.CharField(max_length=100, blank=True, default='')
    anime_link = models.CharField(max_length=50, blank=True, default='')

    # For weirdly formatted requirements
    force_raw_edit = models.BooleanField(default=False)
    raw_requirement = models.TextField(blank=True, default='')

    def __str__(self):
        return "{} Requirement {}".format(self.challenge, self.number)

class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    thread_id = models.IntegerField()
    comment_id = models.IntegerField()

    submission_comment_id = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return "{} Submission".format(self.challenge)
