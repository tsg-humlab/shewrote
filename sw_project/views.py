from django.shortcuts import render
from django.conf import settings

def robots(request):
    template_name = 'robots_disallow_all.txt' if getattr(settings, 'ROBOTS_TXT_DISALLOW_ALL', True) \
        else 'robots_disallow_ai_bots.txt'
    return render(request, template_name, {}, 'text/plain')