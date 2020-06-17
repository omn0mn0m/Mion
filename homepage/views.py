from django.shortcuts import render

import os

anilist_client_id = os.environ.get('ANILIST_CLIENT_ID')
anilist_client_secret = os.environ.get('ANILIST_CLIENT_SECRET')
anilist_redirect_uri= os.environ.get('ANILIST_REDIRECT_URI')

# Create your views here.
def index(request):
    context = {
        'home': True
    }
    
    return render(request, 'homepage/index.html', context)

