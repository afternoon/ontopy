"""Provide a simple Pythonic API for RDF data.

This module provides bases for creating Python classes to manipulate data of
given RDF or OWL classes. The Python classes are easy to write and are designed
to be generated automatically from an RDFS or OWL ontology or by introspecting
an RDF graph.

"""
from rdflib.term import bind, URIRef
from rdflib.graph import Graph
from rdflib.namespace import Namespace

from sparql import a, SPARQLEndpoint, SelectQuery


# dump lots of debug info
DEBUG = False


# by default return rdflib.term.Literals as Unicode strings
bind(None, unicode)


class RDFClassManager(object):
    """A container like object which represents a SPARQL query and returns
    RDFClass objects.
    
    """
    def __init__(self, cls):
        self.cls = cls
        self.query = SelectQuery().select("?resource").where("?resource", a,
                cls.class_uri)

    def run_query(self):
        """Return a list of URIs representing each of the objects matched by the
        query.
        
        """
        return self.cls.endpoint.simple_query(str(self.query))

    def __iter__(self):
        """Return a generator which yields objects of the type passed to the
        constructor.

        """
        return (self.cls(uri) for uri in self.run_query())

    def __getitem__(self, k):
        """Return a single object of type cls if k is a long or an int, return
        an iterator over a sequence of objects of type cls is k is a slice.
        
        """
        results = self.run_query()[k]
        if isinstance(k, (int, long)):
            return self.cls(results)
        elif isinstance(k, slice):
            return (self.cls(uri) for uri in results)

    def __getattr__(self, name, *args, **kwargs):
        attr = getattr(self.query, name)
        self.query = attr(*args, **kwargs)


class RDFClassMetaclass(type):
    """Factory metaclass for RDFClass classes. Metaclass hacking required to
    create static resources attribute.
    
    """
    def __init__(cls, name, bases, dct):
        """Create a new RDFClass. Read the definition given by the author and
        infer a class URI for the RDFS/OWL class, a Namespace for the data types
        expected to be found in the data set, the SPARQL endpoint URI where
        objects of this class can be discovered and finally a RDFClassManager
        object which adapts SPARQL queries into sequences of objects of type cls.
        
        """
        super(RDFClassMetaclass, cls).__init__(name, bases, dct)

        if "endpoint_uri" in dct and "prefix" in dct:
            label = dct["label"] if "label" in dct else unicode(cls.__name__)

            setattr(cls, "label", label)
            setattr(cls, "ns", Namespace(dct["prefix"]))
            setattr(cls, "class_uri", URIRef(dct["prefix"] + label))

            if "endpoint_username" in dct and "endpoint_password" in dct:
                setattr(cls, "endpoint", SPARQLEndpoint(dct["endpoint_uri"],
                        dct["endpoint_username"], dct["endpoint_password"]))
            else:
                setattr(cls, "endpoint", SPARQLEndpoint(dct["endpoint_uri"]))

            # create resources attribute which looks-up resources from the
            # SPARQL endpoint
            setattr(cls, "resources", RDFClassManager(cls))


class RDFClass(object):
    """Represent an RDF class.

    It is assumed that resources of this class are accessible as RDF documents
    on the web and that they can be discovered by interrogating an RDF database.
    
    We can define a subclass Band easily:

    >>> class Band(RDFClass):
    ...     endpoint_uri = "http://dbpedia.org/sparql"
    ...     prefix = "http://dbpedia.org/ontology/"
    >>> Band.label
    u'Band'
    >>> Band.ns
    rdflib.term.URIRef('http://dbpedia.org/ontology/')
    >>> Band.class_uri
    rdflib.term.URIRef('http://dbpedia.org/ontology/Band')
    >>> Band.endpoint
    <SPARQLEndpoint: http://dbpedia.org/sparql>

    Given this subclass, we can get a particular band by it's resource URI:
    
    >>> kraftwerk = Band("http://dbpedia.org/resource/Kraftwerk")
    >>> kraftwerk
    <Band: http://dbpedia.org/resource/Kraftwerk>
    >>> from rdflib.namespace import RDFS
    >>> kraftwerk[RDFS.label]
    u'Kraftwerk'

    Iterate over all bands known to the SPARQL endpoint:

    >>> Band.resources[0]
    <Band: http://dbpedia.org/resource/%21%21%21>

    >>> for b in Band.resources[:5]:
    ...     print b
    <Band: http://dbpedia.org/resource/%21%21%21>
    <Band: http://dbpedia.org/resource/%21Action_Pact%21>
    <Band: http://dbpedia.org/resource/%21T.O.O.H.%21>
    <Band: http://dbpedia.org/resource/%22Weird_Al%22_Yankovic>
    <Band: http://dbpedia.org/resource/%2768_Comeback>
    
    """
    __metaclass__ = RDFClassMetaclass
    lang = u"en"

    def __init__(self, resource_uri):
        self.resource_uri = resource_uri

        # create a SPARQLEndpoint object representing the endpoint from which we
        # can discover resources of this class
        self.endpoint = SPARQLEndpoint(self.endpoint_uri)

    def __repr__(self):
        return u"<%s: %s>" % (self.label, self.resource_uri)

    def get_properties(self):
        """Load data about this resource from the specified URI."""
        self.graph = Graph()
        if DEBUG:
            print "Loading %s" % self.resource_uri
        self.graph.parse(self.resource_uri)
        
        # load data from all triples with our prefix
        # TODO query rather than iterating?
        self.properties = {}
        for (subj, pred, obj) in self.graph:
            if DEBUG:
                print (subj, pred, obj)
                print "language", getattr(obj, "language", None)
            if getattr(obj, "language", None) == self.lang:
                if hasattr(obj, "toPython"):
                    self.properties[pred] = obj.toPython()
                else:
                    self.properties[pred] = obj

    def __getitem__(self, key):
        """Emulate a container, serving up properties from the specified RDF
        resource.
        
        """
        if not hasattr(self, "properties"):
            self.get_properties()
        return self.properties[key]



if __name__ == "__main__":
    from doctest import testmod
    testmod()
