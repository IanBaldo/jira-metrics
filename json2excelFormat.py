import json

teamsFile = open("./config.json")
teams = json.load(teamsFile)

workFile = open("./produtiv.json")
workItems = json.load(workFile)


for developer in workItems:
    print(developer)