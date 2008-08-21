############
# CGI script invoked by the Big Brother system monitor to determine if
# the CDR server is up and responding properly.
#
# If error, reports to default log file (debug.log) and to web client.
#
# $Id: cdrping.py,v 1.1 2008-08-07 19:39:03 ameyer Exp $
#
# $Log: not supported by cvs2svn $
############

import cdr

def report(what):
    print """\
Content-type: text/plain

CDR %s""" % what

# Uncomment if needed
# cdr.logwrite("cdrping called")
try:
    response = cdr.getDoctypes('guest')
    if type(response) in (str, unicode):
        cdr.logwrite("cdrping getDoctypes error: %s" % response)
        report("CORRUPT")
    else:
        report("OK")
except Exception, e:
    cdr.logwrite("cdrping getDoctypes exception type=%s  value=%s" %
                 (type(e), e))
    report("UNAVAILABLE")