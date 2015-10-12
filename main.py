import urllib
import os
import pytz

from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2
import jinja2
import random

# Tell program where your templates are
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates"),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


def datetimeformat(value, format='(%d-%m-%Y) %H:%M:%S'):
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
    temperature = ndb.FloatProperty(indexed=False, default=0)
    heart_rate = ndb.IntegerProperty(indexed=False, default=0)
    bp = ndb.IntegerProperty(indexed=False, default=0)
    respo_rate = ndb.IntegerProperty(indexed=False, default=0)
    date = ndb.DateTimeProperty(auto_now_add=True)
    travel_history = ndb.StringProperty(indexed=False)
    chief_complaint = ndb.StringProperty(indexed=False)
    classification = ndb.IntegerProperty(indexed=False, default=0)


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
        nric_num = self.request.get('nric')
        if len(nric_num) == 0 :
            template_values = {
                'nric_num': nric_num,
            }
            template = JINJA_ENVIRONMENT.get_template('registration.html')
            self.response.write(template.render(template_values))
        else:
            reading = PatientProfile.get_by_id(id=nric_num,  parent=hospital_key(DEFAULT_HOSPITAL_NAME))
            template_values = {
                'nric_num': nric_num,
                'reading': reading
            }
            template = JINJA_ENVIRONMENT.get_template('registration_scanner.html')
            self.response.write(template.render(template_values))

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


class Triage(webapp2.RequestHandler):
    def get(self):
        nric_num = self.request.get('nric')
        reading = PatientProfile.get_by_id(id=nric_num,  parent=hospital_key(DEFAULT_HOSPITAL_NAME))

        if reading.classification == 0:
            measurements = classify_patient()
        else:
            measurements = {'bp': reading.bp, 'respo_rate': reading.respo_rate, 'temperature': round(reading.temperature, 1),
                    'heart_rate': reading.heart_rate, 'classification': reading.classification}

        template_values = {
            'nric_num': nric_num,
            'reading': reading,
            'measurements': measurements
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
        patient_bp = self.request.get('bp')
        patient_heart_rate = self.request.get('heart_rate')
        patient_respo_rate = self.request.get('respo_rate')
        patient_temperature = self.request.get('temperature')
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
            # reading.bp = int(patient_bp)
            # reading.temperature = float(patient_temperature)
            # reading.respo_rate = int(patient_respo_rate)
            # reading.heart_rate = int(patient_heart_rate)
            reading.classification = int(patient_classification)
            reading.put()

        query_params = {'hospital_name': DEFAULT_HOSPITAL_NAME}
        self.redirect("listall")


def classify_patient():
    bp = random.randint(60, 210) # typical range is 70 to 200
    respo_rate = random.randint(1, 60) # typical range is 12-20 for adults, 60 for newborns
    # Will use actual data for the two variables below
    temperature = random.uniform(35.5, 41.0)
    heart_rate = random.randint(40, 150)
    measurements = {'bp': bp, 'respo_rate': respo_rate, 'temperature': round(temperature, 1),
                    'heart_rate': heart_rate}

    sum = 0;
    # Calculate bp score
    if bp <= 70:
        sum += 3
    elif bp <= 80:
        sum += 2
    elif bp <= 100:
        sum += 1
    elif bp <= 199:
        sum += 0
    else:
        sum += 2

    if respo_rate < 9:
        sum += 3
    elif respo_rate <= 14:
        sum += 1
    elif respo_rate <= 20:
        sum += 0
    elif respo_rate <= 29:
        sum += 1
    else:
        sum += 3

    if temperature < 35:
        sum += 3
    elif temperature <= 38.4:
        sum += 0
    else:
        sum += 2

    if heart_rate <= 40:
        sum += 2
    elif heart_rate <= 50:
        sum += 1
    elif heart_rate <= 100:
        sum += 0
    elif heart_rate <= 110:
        sum += 1
    elif heart_rate <= 129:
        sum += 2
    else:
        sum += 3

    measurements['MEWS'] = sum

    classification = 0
    if sum <= 2:
        classification = 4
    elif sum <= 4:
        classification = 3
    elif sum <= 8:
        classification = 2
    else:
        classification = 1

    measurements['classification'] = classification
    return measurements


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
