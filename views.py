from django.shortcuts import render
from django.http import HttpResponse

from collections import OrderedDict
import operator
import os
import loadme
import statsloaderx
from mccme.models import Problem, UserProfile

#from pre_test import *

def test(request):
    return HttpResponse('Hello World')

def action(request):
#    return HttpResponse(request.body)

    urlrangex = list()

    with open(os.path.join('/home/django/django_project/mccme','plist.txt'), 'r') as plist:
        content = plist.readlines()

    def get_last_page_url(pid):
        trg = 'http://informatics.mccme.ru/moodle/ajax/ajax.php?problem_id=' + str(pid) + \
            '&group_id=-1' + \
            '&user_id=-1' + \
            '&lang_id=-1' + \
            '&status_id=-1' + \
            '&statement_id=0' + \
            '&objectName=submits' + \
            '&count=1' + \
            '&with_comment=' + \
            '&page=-1' + \
            '&action=getPageCount'
        return trg

    content = map(str.strip, content)
    for el in content:
        urlrangex.append(get_last_page_url(el))
    stats = dict()
    for r in loadme.load(urlrangex, 75):
        stats[int(r[1])] = int(r[0].split()[2][:-2])

    problems_in_db = Problem.objects.all()
    for pid, submits in stats.iteritems():
        problems= problems_in_db.filter(pid=pid)
        if problems:
            if problems[0].submits != submits:
                problems[0].submits = submits
                problems[0].save()
        else:
            # problem = Problem(pid=pid, submits=submits)
            problem = Problem()
            problem.pid = pid
            problem.submits = submits
            problem.save()


#    print r
#print stats # problem : attempts
##    with open('byproblem.txt', 'w') as bp:
  ##      for k, v in collections.OrderedDict(sorted(stats.iteritems())).iteritems():
#        print str(k) + '\t' + str(v)
    ##        bp.write(str(k) + '\t' + str(v) + '\n')

# ss = sorted(stats.items(), key=operator.itemgetter(1))
# print ss

##    with open('bysolutions.txt', 'w') as bs:
  ##      for k, v in sorted(stats.items(), key=operator.itemgetter(1)):
#        print str(k) + '\t' + str(v)
    ##        bs.write(str(k) + '\t' + str(v) + '\n')

    return HttpResponse(str(stats))

def show_me(request):
    return render(request, 'mccme/problems.html', {
        'problems': sorted(Problem.objects.all(), key=operator.attrgetter('submits'), reverse=True)
        })

def user_stats(request, uid):
    data_stats = statsloaderx.get_user_success_info(int(uid), 75, 100)
    solved = map(int, data_stats[0])
    unsolved = map(int, data_stats[1])
    users_in_db = UserProfile.objects.all()
    cuser = users_in_db.filter(uid=uid)
    if cuser:
        # cu.solved_problems.all().delete
        cuser = cuser[0]
        cuser.solved_problems.clear()
        cuser.unsolved_problems.clear()
        for ep in solved:
            cproblem = Problem.objects.all().filter(pid=ep)[0]
            cuser.solved_problems.add(cproblem)
        for ep in unsolved:
            cproblem = Problem.objects.all().filter(pid=ep)[0]
            cuser.unsolved_problems.add(cproblem)
        cuser.save()
    else:
        cuser = UserProfile(uid=uid)
        cuser.save()
        for ep in solved:
            cproblem = Problem.objects.all().filter(pid=ep)[0]
            cuser.solved_problems.add(cproblem)
        for ep in unsolved:
            cproblem = Problem.objects.all().filter(pid=ep)[0]
            cuser.unsolved_problems.add(cproblem)
        # cuser.save()
        # cuser = UserProfile(uid=uid, solved_problems=data_stats[0], unsolved_problems=data_stats[1])
        cuser.save()
    # return HttpResponse('user_stats: ' + uid + '\nsuccess: ' + str(data_stats[0]))
    # return HttpResponse('user_stats: ' + uid + '\nsuccess: ' + str(cuser.solved_problems.all()) + '\n' + str(cuser.unsolved_problems.all()))
    return render(request, 'mccme/userinfo.html',
                  {'problems_solved': cuser.solved_problems.all(),
                   'problems_unsolved': cuser.unsolved_problems.all()
                   })

