import random
from openpyxl import Workbook

def do_distribution(participants):
    ids = [p[1] for p in participants]
    shuffled = ids.copy()

    while True:
        random.shuffle(shuffled)
        if all(a != b for a, b in zip(ids, shuffled)):
            break

    return dict(zip(ids, shuffled))

def export_to_excel(participants, filename):
    wb = Workbook()
    ws = wb.active
    ws.append(["Username", "Full name", "Wishes"])

    for _, _, username, full_name, wishes in participants:
        ws.append([username, full_name, wishes])

    wb.save(filename)
