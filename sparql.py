from copy import deepcopy
from functools import update_wrapper
from urllib import urlencode
from urllib2 import build_opener, HTTPBasicAuthHandler, \
    HTTPError, HTTPPasswordMgrWithDefaultRealm, urlopen
from xml.etree.cElementTree import dump, parse

from rdflib.term import URIRef, Literal
from rdflib.namespace import Namespace


SPARQL_NS = "http://www.w3.org/2005/sparql-results#"


class SPARQLQueryException(Exception):
    pass


class APredicate(object):
    pass
a = APredicate()


def format_literal(o):
    if isinstance(o, APredicate):
        return u"a"
    elif isinstance(o, URIRef):
        return u"<%s>" % o
    elif hasattr(o, "resource_uri"): # duck typing to avoid importing RDFClass
        return u"<%s>" % o.resource_uri
    elif isinstance(o, basestring) and o[0] != u"?":
        return u"\"%s\"" % o
    else:
        return str(o)


def format_tuple(tp):
    return u"%s %s %s" % tuple(map(format_literal, tp))


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
        try:
            response = self.open(url)
        except HTTPError, e:
            if e.code == 400:
                raise SPARQLQueryException("'%s' is not a valid SPARQL query." %
                        query)
            else:
                raise e
        return parse(response)

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
        """Get a list of all predicates used for a given class in the dataset.
        This could be a very wide selection with predicates from lots of
        different namespaces.

        """
        return self.simple_query("""select distinct ?property where { ?object a <%s> . ?object ?property ?x }""" % class_uri)

    def resources(self, class_uri):
        q = SelectQuery().select("?resource").where("?resource", a, u)
        return self.simple_query(str(q))


def return_clone(method):
    def wrapped(self, *args, **kwargs):
        cl = self._clone()
        method(cl, *args, **kwargs)
        return cl
        
    update_wrapper(method, wrapped)
    return wrapped


class SelectQuery(object):
    """Represent a SPARQL query. Allow queries to be built incrementally, a la
    Django's ORM, jQuery, rdfQuery, etc.
    
    >>> q = SelectQuery()
    >>> band = URIRef("http://dbpedia.org/ontology/Band")
    >>> q2 = q.select("?resource").where("?resource", a, band)
    >>> str(q2)
    'select ?resource where { ?resource a <http://dbpedia.org/ontology/Band> }'
    >>> person = URIRef("http://dbpedia.org/ontology/Person")
    >>> q2a = q.select("?resource").where("?resource", a, person)
    >>> str(q2a)
    'select ?resource where { ?resource a <http://dbpedia.org/ontology/Person> }'
    >>> from rdflib.namespace import RDFS
    >>> q3 = q2.optional("?resource", RDFS.label, "Kraftwerk")
    >>> str(q3)
    'select ?resource where { ?resource a <http://dbpedia.org/ontology/Band> optional { ?resource <http://www.w3.org/2000/01/rdf-schema#label> "Kraftwerk" } }'

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
        return deepcopy(self)

    def __deepcopy__(self, memodict):
        return self.__class__(deepcopy(self._q, memodict))

    @return_clone
    def select(cl, var_or_vars):
        if isinstance(var_or_vars, basestring):
            cl._q["select"].append(var_or_vars)
        else:
            cl._q["select"] += var_or_vars

    @return_clone
    def distinct(cl):
        cl._q["distinct"] = True

    @return_clone
    def where(cl, subj, pred, obj):
        cl._q["where"].append((subj, pred, obj))

    @return_clone
    def optional(cl, subj, pred, obj):
        cl._q["optional"].append((subj, pred, obj))

    @return_clone
    def __getitem__(cl, k):
        """Restrict number results returned.
        
        >>> band = URIRef("http://dbpedia.org/ontology/Band")
        >>> q = SelectQuery().select("?resource").where("?resource", a, band)
        >>> str(q[0])
        'select ?resource where { ?resource a <http://dbpedia.org/ontology/Band> } limit 1'
        >>> str(q[1])
        'select ?resource where { ?resource a <http://dbpedia.org/ontology/Band> } limit 1 offset 1'
        >>> str(q[:5])
        'select ?resource where { ?resource a <http://dbpedia.org/ontology/Band> } limit 5'

        """
        if isinstance(k, (int, long)):
            cl._q["offset"] = k
            cl._q["limit"] = 1
        elif isinstance(k, slice):
            if k.step is not None and k.step != 1:
                raise ValueError("SelectQuery only supports a step of 1")
            offset = k.start or 0
            if offset > 0:
                cl._q["offset"] = offset
            if k.stop is not None:
                cl._q["limit"] = k.stop - offset
        else:
            raise TypeError("Slice arguments must be of type slice, int or long")

    def __repr__(self):
        return "<Query: %s>" % self

    def __str__(self):
        """Return this query as a SPARQL query string."""
        q = []

        # select vars
        q.append(u"select")
        if self._q["distinct"]:
            q.append(u"distinct")
        if self._q["select"]:
            q += [var for var in self._q["select"]]
        else:
            q.append(u"*")

        # where clauses
        if self._q["where"]:
            q += [u"where", u"{"]
            q.append(u" . ".join([format_tuple(tp) for tp in self._q["where"]]))

            if self._q["optional"]:
                q += [u"optional", u"{"]
                q.append(u" . ".join([format_tuple(tp) for tp in self._q["optional"]]))
                q.append(u"}")

            q.append(u"}")
        else:
            raise MalformattedQueryException("Missing where clause")

        # order by
        if self._q["order_by"]:
            q.append(u"order by")
            q.append(u", ".join([o for o in self._q["order_by"]]))

        # offset row results
        if self._q["offset"] is not None:
            q += [u"offset", str(self._q["offset"])]

        # limit number of rows returned
        if self._q["limit"] is not None:
            q += [u"limit", str(self._q["limit"])]

        return u" ".join(q)


if __name__ == "__main__":
    from doctest import testmod
    testmod()
