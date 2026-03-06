from django.conf import settings
from django.shortcuts import render
from django.urls import reverse


def swagger_ui(request):
    return render(request, 'swagger_ui.html', {
        'schema_url': reverse('schema'),
        'umami_website_id': getattr(settings, 'UMAMI_WEBSITE_ID', ''),
    })
