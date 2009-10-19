"""Provide a simple Pythonic API for RDF data.

This module provides bases for creating Python classes to manipulate data of
given RDF or OWL classes. The Python classes are easy to write and are designed
to be generated automatically from an RDFS or OWL ontology or by introspecting
an RDF graph.

"""
from rdflib.graph import Graph
from rdflib.namespace import Namespace

from sparql import SPARQLEndpoint


class RDFClassMetaclass(type):
    """Factory metaclass for RDFClass classes. Metaclass hacking required to
    create static resources attribute.
    
    """
    def __init__(cls, name, bases, dct):
        super(RDFClassMetaclass, cls).__init__(name, bases, dct)

        if "endpoint_uri" in dct and "prefix" in dct and "label" in dct:
            # create class_uri, ns and endpoint static attributes
            setattr(cls, "class_uri", dct["prefix"] + dct["label"])
            setattr(cls, "ns", Namespace(dct["prefix"]))
            if "endpoint_username" in dct and "endpoint_password" in dct:
                setattr(cls, "endpoint", SPARQLEndpoint(dct["endpoint_uri"],
                        dct["endpoint_username"], dct["endpoint_password"]))
            else:
                setattr(cls, "endpoint", SPARQLEndpoint(dct["endpoint_uri"]))

            # create resources static attribute which looks-up resources from
            # the SPARQL endpoint
            def resources():
                return (cls(resource_uri) for resource_uri in
                        cls.endpoint.resources(cls.class_uri))
            setattr(cls, "resources", staticmethod(resources))


class RDFClass(object):
    """Represent an RDF class.

    It is assumed that resources of this class are accessible as RDF documents
    on the web and that they can be discovered by interrogating an RDF database.
    
    We can define a subclass Band easily:

    >>> class Band(RDFClass):
    ...     endpoint_uri = "http://dbpedia.org/sparql"
    ...     prefix = "http://dbpedia.org/ontology/"
    ...     label = "Band"
    >>> Band.class_uri
    'http://dbpedia.org/ontology/Band'
    >>> Band.endpoint
    <SPARQLEndpoint: http://dbpedia.org/sparql>

    Given this subclass, we can get a particular band by it's resource uri:
    
    >>> kraftwerk = Band("http://dbpedia.org/page/Kraftwerk")
    >>> kraftwerk
    <Band: http://dbpedia.org/page/Kraftwerk>

    Iterate over all bands known to the SPARQL endpoint:

    >>> list(Band.resources())[0]
    <Band: http://dbpedia.org/resource/%21%21%21>

    Iterate over a subset of bands using something like `for b in
    Band.filter("size > 100"): print b[rdfs.label]`
    """
    __metaclass__ = RDFClassMetaclass

    def __init__(self, resource_uri):
        self.resource_uri = resource_uri

        # create a SPARQLEndpoint object representing the endpoint from which we
        # can discover resources of this class
        self.endpoint = SPARQLEndpoint(self.endpoint_uri)

    def __repr__(self):
        return u"<%s: %s>" % (self.label, self.resource_uri)

    def get_properties(self):
        """Load data about this resource from the specified uri."""
        self.graph = Graph()
        self.graph.parse(self.resource_uri)
        
        # load data from all triples with our prefix
        # TODO query rather than iterating?
        self.properties = {}
        for (subj, pred, obj) in self.graph:
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
