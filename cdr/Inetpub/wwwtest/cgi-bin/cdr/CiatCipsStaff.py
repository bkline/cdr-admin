#----------------------------------------------------------------------
#
# $Id: CiatCipsStaff.py,v 1.1 2003-12-16 16:06:08 bkline Exp $
#
# Main menu for CIAT/CIPS staff.
#
# $Log: not supported by cvs2svn $
#----------------------------------------------------------------------
import cgi, cdr, cdrcgi, re, string

#----------------------------------------------------------------------
# Set the form variables.
#----------------------------------------------------------------------
fields  = cgi.FieldStorage()
session = cdrcgi.getSession(fields)

#----------------------------------------------------------------------
# Make sure the login was successful.
#----------------------------------------------------------------------
if not session: cdrcgi.bail('Unknown user id or password.')

#----------------------------------------------------------------------
# Put up the menu.
session = "?%s=%s" % (cdrcgi.SESSION, session)
title   = "CDR Administration"
section = "CIAT/CIPS Staff"
buttons = []
html    = cdrcgi.header(title, title, section, "", buttons) + """\
   <ol>
"""
items   = (('AdvancedSearch.py', 'Advanced Search' ),
           ('Reports.py',        'Reports'         ),
           ('MergeProt.py',      'Protocol Merge'  ),
           ('CTGov.py',          'CTGov Protocols' ),
           ('Mailers.py',        'Mailers'         ),
           ('GlobalChange.py',   'Global Changes'  ),
           ('getBatchStatus.py', 'Batch Job Status')
           )
for item in items:
    html += """\
    <li><a href='%s/%s%s'>%s</a></li>
""" % (cdrcgi.BASE, item[0], session, item[1])

cdrcgi.sendPage(html + """\
   </ol>
  </form>
 </body>
</html>
""")