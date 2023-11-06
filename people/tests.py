from django.test import TestCase

# Create your tests here.
from views.ldapView import find_ad_users, get_attributes

class PeopleTestCase(TestCase):
    def testConnection(self):
        #find_ad_users('aprende\cmalvaez')
        get_attributes('cmalvaez', 'Aprende2022')


