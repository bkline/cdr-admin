#----------------------------------------------------------------------
#
# $Id: PreMailerProtReport.py,v 1.1 2003-01-29 18:47:47 bkline Exp $
#
# Checks run prior to generating mailers for protocols.
#
# $Log: not supported by cvs2svn $
#----------------------------------------------------------------------
import cdr, cdrdb, cdrcgi, cgi

#----------------------------------------------------------------------
# Set the form variables.
#----------------------------------------------------------------------
fields  = cgi.FieldStorage()
session = cdrcgi.getSession(fields)
request = cdrcgi.getRequest(fields)
jobId   = fields and fields.getvalue('JobId') or None
SUBMENU = "Report Menu"
buttons = [SUBMENU, cdrcgi.MAINMENU, "Log Out"]
script  = "PreMailerProtReport.py"
title   = "CDR Administration"
section = "Pre-Mailer Protocol Check"
header  = cdrcgi.header(title, title, section, script, buttons)

#----------------------------------------------------------------------
# Make sure we're logged in.
#----------------------------------------------------------------------
if not jobId and not session: cdrcgi.bail('Unknown or expired CDR session.')

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
# Connect to the CDR database.
#----------------------------------------------------------------------
try:
    conn   = cdrdb.connect('CdrGuest')
    cursor = conn.cursor()
except cdrdb.Error, info:
    cdrcgi.bail('Database connection failure: %s' % info[1][0])

#----------------------------------------------------------------------
# Submit some queries.
#----------------------------------------------------------------------
brussels   = 'NCI Liaison Office-Brussels'
statusPath = '/InScopeProtocol/ProtocolAdminInfo/CurrentProtocolStatus'
sourcePath = '/InScopeProtocol/ProtocolSources/ProtocolSource/SourceName'
rolePath   = '/InScopeProtocol/ProtocolAdminInfo/ProtocolLeadOrg' \
             '/LeadOrgPersonnel/PersonRole'
modePath   = '/Organization/OrganizationDetails' \
             '/PreferredProtocolContactMode'
matPath    = '/InScopeProtocol/ProtocolAdminInfo/ProtocolLeadOrg' \
             '/MailAbstractTo'
lopPath    = '/InScopeProtocol/ProtocolAdminInfo/ProtocolLeadOrg' \
             '/LeadOrgPersonnel/@cdr:id'
loPath     = '/InScopeProtocol/ProtocolAdminInfo/ProtocolLeadOrg' \
             '/LeadOrganizationID/@cdr:ref'
