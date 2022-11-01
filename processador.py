import json
import csv
from ApiConnector import ApiConnector
from datetime import datetime, timedelta
from dateutil import parser
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

configFile = open("./config.json")
config = json.load(configFile)

jira_api = ApiConnector(config['jira_server_url'], config['email'], config['api_token'])
configFile.close()

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
        if len(data[status]) == 0:
            data[status] = 0
            continue
        data[status] = round((sum(data[status]) / len(data[status])), 1)
    return data

def calcLeadTime(cycle_time_avg):
    progress_status_list = ["Doing", "In Code Review", "Ready QA", "Em QA", "To Review"]
    lead_time_avg = 0
    for status in cycle_time_avg:
        if status in progress_status_list:
            lead_time_avg += cycle_time_avg[status]
            
    return round(lead_time_avg, 1)

def plotCycleTime(cycle_time, ax=None):
    ax = ax or plt.gca()

    status = cycle_time.keys()
    values = cycle_time.values()

    rects = ax.bar(status, values)
    ax.bar_label(rects, padding=3)

    ax.set_ylabel('Dias')
    ax.set_title('Cycle Time(Avg)')

    plt.plot()

def plotThroughtputAndLeadTime(throughput, lead_time):
    plt.text(0.18, 1, "Throughput", size=15)
    plt.text(0.35, 0.8, throughput, size=15, bbox=dict(boxstyle="round"))

    plt.text(0.2, 0.5, "Lead Time", size=15)
    plt.text(0.3, 0.3, lead_time, size=15, bbox=dict(boxstyle="round"))

def plot2Pdf(pdf_title, cycle_time_avg, throughput):
    deepgreen = '#8c9344'
    lightbeige = '#eef1d4'
    medgreen = '#a2a963'
    darkbrown = '#242112'

    with PdfPages("%s.pdf" % pdf_title) as pdf:
        # figsize of A4 paper
        fig = plt.figure(figsize=(8.3, 11.7), facecolor=deepgreen)
        rows = 3
        cols = 2
        grid = plt.GridSpec(rows, cols, wspace=0.2, hspace=0.3)

        col = darkbrown
        fig_ax1 = fig.add_subplot(grid[0, 0], facecolor=medgreen)
        fig_ax1.set_axis_off()
        plotThroughtputAndLeadTime(throughput, calcLeadTime(cycle_time_avg))

        desc1 = 'A short description here \n line break continues \n the interesting information.'
        desc2 = '\n \n We can fill the space \n so that it looks nicely placed.'
        desc3 = '\n \n ~ bullet 1 \n ~ bullet 2 \n ~ bullet 3'
        fig.text(1/cols+0.025, 2/rows+0.03, desc1+desc2+desc3, color=darkbrown) # horizontally 1/2 halfway from left, vertically 2/3 from bottom, 0,0 is bottom left, 1,1 is top right
        

        fig_ax3 = fig.add_subplot(grid[1,:2])
        plotCycleTime(cycle_time_avg)
        
        fig_ax4 = fig.add_subplot(grid[2, 0])
        fig_ax5 = fig.add_subplot(grid[2, 1])

        fig.suptitle('Métricas Off-Road', fontsize=38, color=lightbeige, family='monospace')
        
        pdf.savefig(facecolor=deepgreen)
        plt.close()

throughput = 0
throughput_cycle_duration_days = -14
throughput_timeframe = createDateWithDelta(throughput_cycle_duration_days)

cycle_time_data = {
    "Doing" : [],
    "In Code Review" : [],
    "Ready QA" : [],
    "Em QA" : [],
    "To Review" : [],
    "PO Validation" : [],
}

processados = 1

# * Jql partindo do config vai ter que aguardar algum desses itens:
# * Alteração do filtro (nome de campo e status) para não usar acentuação
# * Solução do problema com o encoding quando passados por parâmetro
# jql = config['jql'] % throughput_timeframe

issues = jira_api.getIssuesByJQL(throughput_timeframe)
for issue in issues:
    # Throughtput
    if issue["status"] in ["PO Validation","Item Conclu\u00eddo"]:
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

    processados += 1

plot2Pdf('metricas off-road', calcCycleTimeAvg(cycle_time_data), throughput)