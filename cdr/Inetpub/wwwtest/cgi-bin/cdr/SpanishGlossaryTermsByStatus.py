#----------------------------------------------------------------------
#
# $Id: SpanishGlossaryTermsByStatus.py,v 1.1 2006-05-17 14:17:05 bkline Exp $
#
# Split off from the base glossary terms by status report because new
# requirements force the report to be performed in batch mode.
#
# $Log: not supported by cvs2svn $
#----------------------------------------------------------------------
import cgi, cdr, cdrdb, cdrcgi, string, time, cdrbatch

#----------------------------------------------------------------------
# Set the form variables.
#----------------------------------------------------------------------
fields   = cgi.FieldStorage()
status   = fields and fields.getvalue("status") or 'Translation pending'
session  = fields and fields.getvalue("Session") or 'guest'
request  = cdrcgi.getRequest(fields)
fromDate = fields and fields.getvalue('FromDate') or '2002-01-01'
toDate   = fields and fields.getvalue('ToDate') or '2006-06-01'
email    = fields and fields.getvalue("Email")    or '***REMOVED***'
title    = "CDR Administration"
instr    = "Spanish Glossary Terms by Status"
SUBMENU  = "Report Menu"
buttons  = ["Submit Request", "Report Menu", cdrcgi.MAINMENU, "Log Out"]
script   = "SpanishGlossaryTermsByStatus.py"
command  = 'lib/Python/CdrLongReports.py'
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
if not fromDate or not toDate or not status or not email:
    now         = time.localtime(time.time())
    toDateNew   = time.strftime("%Y-%m-%d", now)
    then        = list(now)
    then[1]    -= 1
    then[2]    += 1
    then        = time.localtime(time.mktime(then))
    fromDateNew = time.strftime("%Y-%m-%d", then)
    toDate      = toDate or toDateNew
    fromDate    = fromDate or fromDateNew
    style       = "style='width: 200px'"
    form        = """\
   <P>
    This report requires a few minutes to complete.
    When the report processing has completed, email notification
    will be sent to the addresses specified below.  At least
    one email address must be provided.  If more than one
    address is specified, separate the addresses with a blank.
   </P>
   <BR>
   <INPUT TYPE='hidden' NAME='%s' VALUE='%s'>
   <TABLE BORDER='0'>
    <TR>
     <TD ALIGN='right'><B>Start Date:&nbsp;</B></TD>
     <TD><INPUT NAME='FromDate' VALUE='%s' %s>&nbsp;
         (use format YYYY-MM-DD for dates, e.g. 2002-01-01)</TD>
    </TR>
    <TR>
     <TD ALIGN='right'><B>End Date:&nbsp;</B></TD>
     <TD><INPUT NAME='ToDate' VALUE='%s' %s>&nbsp;</TD>
    </TR>
<!--
    <TR>
     <TD>&nbsp;</TD>
     <TD>and select:</TD>
    </TR>
  -->
    <TR>
     <TD ALIGN='right'><B>Term Status:&nbsp;</TD>
     <TD>
      <SELECT NAME='status' %s>
       <OPTION VALUE=''>Select One</OPTION>
       <OPTION VALUE='Translation approved'>Translation approved</OPTION>
       <OPTION VALUE='Translation pending'>Translation pending</OPTION>
       <OPTION VALUE='Translation revision pending'>Translation
            revision pending</OPTION>
      </SELECT>
     </TD>
    </TR>
    <TR>
     <TD ALIGN='right'>
      <B>Email address(es):&nbsp;</B>
     </TD>
     <TD>
      <INPUT NAME='Email' SIZE='30' VALUE='%s' %s> (Required)
     </TD>
    </TR>
   </TABLE>
  </FORM>
 </BODY>
</HTML>
""" % (cdrcgi.SESSION, session, fromDate, style, toDate, style, style,
       cdr.getEmail(session) or '', style)
    cdrcgi.sendPage(header + form)

#----------------------------------------------------------------------    
# If we get here, we're ready to queue up a request for the report.
#----------------------------------------------------------------------
args = (
    ('from', fromDate),
    ('to',   toDate),
    ('status', status)
    )
batch = cdrbatch.CdrBatch(jobName = instr, email = email, args = args,
                          command = command)
try:
    batch.queue()
except Exception, e:
    cdrcgi.bail("Could not start job: " + str(e))
jobId       = batch.getJobId()
buttons     = [SUBMENU, cdrcgi.MAINMENU, "Log Out"]
script      = 'SpanishGlossaryTermsByStatus.py'
header      = cdrcgi.header(title, title, instr, script, buttons, 
                            stylesheet = """\
  <style type='text/css'>
   body { font-family: Arial }
  </style>
 """)
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
