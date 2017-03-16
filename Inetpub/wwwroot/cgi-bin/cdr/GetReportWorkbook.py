#----------------------------------------------------------------------
# Sends back Excel workbook report to client.
#----------------------------------------------------------------------
import cgi, cdrcgi, os, msvcrt, sys

msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
fields = cgi.FieldStorage()
name   = fields and fields.getvalue('name') or cdrcgi.bail('Missing name')
try:
    fobj = file('d:/cdr/Reports/%s' % name, 'rb')
except:
    cdrcgi.bail('Report %s not found' % name)
book = fobj.read()
fobj.close()

print """\
Content-type: application/vnd.ms-excel
Content-disposition: attachment;filename=%s
""" % name
sys.stdout.write(book)
