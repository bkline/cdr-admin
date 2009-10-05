#----------------------------------------------------------------------
#
# $Id: EditCSS.py,v 1.4 2002-07-30 13:08:56 bkline Exp $
#
# Prototype for editing CSS stylesheets.
#
# $Log: not supported by cvs2svn $
# Revision 1.3  2002/02/21 15:22:02  bkline
# Added navigation buttons.
#
# Revision 1.2  2001/12/01 17:58:02  bkline
# Added support for version and checkin parameters of repDoc().
#
# Revision 1.1  2001/06/13 22:28:28  bkline
# Initial revision
#
#----------------------------------------------------------------------

#----------------------------------------------------------------------
# Import required modules.
#----------------------------------------------------------------------
import cgi, cdr, re, cdrcgi, sys

#----------------------------------------------------------------------
# Set some initial values.
#----------------------------------------------------------------------
banner   = "CDR CSS Stylesheet Editing"
title    = "Edit CSS Stylesheet"
cdrDoc   = """\
<CdrDoc Type='css' %s%s>
 <CdrDocCtl>
  <DocTitle>%s</DocTitle>
 </CdrDocCtl>
 <CdrDocXml><![CDATA[<]]></CdrDocXml>
</CdrDoc>
"""

#----------------------------------------------------------------------
# Load the fields from the form.
#----------------------------------------------------------------------
fields  = cgi.FieldStorage()
if not fields: cdrcgi.bail("Unable to read form fields", banner)
session = cdrcgi.getSession(fields)
request = cdrcgi.getRequest(fields)
docId   = fields.getvalue("DocId")    or None
css     = fields.getvalue("Css")      or None
name    = fields.getvalue("FileName") or None
version = fields.getvalue("Version")  or None
checkin = fields.getvalue("Checkin")  or None
SUBMENU = "CSS Menu"
if not session: cdrcgi.bail("Unable to log into CDR Server", banner)
if not request: cdrcgi.bail("No request submitted", banner)

#----------------------------------------------------------------------
# Handle navigation requests.
#----------------------------------------------------------------------
if request == cdrcgi.MAINMENU:
    cdrcgi.navigateTo("Admin.py", session)
elif request == SUBMENU:
    cdrcgi.navigateTo("EditCSSs.py", session)

#----------------------------------------------------------------------
# Display the CDR document form.
#----------------------------------------------------------------------
def showForm(fileName, css, docId, subBanner, buttons):
    css = css.replace('\r', '')
    hdr = cdrcgi.header(title, banner, subBanner, "EditCSS.py", buttons)
    html = hdr + ("<TABLE><TR><TD ALIGN='right'><B>Filename: </B></TD>"
                  "<TD><INPUT NAME='FileName' VALUE='%s'>"
                  "&nbsp;&nbsp;<INPUT TYPE='checkbox' NAME='Version'>"
                  "Create new version when saving"
                  "&nbsp;&nbsp;<INPUT Type='checkbox' NAME='Checkin'>"
                  "Check in when saving</TD></TR>"
                  "<TR><TD ALIGN='right' VALIGN='top'><B>Stylesheet: </B></TD>"
                  "<TD><TEXTAREA NAME='Css' ROWS='20' COLS='80'>%s"
                  "</TEXTAREA></TD></TR></TABLE>"
                  "<INPUT TYPE='hidden' NAME='%s' VALUE='%s'>"
                  "<INPUT TYPE='hidden' NAME='DocId' VALUE='%s'>"
                  "</FORM></CENTER></BODY></HTML>"
                  % (fileName, css, cdrcgi.SESSION, session, docId))
    cdrcgi.sendPage(html)

#----------------------------------------------------------------------
# Retrieve css document and extract the title and stylesheet.
#----------------------------------------------------------------------
def fetch(id):
    doc = cdr.getDoc(session, id, 'Y', getObject = 1)
    if type(doc) == type(""): cdrcgi.bail(doc, banner)
    return doc

#----------------------------------------------------------------------
# Load an existing document.
#----------------------------------------------------------------------
if request in ("Load", "Fetch"):
    if not docId:
        cdrcgi.bail("No document ID specified", banner)
    doc = fetch(docId)
    showForm(doc.ctrl['DocTitle'], 
             doc.blob, 
             doc.id, 
             "Editing existing document", 
            ("New", "Save", "Clone", SUBMENU, cdrcgi.MAINMENU))

#----------------------------------------------------------------------
# Create a template for a new document.
#----------------------------------------------------------------------
elif request == 'New':
    showForm("", "", "", "Editing new document", 
            ("Save", SUBMENU, cdrcgi.MAINMENU))

#--------------------------------------------------------------------
# Create a new document using the existing data.
#----------------------------------------------------------------------
elif request == 'Clone':
    if not css:
        cdrcgi.bail("No document to clone")
    showForm('', css, '', "Editing new document", 
            ("New", "Save", SUBMENU, cdrcgi.MAINMENU))

#--------------------------------------------------------------------
# Save the changes to the current document.
#----------------------------------------------------------------------
elif request == 'Save':
    if not css:
        cdrcgi.bail("No document to save")
    if not name:
        cdrcgi.bail("Missing required CSS filename")
    doc = cdr.Doc('<FileName>%s</FileName>' % name, 'css',
            { 'DocTitle': name }, css, docId or None)
    cmd = docId and cdr.repDoc or cdr.addDoc
    docId = cmd(session, doc = doc, ver = version and 'Y' or 'N',
                checkIn = checkin and 'Y' or 'N')
    if docId.find("<Errors>") >= 0:
        err = cdr.checkErr(docId)
        if err: cdrcgi.bail(err, banner)
        else: cdrcgi.bail("Unparseable error return: %s" % docId, banner)
    if checkin:
        cdrcgi.navigateTo('EditCSSs.py', session)
    doc = fetch(docId)
    showForm(doc.ctrl['DocTitle'], 
             doc.blob, 
             doc.id, 
             "Editing existing document", 
            ("New", "Save", "Clone", SUBMENU, cdrcgi.MAINMENU))

#----------------------------------------------------------------------
# Tell the user we don't know how to do what he asked.
#----------------------------------------------------------------------
else: cdrcgi.bail("Request not yet implemented: " + request, banner)