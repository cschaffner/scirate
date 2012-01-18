from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ARXIV_MIRRORS = (
        ('au', 'Australia'),
        ('br', 'Brazil'),
        ('cn', 'China'),
        ('fr', 'France'),
        ('de', 'Germany'),
        ('in', 'India'),
        ('il', 'Israel'),
        ('jp', 'Japan'),
        ('ru', 'Russia'),
        ('es', 'Spain'),
        ('tw', 'Taiwan'),
        ('uk', 'U.K.'),
        ('aps', 'U.S. mirror'),
        ('lanl', 'U.S. mirror'),
    )
    user = models.ForeignKey(User, unique=True)
    mirror_pref = models.CharField(max_length=4, choices=ARXIV_MIRRORS, blank=True, null=True)
    #  arxiv_category_pref

    def __unicode__(self):
        return self.user

class Article(models.Model):
    identifier = models.CharField(max_length=20, primary_key=True)
    title = models.CharField(max_length=200)
    authors = models.CharField(max_length=300)
    abstract = models.TextField()
    date = models.DateField()
    journal_ref = models.CharField(max_length=300, blank=True)
    arxiv_comments = models.CharField(max_length=300, blank = True)
    likes = models.ManyToManyField(User, related_name='liked', blank=True)
    dislikes = models.ManyToManyField(User, related_name='disliked', blank=True)
    abstract_expansions = models.ManyToManyField(User, related_name='abs_expanded', blank=True)
    anonymous_abs_exp = models.IntegerField()
    comments = models.ManyToManyField(User, through='Comment', blank=True)

    def __unicode__(self):
        return self.identifier

class Comment(models.Model):
    user = models.ForeignKey(User)
    article = models.ForeignKey(Article)
    datetime = models.DateTimeField()
    comment = models.TextField()

    def __unicode__(self):
        return self.comment
