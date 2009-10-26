Ontopy
======

Simple RDF to Python mapper built on top of rdflib.

Ontopy is very alpha.
  
Installation
------------

Use setuptools to install Ontopy.

    easy_install ontopy

Usage
-----

Declare resource classes as Python classes.

    >>> class Band(RDFClass):
    ...     endpoint_uri = "http://dbpedia.org/sparql"
    ...     prefix = "http://dbpedia.org/ontology/"
    ...     label = "Band" # optional - class name used as default

Interact with their data in a nice friendly Python way:

    >>> Band.resources[0]
    <Band: http://dbpedia.org/resource/%21%21%21>
    >>> kraftwerk = Band("http://dbpedia.org/resource/Kraftwerk")
    >>> kraftwerk
    <Band: http://dbpedia.org/resource/Kraftwerk>

RDF property names are commonly URIs. rdflib namespaces provide convenient
shortcuts for names.

    >>> from rdflib.namespace import RDFS
    >>> kraftwerk[RDFS.label]
    u'Kraftwerk'
