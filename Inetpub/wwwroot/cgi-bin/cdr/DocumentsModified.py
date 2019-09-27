#----------------------------------------------------------------------
# "We need a simple 'Documents Modified' Report to be generated in an Excel
# spreadsheet, which verifies what documents were changed within a given time
# frame."
#
# JIRA::OCECDR-3800
#----------------------------------------------------------------------
import cgi
import cdr
import cdrcgi
from cdrapi import db
import re
import time
import sys

#----------------------------------------------------------------------
# Set the form variables.
#----------------------------------------------------------------------
fields     = cgi.FieldStorage()
doc_type   = fields.getvalue("doctype") or "0"
start_date = fields.getvalue("startdate")
end_date   = fields.getvalue("enddate")
session    = cdrcgi.getSession(fields)
request    = cdrcgi.getRequest(fields)
title      = "Documents Modified Report"
script     = "DocumentsModified.py"
SUBMENU    = "Report Menu"
buttons    = ("Submit Request", SUBMENU, cdrcgi.MAINMENU, "Log Out")

#----------------------------------------------------------------------
# Handle navigation requests.
#----------------------------------------------------------------------
if request == cdrcgi.MAINMENU:
    cdrcgi.navigateTo("Admin.py", session)
elif request == SUBMENU:
    cdrcgi.navigateTo("reports.py", session)

#----------------------------------------------------------------------
# Handle request to log out.
#----------------------------------------------------------------------
if request == "Log Out":
    cdrcgi.logout(session)

#----------------------------------------------------------------------
# Connect to the database.
#----------------------------------------------------------------------
try:
    conn = db.connect(user="CdrGuest")
    cursor = conn.cursor()
except:
    cdrcgi.bail("Unable to connect to the CDR database")

#----------------------------------------------------------------------
# Build a picklist for document types.
#----------------------------------------------------------------------
def get_doctypes():
    try:
        cursor.execute("""\
  SELECT id, name
    FROM doc_type
   WHERE xml_schema IS NOT NULL
     AND active = 'Y'
ORDER BY name""")
        return [[0, "All Types"]] + [tuple(row) for row in cursor.fetchall()]
    except:
        cdrcgi.bail("Failure building document type picklist")

#----------------------------------------------------------------------
# If we don't have the required parameters, ask for them.
#----------------------------------------------------------------------
if not cdrcgi.is_date(start_date) or not cdrcgi.is_date(end_date):
    page = cdrcgi.Page(title, subtitle=title, action=script, buttons=buttons,
                       session=session)
    page.add("<fieldset>")
    page.add(page.B.LEGEND("Report Parameters"))
    page.add_select("doctype", "Doc Type", get_doctypes())
    page.add_date_field("startdate", "Start Date")
    page.add_date_field("enddate", "End Date")
    page.add("</fieldset>")
    page.send()

#----------------------------------------------------------------------
# Create the report.
#----------------------------------------------------------------------
try:
    doc_type = int(doc_type)
except:
    cdrcgi.bail()
where = doc_type and ("AND doc_type = %d" % doc_type) or ""
cursor.execute("CREATE TABLE #t (id INTEGER, ver INTEGER)")
conn.commit()
cursor.execute("""\
INSERT INTO #t
     SELECT id, MAX(num)
       FROM doc_version
      WHERE dt BETWEEN ? AND ?
        %s
   GROUP BY id""" % where, (start_date, "%s 23:59:59" % end_date))
conn.commit()
cursor.execute("""\
SELECT t.id, v.title, t.ver, v.publishable
      FROM #t t
      JOIN doc_version v
        ON v.id = t.id
       AND v.num = t.ver
  ORDER BY t.id""")
rows = []
for doc_id, doc_title, doc_version, publishable in cursor.fetchall():
    rows.append([
        cdrcgi.Report.Cell(doc_id, center=True),
        cdrcgi.Report.Cell(doc_title),
        cdrcgi.Report.Cell(doc_version, center=True),
        cdrcgi.Report.Cell(publishable, center=True),
    ])
columns = (
    cdrcgi.Report.Column("Doc ID", width="70px"),
    cdrcgi.Report.Column("Doc Title", width="700px"),
    cdrcgi.Report.Column("Last Version", width="100px"),
    cdrcgi.Report.Column("Publishable", width="100px"),
)
table = cdrcgi.Report.Table(columns, rows, sheet_name="Modified Documents")
report = cdrcgi.Report(title, [table])
report.send("excel")
