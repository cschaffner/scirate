from django.db import models
from django.contrib.auth.models import User
from datetime import *
from xml.dom.minidom import parse
import urllib

# import the logging library
import logging

class DownloadAction(models.Model):
    # all times in this project are UTC
    download_time = models.DateTimeField()
    nextdata = models.DateTimeField()
    num_new_articles = models.IntegerField()
    num_skipped_articles = models.IntegerField()

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

class ArticleManager(models.Manager):
    def update(self):
        # Get an instance of a logger
        logger = logging.getLogger('scirate.rate')

        # first check if the database of downloaded articles is up to date
        lastdown=DownloadAction.objects.order_by('download_time').reverse()[:1][0]
        now=datetime.utcnow()
        added=0
        skipped=0
        if lastdown.nextdata < now:
            # download required
    
            URL = "http://export.arxiv.org/oai2?verb=ListRecords&set=physics:quant-ph&from=%d-%02d-%02d&until=%d-%02d-%02d&metadataPrefix=arXivRaw" % \
            (lastdown.download_time.year, lastdown.download_time.month, lastdown.download_time.day, now.year, now.month, now.day)
            logger.info(URL)
            
            dom = parse(urllib.urlopen(URL))
#            dom = parse('biglist.xml')
    
            articles = dom.getElementsByTagName('record')
        
            for node in articles:
                nodedata = node.childNodes.item(3).childNodes.item(1)
                ident = nodedata.getElementsByTagName('id').item(0).childNodes.item(0).nodeValue
                if Article.objects.filter(identifier=ident).count()==0:
                    art = Article()
                    art.identifier = nodedata.getElementsByTagName('id').item(0).childNodes.item(0).nodeValue
                    art.title = nodedata.getElementsByTagName('title').item(0).childNodes.item(0).nodeValue
                    art.authors = nodedata.getElementsByTagName('authors').item(0).childNodes.item(0).nodeValue
                    art.abstract = nodedata.getElementsByTagName('abstract').item(0).childNodes.item(0).nodeValue
                    if nodedata.getElementsByTagName('journal-ref').length==1:
                        art.journal_ref = nodedata.getElementsByTagName('journal-ref').item(0).childNodes.item(0).nodeValue
                    if nodedata.getElementsByTagName('comments').length==1:
                        art.arxiv_comments = nodedata.getElementsByTagName('comments').item(0).childNodes.item(0).nodeValue
                    # determine date from first available version
                    datestring = nodedata.getElementsByTagName('version').item(0).childNodes.item(0).childNodes.item(0).nodeValue
                    date = datetime.strptime(datestring,'%a, %d %b %Y %H:%M:%S GMT')
                    art.date = date.date()
                    art.anonymous_abs_exp = 0
                    art.save()
                    added += 1
                else:
                    skipped += 1  
            
            # register download-action
            down=DownloadAction()
            down.download_time=now
            down.nextdata=self.nextdata(now)
            down.num_new_articles = added
            down.num_skipped_articles = skipped
            down.save()
            
            logger.info("Added %d articles, and skipped %d" % (added,skipped))
                        
            return added
        else:
            return 0
    
    def nextdata(self,now):
        # returns the next datetime after now (given in UTC) when new data will be available to harvest on the arxiv
        # on http://arxiv.org/help/oa/index, they say that 
        # Update schedule -- New papers are accepted daily and metadata is made available via the OAI-PMH interface 
        # by 10pm EST Sunday through Thursday.
        
        # I think that 10pm EST Sunday through Thursday corresponds to
        # 3am UTC Monday through Friday
        # to be on the safe side, let's say 4am UTC Monday through Friday
        
        # let's first move to the next 4am
        nextdata=datetime(now.year,now.month,now.day,4,0)
        diff=nextdata-now
        if diff.total_seconds() < 0:
            nextdata=datetime(now.year,now.month,now.day+1,4,0)
        
        if nextdata.weekday()>4: # larger than Friday
            # then move to Monday
            nextdata=nextdata+timedelta(days=7-nextdata.weekday())      
        return nextdata
        

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
    score = models.IntegerField()
    comments = models.ManyToManyField(User, through='Comment', blank=True)
    objects = ArticleManager()

    def __unicode__(self):
        return self.identifier
    
    def updatescore(self):
        # Get an instance of a logger
        logger = logging.getLogger('scirate.rate')
        self.score = self.likes.count() - self.dislikes.count()
        self.save()
        logger.info('updated score of '+self.identifier+' to '+str(self.score))
        return self.score
        
#    def save(self, *args, **kwargs):
#        self.updatescore()
#        super(Article, self).save(*args, **kwargs) # Call the "real" save() method.
        
        

class Comment(models.Model):
    user = models.ForeignKey(User)
    article = models.ForeignKey(Article)
    datetime = models.DateTimeField()
    comment = models.TextField()

    def __unicode__(self):
        return self.comment
