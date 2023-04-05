import json
import sys

argv = sys.argv[1:]

def getDeveloperList(teams):
    devs = []
    for team in teams:
        devs += team["devs"]
    return devs

def cleanDeveloperNames(csv_dev_list):
    # - agostinho.t.junior@globalhitss.com.br
    dev_list = csv_dev_list.split(';')
    clean_list = []
    for name in dev_list:
        clean_list.append(name[1:].split('.')[0].strip().capitalize())
    
    return ";".join(clean_list)
        

teamsFile = open("./dev_teams.json")
teams = json.load(teamsFile)

workFile = open("./%s" % argv[0])
metricsItems = json.load(workFile)

team_developers = getDeveloperList(teams)

for team in teams:
    devs = ""
    data = "entregas;"
    for developer in metricsItems:
        
        if developer in team["devs"]:
            devs += (developer+";")
            data += (str(metricsItems[developer]["total"]) + ";")

    print(team["team"])
    print(";"+cleanDeveloperNames(devs))
    print(data)