from openpyxl import Workbook
from database import get_total_rekap

def generate_excel(filename):
    wb = Workbook()
    ws = wb.active
    ws.title = "Ranking Total"

    ws.append(["Username", "Total Poin"])

    data = get_total_rekap()
    for row in data:
        ws.append(row)

    wb.save(filename)
