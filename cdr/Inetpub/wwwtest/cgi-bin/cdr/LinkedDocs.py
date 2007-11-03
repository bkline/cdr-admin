#----------------------------------------------------------------------
#
# $Id: LinkedDocs.py,v 1.6 2007-11-03 14:15:07 bkline Exp $
#
# Reports on documents which link to a specified document.
#
# $Log: not supported by cvs2svn $
# Revision 1.5  2005/02/17 22:48:45  venglisc
# Added CDR-ID to header of report and changed display of header from
# using H4 tags to using table and CSS format (Bug 1532).
#
# Revision 1.4  2002/06/24 17:15:45  bkline
# Fixed encoding problems.
#
# Revision 1.3  2002/04/24 20:36:03  bkline
# Changed "Title" label to "DocTitle" as requested by Eileen (issue #161).
#
# Revision 1.2  2002/02/21 15:22:03  bkline
# Added navigation buttons.
#
# Revision 1.1  2002/01/22 21:36:08  bkline
# Initial revision
#
#----------------------------------------------------------------------
import cgi, cdr, cdrcgi, re, string, cdrdb, time

#----------------------------------------------------------------------
# Set the form variables.
#----------------------------------------------------------------------
fields   = cgi.FieldStorage()
docId    = fields and fields.getvalue("DocId")          or None
docTitle = fields and fields.getvalue("DocTitle")       or None
docType  = fields and fields.getvalue("DocType")        or None
ldt      = fields and fields.getvalue("LinkingDocType") or None
session  = cdrcgi.getSession(fields)
request  = cdrcgi.getRequest(fields)
title    = "Linked Documents Report"
instr    = "Report on documents which link to a specified document"
script   = "LinkedDocs.py"
SUBMENU  = 'Report Menu'
buttons  = (SUBMENU, cdrcgi.MAINMENU)

#----------------------------------------------------------------------
# Handle navigation requests.
#----------------------------------------------------------------------
if request == cdrcgi.MAINMENU:
    cdrcgi.navigateTo("Admin.py", session)
elif request == SUBMENU:
    cdrcgi.navigateTo("reports.py", session)

#----------------------------------------------------------------------
# Set up a database connection and cursor.
#----------------------------------------------------------------------
try:
    conn = cdrdb.connect("CdrGuest")
    cursor = conn.cursor()
except cdrdb.Error, info:
    cdrcgi.bail('Database connection failure: %s' % info[1][0])

#----------------------------------------------------------------------
# Extract integer for document ID.
#----------------------------------------------------------------------
def extractDocId(id):
    if id is None: return None
    if type(id) == type(9): return id
    digits = re.sub('[^\d]', '', id)
    return string.atoi(digits)

#----------------------------------------------------------------------
# Create string representing the current date.
#----------------------------------------------------------------------
def makeDate():
    now = time.time()
    return time.strftime("%B %d, %Y", time.localtime(now))

#----------------------------------------------------------------------
# Retrieve the list of document type names.
#----------------------------------------------------------------------
def getDocTypes():
    try:
        cursor.execute("""\
SELECT DISTINCT name 
           FROM doc_type 
          WHERE name IS NOT NULL and name <> '' AND active = 'Y'
       ORDER BY name
""")
        return cursor.fetchall()
    except cdrdb.Error, info:
        cdrcgi.bail('Database query failure: %s' % info[1][0])

#----------------------------------------------------------------------
# Create a picklist for document types.
#----------------------------------------------------------------------
def makeList(fieldName, docTypes):
    picklist = u"<SELECT NAME='%s'><OPTION SELECTED>Any Type</OPTION>" \
        % fieldName
    for docType in docTypes:
        picklist += u"<OPTION>%s</OPTION>" % docType[0]
    return picklist + u"</SELECT>"

#----------------------------------------------------------------------
# Get the user name and format it for display at the bottom of the page.
#----------------------------------------------------------------------
def getUser():
    if not session: return u""
    try:
        cursor.execute("""
SELECT DISTINCT u.fullname
           FROM usr u
           JOIN session s
             ON s.usr = u.id
          WHERE s.name = ?""", session)
        uName = cursor.fetchone()[0]
        if not uName: return u""
        return u"<BR><I><FONT SIZE='-1'>%s</FONT></I><BR>" % uName
    except: return u""
