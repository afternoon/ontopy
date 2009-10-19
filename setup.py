#!/usr/bin/env python
from distutils.core import setup


setup(name="ontopy",
		version="0.1",
		description="Simple RDF to Python mapper built on top of rdflib",
		py_modules=["ontopy", "sparql"],

		author="Ben Godfrey",
		author_email="ben@ben2.com",
		url="http://aftnn.org/",

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
