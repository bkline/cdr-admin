#----------------------------------------------------------------------
#
# $Id: SummaryMetaData.py,v 1.1 2003-11-10 18:14:24 bkline Exp $
#
# Report on the metadata for one or more summaries.
#
# $Log: not supported by cvs2svn $
#----------------------------------------------------------------------
import cdr, cgi, cdrcgi, cdrdb, re

#----------------------------------------------------------------------
# Get the parameters from the request.
#----------------------------------------------------------------------
fields   = cgi.FieldStorage()
session  = cdrcgi.getSession(fields)
request  = cdrcgi.getRequest(fields)
docId    = fields and fields.getvalue('id')       or None #"62864"
docTitle = fields and fields.getvalue('title')    or None
board    = fields and fields.getvalue('board')    or None
audience = fields and fields.getvalue('audience') or None
language = fields and fields.getvalue('language') or None
trimPat  = re.compile("[\s;]+$")
SUBMENU  = "Report Menu"
buttons  = ["Submit Request", SUBMENU, cdrcgi.MAINMENU, "Log Out"]
script   = "SummaryMetaData.py"
title    = "CDR Administration"
section  = "Summary Metadata Report"
header   = cdrcgi.header(title, title, section, script, buttons)
rptHead  = """\
 <head>
  <title>Summary Metadata Report</title>
  <style type='text/css'>
   body { font-family: Arial }
  </style>
 </head>"""

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
# Returns a copy of a doc title without trailing whitespace or semicolons.
#----------------------------------------------------------------------
def trim(s):
    return trimPat.sub("", s)

#----------------------------------------------------------------------
# Prepare the picklist for summary audiences.
#----------------------------------------------------------------------
def getAudiences():
    picklist = "<select name='audience'><option selected></option>"
    try:
        cursor.execute("""\
SELECT DISTINCT value
           FROM query_term
          WHERE path = '/Summary/SummaryMetaData/SummaryAudience'
       ORDER BY value""")
        for row in cursor.fetchall():
            if row[0]:
                picklist += "<option>%s</option>" % row[0]
    except cdrdb.Error, info:
        cdrcgi.bail('Database query failure: %s' % info[1][0])
    return picklist + "</select>"

#----------------------------------------------------------------------
# Prepare the picklist for summary boards.
#----------------------------------------------------------------------
def getBoards():
    picklist = "<select name='board'><option selected></option>"
    try:
        cursor.execute("""\
SELECT DISTINCT board.id, board.title
           FROM document board
           JOIN query_term org_type
             ON org_type.doc_id = board.id
          WHERE org_type.path = '/Organization/OrganizationType'
            AND org_type.value IN ('PDQ Editorial Board',
                                   'PDQ Advisory Board')
       ORDER BY board.title""")
        for row in cursor.fetchall():
            semi = row[1].find(';')
            if semi != -1: boardTitle = trim(row[1][:semi])
            else:          boardTitle = trim(row[1])
            picklist += "<option>[CDR%010d] %s</option>" % (row[0], boardTitle)
    except cdrdb.Error, info:
        cdrcgi.bail('Database query failure: %s' % info[1][0])
    return picklist + "</select>"

#----------------------------------------------------------------------
# Prepare the picklist for summary languages.
#----------------------------------------------------------------------
def getLanguages():
    picklist = "<select name='language'><option selected></option>"
    try:
        cursor.execute("""\
   SELECT DISTINCT value
              FROM query_term
             WHERE path = '/Summary/SummaryMetaData/SummaryLanguage'
          ORDER BY value""")
        for row in cursor.fetchall():
            if row[0]:
                picklist += "<option>%s</option>" % row[0]
    except cdrdb.Error, info:
        cdrcgi.bail('Database query failure: %s' % info[1][0])
    return picklist + "</select>"

class SummarySection:
    def __init__(self, title, diagnoses, types):
        self.title     = title
        self.diagnoses = diagnoses
        self.types     = types

