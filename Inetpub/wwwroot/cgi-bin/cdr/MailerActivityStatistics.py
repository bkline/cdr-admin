#----------------------------------------------------------------------
# Generates report of counts of mailers of each type, generated during
# a specified date range.
#----------------------------------------------------------------------
import cdr, cdrcgi, cgi
import datetime
from cdrapi import db

#----------------------------------------------------------------------
# Set the form variables.
#----------------------------------------------------------------------
fields    = cgi.FieldStorage()
session   = cdrcgi.getSession(fields)
request   = cdrcgi.getRequest(fields)
fromDate  = fields and fields.getvalue('FromDate') or None
toDate    = fields and fields.getvalue('ToDate')   or None
SUBMENU   = "Report Menu"
buttons   = ["Submit Request", SUBMENU, cdrcgi.MAINMENU, "Log Out"]
script    = "MailerActivityStatistics.py"
title     = "CDR Administration"
section   = "Mailer Activity Statistics"
header    = cdrcgi.header(title, title, section, script, buttons)
today     = datetime.date.today()

#----------------------------------------------------------------------
# Make sure we're logged in.
#----------------------------------------------------------------------
if not session: cdrcgi.bail('Unknown or expired CDR session.')

#----------------------------------------------------------------------
# Handle navigation requests.
#----------------------------------------------------------------------
if request == cdrcgi.MAINMENU:
    cdrcgi.navigateTo("Admin.py", session)
elif request == SUBMENU:
    cdrcgi.navigateTo("Reports.py", session)

#----------------------------------------------------------------------
# Handle request to log out.
#----------------------------------------------------------------------
if request == "Log Out":
    cdrcgi.logout(session)

#----------------------------------------------------------------------
# If we don't have a request, put up the request form.
#----------------------------------------------------------------------
if not fromDate or not toDate:
    toDate      = str(today)
    fromDate    = str(today - datetime.timedelta(7))
    form = """\
   <INPUT TYPE='hidden' NAME='%s' VALUE='%s'>
   <TABLE BORDER='0'>
    <TR>
     <TD><B>Start Date:&nbsp;</B></TD>
     <TD><INPUT NAME='FromDate' VALUE='%s'>&nbsp;
         (use format YYYY-MM-DD for dates, e.g. 2002-01-01)</TD>
    </TR>
    <TR>
     <TD><B>End Date:&nbsp;</B></TD>
     <TD><INPUT NAME='ToDate' VALUE='%s'>&nbsp;</TD>
    </TR>
   </TABLE>
  </FORM>
 </BODY>
</HTML>
""" % (cdrcgi.SESSION, session, fromDate, toDate)
    cdrcgi.sendPage(header + form)

#----------------------------------------------------------------------
# Validate input dates
#----------------------------------------------------------------------
if not cdr.strptime(fromDate, '%Y-%m-%d'):
    cdrcgi.bail('Start Date must be valid date in YYYY-MM-DD format')
if not cdr.strptime(toDate, '%Y-%m-%d'):
    cdrcgi.bail('End Date must be valid date in YYYY-MM-DD format')
if fromDate > toDate:
    cdrcgi.bail('Start Date is greater than End Date')

#----------------------------------------------------------------------
# Connect to the database.
#----------------------------------------------------------------------
try:
    conn   = db.connect()
    cursor = conn.cursor()
except Exception as e:
    cdrcgi.bail('Database connection failure: %s' % e)

#----------------------------------------------------------------------
# We have a request; do it.
#----------------------------------------------------------------------
html = """\
<!DOCTYPE HTML PUBLIC '-//IETF//DTD HTML//EN'>
<html>
 <head>
  <title>Mailer Statistics Report %s</title>
  <basefont face='Arial, Helvetica, sans-serif'>
 </head>
 <body>
  <center>
   <b>
    <font size='4'>Mailer Statistics Report</font>
   </b>
   <br />
   <b>
    <font size='4'>From %s to %s</font>
   </b>
  </center>
  <br />
  <br />
""" % (today, fromDate, toDate)

#----------------------------------------------------------------------
# Extract the information from the database.
#----------------------------------------------------------------------
try:
    cursor.execute("""\
            SELECT t.value,
                   COUNT(*)
              FROM query_term t
              JOIN query_term s
                ON s.doc_id = t.doc_id
             WHERE s.value BETWEEN ? AND ?
               AND t.path = '/Mailer/Type'
               AND s.path = '/Mailer/Sent'
          GROUP BY t.value""", (fromDate, toDate + " 23:59:59"))
    lastGroup  = None
    groupTotal = 0
    grandTotal = 0
    row        = cursor.fetchone()
    if not row:
        cdrcgi.sendPage(html + """\
  <b>
   <font size='3'>No mailers were sent during this period.</font>
  </b>
 </body>
</html>
""")
    while row:
        mailerType, count = row
        group = mailerType.split("-")[0]
        if group != lastGroup:
            if not groupTotal:
                html += """\
  <table border='1' cellspacing='0' cellpadding='2' width='100%%'>
   <tr>
    <td nowrap='1'>
     <b>
      <font size='3'>Type of Mailer</font>
     </b>
    </td>
    <td nowrap='1'>
     <b>
      <font size='3'>Mailer Count</font>
     </b>
    </td>
   </tr>
"""
            else:
                html += """\
   <tr>
    <td>
     <b>
      <font size='3'>%s Mailer Total</font>
     </b>
    </td>
    <td align='right'>
     <font size='3'>%d</font>
    </td>
   </tr>
   <tr>
    <td colspan='2'>&nbsp;</td>
   </tr>
""" % (lastGroup, groupTotal)
            groupTotal = 0
            lastGroup  = group
        html += """\
   <tr>
    <td>
     <font size='3'>%s</font>
    </td>
    <td align='right'>
     <font size='3'>%d</font>
    </td>
   </tr>
""" % (mailerType, count)
        groupTotal += count
        grandTotal += count
        row = cursor.fetchone()
except Exception as e:
    cdrcgi.bail('Failure executing query: %s' % e)

if groupTotal:
    html += """\
   <tr>
    <td>
     <b>
      <font size='3'>%s Mailer Total</font>
     </b>
    </td>
    <td align='right'>
     <font size='3'>%d</font>
    </td>
   </tr>
   <tr>
    <td colspan='2'>&nbsp;</td>
   </tr>
""" % (lastGroup, groupTotal)

cdrcgi.sendPage(html + """\
   <tr>
    <td nowrap='1'>
     <b>
      <font size='3'>TOTAL MAILERS</font>
     </b>
    </td>
    <td align='right'>
     <font size='3'>%d</font>
    </td>
   </tr>
  </table>
 </body>
</html>
""" % grandTotal)
