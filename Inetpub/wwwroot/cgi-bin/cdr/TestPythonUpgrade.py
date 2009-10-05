#----------------------------------------------------------------------
#
# $Id: TestPythonUpgrade.py,v 1.1 2009-02-12 16:22:16 bkline Exp $
#
#----------------------------------------------------------------------
def sendPage(what):
    print """\
Content-type: text/html

%s""" % what

def show(component, version):
    html.append(u"""\
   <tr>
    <td>%s</td>
    <td>%s</td>
   </tr>
""" % (cgi.escape(component), cgi.escape(version)))
html = ["""\
<html>
 <head>
  <title>Python Upgrade Information</title>
  <style type='text/css'>
   body { font-family: Arial, sans-serif; }
   th { color: blue; }
   h1 { font-size: 14pt; color: maroon; }
  </style>
 </head>
 <body>
  <h1>Python Upgrade Information</h1>
  <table border='1' cellpadding='2' cellspacing='0'>
   <tr>
    <th>Component</th>
    <th>Version</th>
   </tr>
"""]
try:
    import sys
    import cgi
    import MySQLdb
    import Image
    import lxml.etree
    import xlrd
    import pyXLWriter
    import cdr
    import cdrdb
    import cdrmailcommon
    from xml.parsers.xmlproc import xmlproc
    conn = cdrmailcommon.emailerConn('dropbox')
    show("Python", sys.version)
    show("lxml", "%d.%d.%d.%d" % lxml.etree.LXML_VERSION[:4])
    show("xmlproc", xmlproc.version)
    show("Image", Image.VERSION)
    show("xlrd", xlrd.__VERSION__)
    show("pyXLWriter", "%s.%s.%s" % pyXLWriter.version_info[:3])
    show("MySQLdb", "%s.%s.%s" % MySQLdb.version_info[:3])
    show("MySQL Server", "%s.%s" % conn._server_version[:2])
    html.append("""\
  </table>
 </body>
</html>""")
    sendPage("".join(html))
except Exception, e:
    sendPage("<pre>%s</pre>" % e)