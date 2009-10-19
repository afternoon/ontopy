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
    ...     label = "Band"

Interact with their data in a nice friendly Python way:

    >>> kraftwerk = Band("http://dbpedia.org/page/Kraftwerk")
    >>> kraftwerk
    <Band: http://dbpedia.org/page/Kraftwerk>
    >>> list(Band.resources())[0]
    <Band: http://dbpedia.org/resource/%21%21%21>
