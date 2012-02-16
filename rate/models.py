from django.db import models
from django.contrib.auth.models import User
from datetime import *
from xml.dom.minidom import parse
import urllib2

# import the logging library
import logging

class DownloadAction(models.Model):
    # all times in this project are UTC
    
    # when has data been downloaded from arxiv
    download_time = models.DateTimeField()
    # when will be new data available from the arxiv
    nextdata = models.DateTimeField()
    # how many articles have been downloaded
    num_new_articles = models.IntegerField()
    # how many articles have been updated (i.e. were already in the database)
    # these articles are included in the arxiv-update, as every change, also in the
    # metadata, shows up in the arxiv-listing.
    # One could silently update the article in the database with this latest data
    # (which actually means that the original "voting" 
    #  might have been for a previous version of the article, 
    # TODO: maybe the voting should be for a particular version instead?)
    # So far, nothing is done with articles that already exist in the database
    num_updated_articles = models.IntegerField()

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
    # UserProfile has a 1-to-1 relation with django's built-in User-class which is used for authentication
    # i.e. it just extends that class
    user = models.ForeignKey(User, unique=True)
    # users can have a preference for a particular arxiv-mirror
    mirror_pref = models.CharField(max_length=4, choices=ARXIV_MIRRORS, blank=True, null=True)
    # TODO: have a preference for a particular arxiv-category
    # so far, the whole project is only for quant-ph.
    # arxiv_category_pref

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
        updated=0
        if lastdown.nextdata < now:
            # download required
    
            URL = "http://export.arxiv.org/oai2?verb=ListRecords&set=physics:quant-ph&from=%d-%02d-%02d&until=%d-%02d-%02d&metadataPrefix=arXivRaw" % \
            (lastdown.download_time.year, lastdown.download_time.month, lastdown.download_time.day, now.year, now.month, now.day)
            logger.info(URL)
            
            try:
                xmlfile=urllib2.urlopen(URL)
            except urllib2.HTTPError, e:
                if e.code == 503:
                    # don't do anything at the moment, but wait until articles are loaded again
                    # in particular, do not add a DownloadAction event 
                    return
                else:
                    # raise the error
                    raise
            except urllib2.URLError, e:
                logger.error('we are probably offline. Do not do anything for now.')
                return
                    
            
            # parse xmlfile into a DOM-object
            dom = parse(xmlfile)
