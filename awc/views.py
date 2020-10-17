from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from .anilist import Anilist
from .models import Submission, Challenge
from .utils import Utils
from .forms import CreateChallengeForm, AddExistingSubmissionForm

from core.models import User

import json
import os

from datetime import date

anilist_client_id = os.environ.get('ANILIST_CLIENT_ID')
anilist_client_secret = os.environ.get('ANILIST_CLIENT_SECRET')
anilist_redirect_uri= os.environ.get('ANILIST_REDIRECT_URI')

anilist = Anilist(anilist_client_id, anilist_client_secret, anilist_redirect_uri)

# Create your views here.
def index(request):
    context = {}

    if 'user' in request.session:
        try:
            context['user'] = User.objects.get(name=request.session['user']['name'])
        except Exception as err:
            print(err)
    else:
        if 'user' in context:
            del context['user']
    
    if request.method == "POST":
        selected_challenges = request.POST.getlist('challenges[]')
        
        for challenge_id in selected_challenges:
            if not Submission.objects.filter(user__name=request.session['user']['name'], challenge__id=challenge_id).exists():
                challenge = get_object_or_404(Challenge, id=int(challenge_id))

                # Check for if user has prerequisites
                prerequisites_failed = False

                for prerequisite in challenge.prerequisites.all():
                    if not context['user'].submission_set.filter(challenge__name=prerequisite.name).exists():
                        prerequisites_failed = True

                if prerequisites_failed:
                    print("Some prerequisites missing...")
                    continue

                # Sets up default challenge info
                post = request.POST.copy()
                post['challenge-start'] = date.today().isoformat()
                post['format'] = 'new' # sets challenge to use the format
                request.POST = post

                category = challenge.category
                challenge_extra = challenge.extra

                # Generates the challenge comment
                filled_code = Utils.create_comment_string(request, challenge, context['user'])

                # Variables for the GraphQL query
                variables = {
                    'thread_id': challenge.thread_id,
                    'comment': filled_code
                }

                # Make the HTTP Api request
                response_data = json.loads(anilist.post_authorised_query(request.session['access_token'], anilist.MAKE_POST_QUERY, variables))

                context['comment_id'] = response_data['data']['SaveThreadComment']['id']

                submission = Submission(user=User.objects.get(name=request.session['user']['name']),
                                        challenge=challenge,
                                        thread_id=challenge.thread_id,
                                        comment_id=context['comment_id']).save()

    if 'user' in request.session:
        try:
            context['user_genre_challenge_list'] = context['user'].submission_set.filter(challenge__category=Challenge.GENRE, challenge__archived=False).order_by('challenge__name')
            context['user_timed_challenge_list'] = context['user'].submission_set.filter(challenge__category=Challenge.TIMED, challenge__archived=False).order_by('challenge__name')
            context['user_tier_challenge_list'] = context['user'].submission_set.filter(challenge__category=Challenge.TIER, challenge__archived=False).order_by('challenge__name')
            context['user_collection_challenge_list'] = context['user'].submission_set.filter(challenge__category=Challenge.COLLECTION, challenge__archived=False).order_by('challenge__name')
            context['user_classic_challenge_list'] = context['user'].submission_set.filter(challenge__category=Challenge.CLASSIC, challenge__archived=False).order_by('challenge__name')
            context['user_puzzle_challenge_list'] = context['user'].submission_set.filter(challenge__category=Challenge.PUZZLE, challenge__archived=False).order_by('challenge__name')
            context['user_special_challenge_list'] = context['user'].submission_set.filter(challenge__category=Challenge.SPECIAL, challenge__archived=False).order_by('challenge__name')
            context['user_archived_challenge_list'] = context['user'].submission_set.filter(challenge__archived=True).order_by('challenge__name')

            context['genre_challenge_list'] = Challenge.objects.filter(category=Challenge.GENRE, archived=False).exclude(id__in=context['user_genre_challenge_list'].values('challenge')).order_by('name')
            context['timed_challenge_list'] = Challenge.objects.filter(category=Challenge.TIMED, archived=False).exclude(id__in=context['user_timed_challenge_list'].values('challenge')).order_by('name')
            context['tier_challenge_list'] = Challenge.objects.filter(category=Challenge.TIER, archived=False).exclude(id__in=context['user_tier_challenge_list'].values('challenge')).order_by('name')
            context['collection_challenge_list'] = Challenge.objects.filter(category=Challenge.COLLECTION, archived=False).exclude(id__in=context['user_collection_challenge_list'].values('challenge')).order_by('name')
            context['classic_challenge_list'] = Challenge.objects.filter(category=Challenge.CLASSIC, archived=False).exclude(id__in=context['user_classic_challenge_list'].values('challenge')).order_by('name')
            context['puzzle_challenge_list'] = Challenge.objects.filter(category=Challenge.PUZZLE, archived=False).exclude(id__in=context['user_puzzle_challenge_list'].values('challenge')).order_by('name')
            context['special_challenge_list'] = Challenge.objects.filter(category=Challenge.SPECIAL, archived=False).exclude(id__in=context['user_special_challenge_list'].values('challenge')).order_by('name')
            context['archived_challenge_list'] = Challenge.objects.filter(archived=True).exclude(id__in=context['user_archived_challenge_list'].values('challenge')).order_by('name')
        except Exception as err:
            print(err)
    else:
        if 'user' in context:
            del context['user']
    
    context['anilist_redirect_uri'] = anilist_redirect_uri
    context['anilist_client_id'] = anilist_client_id
    
    return render(request, 'awc/index.html', context)

