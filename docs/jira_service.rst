=====================
JIRA Service Features
=====================

The JIRA integration is split into two implementation patterns: *poll* and *wait*. 

The poll implementation checks a JIRA filter at a specified interval and prints any new issues that are found, or when certain fields have changed (priority, title, assignee, etc)

The wait implementation sits waiting for a remote agent, most likely a JIRA plugin, to send a request to print a given issue when it changes under the same criteria.

Both implementations have advantages in different situations, so we will likely implement both.

They share a lot of common functionality. The way they communicate with the Print Service, how they are configured, and any convenience functionality (reprinting, browsing JIRA, etc). 

Configuration
=============

Actors
------

Admin
    The person who installed the application. 
JIRA
    The JIRA issue tracking system
    
    
