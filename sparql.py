from urllib import urlencode
from urllib2 import build_opener, HTTPBasicAuthHandler, \
    HTTPPasswordMgrWithDefaultRealm, urlopen
from xml.etree.cElementTree import dump, parse

from rdflib.term import URIRef, Literal
from rdflib.namespace import Namespace


SPARQL_NS = "http://www.w3.org/2005/sparql-results#"


class ACombinator(object):
    pass
a = ACombinator()


def format_literal(o):
    if isinstance(o, ACombinator):
        return u"a"
    elif isinstance(o, URIRef):
        return u"<%s>" % o
    elif isinstance(o, basestring) and o[0] != u"?":
        return u"\"%s\"" % o
    else:
        return o


def format_tuple(tp):
    s, p, o = tp
    return u"%s %s %s" % (format_literal(s), format_literal(p), format_literal(o))


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


class SelectQuery(object):
    """Represent a SPARQL query. Allow queries to be built incrementally, a la
    Django's ORM, jQuery, rdfQuery, etc.
    
    >>> q = SelectQuery()
    >>> band = URIRef("http://dbpedia.org/ontology/Band")
    >>> q2 = q.select("?resource").where("?resource", a, band)
    >>> str(q2)
    'select ?resource where { ?resource a <http://dbpedia.org/ontology/Band> }'
    >>> q3 = q2.limit(1)
    >>> str(q3)
    'select ?resource where { ?resource a <http://dbpedia.org/ontology/Band> } limit 1'
    >>> rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
    >>> q4 = q3.optional("?resource", rdfs.label, "Kraftwerk")
    >>> str(q4)
    'select ?resource where { ?resource a <http://dbpedia.org/ontology/Band> optional { ?resource <http://www.w3.org/2000/01/rdf-schema#label> "Kraftwerk" } } limit 1'

    This class uses a dictionary to keep track of the various parts of the
    query. Only "flat" queries can be represented. A SPARQL query is a tree
    however, due to the complexity of the where clause. An improved version of
    this class would represent the query as so.
    
    """
    def __init__(self, q=None):
        self._q = q if q else self._empty_query()

    def _empty_query(self):
        return {"select": [], "distinct": False, "where": [], "optional": [],
                "filter": [], "order_by": [], "limit": None, "offset": None}

    def _clone(self):
        return self.__class__(self._q)

    def select(self, var_or_vars):
        cl = self._clone()
        if isinstance(var_or_vars, basestring):
            cl._q["select"].append(var_or_vars)
        else:
            cl._q["select"] += var_or_vars
        return cl

    def where(self, subj, pred, obj):
        cl = self._clone()
        cl._q["where"].append((subj, pred, obj))
        return cl

    def optional(self, subj, pred, obj):
        cl = self._clone()
        cl._q["optional"].append((subj, pred, obj))
        return cl

    def limit(self, limit):
        cl = self._clone()
        cl._q["limit"] = limit
        return cl

    def __repr__(self):
        return "<Query: %s>" % self

    def __str__(self):
        """Return this query as a SPARQL query string."""
        q = []

        # select vars
        q.append(u"select")
        if self._q["select"]:
            q += [var for var in self._q["select"]]
        else:
            q.append(u"*")

        # where clauses
        if self._q["where"]:
            q += [u"where", u"{"]
            q += [format_tuple(tp) for tp in self._q["where"]]

            if self._q["optional"]:
                q += [u"optional", u"{"]
                q += [format_tuple(tp) for tp in self._q["optional"]]
                q.append(u"}")

            q.append(u"}")
        else:
            raise MalformattedQueryException("Missing where clause")

        # order by
        if self._q["order_by"]:
            q.append(u"order by")
            q.append(u", ".join([o for o in self._q["order_by"]]))

        # limit number of rows returned
        if self._q["limit"] is not None:
            q += [u"limit", str(self._q["limit"])]

        # offset row results
        if self._q["offset"] is not None:
            q += [u"offset", str(self._q["offset"])]

        return u" ".join(q)


if __name__ == "__main__":
    from doctest import testmod
    testmod()
