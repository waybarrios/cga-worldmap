# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.contrib.auth.models import User
from account.models import Account

class Migration(DataMigration):

    def forwards(self, orm):
        # we need to associate each user to an account object
        for user in User.objects.all():
            a = Account()
            a.user = user
            a.language = 'en' # default language
            a.save()

    def backwards(self, orm):
        # we need to delete all the accounts records
        Account.objects.all().delete()

