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
            "issue_type" : issue["issue_type"],
            "time_in_status" : getDateDiff(dateNow(), issue["last_status_change"])
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

status_to_display_cycle_time = 'Doing', 'Ready QA', 'Em QA', 'In Development', 'In Code Review', 'To Test', 'In Test', 'To Review'
cycle_time_plotable = df.query("status in (@status_to_display_cycle_time)").groupby(by=["issue_type", "status"]).mean("time").reset_index(level=[0,1])
cycle_time_story = cycle_time_plotable.query("issue_type == 'Story'")
cycle_time_bug = cycle_time_plotable.query("issue_type == 'Bug'")

complete_tasks_df = df.query("status in ('PO Validation', 'In Review', 'Done', 'Item Conclu\u00eddo')")
complete_tasks_keys_set = set(complete_tasks_df['key'])

status_lead_time = 'Doing', 'Ready QA', 'Em QA', 'To Review', 'In Development', 'In Code Review', 'To Test', 'In Test',
cycle_time_completed_only = df.query("status in (@status_lead_time) & key in @complete_tasks_keys_set").groupby(by=["issue_type", "status"]).mean("time").reset_index(level=[0,1])

cycle_time_complete_stories = cycle_time_completed_only.query("issue_type == 'Story'")
cycle_time_complete_bugs = cycle_time_completed_only.query("issue_type == 'Bug'")

lead_time_story = cycle_time_completed_only.query("issue_type == 'Story'")["time"].sum()
lead_time_bug = cycle_time_completed_only.query("issue_type == 'Bug'")["time"].sum()

title = "Periodo: %s - %s" % (date2human(throughput_timeframe), date2human(dateNow()))

fig = make_subplots(
    rows=3,
    cols=3,
    specs=[
        [{"type" : "indicator"}, {"type" : "indicator"}, {"type" : "indicator"}],
        [{"type": "bar", "colspan": 2}, {}, {"type" : "bar"}],
        [{"type": "bar", "colspan": 2}, {}, {}]
    ],
    subplot_titles=("", "", "", "Cycle Time ( In Progress )", "", "Tarefas Bloqueadas", "Cycle Time ( Done )", "", "Tempo no Status de Bloqueio")
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
        cliponaxis = False,
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
        cliponaxis = False,
        offsetgroup=1
        ),
    row=2, col=1
)


if len(blocked_issues):
    blocked_issues_df = pd.DataFrame(blocked_issues)
    blocked_issues_filtered = blocked_issues_df.query("status in (@status_to_display_cycle_time)").groupby(by=["issue_type", "status"]).count().reset_index(level=[0,1])

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
            showlegend=False,
            cliponaxis = False,
            width=0.1
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
            showlegend=False,
            cliponaxis = False,
            width=0.1
            ),
        row=2, col=3
    )


if not cycle_time_complete_stories.empty:
    fig.add_trace(
        go.Bar(
            name="Story",
            x=cycle_time_complete_stories['status'],
            y=cycle_time_complete_stories['time'],
            marker_color='green',
            text = cycle_time_complete_stories['time'],
            texttemplate="%{text:.1f}",
            textposition="outside",
            showlegend=False,
            cliponaxis = False,
            offsetgroup=0
            ),
        row=3, col=1
    )

if not cycle_time_complete_bugs.empty:
    fig.add_trace(
        go.Bar(
            name="Bug",
            x=cycle_time_complete_bugs['status'],
            y=cycle_time_complete_bugs['time'],
            marker_color='crimson',
            text = cycle_time_complete_bugs['time'],
            texttemplate="%{text:.1f}",
            textposition="outside",
            cliponaxis = False,
            showlegend=False,
            offsetgroup=1
            ),
        row=3, col=1
    )


fig.add_trace(
    go.Bar(
        name='Story',
        x=blocked_issues_df['key'],
        y=blocked_issues_df['time_in_status'],
        marker_color='green',
        text = blocked_issues_df['time_in_status'],
        texttemplate="%{text:.1f}",
        textposition="outside",
        offsetgroup=0,
        showlegend=False,
        cliponaxis = False
    ),
    row=3, col=3
)

fig.update_layout(
    # xaxis=dict(tickmode="linear"),
    paper_bgcolor="rgba(244, 241, 222, 1)",
    # plot_bgcolor="rgba(206, 212, 218, 1)",
    # yaxis=(dict(showgrid=False)),
    legend=dict(
        x=0,
        y=0.62,
        yanchor="bottom",
        xanchor="left"
    ),
    title=title,
    template="ggplot2"
)

fig.show()