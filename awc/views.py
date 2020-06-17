from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from .models import User, Submission, Challenge
from .utils import Utils

from .forms import CreateChallengeForm, AddExistingSubmissionForm

import requests
import json
import os

ANILIST_API_URL = 'https://graphql.anilist.co'
ANILIST_AUTH_URL = 'https://anilist.co/api/v2/oauth/token'

anilist_client_id = os.environ.get('ANILIST_CLIENT_ID')
anilist_client_secret = os.environ.get('ANILIST_CLIENT_SECRET')
anilist_redirect_uri= os.environ.get('ANILIST_REDIRECT_URI')

# View Utilities
def get_comment_string(challenge_info, requirements, category, request):
    reqs = []
    
    for requirement in requirements:
        req = {}

        req['number'] = requirement.number
        req['text'] = requirement.text
        req['extra_newline'] = requirement.extra_newline
        req['bonus'] = requirement.bonus

        if requirement.bonus:
            req['mode'] = request.POST.get('mode-bonus-{}'.format(requirement.number), 'D').strip()

            if request.POST.get('completed-bonus-{}'.format(requirement.number), "off") == 'on':
                req['completed'] = 'X'
            else:
                req['completed'] = 'O'

            req['start'] = request.POST.get('requirement-start-bonus-{}'.format(requirement.number), "DD/MM/YYYY").strip()
            req['finish'] = request.POST.get('requirement-finish-bonus-{}'.format(requirement.number), "DD/MM/YYYY").strip()
            req['anime'] = request.POST.get('requirement-anime-bonus-{}'.format(requirement.number), "Anime Title").strip()
            req['link'] = request.POST.get('requirement-link-bonus-{}'.format(requirement.number), "https://anilist.co/anime/00000/").strip()
            req['extra'] = request.POST.get('requirement-extra-bonus-{}'.format(requirement.number), "").strip()
        else:
            req['mode'] = request.POST.get('mode-{}'.format(requirement.number), 'D').strip()

            if request.POST.get('completed-{}'.format(requirement.number), "off") == 'on':
                req['completed'] = 'X'
            else:
                req['completed'] = 'O'

            req['start'] = request.POST.get('requirement-start-{}'.format(requirement.number), "DD/MM/YYYY").strip()
            req['finish'] = request.POST.get('requirement-finish-{}'.format(requirement.number), "DD/MM/YYYY").strip()
            req['anime'] = request.POST.get('requirement-anime-{}'.format(requirement.number), "Anime Title").strip()
            req['link'] = request.POST.get('requirement-link-{}'.format(requirement.number), "https://anilist.co/anime/00000/").strip()
            req['extra'] = request.POST.get('requirement-extra-{}'.format(requirement.number), "").strip()

        reqs.append(req)

    return Utils.create_comment_string(challenge_info, reqs, category)

# Create your views here.
def index(request):
    context = {
        'genre_challenge_list': Challenge.objects.filter(category=Challenge.GENRE).order_by('name'),
        'timed_challenge_list': Challenge.objects.filter(category=Challenge.TIMED).order_by('name'),
        'tier_challenge_list': Challenge.objects.filter(category=Challenge.TIER).order_by('name'),
        'collection_challenge_list': Challenge.objects.filter(category=Challenge.COLLECTION).order_by('name'),
        'classic_challenge_list': Challenge.objects.filter(category=Challenge.CLASSIC).order_by('name'), 
        'puzzle_challenge_list': Challenge.objects.filter(category=Challenge.PUZZLE).order_by('name'),
        'special_challenge_list': Challenge.objects.filter(category=Challenge.SPECIAL).order_by('name'),
    }

    if 'user' in request.session:
        try:
            context['user'] = User.objects.get(name=request.session['user']['name'])
        except:
            pass
    else:
        if 'user' in context:
            del context['user']

    context['anilist_redirect_uri'] = anilist_redirect_uri
    context['anilist_client_id'] = anilist_client_id
    
    return render(request, 'awc/index.html', context)