#----------------------------------------------------------------------
# If we have a document ID, produce a report.
#----------------------------------------------------------------------
if docId:
    docId = extractDocId(docId)
    try:
        # Get the target doc info.
        cursor.execute("""\
SELECT d.title, t.name
  FROM document d
  JOIN doc_type t
    ON t.id = d.doc_type
 WHERE d.id = ?""", docId)
        targetDocInfo = cursor.fetchone()
    except cdrdb.Error, info:
        cdrcgi.bail('Database query failure: %s' % info[1][0])

    # Get the info for the linking docs.
    ldtConstraint = ""
    if ldt and ldt != 'Any Type':
        ldtConstraint = "AND t.name = '%s'" % ldt
    query = """\
SELECT DISTINCT d.id, d.title, t.name, n.source_elem, n.target_frag
           FROM document d
           JOIN doc_type t
             ON t.id = d.doc_type
           JOIN link_net n
             ON n.source_doc = d.id
          WHERE n.target_doc = ?
            %s
       ORDER BY t.name, d.id, n.source_elem, n.target_frag""" % ldtConstraint
    try:
        cursor.execute(query, extractDocId(docId))
    except cdrdb.Error, info:
        cdrcgi.bail('Database query failure: %s' % info[1][0])

    # Build the report and show it.
    title2 = u"%s for %s Document CDR%d %s" % (title, targetDocInfo[1], 
            docId, makeDate())
    html = cdrcgi.header(title2, title, instr, script, buttons)
    report = u"""\
    <table>
     <tr>
      <td class="docLabel" align="right">Document Type:</td>
      <td class="docValue">%s</td>
     </tr>
     <tr>
      <td class="docLabel" align="right">Document Title:</td>
      <td class="docValue">%s</td>
     </tr>
     <tr>
      <td class="docLabel" align="right">Document ID:</td>
      <td class="docValue">%s</td>
     </tr>
    </table>
<BR>

<B><I>Linked Documents</I></B>
<BR>&nbsp;<BR>
""" % (targetDocInfo[1], targetDocInfo[0], docId)

    prevDocType = ""
    row = cursor.fetchone()
    while row:
        linkingDocId       = row[0]
        linkingDocTitle    = row[1]
        linkingDocType     = row[2]
        linkingElementName = row[3]
        linkingFragId      = row[4]
        if linkingDocType != prevDocType:
            if prevDocType:
                report += u"""\
  </TABLE>"""
            prevDocType = linkingDocType
            report += u"""\
  <BR><B>%s</B><BR><BR>
  <TABLE CELLSPACING='0' CELLPADDING='2' BORDER='1'>
   <TR>
    <TD><B>DocID</B></TD>
    <TD><B>DocTitle</B></TD>
    <TD><B>ElementName</B></TD>
    <TD><B>FragmentID</B></TD>
   </TR>""" % linkingDocType
        report += u"""\
   <TR>
    <TD VALIGN='top'>CDR%010d</TD>
    <TD VALIGN='top'>%s</TD>
    <TD VALIGN='top'>%s</TD>
    <TD VALIGN='top'>%s</TD>
   </TR>""" % (linkingDocId, linkingDocTitle, linkingElementName,
               linkingFragId or "&nbsp;")
        row = cursor.fetchone()
    if prevDocType:
        html += report + u"""\
  </TABLE>"""
    else:
        html += u"""\
  <H3>No Documents Currently Link to CDR%010d</H3>""" % docId
    html += u"""\
  </FORM>
  %s
 </BODY>
</HTML>""" % getUser()
    cdrcgi.sendPage(html)

#----------------------------------------------------------------------
# Search for linked document by title, if so requested.
#----------------------------------------------------------------------
if docTitle:
    header   = cdrcgi.header(title, title, instr, script, ("Submit",
                                                           SUBMENU,
                                                           cdrcgi.MAINMENU))
    docTypes = getDocTypes()
    dtConstraint = ""
    if docType and docType != 'Any Type':
        dtConstraint = "AND t.name = '%s'" % docType
    titleParam = docTitle
    if docTitle[-1] != '%':
        titleParam += '%'
    query = """\
SELECT d.id, d.title
  FROM document d
  JOIN doc_type t
    ON t.id = d.doc_type
 WHERE d.title LIKE ?
   %s""" % dtConstraint
    try:
        cursor.execute(query, titleParam)
        row = cursor.fetchone()

        # Check to make sure we got at least one row.
        if not row:
            cdrcgi.bail("No documents match '%s'" % docTitle)
        form     = u"""\
   <BR>
   <B>Linking Document Type:&nbsp;</B>
   %s
   <BR><BR>
   <TABLE CELLSPACING='4' CELLPADDING='0' BORDER='0'>""" % makeList(
        "LinkingDocType", docTypes)
        while row:
            form += u"""\
    <TR>
     <TD VALIGN='top'>
      <INPUT TYPE='radio' NAME='DocId' VALUE='%d'>
     </TD>
     <TD VALIGN='top'>CDR%010d</TD>
     <TD>%s</TD>
    </TR>""" % (row[0], row[0], row[1])
            row = cursor.fetchone()
        form += u"""\
   </TABLE>
   <INPUT TYPE='hidden' NAME='%s' VALUE='%s'>
  </FORM>
 </BODY>
</HTML>""" % (cdrcgi.SESSION, session and session or '')
    except cdrdb.Error, info:
        cdrcgi.bail('Database query failure: %s' % info[1][0])
    cdrcgi.sendPage(header + form)

#----------------------------------------------------------------------
# Put up the main request form.
#----------------------------------------------------------------------
header   = cdrcgi.header(title, title, instr, script, ("Submit",
                                                       SUBMENU,
                                                       cdrcgi.MAINMENU))
docTypes = getDocTypes()
form     = u"""\
   <H3>Report On Specific Document ID</H3>
   <TABLE CELLSPACING='1' CELLPADDING='1' BORDER='0'>
    <TR>
     <TD ALIGN='right'><B>Document ID:&nbsp;</B></TD>
     <TD><INPUT NAME='DocId'></TD>
    <TR>
     <TD ALIGN='right'><B>Linking Document Type:&nbsp;</B></TD>
     <TD>%s</TD>
    </TR>
   </TABLE>
   <HR />
   <H3>Find Document By Document Type and Title</H3>
   <TABLE CELLSPACING='1' CELLPADDING='1' BORDER='0'>
    <TR>
     <TD ALIGN='right'><B>Document Title:&nbsp;</B></TD>
     <TD><INPUT NAME='DocTitle' SIZE='70'></TD>
    </TR>
    <TR>
     <TD ALIGN='right'><B>Document Type:&nbsp;</B></TD>
     <TD>%s</TD>
    </TR>
   </TABLE>
   <INPUT TYPE='hidden' NAME='%s' VALUE='%s'
  </FORM>
 </BODY>
</HTML>
""" % (makeList("LinkingDocType", docTypes), 
       makeList("DocType", docTypes),
       cdrcgi.SESSION, session and session or '')
cdrcgi.sendPage(header + form)
