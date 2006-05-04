#----------------------------------------------------------------------
#
# $Id: ProtProcReport.py,v 1.1 2006-05-04 15:08:52 bkline Exp $
#
# Report of protocol processing status.
#
# $Log: not supported by cvs2svn $
#----------------------------------------------------------------------

import cdrbatch, cdrcgi, cgi, cdrdb, cdr, time

#----------------------------------------------------------------------
# Set the form variables.
#----------------------------------------------------------------------
fields      = cgi.FieldStorage()
session     = cdrcgi.getSession(fields) or cdrcgi.bail('not logged in to CDR')
request     = cdrcgi.getRequest(fields)
email       = cdr.getEmail(session)
title       = "CDR Administration"
section     = "Protocol Processing Status Report"
SUBMENU     = "Report Menu"
buttons     = [SUBMENU, cdrcgi.MAINMENU, "Log Out"]
script      = 'ProtProcReport.py'
command     = 'lib/Python/CdrLongReports.py'
header      = cdrcgi.header(title, title, section, script, buttons,
                            stylesheet = """\
  <style type='text/css'>
   body { font-family: Arial }
  </style>
 """)

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
# Queue up a request for the report.
#----------------------------------------------------------------------
if not email or '@' not in email:
    cdrcgi.bail("No email address for logged-in user")
try:
    batch = cdrbatch.CdrBatch(jobName = section, email = email, 
                              command = command)
except Exception, e:
    cdrcgi.bail(str(e))

#cdrcgi.bail('milepost')
try:
    batch.queue()
except Exception, e:
    cdrcgi.bail("Could not start job: " + str(e))
jobId = batch.getJobId()
cdrcgi.sendPage(header + """\
   <h4>Report has been queued for background processing</h4>
   <p>
    To monitor the status of the job, click this
    <a href='http://%s%s/getBatchStatus.py?%s=%s&jobId=%s'><u>link</u></a>
    or use the CDR Administration menu to select 'View
    Batch Job Status'.
   </p>
  </form>
 </body>
</html>
""" % (cdrcgi.WEBSERVER, cdrcgi.BASE, cdrcgi.SESSION, session, jobId))
