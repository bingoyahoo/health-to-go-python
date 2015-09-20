import cgi
import urllib
import os
import pytz

from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2
import jinja2

# Tell program where your templates are
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates"),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def datetimeformat(value, format='%H:%M:%S / %d-%m-%Y'):
    return value.strftime(format)

JINJA_ENVIRONMENT.filters['datetimeformat'] = datetimeformat

DEFAULT_HOSPITAL_NAME = 'SGH'

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


class PatientProfile(ndb.Model):
    """A main model for representing an individual Patient entry."""
    hospitalStaff = ndb.StructuredProperty(HospitalStaff)
    # Profile information
    name = ndb.StringProperty()
    nric_num = ndb.StringProperty()
    gender = ndb.StringProperty(indexed=False, choices=set(["male", "female"]))
    nationality = ndb.StringProperty(indexed=False)
    dob = ndb.StringProperty(indexed=False)
    race = ndb.StringProperty(indexed=False)
    mobile_number = ndb.StringProperty(indexed=False)
    address = ndb.StringProperty(indexed=False)
    add_info = ndb.StringProperty(indexed=False)
    # Triage Readings
    temperature = ndb.StringProperty(indexed=False)
    heartrate = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)
    travel_history = ndb.StringProperty(indexed=False)
    chief_complaint = ndb.StringProperty(indexed=False)
    classification = ndb.IntegerProperty(indexed=False, default=3)


class MainPage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('main.html')
        self.response.write(template.render())


class ListAll(webapp2.RequestHandler):
    def post(self):
        nric_num = self.request.get('nric_num')
        self.redirect("/triage?nric=" + nric_num)

    def get(self):
        hospital_name = self.request.get('hospital_name',
                                         DEFAULT_HOSPITAL_NAME)
        readings_query = PatientProfile.query(
            ancestor=hospital_key(hospital_name)).order(PatientProfile.date)
        readings = readings_query.fetch(100)

        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        local_tz = pytz.timezone('Asia/Singapore')
        for reading in readings:
            dt = reading.date
            reading.date = dt.replace(tzinfo=pytz.utc).astimezone(local_tz).replace(tzinfo=None)

        template_values = {
            'user': user,
            'readings': readings,
            'hospital_name': urllib.quote_plus(hospital_name),
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('listall.html')
        self.response.write(template.render(template_values))

class Create(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('registration.html')
        self.response.write(template.render())

    def post(self):
        # We set the same parent key on the 'PatientProfile' to ensure each
        # PatientProfile is in the same entity group. Queries across the
        # single entity group will be consistent. However, the write
        # rate to a single entity group should be limited to
        # ~1/second.
        patient_nric = self.request.get('nricNum')
        reading = PatientProfile( id=patient_nric, parent=hospital_key(DEFAULT_HOSPITAL_NAME))

        if users.get_current_user():
            reading.hospitalStaff = HospitalStaff(
                identity=users.get_current_user().user_id(),
                email=users.get_current_user().email())

        patient_name = self.request.get('name')
        patient_gender = self.request.get('gender')
        patient_dob = self.request.get('dob')
        patient_race = self.request.get('race')
        patient_mobile_num = self.request.get('mobile_number')
        patient_address = self.request.get('address')
        patient_add_info = self.request.get('add_info')
        patient_nationality = self.request.get('nationality')

        # Do some input validation before putting data into Datastore
        if patient_nric.isalnum() and len(patient_nric) == 9 :
            reading.name = patient_name
            reading.nric_num = patient_nric
            reading.gender = patient_gender
            reading.dob = patient_dob
            reading.race = patient_race
            reading.mobile_number = patient_mobile_num
            reading.address = patient_address
            reading.add_info = patient_add_info
            reading.nationality = patient_nationality
            reading.put()

        query_params = {'hospital_name': DEFAULT_HOSPITAL_NAME}
        self.redirect("listall")
        # self.redirect('listall/?' + urllib.urlencode(query_params))


class Triage(webapp2.RequestHandler):
    def get(self):
        nric_num = self.request.get('nric')
        readings = PatientProfile.query(PatientProfile.nric_num== nric_num)

        template_values = {
            'nric_num': nric_num,
            'readings': readings
        }
        template = JINJA_ENVIRONMENT.get_template('triage.html')
        self.response.write(template.render(template_values))

    def post(self):
        # We set the same parent key on the 'PatientProfile' to ensure each
        # PatientProfile is in the same entity group. Queries across the
        # single entity group will be consistent. However, the write
        # rate to a single entity group should be limited to
        # ~1/second.
        patient_nric = self.request.get('nric')
        reading = PatientProfile( id=patient_nric, parent=hospital_key(DEFAULT_HOSPITAL_NAME))

        if users.get_current_user():
            reading.hospitalStaff = HospitalStaff(
                identity=users.get_current_user().user_id(),
                email=users.get_current_user().email())

        patient_name = self.request.get('name')
        patient_gender = self.request.get('gender')
        patient_dob = self.request.get('dob')
        patient_race = self.request.get('race')
        patient_mobile_num = self.request.get('mobile_number')
        patient_address = self.request.get('address')
        patient_add_info = self.request.get('add_info')
        patient_nationality = self.request.get('nationality')
        # Get triage information
        patient_travel_history = self.request.get('travel_history')
        patient_chief_complaint = self.request.get('chief_complaint')
        patient_classification = self.request.get('classification')

        # Do some input validation before putting data into Datastore
        if patient_nric.isalnum() and len(patient_nric) == 9 :
            reading.name = patient_name
            reading.nric_num = patient_nric
            reading.gender = patient_gender
            reading.dob = patient_dob
            reading.race = patient_race
            reading.mobile_number = patient_mobile_num
            reading.address = patient_address
            reading.add_info = patient_add_info
            reading.nationality = patient_nationality
            # Add triage information into database
            reading.travel_history = patient_travel_history
            reading.chief_complaint= patient_chief_complaint
            reading.classification = int(patient_classification)
            reading.put()

        query_params = {'hospital_name': DEFAULT_HOSPITAL_NAME}
        self.redirect("listall")

class Faq(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('faq.html')
        self.response.write(template.render())

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/listall', ListAll),
    ('/create', Create),
    ('/triage', Triage),
    ('/faq', Faq)
], debug=True)
