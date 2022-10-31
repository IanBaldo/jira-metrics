import json
import csv
from ApiConnector import ApiConnector
from datetime import datetime, timedelta
from dateutil import parser
import matplotlib.pyplot as plt

configFile = open("./config.json")
config = json.load(configFile)

jira_api = ApiConnector(config['jira_server_url'], config['email'], config['api_token'])
configFile.close()

def simplifyObject(headers, row):
    obj = {}
    for i in range(len(headers)):
        if not row[i]: continue
        obj[headers[i]] =row[i]
    return obj

def createDateWithDelta(n_days):
    today = datetime.now()
    new_date = today + timedelta(days=n_days)
    return new_date.strftime("%Y-%m-%d")

def dateCmp(dt_1, dt_2):
    epoch = datetime.utcfromtimestamp(0)
    diff_1 = (parser.parse(dt_1) - epoch).total_seconds()
    diff_2 = (parser.parse(dt_2) - epoch).total_seconds()

    if (diff_1 - diff_2) > 0:
        return 1
    if (diff_1 - diff_2) == 0:
        return 0
    if (diff_1 - diff_2) < 0:
        return -1

def getDateDiff(dt_1, dt_2):
    return (parser.parse(dt_1) - parser.parse(dt_2)).days

def dateNow():
    return datetime.now().strftime("%Y-%m-%d")

def calcCycleTimeAvg(data):
    for status in data:
        data[status] = (sum(data[status]) / len(data[status]))
    return data

def plotCycleTime(cycle_time):
    fig, ax = plt.subplots()

    status = cycle_time.keys()
    values = cycle_time.values()

    ax.bar(status, values)

    ax.set_ylabel('Tempo em Dias (avg)')
    ax.set_title('Cycle Time')

    plt.show()

f = open("output.json", "w")

# Open file 
with open('data.csv') as file_obj:
      
    # Create reader object by passing the file 
    # object to reader method
    reader_obj = csv.reader(file_obj)
    headers = next(reader_obj)

    throughput = 0
    throughput_cycle_duration_days = -14
    throughput_timeframe = createDateWithDelta(throughput_cycle_duration_days)

    cycle_time_data = {
        "Doing" : [],
        "In Code Review" : [],
        "Ready QA" : [],
        "QA Validation" : [],
        "To Review" : [],
        "PO Validation" : [],
    }

    processados = 1
    for row in reader_obj:
        issue = simplifyObject(headers,row)
        issue = jira_api.getIssueData(issue["Issue key"])

        # Throughtput
        if issue["status"] == "PO Validation":
            if getDateDiff(issue["last_status_change"], throughput_timeframe) >= 0:
                throughput += 1
        
        # Cycle Time
        prev_status_change_date = None
        for event in issue["status_history"]:
            if prev_status_change_date is None and event["to"] == "Doing":
                prev_status_change_date = event["date"]
                if len(issue["status_history"]) == 1:
                    cycle_time_data["Doing"].append(getDateDiff(dateNow(), event["date"]))
                continue

            if not event["from"] in cycle_time_data:
                continue

            cycle_time_data[event["from"]].append(getDateDiff(event["date"], prev_status_change_date))
            prev_status_change_date = event["date"]


        # f.write(jira_api.getIssueData(issue['Issue key'])+"\n")
        print("Processando %s: %s %s" % (processados, issue["status"], issue["last_status_change"]))
        processados += 1
print("Throughput: %s" % throughput)
plotCycleTime(calcCycleTimeAvg(cycle_time_data))
f.close()
