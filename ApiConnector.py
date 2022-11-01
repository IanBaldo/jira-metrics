import requests
import json
import base64
from dateutil import parser

class ApiConnector():

    def __init__(self, jira_server_url, email, token):
        self.base_url = jira_server_url
        self.headers = {
            "Accept": "application/json",
            "Authorization" : "Basic " + self.authKey(email, token)
        }

    def authKey(self, email, token):
        key = "%s:%s" % (email, token)
        key_bytes = key.encode('ascii')
        base64_bytes = base64.b64encode(key_bytes)
        base64_key = base64_bytes.decode('ascii')
        return base64_key 
    
    def response2json(self, object):
        if not isinstance(object, str):
            object = json.dumps(object)
        return json.dumps(json.loads(object), sort_keys=True, indent=4, separators=(",", ": "))

    def getIssuesByJQL(self, dt):
        url = "%s/rest/api/3/search" % (self.base_url)
        
        # * O filtro JQL deveria vir de fora, mas tive problemas com o encoding dos acentos
        # * Isso estava quebrando o filtro e resultando em retorno vazio
        query = {
            'jql': "(project = NOW AND (\"FORA DO PADRÃO - NOW Team (migrated 3)[Dropdown]\" in (\"Off Road\", Roku) or \"Squad[Dropdown]\" in (\"Off Road\", Roku)) and issuetype in (Story,Bug) and status not in (\"Item Concluído\", \"Tarefas pendentes.\", REFINADO, \"Aguardando Deploy\", \"Ready to Merge\", bloqueada)) or (project = NOW AND (\"FORA DO PADRÃO - NOW Team (migrated 3)[Dropdown]\" in (\"Off Road\", Roku) or \"Squad[Dropdown]\" in (\"Off Road\", Roku)) and issuetype in (Story,Bug) and status = \"Item Concluído\" and statusCategoryChangedDate >= '%s')" % dt
        }
        
        response = requests.request(
            "GET",
            url,
            headers=self.headers,
            params=query
        )

        issues = []
        data = json.loads(response.text)
        if not "issues" in data:
            return issues
            
        for api_issue in data["issues"]:
            issue = {
                "key" : api_issue["key"],
                "status" : api_issue["fields"]["status"]["name"],
                "last_status_change" : parser.parse(api_issue["fields"]["statuscategorychangedate"]).strftime("%Y-%m-%d"),
                "now_team" : api_issue["fields"]["customfield_11377"]["value"],
                "squad" : api_issue["fields"]["customfield_12124"]["value"],
                "train" : api_issue["fields"]["customfield_11216"]["value"],
                "estimate" : api_issue["fields"]["aggregatetimeoriginalestimate"],
                "link" : api_issue["self"],
                "is_blocked" : False if api_issue["fields"]["customfield_10048"] == None else True,
                "status_history" : self.getIssueStatusHistory(api_issue["key"])
            }
            issues.append(issue)
            print("Processed %d/%d" % (len(issues), len(data["issues"])), end = "\r")

        return issues

    def getIssueData(self, issue_key):
        url = "%s/rest/api/2/issue/%s" % (self.base_url, issue_key)
        response = requests.request(
            "GET",
            url,
            headers=self.headers
        )

        data = json.loads(response.text)
        issue = {
            "key" : data["key"],
            "status" : data["fields"]["status"]["name"],
            "last_status_change" : parser.parse(data["fields"]["statuscategorychangedate"]).strftime("%Y-%m-%d"),
            "now_team" : data["fields"]["customfield_11377"]["value"],
            "train" : data["fields"]["customfield_11216"]["value"],
            "estimate" : None if not "originalEstimateSeconds" in data["fields"]["timetracking"] else data["fields"]["timetracking"]["originalEstimateSeconds"],
            "link" : data["self"],
            "is_blocked" : False if data["fields"]["customfield_10048"] == None else True,
            "status_history" : self.getIssueStatusHistory(issue_key)
        }

        return issue

    def getIssueChangelog(self, issue_key):
        url = "%s/rest/api/3/issue/%s/changelog" % (self.base_url, issue_key)
        response = requests.request(
            "GET",
            url,
            headers=self.headers
        )

        return self.response2json(response.text)

    def getIssueStatusHistory(self, issue_key):
        change_log = json.loads(self.getIssueChangelog(issue_key))
        status_history = []
        for entry in change_log['values']:
            # ! Temp (ugly solution) need to adjust. Can't think atm
            is_status_change = False
            index = 0
            while index < len(entry["items"]):
                if entry["items"][index]["field"] == 'status':
                    is_status_change = True
                    break
                index += 1

            if not is_status_change:
                continue

            status_change = {
                'date': parser.parse(entry["created"]).strftime("%Y-%m-%d"),
                'from': entry["items"][index]["fromString"],
                'to': entry["items"][index]["toString"],
                'by_user':  entry["author"]["displayName"]
            }
            status_history.append(status_change)
        return status_history