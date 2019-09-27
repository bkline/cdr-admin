#----------------------------------------------------------------------
# Gets a schema document from the repository and returns it as a plain
# text file.
#----------------------------------------------------------------------
import cgi, cdrcgi, sys
from cdrapi import db
from html import escape as html_escape

#----------------------------------------------------------------------
# Set the form variables.
#----------------------------------------------------------------------
fields  = cgi.FieldStorage()
id      = fields and fields.getvalue("id")

conn = db.connect(user='CdrGuest')
cursor = conn.cursor()

if id:
    cursor.execute("SELECT title, xml FROM document WHERE id = %s" % id)
    rows = cursor.fetchall()
    if not rows:
        cdrcgi.bail("Can't retrieve XML for document %s" % id)
    sys.stdout.write("""\
Content-type: text/html; charset: utf-8

<html>
 <body>
  <h1>%s</h1>
  <pre>%s</pre>
 </body>
</html>
""" % (rows[0][0],
       html_escape(rows[0][1]).encode('utf-8')))
    sys.exit(0)

cursor.execute("""\
    SELECT d.id, d.title
      FROM document d
      JOIN doc_type t
        ON t.id = d.doc_type
     WHERE t.name = 'Schema'
  ORDER BY d.title""")
html = ["""\
<html>
 <head>
  <title>CDR Schemas</title>
  <style type='text/css'>
   body { font-family: Arial }
  </style>
 </head>
 <body>
  <h1>CDR Schemas</h1>"""]
for row in cursor.fetchall():
    line = ("  <a href='GetSchema.py?id=%d'>%s</a><br />" %
            (row[0], html_escape(row[1])))
    html.append(line)
html.append("""\
 </body>
</html>
""")
cdrcgi.sendPage("\n".join(html))
