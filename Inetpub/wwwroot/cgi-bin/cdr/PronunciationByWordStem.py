#----------------------------------------------------------------------
# "The Glossary Terms by Status Report will list terms and their
# pronunciations by the user requesting a specific word stem from
# the Glossary Term name or Term Pronunciation." (request 2643)
#
# BZIssue::2643
#----------------------------------------------------------------------
import cgi, cdr, cdrcgi, string, time, xml.dom.minidom, xml.sax.saxutils
from cdrapi import db
from html import escape as html_escape
from operator import attrgetter

#----------------------------------------------------------------------
# Set the form variables.
#----------------------------------------------------------------------
fields   = cgi.FieldStorage()
name     = fields and fields.getvalue("name") or None
pron     = fields and fields.getvalue("pron") or None
session  = cdrcgi.getSession(fields)
request  = cdrcgi.getRequest(fields)
title    = "CDR Administration"
instr    = "Pronunciation by Term Stem Report"
buttons  = ["Submit Request", "Report Menu", cdrcgi.MAINMENU, "Log Out"]
script   = "PronunciationByWordStem.py"
header   = cdrcgi.header(title, title, instr, script, buttons)

#----------------------------------------------------------------------
# Handle requests.
#----------------------------------------------------------------------
if request == cdrcgi.MAINMENU:
    cdrcgi.navigateTo("Admin.py", session)
elif request == "Report Menu":
    cdrcgi.navigateTo("Reports.py", session)
elif request == "Log Out":
    cdrcgi.logout(session)

#----------------------------------------------------------------------
# As the user for the report parameters.
#----------------------------------------------------------------------
if not (name and name.strip()) and not (pron and pron.strip()):
    form = """\
   <INPUT TYPE='hidden' NAME='%s' VALUE='%s'>
   <TABLE BORDER='0'>
    <TR>
     <TD align='right'><B>Stem of a Glossary Term Name:&nbsp;</B></TD>
     <TD><INPUT NAME='name' />
    </TR>
    <TR>
     <TD COLSPAN='2' ALIGN='CENTER'><b>Or</b></TD>
    </TR>
    <TR>
     <TD align='right'><B>Stem of a Term Pronunciation:&nbsp;</B></TD>
     <TD><INPUT NAME='pron' />
    </TR>
   </TABLE>
  </FORM>
 </BODY>
</HTML>
""" % (cdrcgi.SESSION, session)
    cdrcgi.sendPage(header + form)

#----------------------------------------------------------------------
# Escape markup special characters.
#----------------------------------------------------------------------
def fix(me):
    if not me:
        return "&nbsp;"
    return me # xml.sax.saxutils.escape(me)

#----------------------------------------------------------------------
# Prepare definitions for display.
#----------------------------------------------------------------------
def fixList(defs):
    if not defs:
        return "&nbsp;"
    return fix("; ".join(defs))

#----------------------------------------------------------------------
# Extract the complete content of an element, tags and all.
#----------------------------------------------------------------------
def getNodeContent(node, pieces = None):
    if pieces is None:
        pieces = []
    for child in node.childNodes:
        if child.nodeType in (child.TEXT_NODE, child.CDATA_SECTION_NODE):
            if child.nodeValue:
                pieces.append(xml.sax.saxutils.escape(child.nodeValue))
        elif child.nodeType == child.ELEMENT_NODE:
            if child.nodeName == 'Insertion':
                pieces.append("<span style='color: red'>")
                getNodeContent(child, pieces)
                pieces.append("</span>")
            elif child.nodeName == 'Deletion':
                pieces.append("<span style='text-decoration: line-through'>")
                getNodeContent(child, pieces)
                pieces.append("</span>")
            elif child.nodeName == 'Strong':
                pieces.append("<b>")
                getNodeContent(child, pieces)
                pieces.append("</b>")
            elif child.nodeName in ('Emphasis', 'ScientificName'):
                pieces.append("<i>")
                getNodeContent(child, pieces)
                pieces.append("</i>")
            else:
                getNodeContent(child, pieces)
    return "".join(pieces)

class Comment:
    def __init__(self, node):
        self.text = getNodeContent(node)
        self.user = node.getAttribute('user')
        self.date = node.getAttribute('date')

