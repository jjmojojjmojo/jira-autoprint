"""
Printing Service - listens for REST requests, dispatches a renderer to build
a printable file, then sends it to CUPS
"""
import os
from jinja2 import Environment, FileSystemLoader

template_path = os.path.join(os.path.dirname(__file__), 'templates')

static_path = os.path.join(template_path, 'static')

templates = Environment(loader=FileSystemLoader(template_path))
