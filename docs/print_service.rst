======================
Print Service Features
======================

This document covers the planned features for the Print Service. The form specified is a User Story, followed by use cases as appropriate.

Remote Printing
===============
The core feature of the Print Service is to accept remote printing requests, in a structured way, and pass them on to a print queue. 

Actors
------
Admin:
    A person interacting with the system who has rights to configure the system
User:
    A person interacting with the system who can not configure things.
Consumer:
    A remote service that sends print requests.
Service:
    This service
Renderer:
    A python module that receives a dictionary of information and returns a file path (the intent is that the path represents a printable file that the renderer created)

Use Cases
---------
Configure Authentication
~~~~~~~~~~~~~~~~~~~~~~~~
Admin asks Service to generate an oAuth key for a given Consumer. Admin uses that key to configure that Consumer. The key is stored and used to authenticate future requests from that Consumer. 
    
Print
~~~~~
1. User or Consumer sends a request to the Service indicating what Renderer they want to use, and any expected information the Renderer requires, and an oAuth key as configured in `Configure Authentication`.
2. Service checks the key provided against the one stored.
3. Service responds with a successful status code, and any output from the Renderer.

Extensions:
    2. a. Authentication fails. Service responds with an error status code (*401 Unauthorized*?).
        
    3. (a) Renderer does not exist. Service responds with an error status code (*404 Not Found*?), and information notifying the User/Consumer of that fact.
    
    3. (b) Renderer does not get necessary information in the request. Service responds with an error status code, and output from the Renderer.
    
Query Renderer
~~~~~~~~~~~~~~
1. A User or Consumer sends a request to the Service asking what the expected parameters of a given Renderer are.
2. Service asks Renderer for parameters, and returns to the User/Consumer

Query Service: Renderers
~~~~~~~~~~~~~~~~~~~~~~~~
A User or Consumer sends a request to the Service asking what renderers are available. The Service retrieves information about each available renderer and returns it to the User/Consumer.

Questions:
    #. Is authorization required to query the service?

Query Service: Printer Status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A User or Consumer sends a request to the Service asking what the status of the printer and it's queue is. 

Query Service: Log Viewing
~~~~~~~~~~~~~~~~~~~~~~~~~~
An Admin logs into the Service and can browse the log.
    
Administration and Configuration
================================
It should be possible to configure the application both at run time, and through a configuration file.

Actors
------
Adminstrator:
    End user of the Service with elevated privileges
System Admin:
    Person installing the Service on a server. 
Service:
    This service

Use Cases
---------
Configure Service
~~~~~~~~~~~~~~~~~
A System Admin edits a configuration file to specify common parameters:

    * the port that the service listens on
    * the IP address the service listens on
    * log level
    * log location

Configure Printing
~~~~~~~~~~~~~~~~~~
An Admin logs into the Service. They are able to configure what printer to use, and tweak a subset of the standard printing dialog.

.. todo::
   Elaborate on the available settings.

Questions:
    #. How much control should the Admin have? Are we presenting the whole of the CUPS interface or a Print Dialog here? - *No, the UI will be limited to common printing tweaks, to be determined and added to the use case*
    #. How many printers does the Service support? - *Just one. It can use any printer that is configured in CUPS, but only one at a time*

