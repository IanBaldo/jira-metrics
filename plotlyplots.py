import pandas as pd
import plotly_express as px
import json
from ApiConnector import ApiConnector
from DateModule import *
import copy
import plotly.graph_objects as go
from plotly.subplots import make_subplots

configFile = open("./config.json")
config = json.load(configFile)

jira_api = ApiConnector(config['jira_server_url'], config['email'], config['api_token'])
configFile.close()

throughput = 0
throughput_cycle_duration_days = -14
throughput_timeframe = createDateWithDelta(throughput_cycle_duration_days)

issues = []
issues = jira_api.getIssuesByJQL(throughput_timeframe)



cycle_time = []
blocked_issues = []

for issue in issues:
    cycle_time_data = {
        "key" : issue["key"],
        "issue_type" : issue["issue_type"],
        "status" : "Backlog",
        "time" : 0
    }

    if issue["is_blocked"]:
        blocked_issues.append({
            "key" : issue["key"],
            "status" : issue["status"],
            "issue_type" : issue["issue_type"]
        })

    if issue["status"] in ["PO Validation","Item Conclu\u00eddo", "Done", "In Review"]:
        if getDateDiff(issue["last_status_change"], throughput_timeframe) >= 0:
            throughput += 1
   
    prev_status_change = None
    for event in issue["status_history"]:
        if prev_status_change is None:
            prev_status_change = event
            continue

        cycle_time_data["status"] = event["from"]
        cycle_time_data["time"] = getDateDiff(event["date"], prev_status_change["date"])
        prev_status_change = event
        cycle_time.append(copy.copy(cycle_time_data))

    if prev_status_change != None:
        cycle_time_data["status"] = prev_status_change["to"]
        cycle_time_data["time"] = getDateDiff(dateNow(), prev_status_change["date"])
        cycle_time.append(copy.copy(cycle_time_data))

df = pd.DataFrame(cycle_time)

status_to_display = 'Doing', 'Ready QA', 'Em QA', 'To Review', 'PO Validation', 'In Development', 'In Code Review', 'To Test', 'In Test', 'To Review', 'In Review'
cycle_time_plotable = df.query("status in (@status_to_display)").groupby(by=["issue_type", "status"]).mean("time").reset_index(level=[0,1])
cycle_time_story = cycle_time_plotable.query("issue_type == 'Story'")
cycle_time_bug = cycle_time_plotable.query("issue_type == 'Bug'")

lead_time_story = cycle_time_story['time'].sum()
lead_time_bug = cycle_time_bug['time'].sum()

fig = make_subplots(
    rows=2,
    cols=3,
    specs=[
        [{"type" : "indicator"}, {"type" : "indicator"}, {"type" : "indicator"}],
        [{"type": "bar", "colspan": 2}, {}, {"type" : "bar"}]
    ],
    subplot_titles=("", "", "", "Cycle Time", "", "Tarefas Bloqueadas")
)

fig.add_trace(
    go.Indicator(
    mode = "number",
    value = throughput,
    title = {"text": "Throughtput"}),
    row=1, col=1
)

fig.add_trace(
    go.Indicator(
    mode = "number",
    value = lead_time_story,
    number={'font_color':'green'},
    title = {"text": "Lead Time ( Story )"}),
    row=1, col=2
)

fig.add_trace(
    go.Indicator(
    mode = "number",
    value = lead_time_bug,
    number={'font_color':'crimson'},
    title = {"text": "Lead Time ( Bug )"}),
    row=1, col=3
)

fig.add_trace(
    go.Bar(
        name="Story",
        x=cycle_time_story['status'],
        y=cycle_time_story['time'],
        marker_color='green',
        text = cycle_time_story['time'],
        texttemplate="%{text:.1f}",
        textposition="outside",
        offsetgroup=0
        ),
    row=2, col=1
)

fig.add_trace(
    go.Bar(
        name="Bug",
        x=cycle_time_bug['status'],
        y=cycle_time_bug['time'],
        marker_color='crimson',
        text = cycle_time_bug['time'],
        texttemplate="%{text:.1f}",
        textposition="outside",
        offsetgroup=1
        ),
    row=2, col=1
)


if len(blocked_issues):
    blocked_issues_df = pd.DataFrame(blocked_issues)
    blocked_issues_filtered = blocked_issues_df.query("status in (@status_to_display)").groupby(by=["issue_type", "status"]).count().reset_index(level=[0,1])

    blocked_issues_stories = blocked_issues_filtered.query("issue_type == 'Story'")
    blocked_issues_bugs = blocked_issues_filtered.query("issue_type == 'Bug'")

    fig.add_trace(
        go.Bar(
            name='Story',
            x=blocked_issues_stories['key'],
            y=blocked_issues_stories['status'],
            marker_color='green',
            text = blocked_issues_stories['key'],
            texttemplate="%{text:.1f}",
            textposition="outside",
            offsetgroup=0,
            orientation='h',
            showlegend=False
            ),
        row=2, col=3
    )

    fig.add_trace(
        go.Bar(
            name='Bug',
            x=blocked_issues_bugs['key'],
            y=blocked_issues_bugs['status'],
            marker_color='green',
            text = blocked_issues_bugs['key'],
            texttemplate="%{text:.1f}",
            textposition="outside",
            offsetgroup=0,
            orientation='h',
            showlegend=False
            ),
        row=2, col=3
    )

fig.update_layout(
    xaxis=dict(tickmode="linear"),
    plot_bgcolor="rgba(0,0,0,0)",
    yaxis=(dict(showgrid=False)),
    legend=dict(
        x=0.6,
        yanchor="bottom",
        xanchor="left",
        y=0.3
    )
)

fig.show()