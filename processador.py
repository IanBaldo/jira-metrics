import json
import copy
from ApiConnector import ApiConnector
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
from DateModule import *

configFile = open("./config.json")
config = json.load(configFile)

jira_api = ApiConnector(config['jira_server_url'], config['email'], config['api_token'])
configFile.close()

story_color = '#1ab802'
bug_color = '#cc3333'
background = '#ffffff'
title_color = '#000000'
font_color = '#000000'

def calcLeadTime(cycle_time_avg):
    progress_status_list = ["Doing", "In Code Review", "Ready QA", "Em QA", "To Review"]
    lead_time_avg = {}
    for issue_type in cycle_time_avg:
        lead_time_avg[issue_type] = 0
        for status in cycle_time_avg[issue_type]:
            if status in progress_status_list:
                lead_time_avg[issue_type] += cycle_time_avg[issue_type][status]
        lead_time_avg[issue_type] = round(lead_time_avg[issue_type], 1)
    return lead_time_avg

def plotCycleTime(cycle_time, ax=None):
    ax = ax or plt.gca()

    status = cycle_time["Story"].keys()

    values = {}
    for issue_type in cycle_time:
        values[issue_type] = []
        for status in cycle_time[issue_type]:
            values[issue_type].append(cycle_time[issue_type][status])

    x_pos = np.arange(len(values["Story"]))
    width = 0.35
    rects1 = ax.bar(x_pos - width/2, values["Story"], width, label='Story', color=story_color)
    rects2 = ax.bar(x_pos + width/2, values["Bug"], width, label='Bug', color=bug_color)

    ax.bar_label(rects1, label_type='center')
    ax.bar_label(rects2, label_type='center')
    ax.tick_params(labelcolor=font_color)
    ax.spines['bottom'].set_color(font_color)
    ax.spines['top'].set_color(font_color) 
    ax.spines['right'].set_color(font_color)
    ax.spines['left'].set_color(font_color)

    ax.legend()

    ax.set_ylabel('Dias', color=font_color)
    ax.set_title('Cycle Time(Avg)', color=font_color)

    plt.plot()

def plotBlockedIssues(blocked_issues, ax=None):
    ax = ax or plt.gca()

    status = blocked_issues.keys()
    values = blocked_issues.values()

    y_pos = np.arange(len(status))
    bars = ax.barh(y_pos, values, align='center')
    ax.bar_label(bars, label_type='center')
    ax.set_yticks(y_pos, labels=status, color=font_color)
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.set_xlabel('Total', color=font_color)
    ax.set_title('Quantas tarefas estão bloqueadas?', color=font_color)

    plt.plot()

def plotThroughtputAndLeadTime(throughput, lead_time):
    plt.text(0.18, 1, "Throughput", size=15, color=font_color)
    plt.text(0.35, 0.8, throughput, size=15, bbox=dict(boxstyle="round"))

    plt.text(0.2, 0.5, "Lead Time (Story)", size=15, color=font_color)
    plt.text(0.3, 0.35, lead_time["Story"], size=15, bbox=dict(boxstyle="round"))

    plt.text(0.2, 0.2, "Lead Time (Bug)", size=15, color=font_color)
    plt.text(0.3, 0.05, lead_time["Bug"], size=15, bbox=dict(boxstyle="round"))