try:

    # Which protocols are candidates for summary mailers?
    cursor.execute("""\
        SELECT DISTINCT protocol.id,
                        MAX(doc_version.num) AS ver_num
                   INTO #candidate_summary_protocols
                   FROM doc_version
                   JOIN document protocol
                     ON protocol.id = doc_version.id
                   JOIN query_term prot_status
                     ON prot_status.doc_id = protocol.id
        LEFT OUTER JOIN ready_for_review
                     ON ready_for_review.doc_id = doc_version.id
                  WHERE prot_status.value IN ('Active', 
                                              'Approved-not yet active')
                    AND prot_status.path = '%s'
                    AND doc_version.val_status = 'V'
                    AND (doc_version.publishable = 'Y'
                     OR ready_for_review.doc_id IS NOT NULL)

                    -- We don't send mailers to Brussels.
                    AND protocol.id NOT IN (SELECT doc_id
                                              FROM query_term
                                             WHERE value = '%s'
                                               AND path  = '%s')

               GROUP BY protocol.id, protocol.title""" % (statusPath,
                                                          brussels,
                                                          sourcePath),
                   timeout = 120)
    conn.commit()

    # Which ones have someone to mail the abstract to?
    cursor.execute("""\
        SELECT cp.id
          INTO #have_mail_abstract_to
          FROM #candidate_summary_protocols cp
          JOIN query_term mat
            ON mat.doc_id = cp.id
          JOIN query_term lop
            ON lop.doc_id = mat.doc_id
           AND lop.value = mat.value
         WHERE mat.path = '%s'
           AND lop.path = '%s'""" % (matPath, lopPath), timeout = 120)
    conn.commit()

    # The rest are the problems we report.
    cursor.execute("""\
        SELECT d.id, d.title
          FROM #candidate_summary_protocols c
          JOIN document d
            ON d.id = c.id
         WHERE d.id NOT IN (SELECT id 
                              FROM #have_mail_abstract_to)""", timeout = 120)
    missingMailAbstractTo = cursor.fetchall()

    # Which protocols are eligible for status and participant mailers?
    cursor.execute("""\
             SELECT protocol.id,
                    MAX(doc_version.num) AS ver_num
               INTO #s_and_p_candidates
               FROM document protocol
               JOIN doc_version
                 ON doc_version.id = protocol.id
               JOIN query_term prot_status
                 ON prot_status.doc_id = protocol.id
               JOIN query_term lead_org
                 ON lead_org.doc_id = protocol.id
    LEFT OUTER JOIN ready_for_review
                 ON ready_for_review.doc_id = protocol.id

              -- We only send mailers for active or approved protocols.
              WHERE prot_status.value IN ('Active', 
                                          'Approved-Not Yet Active')
                AND prot_status.path       = '%s'
                AND lead_org.path          = '%s'
                AND doc_version.val_status = 'V'
                AND (ready_for_review.doc_id IS NOT NULL
                 OR  doc_version.publishable = 'Y')

                -- Don't send paper when they want electronic mailers.
                AND NOT EXISTS (SELECT *
                                  FROM query_term
                                 WHERE doc_id = lead_org.int_val
                                   AND path = '%s')

                -- Don't send mailers for Brussels protocols.
                AND NOT EXISTS (SELECT *
                                  FROM query_term
                                 WHERE value = '%s'
                                   AND path  = '%s'
                                   AND doc_id = protocol.id)

           GROUP BY protocol.id, protocol.title""" % (statusPath,
                                                      loPath,
                                                      modePath,
                                                      brussels,
                                                      sourcePath),
                   timeout = 120)
    conn.commit()

    # Which of those have an update person?
    cursor.execute("""\
         SELECT DISTINCT sp.id
                    INTO #has_update_person
                    FROM #s_and_p_candidates sp
                    JOIN query_term qt
                      ON qt.doc_id = sp.id
                   WHERE qt.path = '%s'
                     AND qt.value = 'Update person'""" % rolePath,
                   timeout = 120)
    conn.commit()

    # The rest are the problems we report.
    cursor.execute("""\
        SELECT d.id, d.title
          FROM #s_and_p_candidates c
          JOIN document d
            ON d.id = c.id
         WHERE d.id NOT IN (SELECT id
                              FROM #has_update_person)""", timeout = 120)
    missingUpdatePersons = cursor.fetchall()
except cdrdb.Error, info:
    cdrcgi.bail('Failure retrieving report information: %s' % info[1][0])

#----------------------------------------------------------------------
# Start the HTML page.
#----------------------------------------------------------------------
html = """\
<!DOCTYPE HTML PUBLIC '-//IETF//DTD HTML//EN'>
<html>
 <head>
  <title>Pre-Mailer Protocol Check</title>
  <style type='text/css'>
   h1 { font-family: sans-serif; font-size: 18; font-weight: bold }
   h2 { font-family: sans-serif; font-size: 16; }
   th { font-family: serif; font-size: 14; font-weight: bold; }
   td { font-family: sans-serif; font-size: 14; }
  </style>
 </head>
 <body>
  <h1>Pre-Mailer Protocol Check</h1>
  <br>
  <h2>Protocols without MailAbstractTo element</h2>
"""

if not missingMailAbstractTo:
    html += """\
  <p>None</p>
"""
else:
    html += """\
  <table border='1' cellspacing='0' cellpadding='2'>
   <tr>
    <th nowrap='1'>Document ID</th>
    <th nowrap='1'>Document Title</th>
   </tr>
"""
    for row in missingMailAbstractTo:
        html += """\
   <tr>
    <td valign='top'>CDR%010d</td>
    <td>%s</td>
   </tr>
""" % (row[0], cgi.escape(row[1]))
    html += """\
  </table>
"""

html += """\
  <br>
  <h2>Protocols without update persons</h2>
"""

if not missingUpdatePersons:
    html += """\
  <p>None</p>
"""
else:
    html += """\
  <table border='1' cellspacing='0' cellpadding='2'>
   <tr>
    <th nowrap='1'>Document ID</th>
    <th nowrap='1'>Document Title</th>
   </tr>
"""
    for row in missingUpdatePersons:
        html += """\
   <tr>
    <td valign='top'>CDR%010d</td>
    <td>%s</td>
   </tr>
""" % (row[0], cgi.escape(row[1]))
    html += """\
  </table>
 </body>
</html>
"""
       
cdrcgi.sendPage(html)
