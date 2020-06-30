import json
import re
import collections

from operator import itemgetter

from .models import Challenge, Requirement

class Utils(object):

    # Mode Headers
    MODE_EASY = "__Mode: Easy__"
    MODE_NORMAL = "__Mode: Normal__"
    MODE_HARD = "__Mode: Hard__"

    @staticmethod
    def split_by_key(dict_list, key):
        result = collections.defaultdict(list)

        for item in dict_list:
            result[item[key]].append(item)

        return result
    
    @staticmethod
    def create_requirement_string(requirement):
        requirement_string = "{number}) [{completed}] Start: {start} Finish: {finish} __{text}__ [{anime}]({link})".format(
            number=requirement['number'],
            completed=requirement['completed'],
            start=requirement['start'],
            finish=requirement['finish'],
            text=requirement['text'],
            anime=requirement['anime'],
            link=requirement['link'],
        )

        if requirement['extra_newline']:
            requirement_string = requirement_string + '\n' + requirement['extra'] + '\n'
        else:
            requirement_string = requirement_string + ' ' + requirement['extra'] + '\n'

        return requirement_string
        
    @staticmethod
    def parse_challenge_code(submission, response):
        """Returns a dictionary of the challenge code information"""
        
        response_dict = json.loads(response)
        
        comment = response_dict['data']['ThreadComment'][0]['comment']

        lines = comment.splitlines()

        parsed_comment = {}
        requirements = []

        parsed_comment['start'] = re.split('Start Date: ', lines[2])[1]
        parsed_comment['finish'] = re.split('Finish Date: ', lines[3])[1]
        parsed_comment['category'] = submission.challenge.category

        req_start_index = [i for i, s in enumerate(lines) if "Legend: [X] = Completed [O] = Not Completed" in s][0]

        easy_index = -1
        normal_index = -1
        hard_index = -1
        bonus_index = -1
        
        prev_requirement = {}
        prev_line_is_req = False
        
        for i, line in enumerate(lines[req_start_index + 1:]):
            line = line.strip()

            if Utils.MODE_EASY in line:
                easy_index = i
            elif Utils.MODE_NORMAL in line:
                normal_index = i
            elif Utils.MODE_HARD in line:
                hard_index = i
            elif '__Bonus__' in line:
                bonus_index = i
            elif '---' in line:
                pass
            elif len(line) > 0:
                requirement = {}
                
                # Modes are not used in for this challenge
                if easy_index == -1:
                    requirement['mode'] = Requirement.DEFAULT
                # Modes are used in this challenge
                else:
                    if bonus_index != -1 and i > bonus_index:
                        requirement['mode'] = Requirement.BONUS
                    elif hard_index != -1 and i > hard_index:
                        requirement['mode'] = Requirement.HARD
                    elif normal_index != -1 and i > normal_index:
                        requirement['mode'] = Requirement.NORMAL
                    elif easy_index != -1 and i > easy_index:
                        requirement['mode'] = Requirement.EASY
                    else:
                        print("This should not have happened... Mode not registered")
                
                bonus = line[0] == 'B'

                # If a requirement listing was found
                if line[0].isdigit() or bonus:
                    prev_line_is_req = True

                    requirement['bonus'] = bonus
                    
                    requirement['number'] = re.search(r'([0-9]+)[.\)]', line).group(1)

                    # Determine completed status
                    completed = re.search(r'\[[XO]\]', line).group()

                    if completed == '[X]':
                        requirement['completed'] = True
                    else:
                        requirement['completed'] = False

                    # Determine start and finish dates
                    requirement['start'] = re.search('Start: ([DMY0-9/]+)\s', line).group(1)
                    requirement['finish'] = re.search('Finish: ([DMY0-9/]+)', line).group(1)

                    # Determine requirement text
                    requirement['text'] = submission.challenge.requirement_set.get(number=requirement['number'], bonus=bonus).text
                    
                    # Determine the anime
                    requirement['anime'] = re.search('\_\s\[(.*)\]\(https:\/\/anilist\.co\/anime\/[0-9\/]+\)', line).group(1)
                    requirement['link'] = re.search(r'\((https:\/\/anilist\.co\/anime\/[0-9\/]+)\)', line).group(1)

                    # Get extra stuff
                    requirement['extra_newline'] = submission.challenge.requirement_set.get(number=requirement['number'], bonus=bonus).extra_newline

                    if not requirement['extra_newline']:
                        requirement['extra'] = re.split('\_ \[.+\]\(https:\/\/anilist\.co\/anime\/[0-9\/]+\)', line)[1]
                    prev_requirement = requirement
                    requirements.append(requirement)
                else:
                    if prev_line_is_req and prev_requirement['extra_newline']:
                        print(line)
                        if prev_requirement:
                            prev_requirement['extra'] = line

                            requirements[requirements.index(prev_requirement)] = prev_requirement
                            prev_line_is_req = False
                    else:
                        prev_requirement.clear()
                    
        parsed_comment['requirements'] = requirements
                
        return parsed_comment

    @staticmethod
    def create_comment_string(challenge_info, requirements, category, request):
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
                req['extra'] = request.POST.get('requirement-extra-{}'.format(requirement.number), requirement.extra).strip()

            reqs.append(req)
        
        comment = "# __{name}__\n\nChallenge Start Date: {start}\nChallenge Finish Date: {finish}\nLegend: [X] = Completed [O] = Not Completed\n\n"
        comment = comment.format(**challenge_info)

        reqs = Utils.split_by_key(reqs, 'mode')

        if category == Challenge.TIMED:
            for requirement in reqs[Requirement.DEFAULT]:
                comment = comment + Utils.create_requirement_string(requirement)
        elif category == Challenge.GENRE:
            if reqs[Requirement.EASY]:
                comment = comment + "\n---\n__Mode: Easy__\n"
                
                for requirement in sorted(reqs[Requirement.EASY], key=itemgetter('number')):
                    comment = comment + Utils.create_requirement_string(requirement)
            if reqs[Requirement.NORMAL]:
                comment = comment + "\n---\n__Mode: Normal__\n"

                for requirement in sorted(reqs[Requirement.NORMAL], key=itemgetter('number')):
                    comment = comment + Utils.create_requirement_string(requirement)
            if reqs[Requirement.HARD]:
                comment = comment + "\n---\n__Mode: Hard__\n"

                for requirement in sorted(reqs[Requirement.HARD], key=itemgetter('number')):
                    comment = comment + Utils.create_requirement_string(requirement)
            if reqs[Requirement.BONUS]:
                comment = comment + "\n---\n__Bonus__\n"

                for requirement in sorted(reqs[Requirement.BONUS], key=itemgetter('number')):
                    comment = comment + 'B' + Utils.create_requirement_string(requirement)
            if reqs[Requirement.DEFAULT]:
                comment = comment + "\n---\n__Misc__\n"

                for requirement in sorted(reqs[Requirement.DEFAULT], key=itemgetter('number')):
                    comment = comment + Utils.create_requirement_string(requirement)
        else:
            print("Not implemented...")
        
        return comment

    @staticmethod
    def create_challenge_from_code(thread_id, challenge_code, category):
        lines = challenge_code.splitlines()

        challenge_name = re.search(r'# \_\_(.*)\_\_', lines[0].strip()).group(1)
        
        challenge = Challenge(name=challenge_name, thread_id=thread_id, category=category)
        challenge.save()

        req_start_index = [i for i, s in enumerate(lines) if "Legend: [X] = Completed [O] = Not Completed" in s][0]

        easy_index = -1
        normal_index = -1
        hard_index = -1
        bonus_index = -1
        
        prev_requirement = None

        for i, line in enumerate(lines[req_start_index + 1:]):
            line = line.strip()

            if Utils.MODE_EASY in line:
                easy_index = i
            elif Utils.MODE_NORMAL in line:
                normal_index = i
            elif Utils.MODE_HARD in line:
                hard_index = i
            elif '__Bonus__' in line:
                bonus_index = i
            elif '---' in line:
                pass
            elif len(line) > 0:
                requirement = {}
                
                # Modes are not used in for this challenge
                if easy_index == -1:
                    mode = Requirement.DEFAULT
                # Modes are used in this challenge
                else:
                    if bonus_index != -1 and i > bonus_index:
                        mode = Requirement.BONUS
                    elif hard_index != -1 and i > hard_index:
                        mode = Requirement.HARD
                    elif normal_index != -1 and i > normal_index:
                        mode = Requirement.NORMAL
                    elif easy_index != -1 and i > easy_index:
                        mode = Requirement.EASY
                    else:
                        print("This should not have happened... Mode not registered")
                
                bonus = line[0] == 'B'
                
                if line[0].isdigit() or bonus:
                    num_search = re.search(r'([0-9]+)[.\)]', line).group(1)
                    
                    # Determine requirement text
                    text_regex = re.search('\_\_(.*)\_\_', line)
                    
                    if text_regex != None:
                        text = text_regex.group(1)
                    else:
                        text = ' '
                        
                    extra = re.split('\_ \[.+\]\(https:\/\/anilist\.co\/anime\/[0-9\/]+\)', line)[1]
                    
                    requirement = Requirement(number=num_search, mode=mode, challenge=challenge, text=text, extra=extra, bonus=bonus)
                    prev_requirement = requirement
                    requirement.save()
                else:
                    if lines[req_start_index + 1:][i - 1][0].isdigit() or line[req_start_index + 1:][i - 1][0] == 'B':
                        if prev_requirement:
                            prev_requirement.extra = line
                            prev_requirement.extra_newline = True
                            prev_requirement.save()
                    else:
                        prev_requirement = None