def plot2Pdf(pdf_title, issues, cycle_time_avg, blocked_issues, throughput):
    with PdfPages("%s.pdf" % pdf_title) as pdf:
        # figsize of A4 paper
        fig = plt.figure(figsize=(8.3, 11.7), facecolor=background)
        rows = 3
        cols = 2
        grid = plt.GridSpec(rows, cols, wspace=0.2, hspace=0.3)

        # fig_ax1 = fig.add_subplot(grid[0, 0])
        # fig_ax1.set_axis_off()
        # plotThroughtputAndLeadTime(throughput, calcLeadTime(cycle_time_avg))

        lead_time = calcLeadTime(cycle_time_avg)
        desc1 = '\t Throughput \t Lead Time(Story) \t Lead Time(Bug)'
        desc2 = "\n \t %d \t %.1f \t %.1f" % (throughput, lead_time['Story'], lead_time['Bug'])
        fig.text(1/cols-0.2,0.8,desc1+desc2, color=font_color) # horizontally 1/2 halfway from left, vertically 2/3 from bottom, 0,0 is bottom left, 1,1 is top right
        

        fig_ax3 = fig.add_subplot(grid[1,:2])
        plotCycleTime(cycle_time_avg)
        
        fig_ax4 = fig.add_subplot(grid[2, 0])
        plotBlockedIssues(blocked_issues)
        fig_ax5 = fig.add_subplot(grid[2, 1])
        fig_ax5.set_axis_off()

        # df = pd.DataFrame(data=issues, columns=["key", "issue_type", "status", "is_blocked"])
        # fig_ax6 = fig.add_subplot()
        # fig_ax6.set_axis_off()
        # fig_ax6.table(cellText=df.values, colLabels=df.columns, 
        #         loc='center',             #header cell alignment
        #         cellLoc='center',         #body cell alignment
        #         edges='BRTL')       #turns edges on horizontally
        
        fig.suptitle('Métricas Off-Road', fontsize=38, color=title_color, family='monospace')
        
        pdf.savefig(facecolor=background)
        plt.close()

throughput = 0
throughput_cycle_duration_days = -14
throughput_timeframe = createDateWithDelta(throughput_cycle_duration_days)

cycle_time_data = {
    "Story": {
        "Doing" : [],
        "In Code Review" : [],
        "Ready QA" : [],
        "Em QA" : [],
        "To Review" : [],
        "PO Validation" : [],
    },
    "Bug": {
        "Doing" : [],
        "In Code Review" : [],
        "Ready QA" : [],
        "Em QA" : [],
        "To Review" : [],
        "PO Validation" : [],
    }
}

## New Status
# cycle_time_data = {
#     "IN DEVELOPMENT" : [],
#     "IN CODE REVIEW" : [],
#     "TO TEST" : [],
#     "IN TEST" : [],
#     "TO REVIEW" : [],
#     "IN REVIEW" : [],
# }


# * Jql partindo do config vai ter que aguardar algum desses itens:
# * Alteração do filtro (nome de campo e status) para não usar acentuação
# * Solução do problema com o encoding quando passados por parâmetro
# jql = config['jql'] % throughput_timeframe

# blocked_issues = copy.deepcopy(cycle_time_data)
blocked_issues = {
    "Doing" : 0,
    "In Code Review" : 0,
    "Ready QA" : 0,
    "Em QA" : 0,
    "To Review" : 0,
    "PO Validation" : 0,
}

issues = []
issues = jira_api.getIssuesByJQL(throughput_timeframe)
for issue in issues:

    if issue["is_blocked"]:
        blocked_issues[issue["status"]] += 1

    if issue["status"] in ["PO Validation","Item Conclu\u00eddo"]:
        if getDateDiff(issue["last_status_change"], throughput_timeframe) >= 0:
            throughput += 1
    
    prev_status_change = None
    for event in issue["status_history"]:
        if not event["from"] in cycle_time_data[issue["issue_type"]]:
            prev_status_change = event
            continue

        cycle_time_data[issue["issue_type"]][event["from"]].append(getDateDiff(event["date"], prev_status_change["date"]))
        prev_status_change = event

    if prev_status_change["to"] in cycle_time_data[issue["issue_type"]]:
        cycle_time_data[issue["issue_type"]][prev_status_change["to"]].append(getDateDiff(dateNow(), prev_status_change["date"]))

plot2Pdf('metricas off-road', issues, calcCycleTimeAvg(cycle_time_data), blocked_issues, throughput)