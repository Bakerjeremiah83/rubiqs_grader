# app/routes/__init__.py
from flask import Blueprint

# This is what grader.py imports as: from . import lti
lti = Blueprint("lti", __name__)
