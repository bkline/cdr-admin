#----------------------------------------------------------------------
#
# $Id: UnchangedDocs.py,v 1.1 2001-12-01 18:11:44 bkline Exp $
#
# Reports on documents unchanged for a specified number of days.
#
# $Log: not supported by cvs2svn $
#----------------------------------------------------------------------
import cgi, cdr, cdrcgi, re, string, cdrdb

#----------------------------------------------------------------------
# Set the form variables.
#----------------------------------------------------------------------
fields  = cgi.FieldStorage()
days    = fields and fields.getvalue("Days")    or None
type    = fields and fields.getvalue("DocType") or None
maxRows = fields and fields.getvalue("MaxRows") or None
request = cdrcgi.getRequest(fields)

#----------------------------------------------------------------------
# Create a picklist for document types.
#----------------------------------------------------------------------
def makePicklist(docTypes):
    picklist = "<SELECT NAME='DocType'><OPTION>All</OPTION>"
    selected = " SELECTED"
    for docType in docTypes:
        picklist += "<OPTION%s>%s</OPTION>" % (selected, docType[0])
        selected = ""
    return picklist + "</SELECT>"

#----------------------------------------------------------------------
# Set up a database connection and cursor.
#----------------------------------------------------------------------
try:
    conn = cdrdb.connect()
    cursor = conn.cursor()
except cdrdb.Error, info:
    cdrcgi.bail('Database connection failure: %s' % info[1][0])

#----------------------------------------------------------------------
# Do the report if we have a request.
#----------------------------------------------------------------------
if request:
    maxRows = maxRows and int(maxRows) or 1000
    days = days and int(days) or 365
    if type and type != 'All':
        query   = """\
   SELECT TOP %d d.id AS DocId, 
          d.title AS DocTitle, 
          MAX(a.dt) AS LastChange
     FROM document d, 
          audit_trail a, 
          doc_type t
    WHERE d.id = a.document
      AND d.doc_type = t.id
      AND t.name = '%s'
 GROUP BY d.id, d.title
   HAVING DATEDIFF(day, MAX(a.dt), GETDATE()) > %d
 ORDER BY MAX(a.dt), d.id
""" % (maxRows, type, days)
    else:
        query   = """\
   SELECT TOP %d d.id AS DocId, 
          d.title AS DocTitle, 
          MAX(a.dt) AS LastChange
     FROM document d, 
          audit_trail a
    WHERE d.id = a.document
 GROUP BY d.id, d.title
   HAVING DATEDIFF(day, MAX(a.dt), GETDATE()) > %d
 ORDER BY MAX(a.dt), d.id
""" % (maxRows, days)
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    except cdrdb.Error, info:
        cdrcgi.bail('Database query failure: %s' % info[1][0])

    title   = "Documents Unchanged for %d Days" % days
    instr   = "Document type: %s" % type
    buttons = ()
    header  = cdrcgi.header(title, title, instr, "UnchangedDocs.py", buttons)
    html    = """\
<TABLE BORDER='0' WIDTH='100%%' CELLSPACING='1' CELLPADDING='1'>
 <TR BGCOLOR='silver' VALIGN='top'>
  <TD ALIGN='center'><FONT SIZE='-1'><B>Doc ID</B></FONT></TD>
  <TD ALIGN='center'><FONT SIZE='-1'><B>Title</B></FONT></TD>
  <TD ALIGN='center'><FONT SIZE='-1'><B>Last Change</B></FONT></TD>
 </TR>
"""
    for row in rows:
        title = row[1].encode('latin-1')
        shortTitle = title[:100] 
        if len(title) > 100: shortTitle += " ..."
        html += """\
 <TR>
  <TD BGCOLOR='white' VALIGN='top' ALIGN='center'><FONT SIZE='-1'>CDR%010d</FONT></TD>
  <TD BGCOLOR='white' ALIGN='left'><FONT SIZE='-1'>%s</FONT></TD>
  <TD BGCOLOR='white' VALIGN='top' ALIGN='center'><FONT SIZE='-1'>%s</FONT></TD>
 </TR>
""" % (row[0],
       shortTitle,
       row[2][:10])
    cdrcgi.sendPage(header + html + "</TABLE></BODY></HTML>")

#----------------------------------------------------------------------
# Put out the form if we don't have a request.
#----------------------------------------------------------------------
else:
    try:
        cursor.execute("""\
SELECT DISTINCT name 
           FROM doc_type 
          WHERE name IS NOT NULL and name <> ''
       ORDER BY name
""")
        docTypes = cursor.fetchall()
    except cdrdb.Error, info:
        cdrcgi.bail('Database query failure: %s' % info[1][0])
    title   = "Unchanged Documents"
    instr   = "Select Options and Submit Request"
    buttons = ("Submit Request",)
    header  = cdrcgi.header(title, title, instr, "UnchangedDocs.py", buttons)
    form    = """\
        <TABLE CELLSPACING='0' CELLPADDING='0' BORDER='0'>
        <TR>
          <TD ALIGN='right'><B>Days Since Last Change&nbsp;</B></TD>
          <TD><INPUT NAME='Days' VALUE='365'></TD>
        </TR>
        <TR>
          <TD ALIGN='right'><B>Document Type&nbsp;</B></TD>
          <TD>%s</TD>
        </TR>
        <TR>
          <TD ALIGN='right'><B>Max Rows&nbsp;</B></TD>
          <TD><INPUT NAME='MaxRows' VALUE='1000'></TD>
        </TR>
       </TABLE>
      </FORM>
     </BODY>
    </HTML>
    """ % makePicklist(docTypes)
    cdrcgi.sendPage(header + form)