def edit(request, challenge_name, edit=False):
    if edit:
        submission = get_object_or_404(Submission, user__name=request.session['user']['name'], challenge__name=challenge_name)
        
    challenge = get_object_or_404(Challenge, name=challenge_name)
    requirements = challenge.requirement_set.all().order_by("bonus", "number")

    context = {}

    context['anilist_redirect_uri'] = anilist_redirect_uri
    context['anilist_client_id'] = anilist_client_id

    if edit:
        query = '''
        query ($thread_id: Int, $comment_id: Int) {
          ThreadComment (threadId: $thread_id, id: $comment_id) {
            comment,
            threadId,
            id
          }
        }
        '''

        # Define our query variables and values that will be used in the query request
        variables = {
            'thread_id': submission.thread_id,
            'comment_id': submission.comment_id
        }

        # Make the HTTP Api request
        response = requests.post(ANILIST_API_URL, json={'query': query, 'variables': variables})

        parsed_response = Utils.parse_challenge_code(submission, response.text)

        context = {
            'submission': submission,
            'response': parsed_response,
            'category': challenge.category,
        }
    else:
        context['response'] = {
            'start': 'DD/MM/YYYY',
            'finish': 'DD/MM/YYYY',
            'category': challenge.category,
            'requirements': [],
        }

        for requirement in requirements:
            req = {}

            req['mode'] = requirement.mode
            req['number'] = requirement.number
            req['completed'] = False
            req['start'] = 'DD/MM/YYYY'
            req['finish'] = 'DD/MM/YYYY'
            req['text'] = requirement.text
            req['anime'] = 'Anime Title'
            req['link'] = 'https://anilist.co/anime/00000/'
            req['bonus'] = requirement.bonus
            req['extra'] = requirement.extra
            req['extra_newline'] = requirement.extra_newline

            context['response']['requirements'].append(req)
    
    context['challenge'] = challenge
    context['requirements'] = requirements
    context['edit'] = edit 

    if request.POST:
        try:
            challenge_info = {}
            
            challenge_info['name'] = challenge_name
            challenge_info['start'] = request.POST['challenge-start']
            challenge_info['finish'] = request.POST['challenge-finish']

            category = challenge.category

            filled_code = get_comment_string(challenge_info, challenge.requirement_set.all(), category, request)
            
            context['filled_code'] = filled_code

            headers = {
                'Authorization': 'Bearer ' + request.session['access_token'],
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }

            if edit:
                query = '''
                mutation ($id: Int, $thread_id: Int, $comment: String) {
                  SaveThreadComment (id: $id, threadId: $thread_id, comment: $comment) {
                    id,
                  }
                }
                '''

                variables = {
                    'id': submission.comment_id,
                    'thread_id': challenge.thread_id,
                    'comment': filled_code
                }
            else:
                query = '''
                mutation ($thread_id: Int, $comment: String) {
                  SaveThreadComment (threadId: $thread_id, comment: $comment) {
                    id,
                  }
                }
                '''

                variables = {
                    'thread_id': challenge.thread_id,
                    'comment': filled_code
                }

            # Make the HTTP Api request
            response = requests.post(ANILIST_API_URL, json={'query': query, 'variables': variables}, headers=headers)
            
            if not edit:
                response_data = json.loads(response.text)
                context['comment_id'] = response_data['data']['SaveThreadComment']['id']
                
                submission = Submission(user=User.objects.get(name=request.session['user']['name']),
                                        challenge=challenge,
                                        thread_id=challenge.thread_id,
                                        comment_id=context['comment_id']).save()

            return render(request, 'awc/edit.html', context)
        except Exception as err:
            print("Error: {}".format(err))

    if 'user' in request.session:
        try:
            context['user'] = User.objects.get(name=request.session['user']['name'])
        except:
            pass
    else:
        if 'user' in context:
            del context['user']

    return render(request, 'awc/edit.html', context)

