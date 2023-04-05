import json
from DateModule import *

def getDeveloperList(teams):
    devs = []
    for team in teams:
        devs += team["devs"]
    return devs

def lastChangeByEmerson(issue):
    last_status_change = issue["status_history"][-1]
    if last_status_change["by_user"] == "- emerson.vaz.3@globalhitss.com.br":
        return True
    return False

def isTicketDone(issue):
    complete_status = ["Done", "In Review"]
    last_status_change = issue["status_history"][-1]
    if last_status_change["to"] in complete_status:
        return (True, last_status_change["date"])
    return (False, None)

def isStory(issue):
    if issue["issue_type"] != "Story":
        return False
    return True

def getDeveloper(issue):
    developer_status = ["In Development", "Doing"]
    developer = None
    for hist in issue["status_history"]:
        if hist["to"] in developer_status:
            developer = hist["by_user"]
    return developer

issues_file = open("./all_issues.json")
all_issues = json.load(issues_file)

teamsFile = open("./dev_teams.json")
teams = json.load(teamsFile)

productivity = {
    "no_dev": []
}

totals = {
    "Bug" : 0,
    "Story" : 0
}

team_developers = getDeveloperList(teams)

for issue in all_issues:
    if lastChangeByEmerson(issue):
        continue

    developer = getDeveloper(issue)
    if not developer in team_developers:
        continue

    isDone, doneDate = isTicketDone(issue)
    if isDone and (getDateDiff(doneDate, '2023-01-01') >= 0):
        if issue["issue_type"] in totals:
                totals[issue["issue_type"]] += 1
    else:
        continue

    if isStory(issue):
        continue

    if issue["issue_type"] == 'Bug':
        print(issue["key"])

    if developer:
        if not developer in productivity:
            productivity[developer] = {
                "total": 0,
                "issues" : []
            }
        
        productivity[developer]["issues"].append("%s" % (issue["key"]))
        productivity[developer]["total"] = len(productivity[developer]["issues"])
    else:
        productivity["no_dev"].append(issue["key"])

print (json.dumps(json.loads(json.dumps(totals)), sort_keys=True, indent=4, separators=(",", ": ")))
print('\n')
print (json.dumps(json.loads(json.dumps(productivity)), sort_keys=True, indent=4, separators=(",", ": ")))

# print(getDateDiff('2023-01-17','2022-07-28'))