class Summary:
    def __init__(self, id, cursor):
        self.id       = id
        self.cursor   = cursor
        self.boards   = self.getBoards()
        self.title    = self.getTitle()
        self.language = self.getLanguage()
        self.audience = self.getAudience()
        self.topics   = self.getTopics()
        self.sections = self.getSections()

    def getBoards(self):
        boardPath = '/Summary/SummaryMetaData/PdqBoard/Board/@cdr:ref'
        namePath = ('/Organization/OrganizationNameInformation/OfficialName'
                    '/Name')
        self.cursor.execute("""\
            SELECT DISTINCT board_name.value
                       FROM query_term board_name
                       JOIN query_term summary_board
                         ON summary_board.int_val = board_name.doc_id
                      WHERE summary_board.path = '%s'
                        AND board_name.path = '%s'
                        AND summary_board.doc_id = ?""" % (boardPath,
                                                           namePath), self.id)
        boards = []
        for row in self.cursor.fetchall():
            boards.append(row[0])
        return boards

    def getTitle(self):
        self.cursor.execute("""\
            SELECT value
              FROM query_term
             WHERE path = '/Summary/SummaryTitle'
               AND doc_id = ?""", self.id)
        return self.cursor.fetchall()[0][0]

    def getLanguage(self):
        self.cursor.execute("""\
            SELECT value
              FROM query_term
             WHERE path = '/Summary/SummaryMetaData/SummaryLanguage'
               AND doc_id = ?""", self.id)
        return self.cursor.fetchall()[0][0]

    def getAudience(self):
        self.cursor.execute("""\
            SELECT value
              FROM query_term
             WHERE path = '/Summary/SummaryMetaData/SummaryAudience'
               AND doc_id = ?""", self.id)
        return self.cursor.fetchall()[0][0]

    def getTopics(self):
        mainTopicPath = '/Summary/SummaryMetaData/MainTopics/Term/@cdr:ref'
        secTopicPath = '/Summary/SummaryMetaData/SecondaryTopics/Term/@cdr:ref'
        topics = []
        for path in (mainTopicPath, secTopicPath):
            self.cursor.execute("""\
                SELECT DISTINCT topic_name.value
                           FROM query_term topic_name
                           JOIN query_term summary_topic
                             ON summary_topic.int_val = topic_name.doc_id
                          WHERE summary_topic.path = '%s'
                            AND topic_name.path = '/Term/PreferredName'
                            AND summary_topic.doc_id = ?""" % path, self.id)
            for row in self.cursor.fetchall():
                topic = row[0]
                if path == mainTopicPath:
                    topics.append(topic + " (M)")
                else:
                    topics.append(topic + " (S)")
        return topics

    def getSections(self):
        sections     = []
        titles       = {}
        diagnoses    = {}
        sectionTypes = {}
        keys         = {}
        self.cursor.execute("""\
            SELECT diag_name.value, diagnosis.node_loc
              FROM query_term diag_name
              JOIN query_term diagnosis
                ON diagnosis.int_val = diag_name.doc_id
             WHERE diagnosis.path LIKE '/Summary/%SummarySection/SectMetaData'
                                     + '/Diagnosis/@cdr:ref'
               AND diag_name.path = '/Term/PreferredName'
               AND diagnosis.doc_id = ?
          ORDER BY diagnosis.node_loc""", self.id)
        for row in self.cursor.fetchall():
            diagName  = row[0]
            key       = row[1][:-8]
            keys[key] = 1
            if diagnoses.has_key(key):
                diagnoses[key] += ("; %s" % diagName)
            else:
                diagnoses[key] = diagName
        self.cursor.execute("""\
            SELECT value, node_loc
              FROM query_term
             WHERE path LIKE '/Summary/%SummarySection/SectMetaData'
                           + '/SectionType'
               AND doc_id = ?""", self.id)
        for row in self.cursor.fetchall():
            typeName  = row[0]
            key       = row[1][:-8]
            keys[key] = 1
            if sectionTypes.has_key(key):
                sectionTypes[key] += ("; %s" % typeName)
            else:
                sectionTypes[key] = typeName
        self.cursor.execute("""\
           SELECT value, node_loc
             FROM query_term
            WHERE path LIKE '/Summary/%SummarySection/Title'
              AND doc_id = ?""", self.id)
        for row in self.cursor.fetchall():
            title     = row[0]
            key       = row[1][:-4]
            keys[key] = 1
            if titles.has_key(key):
                titles[key] += ("; %s" % title)
            else:
                titles[key] = title
        sortedKeys = keys.keys()
        sortedKeys.sort()
        for key in sortedKeys:
            sections.append(SummarySection(titles.get(
                key, "[Missing Section Title]"),
                                           diagnoses.get(key, "&nbsp;"),
                                           sectionTypes.get(key, "&nbsp;")))
        return sections

    def getHtml(self, extras):
        html = """\
  <table border='0' cellpadding='2' cellspacing='0'>
"""
        if extras:
            for board in self.boards:
                html += """\
   <tr>
    <td align='right'>
     <b>Board:&nbsp;</b>
    </td>
    <td>%s</td>
   </tr>
""" % board
            html += """\
   <tr>
    <td align='right' valign='top'>
     <b>Audience:&nbsp;</b>
    </td>
    <td>%s</td>
   </tr>
   <tr>
    <td align='right' valign='top'>
     <b>Language:&nbsp;</b>
    </td>
    <td>%s</td>
   </tr>
""" % (self.audience, self.language)
        html += """\
   <tr>
    <td align='right' valign='top'>
     <b>Summary Title:&nbsp;</b>
    </td>
    <td>%s</td>
   </tr>
   <tr>
    <td align='right' valign='top'>
     <b>Topic(s):&nbsp;</b>
    </td>
    <td>
""" % self.title
        if not self.topics:
            html += "None"
        else:
            sep = ""
            for topic in self.topics:
                html += sep + topic
                sep = "<br>"
        html += """\
    </td>
   </tr>
  </table>
  <br>
  <table border='1' cellpadding='2' cellspacing='0' width = '100%'>
   <tr>
    <th width = '50%'>Section Title</th>
    <th width = '20%'>Diagnosis</th>
    <th width = '30%'>Section Type</th>
   </tr>
"""
        for section in self.sections:
            html += """\
   <tr>
    <td valign='top'>%s</td>
    <td valign='top'>%s</td>
    <td valign='top'>%s</td>
   </tr>
""" % (section.title, section.diagnoses, section.types)
        return html + """\
  </table>
  <br><br>
"""

