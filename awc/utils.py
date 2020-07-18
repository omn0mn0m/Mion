
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
        parsed_comment = {}
        requirements = []

        response_dict = json.loads(response)

        comment = 'No comment found...'

        try:
            comment = response_dict['data']['ThreadComment'][0]['comment']

            lines = comment.splitlines()
        
            req_start_index = [i for i, s in enumerate(lines) if "Legend: [X] = Completed [O] = Not Completed" in s][0]

            has_prerequisites = submission.challenge.prerequisites.exists()

            if has_prerequisites:
                parsed_comment['prerequisites'] = {}
            
            for line in lines[:req_start_index]:
                if has_prerequisites:
                    prerequisite_challenge_name = re.search(r'\[(.*)\]', line)
                    prerequisite_finish_date_regex = re.search(r'\) Finish Date: (.*)', line)

                    if prerequisite_challenge_name and prerequisite_finish_date_regex:
                        parsed_comment['prerequisites'][prerequisite_challenge_name.group(1)] = prerequisite_finish_date_regex.group(1)
                
                start_regex = re.search(r'Start Date: (.*)', line)

                if start_regex:
                    parsed_comment['start'] = start_regex.group(1)
                    
                finish_regex = re.search(r'[a-zA-z]+\sFinish Date: (.*)', line)
                
                if finish_regex:
                    parsed_comment['finish'] = finish_regex.group(1)
                
            parsed_comment['category'] = submission.challenge.category
            parsed_comment['extra'] = ''
            
            easy_index = -1
            normal_index = -1
            hard_index = -1
            bonus_index = -1

            prev_requirement = {}

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
                        else:
                            requirement['extra'] = ''

                        prev_requirement = requirement
                        requirements.append(requirement)
                    else:
                        if prev_requirement:
                            if prev_requirement['extra'].isspace():
                                prev_requirement['extra'] = line
                            else:
                                prev_requirement['extra'] += ('\n' + line)

                            requirements[requirements.index(prev_requirement)] = prev_requirement
                        else:
                            if parsed_comment['extra'].isspace() or parsed_comment['extra'] == '':
                                parsed_comment['extra'] = line
                            else:
                                parsed_comment['extra'] += '\n' + line
                else:
                    prev_requirement = None

            parsed_comment['requirements'] = requirements
            parsed_comment['failed'] = False
        except Exception as e:
            print(e)
            
            parsed_comment = {
                'failed': True,
                'error': e,
                'comment': comment,
            }
                
        return parsed_comment

    @staticmethod
    def create_comment_string(request, challenge, user):
        category = challenge.category
        challenge_extra = request.POST.get('challenge-extra', challenge.extra).strip()
            
        reqs = []

        for requirement in challenge.requirement_set.all().order_by('id'):
            req = {}

            req['number'] = requirement.number
            req['text'] = requirement.text
            req['extra_newline'] = requirement.extra_newline
            req['bonus'] = requirement.bonus

            if requirement.bonus:
                req['mode'] = request.POST.get('mode-bonus-{}'.format(requirement.number), requirement.mode).strip()

                if request.POST.get('completed-bonus-{}'.format(requirement.number), "off") == 'on':
                    req['completed'] = 'X'
                else:
                    req['completed'] = 'O'

                req['start'] = request.POST.get('requirement-start-bonus-{}'.format(requirement.number), "DD/MM/YYYY").strip()
                req['finish'] = request.POST.get('requirement-finish-bonus-{}'.format(requirement.number), "DD/MM/YYYY").strip()
                req['anime'] = request.POST.get('requirement-anime-bonus-{}'.format(requirement.number), "Anime Title").strip()
                req['link'] = request.POST.get('requirement-link-bonus-{}'.format(requirement.number), "https://anilist.co/anime/00000/").strip()
                req['extra'] = request.POST.get('requirement-extra-bonus-{}'.format(requirement.number), requirement.extra).strip()
            else:
                req['mode'] = request.POST.get('mode-{}'.format(requirement.number), requirement.mode).strip()

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
        
        comment = "# __{name}__\n\n".format(name=challenge.name)

        # Add prerequitites section
        for prerequisite in challenge.prerequisites.all():
            try:
                prerequisite_challenge = user.submission_set.get(challenge__name=prerequisite.name)
                post_link = "https://anilist.co/forum/thread/{}/comment/{}".format(prerequisite_challenge.challenge.thread_id, prerequisite_challenge.comment_id)
            except Exception as err:
                post_link = "https://anilist.co/forum/thread/0000/comment/00000"

                print(err)
            
            comment += "[{prerequisite_name}]({post_link}) Finish Date: {finish_date}\n".format(prerequisite_name=prerequisite.name,
                                                                                       post_link=post_link,
                                                                                       finish_date=request.POST.get('prerequisite-' + prerequisite.name + '-finish', 'DD/MM/YYYY').strip())

        if challenge.prerequisites.count() > 0:
            comment += '\n'
        
        # Dates
        comment += "Challenge Start Date: {start}\nChallenge Finish Date: {finish}\nLegend: [X] = Completed [O] = Not Completed\n\n".format(start=request.POST.get('challenge-start', 'DD/MM/YYYY').strip(),
                                                                                                                                            finish=request.POST.get('challenge-finish', 'DD/MM/YYYY').strip())

        reqs = Utils.split_by_key(reqs, 'mode')

        if category == Challenge.TIMED:
            for requirement in reqs[Requirement.DEFAULT]:
                comment = comment + Utils.create_requirement_string(requirement)
        elif category == Challenge.GENRE:
            if reqs[Requirement.EASY]:
                comment = comment + "\n---\n__Mode: Easy__\n"
                
                for requirement in sorted(reqs[Requirement.EASY], key=itemgetter('number')):
                    if requirement['bonus']:
                        comment = comment + 'B' + Utils.create_requirement_string(requirement)
                    else:
                        comment = comment + Utils.create_requirement_string(requirement)
            if reqs[Requirement.NORMAL]:
                comment = comment + "\n---\n__Mode: Normal__\n"

                for requirement in sorted(reqs[Requirement.NORMAL], key=itemgetter('number')):
                    if requirement['bonus']:
                        comment = comment + 'B' + Utils.create_requirement_string(requirement)
                    else:
                        comment = comment + Utils.create_requirement_string(requirement)
            if reqs[Requirement.HARD]:
                comment = comment + "\n---\n__Mode: Hard__\n"

                for requirement in sorted(reqs[Requirement.HARD], key=itemgetter('number')):
                    if requirement['bonus']:
                        comment = comment + 'B' + Utils.create_requirement_string(requirement)
                    else:
                        comment = comment + Utils.create_requirement_string(requirement)
            if reqs[Requirement.BONUS]:
                comment = comment + "\n---\n__Bonus__\n"

                for requirement in sorted(reqs[Requirement.BONUS], key=itemgetter('number')):
                    if requirement['bonus']:
                        comment = comment + 'B' + Utils.create_requirement_string(requirement)
                    else:
                        comment = comment + Utils.create_requirement_string(requirement)
            if reqs[Requirement.DEFAULT]:
                comment = comment + "\n---\n__Misc__\n"

                for requirement in sorted(reqs[Requirement.DEFAULT], key=itemgetter('number')):
                    if requirement['bonus']:
                        comment = comment + 'B' + Utils.create_requirement_string(requirement)
                    else:
                        comment = comment + Utils.create_requirement_string(requirement)
        elif category == Challenge.TIER:
            for requirement in reqs[Requirement.DEFAULT]:
                comment = comment + Utils.create_requirement_string(requirement)
        else:
            print("Not implemented...")

        comment = comment + '\n' + request.POST.get('challenge-extra', challenge_extra).strip()
        
        return comment

    @staticmethod
    def create_challenge_from_code(thread_id, challenge_code, category):
        lines = challenge_code.splitlines()

        challenge_name = re.search(r'# \_\_(.*)\_\_', lines[0].strip()).group(1)

        if Challenge.objects.filter(name=challenge_name).exists():
            return
        
        req_start_index = [i for i, s in enumerate(lines) if "Legend: [X] = Completed [O] = Not Completed" in s][0]

        prerequisite_lines = [line for line in lines[:req_start_index] if "Link to entry" in line]
        prerequisites = {}

        challenge = Challenge(name=challenge_name,
                              thread_id=thread_id,
                              category=category)
        challenge.save()
        
        for line in prerequisite_lines:
            prerequisite_name = re.search(r'\[(.*)\]', line.strip()).group(1)
            prerequisite_challenge = Challenge.objects.get(name__contains=prerequisite_name.split(' ')[0])
            challenge.prerequisites.add(prerequisite_challenge)
        
        challenge.save()

        print(challenge.prerequisites.all())
        
        easy_index = -1
        normal_index = -1
        hard_index = -1
        bonus_index = -1
        
        prev_requirement = None

        for i, line in enumerate(lines[req_start_index + 2:]):
            line = line.lstrip()

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
                    line = line.rstrip()
                    
                    num_search = re.search(r'([0-9]+)[.\)]', line).group(1)
                    
                    # Determine requirement text
                    text_regex = re.search('\_\_(.*)\_\_', line)
                    
                    if text_regex != None:
                        text = text_regex.group(1)
                    else:
                        text = ' '

                    # Handles in-line extra info
                    extra = re.split('\_ \[.+\]\(https:\/\/anilist\.co\/anime\/[0-9\/]+\)', line)[1]
                    
                    requirement = Requirement(number=num_search, mode=mode, challenge=challenge, text=text, extra=extra, bonus=bonus)
                    prev_requirement = requirement
                    requirement.save()
                else:
                    # Handles new line extra info
                    if prev_requirement:
                        if prev_requirement.extra.isspace():
                            prev_requirement.extra = line
                            prev_requirement.extra_newline = True
                        else:
                            prev_requirement.extra += ('\n' + line)

                        prev_requirement.save()
                    else:
                        if challenge.extra.isspace() or challenge.extra == '':
                            challenge.extra = line
                        else:
                            challenge.extra += '\n' + line
                            
                        challenge.save()
            else:
                prev_requirement = None
