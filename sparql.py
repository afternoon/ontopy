from urllib import urlencode
from urllib2 import build_opener, HTTPBasicAuthHandler, \
    HTTPPasswordMgrWithDefaultRealm, urlopen
from xml.etree.cElementTree import dump, parse


SPARQL_NS = "http://www.w3.org/2005/sparql-results#"


class SPARQLEndpoint(object):
    """Low-level interface to a SPARQL endpoint via HTTP.
    
    XML result representations are received and return as ElementTree objects.

    """
    def __init__(self, base_url, username=None, password=None):
        """Create an SPARQLEndpoint object for an endpoint url, optionally
        specifying username and password for HTTP Basic Authentication.
        
        """
        self.base_url = base_url
        if username and password:
            pm = HTTPPasswordMgrWithDefaultRealm()
            pm.add_password(None, base_url, username, password)
            handler = HTTPBasicAuthHandler(pm)
            self.open = build_opener(handler).open
        else:
            self.open = urlopen

    def __repr__(self):
        return "<SPARQLEndpoint: %s>" % self.base_url

    def query(self, query):
        """Run a SPARQL query against the endpoint."""
        args = {"query": query}
        url = "%s?%s" % (self.base_url, urlencode(args))
        return parse(self.open(url))

    def simple_query(self, query):
        etree = self.query(query)
        xpath = "//{%(ns)s}results/{%(ns)s}result/{%(ns)s}binding/{%(ns)s}uri" % {"ns": SPARQL_NS}
        return [uri.text for uri in etree.findall(xpath)]

    def classes(self):
        """Get a list of all the classes of things stored in the default graph
        of this endpoint.
        
        """
        return self.simple_query("""select distinct ?class where { ?a a ?class }""")

    def properties(self, class_uri):
        """Get a list of all the properties of things known about the specified
        class. Note not all 
        
        """
        return self.simple_query("""select distinct ?property where { ?object a <%s> . ?object ?property ?x }""" % class_uri)

    def resources(self, class_uri):
        return self.simple_query("""select ?resource where { ?resource a <%s> }""" % class_uri)
