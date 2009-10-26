#!/usr/bin/env python
"""Simple RDF to Python mapper built on top of rdflib.

Manipulate RDF data stored remotely as Python data structures.

Ontopy includes a SPARQL query builder for accessing sets of resources behind
SPARQL endpoints.

"""
from distutils.core import setup


setup(name="ontopy",
		version="0.1.1",
		description=__doc__,
		py_modules=["ontopy", "sparql"],
        platforms=["any"],

		author="Ben Godfrey",
		author_email="ben@ben2.com",
		url="http://github.com/afternoon/ontopy/",

        requires=[
            "rdflib (>=2.5)"
        ],

        license="BSD",
		classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: BSD License",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 2.5",
            "Programming Language :: Python :: 2.6",
            "Programming Language :: Python",
            "Topic :: Internet :: WWW/HTTP",
            "Topic :: Software Development :: Libraries :: Python Modules"
		])