class GlossaryTerm:
    def __init__(self, id, node):
        self.id = id
        self.name = None
        self.pronunciation = None
        self.pronunciationResources = []
        self.comment = None
        for child in node.childNodes:
            if child.nodeName == "TermName":
                for grandchild in child.childNodes:
                    if grandchild.nodeName == 'TermNameString':
                        self.name = getNodeContent(grandchild)
                    elif grandchild.nodeName == "TermPronunciation":
                        self.pronunciation = getNodeContent(grandchild)
                    elif grandchild.nodeName == "PronunciationResource":
                        resource = getNodeContent(grandchild)
                        self.pronunciationResources.append(resource)
                    elif grandchild.nodeName == "Comment" and not self.comment:
                        self.comment = Comment(grandchild)

#----------------------------------------------------------------------
# Create/display the report.
#----------------------------------------------------------------------
conn = db.connect(user='CdrGuest')
cursor = conn.cursor()
nameVal = name and name.strip() or ""
pronVal = pron and pron.strip() or ""
if nameVal and '%' not in nameVal: nameVal = "%%%s%%" % nameVal
if pronVal and '%' not in pronVal: pronVal = "%%%s%%" % pronVal
if nameVal and pronVal:
    stems = ("Name Stem: %s<br />Pronunciation Stem: %s" %
             (html_escape(name), html_escape(pron)))
    cursor.execute("""\
SELECT DISTINCT doc_id
           FROM query_term
          WHERE path = '/GlossaryTermName/TermName/TermNameString'
            AND value LIKE ?
             OR path = '/GlossaryTermName/TermName/TermPronunciation'
            AND value LIKE ?""", (nameVal, pronVal))
else:
    val   = nameVal or pronVal
    elem  = nameVal and 'NameString' or 'Pronunciation'
    stems = "%s Stem: %s" % (elem,
                              nameVal and html_escape(name) or html_escape(pron))
    cursor.execute("""\
SELECT DISTINCT doc_id
           FROM query_term
          WHERE path = '/GlossaryTermName/TermName/Term%s'
            AND value LIKE ?""" % elem, val)
rows = cursor.fetchall()
terms = []
for row in rows:
    doc = cdr.getDoc('guest', row[0], getObject = True)
    dom = xml.dom.minidom.parseString(doc.xml)
    terms.append(GlossaryTerm(row[0], dom.documentElement))

html = ["""\
<!DOCTYPE html>
<html>
 <head>
  <title>Pronunciation by Term Stem Report</title>
  <style type 'text/css'>
   body    { font-family: Arial, Helvetica, sans-serif }
   span.t1 { font-size: 14pt; font-weight: bold }
   span.t2 { font-size: 12pt; font-weight: bold }
   th      { font-size: 10pt; font-weight: bold }
   td      { font-size: 10pt; font-weight: normal }
   @page   { margin-left: 0cm; margin-right: 0cm; }
   body, table   { margin-left: 0cm; margin-right: 0cm; }
  </style>
 </head>
 <body>
  <center>
   <span class='t1'>Pronunciation by Term Stem Report</span>
   <br />
   <br />
   <span class='t2'>%s</span>
   <br />
   <br />
  </center>
  <table border='1' cellspacing='0' cellpadding='2' width='100%%'>
   <tr>
    <th>Doc ID</th>
    <th>Term Name</th>
    <th>Pronunciation</th>
    <th>Pronunciation Resource</th>
    <th>Comments</th>
   </tr>
""" % stems]
for term in sorted(terms, key=attrgetter("name")):
    comment = "&nbsp;"
    if term.comment:
        user = date = ""
        if term.comment.user:
            user = "[user=%s] " % term.comment.user
        if term.comment.date:
            date = "[date=%s] " % term.comment.date
        comment = user + date + fix(term.comment.text)
    html.append("""\
   <tr>
    <td>%d</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
   </tr>
""" % (term.id,
       fix(term.name),
       fix(term.pronunciation),
       fixList(term.pronunciationResources),
       comment))
html.append("""\
  </table>
 </body>
</html>
""")
cdrcgi.sendPage("".join(html))