def add_existing_submission(request):
    if request.method == 'POST':
        form = AddExistingSubmissionForm(request.POST)

        if form.is_valid():
            challenge = form.cleaned_data['challenge']
            thread_id = challenge.thread_id
            comment_id = form.cleaned_data['comment_id']

            submission = Submission(user=User.objects.get(name=request.session['user']['name']),
                                    challenge=challenge,
                                    thread_id=thread_id,
                                    comment_id=comment_id,).save()

            return HttpResponseRedirect(reverse('awc:index'))
    else:
        form = AddExistingSubmissionForm(initial={'challenge': Challenge.objects.first(),
                                                  'comment_id': 00000,})
    context = {
        'form': form,
    }

    context['anilist_redirect_uri'] = anilist_redirect_uri
    context['anilist_client_id'] = anilist_client_id

    if 'user' in request.session:
        try:
            context['user'] = User.objects.get(name=request.session['user']['name'])
        except:
            pass
    else:
        if 'user' in context:
            del context['user']
    
    return render(request, 'awc/add-existing-submission.html', context)

def add_challenge(request):
    if request.method == 'POST':
        form = CreateChallengeForm(request.POST)

        if form.is_valid():
            thread_id = form.cleaned_data['thread_id']
            challenge_code = form.cleaned_data['challenge_code']
            category = form.cleaned_data['category']
            
            Utils.create_challenge_from_code(thread_id, challenge_code, category)

            return HttpResponseRedirect(reverse('awc:index'))
    else:
        form = CreateChallengeForm(initial={'thread_id': 00000,
                                        'challenge_code': ''})
    context = {
        'form': form,
    }

    context['anilist_redirect_uri'] = anilist_redirect_uri
    context['anilist_client_id'] = anilist_client_id

    if 'user' in request.session:
        try:
            context['user'] = User.objects.get(name=request.session['user']['name'])
        except:
            pass
    else:
        if 'user' in context:
            del context['user']
    
    return render(request, 'awc/add-challenge.html', context)

def authenticate(request):
    authorisation_code = request.GET.get('code', '')

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    json_body = {
        'grant_type': 'authorization_code',
        'client_id': anilist_client_id,
        'client_secret': anilist_client_secret,
        'redirect_uri': anilist_redirect_uri,
        'code': authorisation_code,
    }

    response = requests.post(ANILIST_AUTH_URL, json=json_body, headers=headers)

    response_data = json.loads(response.text)

    # Manually save the session if changing an existing access token
    if 'access_token' in request.session:
        request.session['access_token'] = response_data['access_token']
        request.session.modified = True
    # Assign a new access token, which will automatically save the token
    else:
        request.session['access_token'] = response_data['access_token']

    query = '''
    query {
      Viewer {
        id,
        name,
        avatar {
          medium,
        },
      }
    }
    '''

    # Define our query variables and values that will be used in the query request
    variables = {}

    headers = {
        'Authorization': 'Bearer ' + request.session['access_token'],
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    # Make the HTTP Api request
    response = requests.post(ANILIST_API_URL, json={'query': query, 'variables': variables}, headers=headers)

    response_data = json.loads(response.text)
    
    request.session['user'] = response_data['data']['Viewer']

    if not User.objects.filter(name=request.session['user']['name']).exists():
        user = User(name=request.session['user']['name'], user_id=request.session['user']['id'],
                    avatar_url=request.session['user']['avatar']['medium'])

        user.save()
    
    return HttpResponseRedirect(reverse('awc:index'))

def logout(request):
    del request.session['user']
    del request.session['access_token']

    return HttpResponseRedirect(reverse('awc:index'))

def delete_submission(request, comment_id):
    headers = {
        'Authorization': 'Bearer ' + request.session['access_token'],
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    
    query = '''
    mutation ($id: Int) {
      DeleteThreadComment (id: $id) {
        deleted,
      }
    }
    '''

    variables = {
        'id': comment_id
    }

    # Make the HTTP Api request
    response = requests.post(ANILIST_API_URL, json={'query': query, 'variables': variables}, headers=headers)
    
    response_data = json.loads(response.text)

    if response_data['data']['DeleteThreadComment']['deleted']:
        Submission.objects.get(comment_id=comment_id).delete()
    
    return HttpResponseRedirect(reverse('awc:index'))
