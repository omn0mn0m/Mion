import json
import re
import collections
import traceback

from itertools import groupby
from operator import itemgetter
from datetime import datetime

from .models import Challenge, Requirement

def remove_sublist(sublist, nested_list):
    return [i for i in nested_list if i != sublist]

def remove_and_count_sublist(sublist, nested_list):
    count = 0
    fixed_list = []
    
    for i in nested_list:
        if i == sublist:
            count += 1
        else:
            fixed_list.append(i)

    return fixed_list, count

def get_extra(line):
    extra = ''
    
    extra_regex = re.search(r'\(https:\/\/anilist\.co\/anime\/[a-zA-Z0-9-\/]+\)(.*)', line)
    
    if extra_regex != None:
        extra = extra_regex.group(1)

    return extra

def get_requirement_mode(i, easy_index, normal_index, hard_index, bonus_index):
    if bonus_index != -1 and i > bonus_index:
        mode = Requirement.BONUS
    elif hard_index != -1 and i > hard_index:
        mode = Requirement.HARD
    elif normal_index != -1 and i > normal_index:
        mode = Requirement.NORMAL
    elif easy_index != -1 and i > easy_index:
        mode = Requirement.EASY
    else:
        mode = Requirement.DEFAULT

    return mode

def convert_date(raw_date):
    raw_date = raw_date.strip()
    
    if "DD" in raw_date:
        return raw_date
    else:
        for date_format in ('%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d'):
            try:
                date_object = datetime.strptime(raw_date, date_format)

                if date_object:
                    break
            except ValueError:
                pass
            
        return date_object.strftime('%Y-%m-%d')

def convert_extra(raw_extra):
    # Splits the old extra into parts
    raw_extra = raw_extra.replace(', ', '\n')
    extras = raw_extra.split('\n')

    extras = [extra.strip('_') for extra in extras]

    extra = ' // '.join(extras)

    # Replaces old wrappers
    extra = extra.replace('~!', '').replace('!~', '')

    # Replaces old screenshots with new screenshots
    extra = extra.replace('Screenshot:', '').replace('Screenshots:', '')
    extra = extra.replace('img(', '[Screenshot](')

    extra = extra.strip() # Removes any weird lingering spaces
    
    return extra

def ordinal(n):
    n = int(n)

    suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]

    if 11 <= (n % 100) <= 13:
        suffix = 'th'

    return str(n) + suffix

class MockRequirement(object):
    '''Non-functional requirement class for challenges without database requirements'''
    
    def __init__(self, number):
        self.number = number
        self.mode = Requirement.DEFAULT
        self.text = ''
        self.bonus = False
        self.extra = ''
        self.extra_newline = False
        self.anime_title = ''
        self.anime_list = ''
        self.force_raw_edit = False
        self.raw_requirement = ''

class MockRequirementSet(list):
    '''Non-functional requirements list class'''

    def __init__(self, item_count):
        for i in range(item_count):
            self.append(MockRequirement(i + 1))

