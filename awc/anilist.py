import json
import requests
import os

class Anilist:

    API_URL = 'https://graphql.anilist.co'
    AUTH_URL = 'https://anilist.co/api/v2/oauth/token'

    GET_USER_INFO_QUERY = '''
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

    MAKE_POST_QUERY = '''
    mutation ($thread_id: Int, $comment: String) {
      SaveThreadComment (threadId: $thread_id, comment: $comment) {
        id,
        threadId,
      }
    }
    '''

    UPDATE_POST_QUERY = '''
    mutation ($id: Int, $thread_id: Int, $comment: String) {
      SaveThreadComment (id: $id, threadId: $thread_id, comment: $comment) {
        id,
      }
    }
    '''

    DELETE_POST_QUERY = '''
    mutation ($id: Int) {
      DeleteThreadComment (id: $id) {
        deleted,
      }
    }
    '''

    GET_POST_QUERY = '''
    query ($thread_id: Int, $comment_id: Int) {
      ThreadComment (threadId: $thread_id, id: $comment_id) {
        comment,
        threadId,
        id
      }
    }
    '''

    GET_USER_POSTS_QUERY = '''
    query ($page_number: Int, $user_id: Int) {
        Page(page: $page_number, perPage: 50) {
            pageInfo {
                total,
                currentPage,
                lastPage,
                hasNextPage,
                perPage
            }
            threadComments(userId: $user_id) {
                id,
                threadId
            }
        }
    }
    '''

    GET_ANIME_FROM_ID_QUERY = '''
    query ($ids: [Int]) {
        Page(page:1, perPage: 50) {
            pageInfo {
                currentPage
                lastPage
                hasNextPage
                perPage
            }
            media(id_in: $ids, type: ANIME) {
                id,
                title {
                    userPreferred
                },
                coverImage {
                    large
                },
                episodes,
                mediaListEntry {
                    id,
                    status,
                    progress,
                    repeat,
                    startedAt {
                        year,
                        month,
                        day
                    },
                    completedAt {
                        year,
                        month,
                        day
                    }
                }
            }
        }
    }
    '''

    SEARCH_ANIME_QUERY = '''
    query ($search: String) {
        Page(page:1, perPage: 50) {
            pageInfo {
                currentPage
                lastPage
                hasNextPage
                perPage
            }
            media(search: $search, type: ANIME) {
                id,
                title {
                    userPreferred
                },
                coverImage {
                    large
                },
                episodes,
                mediaListEntry {
                    id,
                    status,
                    progress,
                    repeat,
                    startedAt {
                        year,
                        month,
                        day
                    },
                    completedAt {
                        year,
                        month,
                        day
                    }
                }
            }
        }
    }
    '''
    
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def authenticate(self, authorisation_code, client_id, client_secret, redirect_uri):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        json_body = {
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'code': authorisation_code,
        }

        return requests.post(self.AUTH_URL, json=json_body, headers=headers).text

    def post_query(self, query, variables):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        response = requests.post(self.API_URL, json={'query': query, 'variables': variables}, headers=headers)
        return response.text

    def post_authorised_query(self, access_token, query, variables):
        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        response = requests.post(self.API_URL, json={'query': query, 'variables': variables}, headers=headers)
        return response.text

    def delete_post(self, comment_id):
        variables = {
            'id': comment_id
        }

        return self.anilist.post_authorised_query(request.session['access_token'], anilist.DELETE_POST_QUERY, variables)