#----------------------------------------------------------------------
# Get a database connection.
#----------------------------------------------------------------------
conn    = cdrdb.connect('CdrGuest')
cursor  = conn.cursor()
    
#----------------------------------------------------------------------
# If we have a title string but no ID, find the matching summary.
#----------------------------------------------------------------------
if docTitle and not docId:
    try:
        cursor.execute("""\
            SELECT d.id, d.title
              FROM document d
              JOIN doc_type t
                ON t.id = d.doc_type
             WHERE t.name = 'Summary'
               AND d.title LIKE ?
          ORDER BY d.title""", '%' + docTitle + '%')
        rows = cursor.fetchall()
    except Exception, info:
        cdrcgi.bail("Database failure looking up title %s: %s" %
                    (docTitle, str(info)))
    if not rows:
        cdrcgi.bail("No summaries found containing the string %s" % docTitle)
    elif len(rows) == 1:
        docId = str(rows[0][0])
    else:
        form = """\
   <input type='hidden' name ='%s' value='%s'>
   Select Summary:&nbsp;&nbsp;
   <select name='id'>
""" % (cdrcgi.SESSION, session)
        for row in rows:
            form += """\
    <option value='%d'>%s</option>
""" % (row[0], row[1])
        cdrcgi.sendPage(header + form + """\
   </select>
  </form>
 </body>
</html>
""")
    
