from datetime import datetime, timedelta
from dateutil import parser

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
    for issue_type in data:
        for status in data[issue_type]:
            if len(data[issue_type][status]) == 0:
                data[issue_type][status] = 0
                continue
            data[issue_type][status] = round((sum(data[issue_type][status]) / len(data[issue_type][status])), 1)
    return data

def date2human(datestr):
    return parser.parse(datestr).strftime("%d/%m/%Y")