def edit(request, challenge_name):
    submission = get_object_or_404(Submission, user__name=request.session['user']['name'], challenge__name=challenge_name)
        
    challenge = get_object_or_404(Challenge, name=challenge_name)
    requirements = challenge.requirement_set.all().order_by("bonus", "number")

    context = {}

    if 'user' in request.session:
        try:
            context['user'] = User.objects.get(name=request.session['user']['name'])
        except:
            print("User not found...")
    else:
        if 'user' in context:
            del context['user']
    
    if request.POST:
        try:
            filled_code = Utils.create_comment_string(request, challenge, context['user'])

            variables = {
                'id': submission.comment_id,
                'thread_id': challenge.thread_id,
                'comment': filled_code
            }

            # Make the HTTP Api request
            response = anilist.post_authorised_query(request.session['access_token'], anilist.UPDATE_POST_QUERY, variables)

            return render(request, 'awc/edit.html', context)
        except Exception as err:
            print("Error: {}".format(err))

    # Define our query variables and values that will be used in the query request
    variables = {
        'thread_id': submission.thread_id,
        'comment_id': submission.comment_id
    }

    # Make the HTTP Api request
    response = anilist.post_query(anilist.GET_POST_QUERY, variables)

    parsed_response = Utils.parse_challenge_code(submission, response)

    anime_ids = []

    if parsed_response['failed']:
        context['error_message'] = "Failed to parse your challenge code... Make sure that your comment follows the AWC challenge code format for this challenge."
    else:
        for requirement in parsed_response['requirements']:
            if not requirement['force_raw_edit']:
                anime_ids.append(int(requirement['anime_id']))
        
        variables = {
            'ids': anime_ids
        }

        anime = json.loads(anilist.post_authorised_query(request.session['access_token'], anilist.GET_ANIME_FROM_ID_QUERY, variables))

        for i, requirement in enumerate(parsed_response['requirements']):
            if not requirement['force_raw_edit']:
                media = next((item for item in anime['data']['Page']['media'] if item['id'] == requirement['anime_id']), None)

                if media:
                    if media['mediaListEntry'] != None and type(media['mediaListEntry']['startedAt']) is dict:
                        if None not in media['mediaListEntry']['startedAt'].values():
                            media['mediaListEntry']['startedAt'] = date(media['mediaListEntry']['startedAt']['year'], media['mediaListEntry']['startedAt']['month'], media['mediaListEntry']['startedAt']['day']).isoformat()
                        else:
                            media['mediaListEntry']['startedAt'] = "YYYY-MM-DD"

                        if None not in media['mediaListEntry']['completedAt'].values():
                            media['mediaListEntry']['completedAt'] = date(media['mediaListEntry']['completedAt']['year'], media['mediaListEntry']['completedAt']['month'], media['mediaListEntry']['completedAt']['day']).isoformat()
                        else:
                            media['mediaListEntry']['completedAt'] = "YYYY-MM-DD"

                    parsed_response['requirements'][i]['media'] = media

    context['submission'] = submission
    context['response'] = parsed_response
    context['category'] = challenge.category
    context['anilist_redirect_uri'] = anilist_redirect_uri
    context['anilist_client_id'] = anilist_client_id
    context['challenge'] = challenge
    
    return render(request, 'awc/edit.html', context)

def add_existing_submission(request):
    if request.method == 'POST':
        form = AddExistingSubmissionForm(request.POST)

        if form.is_valid():
            challenge = form.cleaned_data['challenge']

            if not Submission.objects.filter(user__name=request.session['user']['name'], challenge__name=challenge.name).exists():
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