#----------------------------------------------------------------------
# Handle request to display report for a single summary.
#----------------------------------------------------------------------
if docId:
    digits  = re.sub('[^\d]+', '', docId)
    intId   = int(digits)
    summary = Summary(intId, cursor)
    html    = """\
<!DOCTYPE HTML PUBLIC '-//IETF//DTD HTML//EN'>
<html>
%s
 <body>
  <center>
   <h2>Summary Metadata Report</h2>
  </center>
  <br>
%s
 </body>
</html>""" % (rptHead, summary.getHtml(extras = 1))
    if fields:
        cdrcgi.sendPage(html)
    else:
        print html

#----------------------------------------------------------------------
# Handle request for all summaries for a given board, audience, language.
#----------------------------------------------------------------------
if board and audience and language:
    pattern = re.compile(r"\[CDR(\d+)\] (.*)")
    match   = pattern.match(board)
    if not match:
        cdrcgi.bail("Unable to parse board value: %s" % board)
    boardId = int(match.group(1))
    boardTitle = match.group(2)
    try:
        cursor.execute("""\
            SELECT DISTINCT b.doc_id, d.title
                       FROM query_term b
                       JOIN query_term a
                         ON a.doc_id = b.doc_id
                       JOIN document d
                         ON d.id = b.doc_id
                       JOIN query_term l
                         ON l.doc_id = a.doc_id
                      WHERE a.path = '/Summary/SummaryMetaData/SummaryAudience'
                        AND l.path = '/Summary/SummaryMetaData/SummaryLanguage'
                        AND b.path = '/Summary/SummaryMetaData/PDQBoard/Board'
                                   + '/@cdr:ref'
                        AND a.value = ?
                        AND b.int_val = ?
                        AND l.value = ?
                   ORDER BY d.title""", (audience, boardId, language))
        rows = cursor.fetchall()
    except Exception, info:
        cdrcgi.bail("Database failure fetching summary document IDs: %s"
                    % str(info))
    if not rows:
        cdrcgi.bail("No %s language %s summaries found for %s" %
                    (language, audience, boardTitle))
    html = """\
<!DOCTYPE HTML PUBLIC '-//IETF//DTD HTML//EN'>
<html>
%s
 <body>
  <center>
   <h2>Summary Metadata Report</h2>
  </center>
  <br><hr>
  <center>
  <table border='0' cellpadding='2' cellspacing='0'>
   <tr>
    <td align='right'>
     <b>Board:&nbsp;</b>
    </td>
    <td>%s</td>
   </tr>
   <tr>
    <td align='right' valign='top'>
     <b>Audience:&nbsp;</b>
    </td>
    <td>%s</td>
   </tr>
   <tr>
    <td align='right' valign='top'>
     <b>Language:&nbsp;</b>
    </td>
    <td>%s</td>
   </tr>
  </table>
  </center>
  <hr><br>
""" % (rptHead, boardTitle, audience, language)
    for row in rows:
        summary = Summary(row[0], cursor)
        html += summary.getHtml(extras = 0)
    cdrcgi.sendPage(html + """\
 </body>
</html>""")

#----------------------------------------------------------------------
# If we got here we don't have a request, so put up the request form.
#----------------------------------------------------------------------
form = """\
   <input type='hidden' name ='%s' value='%s'>
   <table border='0'>
    <tr>
     <td align='right'><b>Document ID:&nbsp;</b></td>
     <td><input name='id'></td>
    </tr>
    <tr>
     <td colspan='2' align='center'><i>... or ...</i></td>
    </tr>
    <tr>
     <td align='right'><b>Summary Title:&nbsp;</b></td>
     <td><input name='title'></td>
    </tr>
    <tr>
     <td colspan='2' align='center'><i>... or (all three required) ...</i></td>
    </tr>
    <tr>
     <td align='right'><b>Board:&nbsp;</b></td>
     <td>%s</td>
    </tr>
    <tr>
     <td align='right'><b>Audience:&nbsp;</b></td>
     <td>%s</td>
    </tr>
    <tr>
     <td align='right'><b>Language:&nbsp;</b></td>
     <td>%s</td>
    </tr>
   </table>
  </form>
 </body>
</html>
""" % (cdrcgi.SESSION, session, getBoards(), getAudiences(), getLanguages())
cdrcgi.sendPage(header + form)