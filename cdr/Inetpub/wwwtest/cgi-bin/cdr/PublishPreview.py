#----------------------------------------------------------------------
#
# $Id: PublishPreview.py,v 1.21 2003-11-25 12:47:41 bkline Exp $
#
# Transform a CDR document using an XSL/T filter and send it back to 
# the browser.
#
# $Log: not supported by cvs2svn $
# Revision 1.20  2003/08/25 20:31:44  bkline
# Eliminated obsolete lists of filters (replaced by named filter sets).
#
# Revision 1.19  2002/11/15 18:36:23  bkline
# Fixed typo (InScopePrototocol).
#
# Revision 1.18  2002/11/13 20:33:37  bkline
# Plugged in filter sets.
#
# Revision 1.17  2002/11/05 14:00:29  bkline
# Updated filter lists from publication control document.
#
# Revision 1.16  2002/10/31 02:06:06  bkline
# Changed www.cancer.gov to stage.cancer.gov for css url.
#
# Revision 1.15  2002/10/28 13:59:11  bkline
# Added hook to debuglevel.  Added link to Cancer.gov stylesheet.
#
# Revision 1.14  2002/10/24 15:38:08  bkline
# Implemented change request from issue #478 to use last publishable
# version instead of current working version.
#
# Revision 1.13  2002/10/22 17:47:05  bkline
# Added, then commented out, the debugging flag for cdr2cg.
#
# Revision 1.12  2002/08/29 12:32:08  bkline
# Hooked up with Cancer.gov.
#
# Revision 1.11  2002/05/30 17:06:41  bkline
# Corrected CVS log comment for previous version.
#
# Revision 1.10  2002/05/30 17:01:06  bkline
# New protocol filters from Cheryl.
#
# Revision 1.9  2002/05/08 17:41:53  bkline
# Updated to reflect Volker's new filter names.
#
# Revision 1.8  2002/04/18 21:46:59  bkline
# Plugged in some additional filters from Cheryl.
#
# Revision 1.7  2002/04/12 19:57:20  bkline
# Installed new filters.
#
# Revision 1.6  2002/04/11 19:41:48  bkline
# Plugged in some new filters.
#
# Revision 1.5  2002/04/11 14:07:49  bkline
# Added denormalization filter for Organization documents.
#
# Revision 1.4  2002/04/10 20:08:45  bkline
# Added denormalizing filter for Person display.
#
# Revision 1.3  2002/01/22 21:31:41  bkline
# Added filter for Protocols.
#
# Revision 1.2  2001/12/24 23:18:15  bkline
# Replaced document IDs with filter names.
#
# Revision 1.1  2001/12/01 18:11:44  bkline
# Initial revision
#
#----------------------------------------------------------------------
import cgi, cdr, cdrcgi, cdrdb, re, cdr2cg, sys

#----------------------------------------------------------------------
# Get the parameters from the request.
#----------------------------------------------------------------------
title   = "CDR Publish Preview"
fields  = cgi.FieldStorage() or None

if not fields:
    session = 'guest'
    docId   = sys.argv[1]
    dbgLog  = len(sys.argv) > 2 and sys.argv[2] or None
    flavor  = len(sys.argv) > 3 and sys.argv[3] or None
else:
    session = cdrcgi.getSession(fields) or cdrcgi.bail("Not logged in")
    docId   = fields.getvalue(cdrcgi.DOCID) or cdrcgi.bail("No Document",
                                                           title)
    flavor  = fields.getvalue("Flavor") or None
    dbgLog  = fields.getvalue("DebugLog") or None

#----------------------------------------------------------------------
# Map for finding the filters for a given document type.
#----------------------------------------------------------------------
filterSets = {
    'Summary'        : ['set:Vendor Summary Set'],
    'InScopeProtocol': ['set:Vendor InScopeProtocol Set']
}

#----------------------------------------------------------------------
# Set up a database connection and cursor.
#----------------------------------------------------------------------
try:
    conn = cdrdb.connect('CdrGuest')
    cursor = conn.cursor()
except cdrdb.Error, info:
    cdrcgi.bail('Database connection failure: %s' % info[1][0])

#----------------------------------------------------------------------
# Determine the document type and version.
#----------------------------------------------------------------------
try:
    digits = re.sub('[^\d]+', '', docId)
    intId  = int(digits)
    cursor.execute("""\
        SELECT doc_type.name, MAX(doc_version.num)
          FROM doc_type
          JOIN document
            ON document.doc_type = doc_type.id
          JOIN doc_version
            ON doc_version.id = document.id
         WHERE document.id = ?
           AND doc_version.publishable = 'Y'
      GROUP BY doc_type.name""", (intId,))

    row = cursor.fetchone()
    if not row:
        cdrcgi.bail("Unable to find document type for %s" % docId)
    docType, docVer = row
except cdrdb.Error, info:    
        cdrcgi.bail('Unable to find document type for %s: %s' % (docId, 
                                                                 info[1][0]))
if not flavor:
    if docType == "Summary": flavor = "summary"
    elif docType == "InScopeProtocol": flavor = "protocol_hp"
    else: cdrcgi.bail(
        "Publish preview only available for Summary and Protocol documents")

#----------------------------------------------------------------------
# Filter the document.
#----------------------------------------------------------------------
if not filterSets.has_key(docType):
    cdrcgi.bail("Don't have filters set up for %s documents yet" % docType)
doc = cdr.filterDoc(session, filterSets[docType], docId = docId, 
                    docVer = docVer)
if type(doc) == type(()):
    doc = doc[0]
pattern1 = re.compile("<\?xml[^?]+\?>", re.DOTALL)
pattern2 = re.compile("<!DOCTYPE[^>]+>", re.DOTALL)
doc = pattern1.sub("", doc)
doc = pattern2.sub("", doc)
#cdrcgi.bail("flavor=%s doc=%s" % (flavor, doc))
try:
    if dbgLog:
        cdr2cg.debuglevel = 1
    resp = cdr2cg.pubPreview(doc, flavor)
except:
    cdrcgi.bail("Preview formatting failure")

#doc = cdrcgi.decode(doc)
#doc = re.sub("@@DOCID@@", docId, doc)

#----------------------------------------------------------------------
# Show it.
#----------------------------------------------------------------------
cdrcgi.sendPage("""\
<html>
 <head>
  <title>Publish Preview for CDR%010d</title>
  <link rel="stylesheet" href="http://stage.cancer.gov/stylesheets/nci.css">
 </head>
 <body>
  %s
 </body>
</html>""" % (intId, resp.xmlResult))
