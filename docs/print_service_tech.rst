============================
Print Service Implementation
============================

This document covers the technical decisions made, and attempts to convey the rationale.

Technical Breakdown
===================
From the requirements, I can see the following areas of core functionality:

1. The printing itself - communications with the CUPs queue.
2. Administration - managing admin users, choosing a printer, granting Authorization requests.
3. Authorization - The oAuth mechanics for authenticating and signing a request.
4. Renderers - a framework for generating printable documents from request data.

General Technological Decisions
===============================
Language
--------
Python, 2.7+:
    Python 2.7 is a very mature, robust version that has some features that can greatly simplify the code and make it easier to test.
    
    I've picked Python in general because it's a language I know well, and I'm confident that it will serve this application well.
    
    Python is also a good choice for this project because of :mod:`pycups`, the python bindings to the CUPS api. 
    
Other Contenders:
    For the sake of comparison, or just my personal edification, I may someday port the app to another platform, specifically Node.js.



Approach
--------
Asynchronous, event-driven:
    This allows for a much more flexible and scalable application, that proactively avoids common sources of slow down and unresponsiveness that are common in other approaches. 
    
RESTful APIs using JSON:
    REST works over HTTP, which makes it easy to write client applications (folks have worked with RESTful APIs through command-line toos like :code:`curl`) The app can also be built to work without a client, allowing direct interaction by presenting standard HTML forms to the user when they aren't interacting as a restful service. 
    
    JSON is preferable (over say, XML or a binary format) because it can be parsed natively by most languages, especially Javascript. This opens the possibilities for front-end applications written entirely in HTML+Javascript, again widening the potential usefulness of the application.

Frameworks
----------
Twisted Python: 
    Twisted is one of the most mature and well respected event-driven libraries for Python. It has very thorough and comprehensive documentation and a fairly intelligent way of handling asynchronous processes.
    
Twisted Web:
    For the user interactions, it makes sense to work with the twisted.web library. This is a departure from what I'm used to, so there is a further learning curve here.
    
pycups:
    A library that wraps the CUPS C API. It's quite mature and Pythonic. It comes to us from Red Hat, and has been in use in Red Hat Linux for many years.

Configuration
-------------
In general, we'll store configuration in a :mod:`ConfigParser` file. It provides a simple, structured format that can be easily edited by a human being. It's a standard library, which helps with portability, and it has some very advanced features, like inline variable substitution.


Persistance
-----------
In general, there shouldn't be much of a need for persistence. CUPS handles print queue tasks for us.

However, there's a requirement for basic user management. This is best implemented in a simple database. I'm inclined to use something like :mod:`shelve`, XML, or a flat file, but there's real potential in scaling this application out beyond a single server, which makes these storage mechanisms sub-optimal.

This may change in the near future, but for now, we'll use SQLite, via the :mod:`twisted.enterprise.adapi` interface and :mod:`sqlite3` (built-in to Python 2.5+). This will allow us to move to a centralized database like PostgreSQL in the future. 

There is currently no need for an ORM or any more advanced data interactions.