def show_user(request, uid):
    data_stats = statsloaderx.get_user_success_info(int(uid), 75, 100)
    solved = map(int, data_stats[0])
    unsolved = map(int, data_stats[1])
    users_in_db = UserProfile.objects.all()
    cuser = users_in_db.filter(uid=uid)
    if cuser:
        cuser = cuser[0]
        cuser.solved_problems.clear()
        cuser.unsolved_problems.clear()
        for ep in solved:
            cuser.solved_problems.add(Problem.objects.all().filter(pid=ep)[0])
        for ep in unsolved:
            cuser.unsolved_problems.add(Problem.objects.all().filter(pid=ep)[0])
        cuser.save()
    else:
        cuser = UserProfile(uid=uid)
        cuser.save()
        for ep in solved:
            cuser.solved_problems.add(Problem.objects.all().filter(pid=ep)[0])
        for ep in unsolved:
            cuser.unsolver_problems.add(Problem.objects.all().filter(pid=ep)[0])
        cuser.save()
    all_problems = {problem: 'unsolved' for problem in Problem.objects.all()}
    for problem in cuser.solved_problems.all():
        if problem in all_problems.keys():
            all_problems[problem] = 'solved'
    for problem in cuser.unsolved_problems.all():
        if problem in all_problems.keys():
            all_problems[problem] = 'in_progress'
    all_problems = OrderedDict(sorted(all_problems.items(), key=lambda x: x[0].submits, reverse=True))
    total_count = len(all_problems.keys())
    solved_count = len(cuser.solved_problems.all())
    trying_count = len(cuser.unsolved_problems.all())
    submitted_by_smb = len([1 for p in Problem.objects.all() if p.submits > 0])
    return render(request, 'mccme/user_progress.html', {
                        'user': uid, 
                        'problems': all_problems,
                        'solved_count': solved_count,
                        'total_count': total_count,
                        'trying_count': trying_count,
                        'progress': '{0:.4f}'.format(float(solved_count)/total_count * 100),
                        'progress_light': '{0:.4f}'.format(float(solved_count)/submitted_by_smb * 100)
                        })

def multi_stats(request, uid):
    page = request.GET.get('page')
    # return HttpResponse(str(uid) + ' - ' + str(page))
    data_stats = statsloaderx.get_user_success_info(int(uid), 75, 100)
    solved = map(int, data_stats[0])
    unsolved = map(int, data_stats[1])
    users_in_db = UserProfile.objects.all()
    cuser = users_in_db.filter(uid=uid)
    if cuser:
        cuser = cuser[0]
        cuser.solved_problems.clear()
        cuser.unsolved_problems.clear()
        for ep in solved:
            cuser.solved_problems.add(Problem.objects.all().filter(pid=ep)[0])
        for ep in unsolved:
            cuser.unsolved_problems.add(Problem.objects.all().filter(pid=ep)[0])
        cuser.save()
    else:
        cuser = UserProfile(uid=uid)
        cuser.save()
        for ep in solved:
            cuser.solved_problems.add(Problem.objects.all().filter(pid=ep)[0])
        for ep in unsolved:
            cuser.unsolver_problems.add(Problem.objects.all().filter(pid=ep)[0])
        cuser.save()
    all_problems = {problem: 'unsolved' for problem in Problem.objects.all()}
    for problem in cuser.solved_problems.all():
        if problem in all_problems.keys():
            all_problems[problem] = 'solved'
    for problem in cuser.unsolved_problems.all():
        if problem in all_problems.keys():
            all_problems[problem] = 'in_progress'
    all_problems = OrderedDict(sorted(all_problems.items(), key=lambda x: x[0].submits, reverse=True))
    total_count = len(all_problems.keys())
    solved_count = len(cuser.solved_problems.all())
    trying_count = len(cuser.unsolved_problems.all())
    submitted_by_smb = len([1 for p in Problem.objects.all() if p.submits > 0])
    return render(request, 'mccme/user_progress.html', {
                        'user': uid,
                        'problems': all_problems[(int(page)-1) * 100:int(page) * 100],
                        'solved_count': solved_count,
                        'total_count': total_count,
                        'trying_count': trying_count,
                        'progress': '{0:.4f}'.format(float(solved_count)/total_count * 100),
                        'progress_light': '{0:.4f}'.format(float(solved_count)/submitted_by_smb * 100)
                        })