class Utils(object):

    # Mode Headers
    MODE_EASY = "__Mode: Easy__"
    MODE_NORMAL = "__Mode: Normal__"
    MODE_HARD = "__Mode: Hard__"
    MODE_BONUS = "__Bonus__"

    @staticmethod
    def is_new_format(line):
        return not bool(re.search(r'Start: [DMY0-9/]+', line))

    @staticmethod
    def split_by_key(dict_list, key):
        result = collections.defaultdict(list)

        for item in dict_list:
            result[item[key]].append(item)

        return result
    
    @staticmethod
    def create_requirement_string(requirement, post_format="old"):
        use_old_format = post_format == "old"
        
        if 'raw_requirement' in requirement:
            if use_old_format:
                requirement_string = requirement['raw_requirement'] + '\n'
            else:
                requirement_string = requirement['raw_requirement'] + '\n\n'
        else:
            if requirement['text'] == '' or requirement['text'] == ' ':
                if requirement['bonus']:
                    requirement_string = "B{number}) [{completed}]"
                else:
                    requirement_string = "{number}) [{completed}]"
                    
                if use_old_format:
                    requirement_string = requirement_string + " Start: {start} Finish: {finish} [{anime}]({link})"
                else:
                    requirement_string = requirement_string + "\n[{anime}]({link})\nStart: {start} Finish: {finish}"
                
                requirement_string = requirement_string.format(
                    number=requirement['number'],
                    completed=requirement['completed'],
                    start=requirement['start'],
                    finish=requirement['finish'],
                    anime=requirement['anime'],
                    link=requirement['link'],
                )
            else:
                if requirement['bonus']:
                    requirement_string = "B{number}) [{completed}]"
                else:
                    requirement_string = "{number}) [{completed}]"
                
                if use_old_format:
                    requirement_string = requirement_string + " Start: {start} Finish: {finish} __{text}__ [{anime}]({link})"
                else:
                    requirement_string = requirement_string + " __{text}__\n[{anime}]({link})\nStart: {start} Finish: {finish}"
                
                requirement_string = requirement_string.format(number=requirement['number'],
                                                               completed=requirement['completed'],
                                                               start=requirement['start'],
                                                               finish=requirement['finish'],
                                                               text=requirement['text'],
                                                               anime=requirement['anime'],
                                                               link=requirement['link'],)

            if use_old_format:
                if requirement['extra_newline']:
                    requirement_string = requirement_string + '\n' + requirement['extra'] + '\n'
                else:
                    requirement_string = requirement_string + ' ' + requirement['extra'] + '\n'
            else:
                if requirement['extra']:
                    requirement_string = requirement_string + ' // ' + convert_extra(requirement['extra']) + '\n\n'
                else:
                    requirement_string = requirement_string + '\n\n'

        return requirement_string

    @staticmethod
    def parse_new_requirements(submission, response):
        """Returns a dictionary of the challenge code information"""
        parsed_comment = {}
        requirements = []

        response_dict = json.loads(response)

        comment = 'No comment found...'

        try:
            comment = response_dict['data']['ThreadComment'][0]['comment']

            lines = comment.splitlines()
            
            req_start_index = [i for i, s in enumerate(lines) if ('01)' in s or 'Mode: Easy' in s)][0]

            # Split requirements into iterable groups list
            grouped_lines = [list(group) for key, group in groupby(lines[req_start_index:], key=lambda line: line != '') if key]

            current_mode = Requirement.DEFAULT

            grouped_lines = remove_sublist(['<hr>'], grouped_lines)
            
            # Parse each group
            for i, group in enumerate(grouped_lines):
                requirement = {}

                if '---' in group:
                    group.remove('---')
                
                if Utils.MODE_EASY in group:
                    current_mode = Requirement.EASY
                    group.remove(Utils.MODE_EASY)
                elif Utils.MODE_NORMAL in group:
                    current_mode = Requirement.NORMAL
                    group.remove(Utils.MODE_NORMAL)
                elif Utils.MODE_HARD in group:
                    current_mode = Requirement.HARD
                    group.remove(Utils.MODE_HARD)
                elif Utils.MODE_BONUS in group:
                    current_mode = Requirement.BONUS
                    group.remove(Utils.MODE_BONUS)
                else:
                    pass

                if "### __Winter__" in group:
                    group.remove("### __Winter__")
                elif "### __Spring__" in group:
                    group.remove("### __Spring__")
                elif "### __Summer__" in group:
                    group.remove("### __Summer__")
                elif "### __Fall__" in group:
                    group.remove("### __Fall__")

                # Get the requirements list for processing
                if "Seasonal" in submission.challenge.name:
                    requirements_list = MockRequirementSet(7)
                elif "Classic" in submission.challenge.name:
                    requirements_list = MockRequirementSet(40)
                else:
                    requirements_list = submission.challenge.requirement_set.all()

                # Check for challenge extra info if at the last group
                if i == len(grouped_lines) - 1:
                    if not len(grouped_lines) == len(requirements_list):
                        extra_index = len(grouped_lines) - 1

                        if i == extra_index:
                            parsed_comment['extra'] = '\n'.join(group)
                            break

                requirement['mode'] = current_mode
                requirement['bonus'] = group[0][0] == 'B' and group[0][1].isdigit()
                requirement['number'] = re.search(r'([0-9]+)[.\)]', group[0]).group(1)

                if "Seasonal" in submission.challenge.name:
                    req_from_db = MockRequirement(number=requirement['number'])
                elif "Classic" in submission.challenge.name:
                    req_from_db = MockRequirement(number=requirement['number'])
                else:
                    req_from_db = submission.challenge.requirement_set.get(number=requirement['number'], bonus=requirement['bonus'])

                requirement['force_raw_edit'] = req_from_db.force_raw_edit

                if req_from_db.force_raw_edit:
                    requirement['raw_requirement'] = '\n'.join(group)
                else:
                    # Determine completed status
                    requirement['completed'] = re.search(r'\[([XOU])\]', group[0]).group(1)

                    # Determine start and finish dates ("Start: YYYY-MM-DD Finish: YYYY-MM-DD")
                    requirement['start'] = convert_date(group[2][7:17])
                    requirement['finish'] = convert_date(group[2][26:36])
                    
                    # Determine requirement text
                    requirement['text'] = req_from_db.text

                    # Determine the anime
                    if req_from_db.anime_title:
                        requirement['anime'] = req_from_db.anime_title
                        requirement['link'] = req_from_db.anime_link
                        requirement['has_set_anime'] = True
                    else:
                        requirement['anime'] = re.search('\[(.+?)\]', group[1]).group(1)
                        requirement['link'] = re.search(r'\((https:\/\/anilist\.co\/anime\/[0-9]+)', group[1]).group(1)
                        requirement['has_set_anime'] = False

                    requirement['anime_id'] = int(re.search(r'https:\/\/anilist\.co\/anime\/([0-9]+)', requirement['link']).group(1))

                    # Handles in-line extra info
                    extra_split = group[2].split('//', 1)

                    if len(extra_split) > 1:
                        requirement['extra'] = extra_split[1]
                    else:
                        requirement['extra'] = ''
                
                requirements.append(requirement)
        except Exception as e:
            parsed_comment = {
                'failed': True,
                'error': traceback.format_exc(),
                'comment': comment,
            }

            return parsed_comment

        parsed_comment['requirements'] = requirements
        parsed_comment['failed'] = False
            
        return parsed_comment
    
    @staticmethod
    def parse_challenge_code(submission, response):
        """Returns a dictionary of the challenge code information"""
        parsed_comment = {}
        requirements = []

        response_dict = json.loads(response)

        comment = 'No comment found...'

        try:
            comment = response_dict['data']['ThreadComment'][0]['comment']

            lines = comment.splitlines()

            grouped_lines = [list(group) for key, group in groupby(lines, key=lambda line: line != '') if key]
            
            req_start_index = [i for i, s in enumerate(lines) if 'Legend' in s][0]

            has_prerequisites = submission.challenge.prerequisites.exists()

            if has_prerequisites:
                parsed_comment['prerequisites'] = {}

                prerequisite_lines = grouped_lines.pop(1)

                for line in prerequisite_lines:
                    prerequisite_challenge_name = re.search(r'\[(.+?)\]', line).group(1)
                    prerequisite_finish_date = re.search(r'Finish Date: ([DMY0-9/\-]+)', line).group(1)
                    
                    parsed_comment['prerequisites'][prerequisite_challenge_name] = convert_date(prerequisite_finish_date)

            parsed_comment['category'] = submission.challenge.category
                    
            try:
                parsed_comment['start'] = convert_date(re.search(r'Start Date: ([DMY0-9/\-]+)', grouped_lines[1][0]).group(1))
                parsed_comment['finish'] = convert_date(re.search(r'Finish Date: ([DMY0-9/\-]+)', grouped_lines[1][1]).group(1))
                requirements_group = grouped_lines[2:]
            except:
                parsed_comment['start'] = convert_date(re.search(r'Start Date: ([DMY0-9/\-]+)', grouped_lines[0][1]).group(1))
                parsed_comment['finish'] = convert_date(re.search(r'Finish Date: ([DMY0-9/\-]+)', grouped_lines[0][2]).group(1))
                requirements_group = grouped_lines[1:]

            prev_requirement = {}

            current_mode = Requirement.DEFAULT

            parsed_comment['is_new_format'] = False

            grouped_lines = remove_sublist(['<hr>'], grouped_lines)
            
            for i, group in enumerate(requirements_group):
                if '---' in group:
                    group.remove('---')
                
                if Utils.MODE_EASY in group:
                    current_mode = Requirement.EASY
                    group.remove(Utils.MODE_EASY)
                elif Utils.MODE_NORMAL in group:
                    current_mode = Requirement.NORMAL
                    group.remove(Utils.MODE_NORMAL)
                elif Utils.MODE_HARD in group:
                    current_mode = Requirement.HARD
                    group.remove(Utils.MODE_HARD)
                elif Utils.MODE_BONUS in group:
                    current_mode = Requirement.BONUS
                    group.remove(Utils.MODE_BONUS)
                else:
                    pass

                # Check for challenge extra info                
                if i == len(requirements_group) - 1:
                    if current_mode == Requirement.DEFAULT:
                        extra_index = 1
                    else:
                        extra_index = 4

                    if i == extra_index:
                        parsed_comment['extra'] = '\n'.join(group)
                        break

                for line in group:
                    requirement = {}
                    
                    if len(line) > 0:
                        requirement['mode'] = current_mode
                        requirement['bonus'] = line[0] == 'B' and line[1].isdigit()
                        
                        if line[0].isdigit() or requirement['bonus']:
                            requirement['number'] = re.search(r'([0-9]+)[.\)]', line).group(1).zfill(2)

                            if "Seasonal" in submission.challenge.name:
                                req_from_db = MockRequirement(number=requirement['number'])
                            elif "Classic" in submission.challenge.name:
                                req_from_db = MockRequirement(number=requirement['number'])
                            else:
                                req_from_db = submission.challenge.requirement_set.get(number=requirement['number'], bonus=requirement['bonus'])

                            requirement['force_raw_edit'] = req_from_db.force_raw_edit

                            if req_from_db.force_raw_edit:
                                requirement['raw_requirement'] = line
                            else:
                                # Determine completed status
                                requirement['completed'] = re.search(r'\[([XOU])\]', line).group(1)

                                # Determine start and finish dates
                                try:
                                    raw_requirement_start = re.search('Start: ([DMY0-9/\-]+)\s', line).group(1)
                                except:
                                    parsed_comment['is_new_format'] = True
                                    parsed_comment = {**parsed_comment, **Utils.parse_new_requirements(submission, response)}
                                    
                                    return parsed_comment

                                requirement['start'] = convert_date(raw_requirement_start)
                                requirement['finish'] = convert_date(re.search('Finish: ([DMY0-9/\-]+)', line).group(1))

                                # Determine requirement text
                                requirement['text'] = req_from_db.text

                                # Determine the anime
                                if req_from_db.anime_title:
                                    requirement['anime'] = req_from_db.anime_title
                                    requirement['link'] = req_from_db.anime_link
                                    requirement['has_set_anime'] = True
                                else:
                                    requirement['anime'] = re.search('\[.+?\].*?\[(.+?)\]', line).group(1)
                                    requirement['link'] = re.search(r'\((https:\/\/anilist\.co\/anime\/[0-9]+)', line).group(1)
                                    requirement['has_set_anime'] = False

                                requirement['anime_id'] = int(re.search(r'https:\/\/anilist\.co\/anime\/([0-9]+)', requirement['link']).group(1))

                                # Get extra stuff
                                requirement['extra_newline'] = req_from_db.extra_newline

                                # Handles in-line extra info
                                requirement['extra'] = get_extra(line)

                            prev_requirement = requirement
                            requirements.append(requirement)
                        else:
                            if not ("### __Winter" in line or "### __Spring" in line or "### __Summer" in line or "### __Fall" in line):
                                if prev_requirement:
                                    if prev_requirement['force_raw_edit']:
                                        prev_requirement['raw_requirement'] += '\n' + line
                                    else:
                                        if prev_requirement['extra'].isspace() or prev_requirement['extra'] == '':
                                            prev_requirement['extra'] = line
                                        else:
                                            prev_requirement['extra'] += ('\n' + line)

                                        requirements[requirements.index(prev_requirement)] = prev_requirement
                    else:
                        prev_requirement = None

            parsed_comment['requirements'] = requirements
            parsed_comment['failed'] = False
        except Exception as e:
            parsed_comment = {
                'failed': True,
                'error': traceback.format_exc(),
                'comment': comment,
            }
                
        return parsed_comment

    @staticmethod
    def create_comment_string(request, challenge, user):
        category = challenge.category
        challenge_extra = request.POST.get('challenge-extra', challenge.extra).strip()
            
        reqs = []

        if "Seasonal" in challenge.name:
            requirements_list = MockRequirementSet(7)
        elif "Classic" in challenge.name:
            requirements_list = MockRequirementSet(40)
        else:
            requirements_list = challenge.requirement_set.all().order_by('id')

        for requirement in requirements_list:
            req = {}

            req['number'] = str(requirement.number).zfill(2)
            req['bonus'] = requirement.bonus

            if category == Challenge.CLASSIC and request.POST.get('format', 'old') == 'new':
                if req['number'] == '01':
                    season = 'Winter'
                    offset = 0
                elif req['number'] == '11':
                    season = 'Spring'
                    offset = 10
                elif req['number'] == '21':
                    season = 'Summer'
                    offset = 20
                elif req['number'] == '31':
                    season = 'Fall'
                    offset = 30
                
                req['text'] = '{} {} Anime'.format(ordinal(int(req['number']) - offset), season)
            elif "Seasonal" in challenge.name:
                req['text'] = '{} Anime'.format(ordinal(int(req['number'])))
            else:
                req['text'] = requirement.text

            req['extra_newline'] = requirement.extra_newline

            if requirement.force_raw_edit:
                req['force_raw_edit'] = True
                req['raw_requirement'] = request.POST.get('requirement-raw-{}'.format(req['number']), requirement.raw_requirement).strip()
            else:
                req['force_raw_edit'] = False

                if requirement.bonus:
                    req['completed'] = request.POST.get('completed-bonus-{}'.format(req['number']), Requirement.NOT_COMPLETED).strip()
                    
                    req['start'] = request.POST.get('requirement-start-bonus-{}'.format(req['number']), "YYYY-MM-DD") if request.POST.get('requirement-start-bonus-{}'.format(req['number']), "YYYY-MM-DD") else 'YYYY-MM-DD'
                    req['finish'] = request.POST.get('requirement-finish-bonus-{}'.format(req['number']), "YYYY-MM-DD") if request.POST.get('requirement-finish-bonus-{}'.format(req['number']), "YYYY-MM-DD") else 'YYYY-MM-DD'

                    if requirement.anime_title:
                        req['anime'] = requirement.anime_title
                        req['link'] = requirement.anime_link
                    else:
                        req['anime'] = request.POST.get('requirement-anime-bonus-{}'.format(req['number']), "Anime_Title").strip()
                        req['link'] = request.POST.get('requirement-link-bonus-{}'.format(req['number']), "https://anilist.co/anime/00000/").strip()
                        
                    req['extra'] = request.POST.get('requirement-extra-bonus-{}'.format(req['number']), requirement.extra).strip()
                else:
                    req['completed'] = request.POST.get('completed-{}'.format(req['number']), Requirement.NOT_COMPLETED).strip()

                    req['start'] =  request.POST.get('requirement-start-{}'.format(req['number']), "YYYY-MM-DD") if request.POST.get('requirement-start-{}'.format(req['number']), "YYYY-MM-DD") else 'YYYY-MM-DD'
                    req['finish'] = request.POST.get('requirement-finish-{}'.format(req['number']), "YYYY-MM-DD") if request.POST.get('requirement-finish-{}'.format(req['number']), "YYYY-MM-DD") else 'YYYY-MM-DD'

                    if requirement.anime_title:
                        req['anime'] = requirement.anime_title
                        req['link'] = requirement.anime_link
                    else:
                        req['anime'] = request.POST.get('requirement-anime-{}'.format(req['number']), "Anime_Title").strip()
                        req['link'] = request.POST.get('requirement-link-{}'.format(req['number']), "https://anilist.co/anime/00000/").strip()

                    req['extra'] = request.POST.get('requirement-extra-{}'.format(req['number']), requirement.extra).strip()

            if requirement.bonus:
                req['mode'] = request.POST.get('mode-bonus-{}'.format(req['number']), requirement.mode).strip()
            else:
                req['mode'] = request.POST.get('mode-{}'.format(req['number']), requirement.mode).strip()

            reqs.append(req)
        
        comment = "# __{name}__\n\n".format(name=challenge.name)

        # Add prerequitites section
        for prerequisite in challenge.prerequisites.all():
            prerequisite_finish = request.POST.get('prerequisite-' + prerequisite.name + '-finish', "YYYY-MM-DD") if request.POST.get('prerequisite-' + prerequisite.name + '-finish', "YYYY-MM-DD") else 'YYYY-MM-DD'
            
            try:
                prerequisite_challenge = user.submission_set.get(challenge__name=prerequisite.name)
                post_link = "https://anilist.co/forum/thread/{}/comment/{}".format(prerequisite_challenge.challenge.thread_id, prerequisite_challenge.comment_id)
            except Exception as err:
                post_link = "https://anilist.co/forum/thread/0000/comment/00000"
            
            comment += "[{prerequisite_name}]({post_link}) Finish Date: {finish_date}\n".format(prerequisite_name=prerequisite.name,
                                                                                       post_link=post_link,
                                                                                       finish_date=prerequisite_finish)

        if challenge.prerequisites.count() > 0:
            comment += '\n'
        
        # Dates Section
        challenge_start = request.POST.get('challenge-start', "YYYY-MM-DD") if request.POST.get('challenge-start', "YYYY-MM-DD") else 'YYYY-MM-DD'
        challenge_finish = request.POST.get('challenge-finish', "YYYY-MM-DD") if request.POST.get('challenge-finish', "YYYY-MM-DD") else 'YYYY-MM-DD'

        comment += "Challenge Start Date: {start}\nChallenge Finish Date: {finish}\n".format(start=challenge_start,
                                                                                             finish=challenge_finish)
        
        if challenge.allows_up_to_date:
            comment += "Legend: [X] = Completed [O] = Not Completed [U] = Up-to-date\n\n"
        else:
            comment += "Legend: [X] = Completed [O] = Not Completed\n\n"

        # Rule Tag for new format
        if request.POST.get('format', 'old') == 'new':
            comment += '<hr>\n\n'

        reqs = Utils.split_by_key(reqs, 'mode')

        if category == Challenge.TIMED or category == Challenge.TIER or category == Challenge.COLLECTION or category == Challenge.PUZZLE or category == Challenge.SPECIAL:
            for requirement in reqs[Requirement.DEFAULT]:
                comment = comment + Utils.create_requirement_string(requirement, request.POST.get('format', 'old'))
        elif category == Challenge.CLASSIC:
            for requirement in reqs[Requirement.DEFAULT]:
                if requirement['number'] == '01':
                    comment = comment + "### __Winter__\n"
                elif requirement['number'] == '11':
                    if request.POST.get('format', 'old') == 'new':
                        comment = comment + "\n<hr>\n"
                        
                    comment = comment + "\n### __Spring__\n"
                elif requirement['number'] == '21':
                    if request.POST.get('format', 'old') == 'new':
                        comment = comment + "\n<hr>\n"
                        
                    comment = comment + "\n### __Summer__\n"
                elif requirement['number'] == '31':
                    if request.POST.get('format', 'old') == 'new':
                        comment = comment + "\n<hr>\n"
                        
                    comment = comment + "\n### __Fall__\n"
                    
                comment = comment + Utils.create_requirement_string(requirement, request.POST.get('format', 'old'))
        elif category == Challenge.GENRE:
            if reqs[Requirement.EASY]:
                comment = comment + "__Mode: Easy__\n"
                
                for requirement in sorted(reqs[Requirement.EASY], key=itemgetter('number')):
                    comment = comment + Utils.create_requirement_string(requirement, request.POST.get('format', 'old'))
            if reqs[Requirement.NORMAL]:
                comment = comment + "\n---\n__Mode: Normal__\n"

                for requirement in sorted(reqs[Requirement.NORMAL], key=itemgetter('number')):
                    comment = comment + Utils.create_requirement_string(requirement, request.POST.get('format', 'old'))
            if reqs[Requirement.HARD]:
                comment = comment + "\n---\n__Mode: Hard__\n"

                for requirement in sorted(reqs[Requirement.HARD], key=itemgetter('number')):
                    comment = comment + Utils.create_requirement_string(requirement, request.POST.get('format', 'old'))
            if reqs[Requirement.BONUS]:
                comment = comment + "\n---\n__Bonus__\n"

                for requirement in sorted(reqs[Requirement.BONUS], key=itemgetter('number')):
                    comment = comment + Utils.create_requirement_string(requirement, request.POST.get('format', 'old'))
            if reqs[Requirement.DEFAULT]:
                comment = comment + "\n---\n__Misc__\n"

                for requirement in sorted(reqs[Requirement.DEFAULT], key=itemgetter('number')):
                    comment = comment + Utils.create_requirement_string(requirement, request.POST.get('format', 'old'))
        else:
            print("Not implemented...")

        extra = request.POST.get('challenge-extra', challenge_extra).strip()

        if extra:
            comment = comment + '\n<hr>\n\n' + request.POST.get('challenge-extra', challenge_extra).strip()
        
        return comment

    @staticmethod
    def create_challenge_from_code(thread_id, challenge_code, category):
        lines = challenge_code.splitlines()

        grouped_lines = [list(group) for key, group in groupby(lines, key=lambda line: line != '') if key]

        challenge_name = grouped_lines[0][0].split('__')[1] # "# __Challenge Name__"

        if Challenge.objects.filter(name=challenge_name).exists():
            return
        
        challenge = Challenge(name=challenge_name,
                              thread_id=thread_id,
                              category=category)

        # Determines if the challenge has unique requirements
        if "Seasonal" in challenge_name:
            challenge.allows_up_to_date = True
            needs_requirements = False
            challenge.extra = "Seasonal Badge Vote (Optional): [Anime_Title](https://anilist.co/anime/00000/)"
        elif "Classic" in challenge_name:
            needs_requirements = False
        else:
            needs_requirements = True
        
        current_mode = Requirement.DEFAULT

        grouped_lines, num_hr = remove_and_count_sublist(['<hr>'], grouped_lines)

        print(num_hr)
        
        if category == Challenge.GENRE:
            last_index = len(grouped_lines)
        else:
            if num_hr == 2:
                last_index = -1
                
                challenge.extra = '\n'.join(grouped_lines[-1])
            else:
                last_index = len(grouped_lines)

        challenge.save()

        for i, group in enumerate(grouped_lines[2:last_index]):
            if '---' in group:
                group.remove('---')

            if Utils.MODE_EASY in group:
                current_mode = Requirement.EASY
                continue
            elif Utils.MODE_NORMAL in group:
                current_mode = Requirement.NORMAL
                continue
            elif Utils.MODE_HARD in group:
                current_mode = Requirement.HARD
                continue
            elif Utils.MODE_BONUS in group:
                current_mode = Requirement.BONUS
                continue
            else:
                pass

            if "### __Winter__" in group:
                group.remove("### __Winter__")
            elif "### __Spring__" in group:
                group.remove("### __Spring__")
            elif "### __Summer__" in group:
                group.remove("### __Summer__")
            elif "### __Fall__" in group:
                group.remove("### __Fall__")

            # TODO Figure out the challenge extra code

            if needs_requirements:
                try:
                    mode = current_mode
                    bonus = group[0][0] == 'B' and group[0][1].isdigit()
                    number = re.search(r'([0-9]+)[.\)]', group[0]).group(1)

                    # Determine requirement text
                    text_regex = re.search(r'\_\_(.*)\_\_', group[0])

                    if text_regex != None:
                        text = text_regex.group(1)
                    else:
                        text = ' '

                    anime_title = re.search('\[(.+?)\]', group[1]).group(1)

                    has_anime_title = anime_title != 'Anime_Title'

                    if has_anime_title:
                        anime_link = re.search(r'\((https:\/\/anilist\.co\/anime\/[0-9]+)', group[1]).group(1)

                    # Handles in-line extra info
                    extra_split = group[2].split('//', 1)

                    if len(extra_split) > 1:
                        extra = extra_split[1]
                    else:
                        extra = ''

                    requirement = Requirement(number=number,
                                              mode=mode,
                                              challenge=challenge,
                                              text=text,
                                              extra=extra,
                                              bonus=bonus)
                except:
                    #Something with the formatting is weird so raw editing will be enforced
                    requirement = Requirement(number=number,
                                              mode=mode,
                                              challenge=challenge,
                                              text='',
                                              extra='',
                                              bonus=bonus,
                                              force_raw_edit=True,
                                              raw_requirement=line)

                if has_anime_title:
                    requirement.anime_title = anime_title
                    requirement.anime_link = anime_link

                requirement.save()
                
    # @staticmethod
    # def create_challenge_from_code(thread_id, challenge_code, category):
    #     lines = challenge_code.splitlines()

    #     challenge_name = re.search(r'# \_\_(.*)\_\_', lines[0].strip()).group(1)

    #     if Challenge.objects.filter(name=challenge_name).exists():
    #         return
        
    #     req_start_index = [i for i, s in enumerate(lines) if 'Legend' in s][0]

    #     # Determines if the challenge allows "Up to Date" requirement status
    #     allows_up_to_date = '[U]' in lines[req_start_index]
        
    #     challenge = Challenge(name=challenge_name,
    #                           thread_id=thread_id,
    #                           category=category,
    #                           allows_up_to_date=allows_up_to_date)

    #     # Determines if the challenge has unique requirements
    #     if "Seasonal" in challenge_name:
    #         needs_requirements = False
    #         challenge.extra = "Favourite (Optional): [Anime Title](https://anilist.co/anime/00000/)"
    #     elif "Classic" in challenge_name:
    #         needs_requirements = False
    #     else:
    #         needs_requirements = True
        
    #     challenge.save()

    #     # Determines if the challenge has prerequisite challenges
    #     prerequisite_lines = [line for line in lines[:req_start_index] if "Link to entry" in line]

    #     if prerequisite_lines:
    #         for line in prerequisite_lines:
    #             prerequisite_name = re.search(r'\[(.*)\]', line.strip()).group(1)
    #             prerequisite_challenge = Challenge.objects.get(name__contains=prerequisite_name.split(' ')[0])
    #             challenge.prerequisites.add(prerequisite_challenge)

    #         challenge.save()

    #     easy_index = normal_index = hard_index = bonus_index = -1

    #     prev_requirement = None

    #     if needs_requirements:
    #         for i, line in enumerate(lines[req_start_index + 2:]):
    #             line = line.lstrip()

    #             if Utils.MODE_EASY in line:
    #                 easy_index = i
    #             elif Utils.MODE_NORMAL in line:
    #                 normal_index = i
    #             elif Utils.MODE_HARD in line:
    #                 hard_index = i
    #             elif '__Bonus__' in line:
    #                 bonus_index = i
    #             elif '---' in line:
    #                 pass
    #             elif len(line) > 0:
    #                 #requirement = {}
                    
    #                 mode = get_requirement_mode(i, easy_index, normal_index, hard_index, bonus_index)

    #                 bonus = line[0] == 'B' and line[1].isdigit()

    #                 if line[0].isdigit() or bonus:
    #                     line = line.rstrip()

    #                     num_search = re.search(r'([0-9]+)[.\)]', line).group(1)

    #                     try:
    #                         # Determine requirement text
    #                         text_regex = re.search(r'\_\_(.*)\_\_', line)

    #                         has_anime_title = False

    #                         if text_regex != None:
    #                             text = text_regex.group(1)

    #                             line = line.replace(text, '')
    #                         else:
    #                             text = ' '
                                
    #                         anime_title = re.search(r'\[(.+?)\]', line).group(1)

    #                         if anime_title != "Anime Title":
    #                             anime_link = re.search(r'\((https:\/\/anilist\.co\/anime\/[0-9\/]+)\)', line).group(1)
    #                             has_anime_title = True

    #                         # Handles in-line extra info
    #                         extra = get_extra(line)

    #                         requirement = Requirement(number=num_search,
    #                                                   mode=mode,
    #                                                   challenge=challenge,
    #                                                   text=text,
    #                                                   extra=extra,
    #                                                   bonus=bonus)
    #                     except:
    #                         # Something with the formatting is weird so raw editing will be enforced
    #                         requirement = Requirement(number = num_search,
    #                                                   mode=mode,
    #                                                   challenge=challenge,
    #                                                   text='',
    #                                                   extra='',
    #                                                   bonus=bonus,
    #                                                   force_raw_edit=True,
    #                                                   raw_requirement=line)

    #                     if has_anime_title:
    #                         requirement.anime_title = anime_title
    #                         requirement.anime_link = anime_link

    #                     prev_requirement = requirement

    #                     requirement.save()
    #                 else:
    #                     # Handles new line extra info
    #                     if prev_requirement:
    #                         if prev_requirement.force_raw_edit:
    #                             prev_requirement.raw_requirement += '\n' + line
    #                         else:
    #                             if prev_requirement.extra.isspace() or prev_requirement.extra == '':
    #                                 prev_requirement.extra = line
    #                                 prev_requirement.extra_newline = True
    #                             else:
    #                                 prev_requirement.extra += ('\n' + line)

    #                         prev_requirement.save()
    #                     else:
    #                         if challenge.extra.isspace() or challenge.extra == '':
    #                             challenge.extra = line
    #                         else:
    #                             challenge.extra += '\n' + line

    #                         challenge.save()
    #             else:
    #                 prev_requirement = None
