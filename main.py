import cgi
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2

MAIN_PAGE_FOOTER_TEMPLATE = """\
    <form action="/sign?%s" method="post">
      <div>NRIC: <input type="text" name="nricNum" placeholder="S1234567A"></div>
      <div>Temperature: <input type="text" name="temperature" placeholder="37"></div>
      <div>Heartbeat: <input type="text" name="heartbeat" placeholder="80"></div>
      <div><input type="submit" value="Insert Reading"></div>
    </form>
    <hr>
    <form>Hospital name:
      <input value="%s" name="hospital_name">
      <input type="submit" value="switch">
    </form>
    <a href="%s">%s</a>
  </body>
</html>
"""

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
    heartRate = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.write('<html><body>')
        hospital_name = self.request.get('hospital_name',
                                          DEFAULT_HOSPITAL_NAME)

        # Ancestor Queries, as shown here, are strongly consistent
        # with the High Replication Datastore. Queries that span
        # entity groups are eventually consistent. If we omitted the
        # ancestor from this query there would be a slight chance that
        # Greeting that had just been written would not show up in a
        # query.
        triage_readings_query = TriageReading.query(
            ancestor=hospital_key(hospital_name)).order(-TriageReading.date)
        readings = triage_readings_query.fetch(10)

        user = users.get_current_user()
        for reading in readings:
            if reading.hospitalStaff:
                hospitalStaff = reading.hospitalStaff.email
                if user and user.user_id() == reading.hospitalStaff.identity:
                    hospitalStaff += ' (You)'
                self.response.write('<b>%s</b> wrote:' % hospitalStaff)
            else:
                self.response.write('An anonymous person wrote:')
            self.response.write('<blockquote>NRIC: %s</blockquote>' % reading.nricNum)
            self.response.write('<blockquote>Temperature: %s</blockquote>' % reading.temperature)
            self.response.write('<blockquote>Heartrate: %s</blockquote>' % reading.heartRate)


        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        # Write the submission form and the footer of the page
        sign_query_params = urllib.urlencode({'hospital_name':
                                              hospital_name})
        self.response.write(MAIN_PAGE_FOOTER_TEMPLATE %
                            (sign_query_params, cgi.escape(hospital_name),
                             url, url_linktext))

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
        heartrate_of_patient = self.request.get('heartRate')

        if (nric_of_patient.isalnum() and len(nric_of_patient) == 9 and temp_of_patient.isdigit() and heartrate_of_patient.isdigit()):
            reading.nricNum = nric_of_patient
            reading.temperature = self.request.get('temperature')
            reading.heartRate - self.request.get('heartRate')
            reading.put()

        query_params = {'hospital_name': hospital_name}
        self.redirect('/?' + urllib.urlencode(query_params))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sign', Triage),
], debug=True)