#            dom = parse('biglist.xml')
    
            # now we can maneuver around in the DOM-object to harvest the needed data
            
            # get the a list of all "articles"
            articles = dom.getElementsByTagName('record')
        
            for node in articles:
                # get the metadata
                nodedata = node.childNodes.item(3).childNodes.item(1)
                # get the identifier
                ident = nodedata.getElementsByTagName('id').item(0).childNodes.item(0).nodeValue
                if Article.objects.filter(identifier=ident).count()==0:
                    # article with this identifier does not exist yet, create a new one
                    art = Article()
                    art.identifier = nodedata.getElementsByTagName('id').item(0).childNodes.item(0).nodeValue
                    art.title = nodedata.getElementsByTagName('title').item(0).childNodes.item(0).nodeValue
                    art.authors = nodedata.getElementsByTagName('authors').item(0).childNodes.item(0).nodeValue
                    art.abstract = nodedata.getElementsByTagName('abstract').item(0).childNodes.item(0).nodeValue
                    if nodedata.getElementsByTagName('journal-ref').length==1:
                        art.journal_ref = nodedata.getElementsByTagName('journal-ref').item(0).childNodes.item(0).nodeValue
                    if nodedata.getElementsByTagName('comments').length==1:
                        art.arxiv_comments = nodedata.getElementsByTagName('comments').item(0).childNodes.item(0).nodeValue
                    # determine mailing date from first available version
                    datestring = nodedata.getElementsByTagName('version').item(0).childNodes.item(0).childNodes.item(0).nodeValue
                    date = datetime.strptime(datestring,'%a, %d %b %Y %H:%M:%S GMT')
                    art.date = self.mailingdata(date).date()
                    
                    # initialize scores:
                    art.anonymous_abs_exp = 0
                    art.score = 0
                    art.save()
                    added += 1
                else:
                    # TODO: think about whether article info should be updated or not
                    # or maybe just journal_ref ??
                    updated += 1  
            
            # register download-action
            down=DownloadAction()
            down.download_time=now
            down.nextdata=self.nextdata(now)
            down.num_new_articles = added
            down.num_updated_articles = updated
            down.save()
            
            logger.info("Added %d articles, and updated %d" % (added,updated))
                        
            return added
        else:
            return 0
    
    def mailingdata(self,upload):
        # returns the date of the mailing in which an article will be announced  which is uploaded at "upload" 
        
        # Get an instance of a logger
        logger = logging.getLogger('scirate.rate')

        # first move to the next 21:00 GMT
        mailing = datetime(upload.year,upload.month,upload.day,21,0)
        diff = mailing - upload
        logger.debug(diff)
        if diff.total_seconds() < 0:
            tom = mailing + timedelta(days=1)
            mailing=datetime(tom.year,tom.month,tom.day,21,0)
        logger.debug('after corr:')
        logger.debug(mailing)
        
        if mailing.weekday()>4: # larger than Friday
            # then move to Monday
            mailing=mailing+timedelta(days=7-mailing.weekday())
            logger.debug('moved to monday: ')
            logger.debug(mailing)      
            
        # now we still have to add a day
        if mailing.weekday() <4: # if it's Monday to Thursday
            # we can simply add a day
            mailing=mailing+timedelta(days=1)
            logger.debug('simply add one day')
        elif mailing.weekday() == 4: # it it's Friday
            # we need to move it to Monday
            mailing=mailing+timedelta(days=3)
            logger.debug('move to monday, add 3 days')

        return mailing
    
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
            tom = now + timedelta(days=1)
            nextdata=datetime(tom.year,tom.month,tom.day,4,0)
        
        if nextdata.weekday()>4: # larger than Friday
            # then move to Monday
            nextdata=nextdata+timedelta(days=7-nextdata.weekday())      
        return nextdata
        

class Article(models.Model):
    # model of an article
    # identifier as primary index, has to be unique
    identifier = models.CharField(max_length=20, primary_key=True)
    title = models.CharField(max_length=200)
    # string of names
    authors = models.CharField(max_length=300)
    abstract = models.TextField()
    # the date of the mailing the article appeared first
    date = models.DateField()
    journal_ref = models.CharField(max_length=300, blank=True)
    arxiv_comments = models.CharField(max_length=300, blank = True)

    # many-to-many relation with Users to indicate a "like", "dislike" and "abstract_expansion" votes
    likes = models.ManyToManyField(User, related_name='liked', blank=True)
    dislikes = models.ManyToManyField(User, related_name='disliked', blank=True)
    abstract_expansions = models.ManyToManyField(User, related_name='abs_expanded', blank=True)

    # number of anonymous abstract extensions
    anonymous_abs_exp = models.IntegerField()
    # score calculated by self.updatescore, basically #likes - #dislikes
    # [CS: it feels a big weird to have this number as property of the class, but it turns out to be 
    #  simpler this way. Otherwise, retrieving articles sorted according to score=#likes-#dislikes
    #  would require custom SQL-code, and I'm trying to avoid that in order to keep compatibility 
    #  with arbitrary databases.]
    score = models.IntegerField()
    # many-to-many relation with Users, the actual comment has its own class below
    # maybe commenting should be rather done with the Django-internal commenting functions?
    comments = models.ManyToManyField(User, through='Comment', blank=True)
    # the model-manager above contains the methods that can be called on Article (such as "update")
    objects = ArticleManager()

    def __unicode__(self):
        return self.identifier
    
    def updatescore(self):
        # updates the score of a paper
        
        # Get an instance of a logger
        logger = logging.getLogger('scirate.rate')
        self.score = self.likes.count() - self.dislikes.count()
        self.save()
        logger.debug('updated score of '+self.identifier+' to '+str(self.score))
        return self.score
        
# probably not necessary, as there are only a few (AJAX-)events when the score actually needs to be updated
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
