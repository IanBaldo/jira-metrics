import json
from ApiConnector import ApiConnector
from DateModule import *
import sys

configFile = open("./config.json")
config = json.load(configFile)

jira_api = ApiConnector(config['jira_server_url'], config['email'], config['api_token'])
configFile.close()

# ultimo ano!
dt = createDateWithDelta(-730)

jql = "project = \"CLARO TV+\" AND \"Squad[Dropdown]\" in (\"Off Road\", Roku) and issuetype in (Bug, Sub-Bug, Sub-task) and status not in (Backlog) and created >= " + dt

all_issues = []
page_num = 1
issues_page, total = jira_api.getIssuesByJQL2(jql, 0)
all_issues = all_issues + issues_page
print("Total Issues: " + str(len(all_issues)) + " of " + str(total))
while(len(all_issues) < total):
    page_num += 1
    issues_page, total = jira_api.getIssuesByJQL2(jql, len(all_issues))
    all_issues = all_issues + issues_page
    print("Total Issues: " + str(len(all_issues)) + " of " + str(total))

with open('all_issues.json', 'w') as f:
    print (json.dumps(json.loads(json.dumps(all_issues)), sort_keys=True, indent=4, separators=(",", ": ")), file=f)
