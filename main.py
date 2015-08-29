import cgi
import urllib
import os

from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2
import jinja2

# Tell program where your templates are
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates"),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DEFAULT_HOSPITAL_NAME = 'default_hospital'


# We set a parent key on the 'Greetings' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent.  However, the write rate should be limited to
# ~1/second.

def hospital_key(hospital_name=DEFAULT_HOSPITAL_NAME):
    """Constructs a Datastore key for a Hospital entity.

    We use hospital_name as the key.
    """
    return ndb.Key('Hospital', hospital_name)


class HospitalStaff(ndb.Model):
    """Sub model for representing a hospital staff."""
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)


class TriageReading(ndb.Model):
    """A main model for representing an individual Patient entry."""
    hospitalStaff = ndb.StructuredProperty(HospitalStaff)
    nricNum = ndb.StringProperty()
    temperature = ndb.StringProperty(indexed=False)
    heartrate = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)


class MainPage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('main.html')
        self.response.write(template.render())


class ListAll(webapp2.RequestHandler):
    def get(self):
        hospital_name = self.request.get('hospital_name',
                                         DEFAULT_HOSPITAL_NAME)
        readings_query = TriageReading.query(
            ancestor=hospital_key(hospital_name)).order(-TriageReading.date)
        readings = readings_query.fetch(10)

        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'user': user,
            'readings': readings,
            'hospital_name': urllib.quote_plus(hospital_name),
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('listall.html')
        self.response.write(template.render(template_values))


class Triage(webapp2.RequestHandler):
    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each
        # Greeting is in the same entity group. Queries across the
        # single entity group will be consistent. However, the write
        # rate to a single entity group should be limited to
        # ~1/second.
        hospital_name = self.request.get('hospital_name',
                                         DEFAULT_HOSPITAL_NAME)
        reading = TriageReading(parent=hospital_key(hospital_name))

        if users.get_current_user():
            reading.hospitalStaff = HospitalStaff(
                identity=users.get_current_user().user_id(),
                email=users.get_current_user().email())

        nric_of_patient = self.request.get('nricNum')
        temp_of_patient = self.request.get('temperature')
        heartrate_of_patient = self.request.get('heartbeat')

        # Do some input validation before putting data into Datastore
        if (nric_of_patient.isalnum() and len(nric_of_patient) == 9
            and temp_of_patient.isdigit() and heartrate_of_patient.isdigit()):
            reading.nricNum = nric_of_patient
            reading.temperature = heartrate_of_patient
            reading.heartrate = heartrate_of_patient
            reading.put()

        query_params = {'hospital_name': hospital_name}
        self.redirect('/?' + urllib.urlencode(query_params))


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/listall', ListAll),
    ('/triage', Triage),
], debug=True)