def profile_code(request):
    user = User.objects.get(name=request.session['user']['name'])
    posts = user.submission_set.all()

    current_posts = []
    past_posts = []

    for post in posts:
        if post.submission_comment_id == None:
            current_posts.append(post)
        else:
            past_posts.append(post)
    
    code = ""

    if current_posts:
        code += "__Current__\n\n"
        
        for post in current_posts:
            code += "[{}](https://anilist.co/forum/thread/{}/comment/{}) | ".format(post.challenge.name,
                                                                                    post.challenge.thread_id,
                                                                                    post.comment_id)

        code = code[:-2]

    if past_posts:
        code += "\n\n__Past__\n\n"
        
        for post in past_posts:
            code += "[{}](https://anilist.co/forum/thread/{}/comment/{}) | ".format(post.challenge.name,
                                                                              post.challenge.thread_id,
                                                                              post.comment_id)
            
        code = code[:-2]
    
    context = {
        'code': code,
    }

    return render(request, 'awc/profile-code.html', context)

def authenticate(request):
    response = anilist.authenticate(request.GET.get('code', ''), anilist_client_id, anilist_client_secret, anilist_redirect_uri)

    response_data = json.loads(response)

    # Manually save the session if changing an existing access token
    if 'access_token' in request.session:
        request.session['access_token'] = response_data['access_token']
        request.session.modified = True
    # Assign a new access token, which will automatically save the token
    else:
        request.session['access_token'] = response_data['access_token']

    # Define our query variables and values that will be used in the query request
    variables = {}
    
    # Make the HTTP Api request
    response_data = json.loads(anilist.post_authorised_query(request.session['access_token'], anilist.GET_USER_INFO_QUERY, variables))
    
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

def submit_post(request, challenge_name, thread_id, comment_id):
    # Handles submission difficulty comment
    if request.POST.get('challenge-difficulty', ''):
        comment = "{} ({}): https://anilist.co/forum/thread/{}/comment/{}".format(challenge_name,
                                                                                  request.POST.get('challenge-difficulty', ''),
                                                                                  thread_id,
                                                                                  comment_id)
    else:
        comment = "{}: https://anilist.co/forum/thread/{}/comment/{}".format(challenge_name,
                                                                             thread_id,
                                                                             comment_id)
    
    # Variables for the GraphQL query
    variables = {
        'thread_id': 4446,
        'comment': comment,
    }
    
    # Make the HTTP Api request
    response_data = json.loads(anilist.post_authorised_query(request.session['access_token'], anilist.MAKE_POST_QUERY, variables))
    
    submission = get_object_or_404(Submission, user__name=request.session['user']['name'], challenge__name=challenge_name)
    submission.submission_comment_id = response_data['data']['SaveThreadComment']['id']
    submission.save()

    return HttpResponseRedirect(reverse('awc:index'))

def delete_post(request, comment_id, full_delete=False, is_submission=False):
    if 'user' in request.session:
        try:
            user = User.objects.get(name=request.session['user']['name'])
            
            if full_delete:
                # Make the HTTP Api request
                response_data = json.loads(anilist.delete_post(comment_id))
            
            if (not full_delete) or response_data['data']['DeleteThreadComment']['deleted']:
                if is_submission:
                    submission = user.submission_set.get(comment_id=comment_id)
                    submission.submission_comment_id = None
                    submission.save()
                else:
                    user.submission_set.get(comment_id=comment_id).delete()
        except Exception as err:
            print(err)
    
    return HttpResponseRedirect(reverse('awc:index'))

def scan(request):
    page_number = 1
    
    while True:
        # Variables for the GraphQL query
        variables = {
            'page_number': page_number,
            'user_id': User.objects.get(name=request.session['user']['name']).user_id
        }
    
        # Make the HTTP Api request
        response = json.loads(anilist.post_query(anilist.GET_USER_POSTS_QUERY, variables))
        
        thread_ids = set(comment['threadId'] for comment in response['data']['Page']['threadComments'])
        
        comments_by_thread = Utils.split_by_key(response['data']['Page']['threadComments'], 'threadId')
    
        for thread_id in thread_ids:
            comments = comments_by_thread[thread_id]
            
            try:
                challenge = Challenge.objects.get(thread_id=thread_id)
                
                if not Submission.objects.filter(user__name=request.session['user']['name'], challenge=challenge).exists():
                    first_comment = min(comments, key=lambda x:x['id'])
                    
                    submission = Submission(user=User.objects.get(name=request.session['user']['name']),
                                            challenge=challenge,
                                            thread_id=thread_id,
                                            comment_id=first_comment['id']).save()
            except:
                pass

        if response['data']['Page']['pageInfo']['currentPage'] == response['data']['Page']['pageInfo']['lastPage']:
            break
        else:
            page_number += 1
    
    return HttpResponseRedirect(reverse('awc:index'))

def search_anime(request):
    variables = {
        'search': request.POST.get("search_anime_title", "")
    }

    data = json.loads(anilist.post_authorised_query(request.session['access_token'], anilist.SEARCH_ANIME_QUERY, variables))
    
    return JsonResponse(data, safe=False)
