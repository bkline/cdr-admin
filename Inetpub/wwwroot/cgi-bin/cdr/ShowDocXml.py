#----------------------------------------------------------------------
#
# $Id: ShowDocXml.py,v 1.2 2002-08-15 19:49:04 bkline Exp $
#
# Sends the raw XML for a document to a browser.  Useful with IE5.x,
# which by default shows a hierarchical tree display for the data.
#
# $Log: not supported by cvs2svn $
# Revision 1.1  2001/06/13 22:16:32  bkline
# Initial revision
#
#
#----------------------------------------------------------------------
import cgi, cdr, cdrcgi, re

#----------------------------------------------------------------------
# Get the parameters from the request.
#----------------------------------------------------------------------
title   = "CDR Document XML"
fields  = cgi.FieldStorage() or cdrcgi.bail("No Request Found", title)
docId   = fields.getvalue(cdrcgi.DOCID) or cdrcgi.bail("No Document", title)

#----------------------------------------------------------------------
# Filter the document.
#----------------------------------------------------------------------
doc = cdrcgi.decode(cdr.getDoc('guest', docId))

#----------------------------------------------------------------------
# Send it.
#----------------------------------------------------------------------
expr = re.compile("<!\[CDATA\[(.*)\]\]>", re.DOTALL)
doc  = expr.findall(doc)[0]
print "Content-type: text/xml\n\n" + doc