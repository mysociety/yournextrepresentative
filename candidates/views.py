from django.shortcuts import render
from django.views.generic import TemplateView

class ConstituencyFinderView(TemplateView):
    template_name = 'candidates/finder.html'
