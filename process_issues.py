import json
from DateModule import *

def getDeveloper(issue):
    developer_status = ["In Code Review"]
    developer = None
    for hist in issue["status_history"]:
        if hist["to"] in developer_status:
            developer = hist["by_user"]
    return developer

issues_file = open("./all_issues.json")
all_issues = json.load(issues_file)

productivity = {}

for issue in all_issues:
    developer = getDeveloper(issue)
    if developer:
        if not developer in productivity:
            productivity[developer] = {
                "issues" : [],
                "total": 0
            }
        
        productivity[developer]["issues"].append("%s" % (issue["key"]))
        productivity[developer]["total"] = len(productivity[developer]["issues"])


print (json.dumps(json.loads(json.dumps(productivity)), sort_keys=True, indent=4, separators=(",", ": ")))

# print(getDateDiff('2023-01-17','2022-07-28'))