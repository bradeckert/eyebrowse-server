from django.db import models
from django.contrib.auth.models import User

from datetime import datetime

class FavData(models.Model):
    """
        Model to hold favorite data that is updated according to django cron tasks
    """
    user = models.ForeignKey(User)

    domain = models.URLField(max_length=2000, default='')
    favIconUrl = models.URLField(max_length=2000, default='')
    
    visit_count = models.IntegerField(blank=True, null=True)
    total_time = models.IntegerField(blank=True, null=True) # store in ms

    def save(self, *args, **kwargs):
        if self.favIconUrl == '':
            self.favIconUrl = "http://www.google.com/s2/favicons?domain=%s" % self.domain
        
        super(FavData, self).save(*args, **kwargs)
        


    def __unicode__(self):
          return "FavData item %s for %s visited %s" % (self.domain, self.user.username, self.visit_count)