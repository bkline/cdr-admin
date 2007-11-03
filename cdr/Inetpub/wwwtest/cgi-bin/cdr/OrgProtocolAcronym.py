#----------------------------------------------------------------------
#
# $Id: OrgProtocolAcronym.py,v 1.3 2007-11-03 14:15:07 bkline Exp $
#
# Creates a report listing Organizations and Protocol Acronym IDs
# sorted by either the Org or the Acronym.
#
# $Log: not supported by cvs2svn $
# Revision 1.2  2004/11/03 20:12:20  venglisc
# Corrected title and added the sort to the title (Bug 1378).
#
# Revision 1.1  2004/10/28 20:20:00  venglisc
# Initial version of Org with Protocol Acronym Report.
#
#----------------------------------------------------------------------
import cdrdb, cdrcgi, cgi, time, string

#----------------------------------------------------------------------
# Set the form variables.
#----------------------------------------------------------------------
fields     = cgi.FieldStorage()
session    = cdrcgi.getSession(fields)
request    = cdrcgi.getRequest(fields)
sortField  = fields and fields.getvalue('SortField') or None
SUBMENU   = "Report Menu"
buttons   = ["Submit Request", SUBMENU, cdrcgi.MAINMENU, "Log Out"]
script    = "OrgProtocolAcronym.py"
title     = "CDR Administration"
section   = "Organizations Protocol Acronym Report"
now       = time.localtime(time.time())

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
# Connect to the database.
#----------------------------------------------------------------------
try:
    conn   = cdrdb.connect()
    cursor = conn.cursor()
except cdrdb.Error, info:
    cdrcgi.bail('Database connection failure: %s' % info[1][0])

#----------------------------------------------------------------------
# If we don't have a request, put up the request form.
#----------------------------------------------------------------------
if not sortField:
    header = cdrcgi.header(title, title, section, script, buttons)
    form   = u"""\
    <INPUT TYPE='hidden' NAME='%s' VALUE='%s'>
    <H3>Organizations with Protocol Acronym Report</H3>
    <TABLE>
     <TR>
      <TD>&nbsp;&nbsp;&nbsp;&nbsp;</TD>
      <TD><INPUT TYPE='radio' NAME='SortField' VALUE='2' CHECKED>
       <B>Sort Output by Organization</B>
      </TD>
     </TR>
     <TR>
      <TD>&nbsp;&nbsp;&nbsp;&nbsp;</TD>
      <TD><INPUT TYPE='radio' NAME='SortField' VALUE='3'>
       <B>Sort Output by Acronym</B>
      </TD>
     </TR>
    </TABLE>
  </FORM>
 </BODY>
</HTML>
""" % (cdrcgi.SESSION, session)
    cdrcgi.sendPage(header + form)

#----------------------------------------------------------------------
# We have a request; do what needs to be done.
#----------------------------------------------------------------------
if sortField:
   sortString = ['Organization', 'Acronym']
      
   html = u"""\
<!DOCTYPE HTML PUBLIC '-//IETF//DTD HTML//EN'>
<html>
 <head>
  <title>Organizations with Protocol Acronym Report (by %s) - %s</title>
  <basefont face='Arial, Helvetica, sans-serif'>
 </head>
 <body>
   <CENTER>
      <H2>Organizations with Protocol Acronym Report - sorted by %s</BR>
          Date: %s</H2>
   </CENTER>
  <p/>
""" % (sortString[string.atoi(sortField) - 2], time.strftime("%Y-%m-%d", now), 
       sortString[string.atoi(sortField) - 2], time.strftime("%Y-%m-%d", now))

   #----------------------------------------------------------------------
   # Extract the group's names from the database.
   #----------------------------------------------------------------------
   try:
      cursor.execute("""\
            SELECT d.id, d.title, acr.value
              FROM document d
	      JOIN query_term acr
	        ON d.id = acr.doc_id
             WHERE path = '/Organization/ProtocolIDAcronym'
              ORDER by %d""" % string.atoi(sortField))
      rows = cursor.fetchall()
      if not rows:
          cdrcgi.bail("Query returned no values")
   except cdrdb.Error, info:
      cdrcgi.bail('Failure fetching organizations: %s' % info[1][0])

   #----------------------------------------------------------------------
   # Put together the body of the report.
   #----------------------------------------------------------------------
   html += u"""\
  <table border='1' width='100%' cellspacing='0' cellpadding='5'>
   <tr>
    <td align='center' valign='top'>
     <b>CDR ID </b>
    </td>
    <td align='center' valign='bottom' valign='top'>
     <b>Organization Title</b>
    </td>
    <td valign='bottom' valign='top'>
     <b>Acronym</b>
    </td>
   </tr>
"""

   # ---------------------------------------------------------------------
   # Put the output in rows in a table
   # ---------------------------------------------------------------------
   for row in rows:
      html += u"""\
   <tr>
    <td align = 'right' valign='top'>%s</td>
    <td>%s</td>
    <td valign='top'>%s</td>
   </tr>
""" % (row[0], row[1], row[2])

   html += u"""\
  </table>
 </body>
</html>
"""
   cdrcgi.sendPage(html)
