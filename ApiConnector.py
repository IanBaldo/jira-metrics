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

    def getIssuesByJQL(self, jql_filter):
        url = "%s/rest/api/3/search" % (self.base_url)

        query = {
            'jql': jql_filter
        }
        
        response = requests.request(
            "GET",
            url,
            headers=self.headers,
            params=query
        )

        issues = []
        data = json.loads(response.text)
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

        return json.dumps(issues)

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
            if not entry["items"][0]["field"] == 'status':
                continue

            status_change = {
                'date': parser.parse(entry["created"]).strftime("%Y-%m-%d"),
                'from': entry["items"][0]["fromString"],
                'to': entry["items"][0]["toString"],
                'by_user':  entry["author"]["displayName"]
            }
            status_history.append(status_change)
        return status_history