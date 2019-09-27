#----------------------------------------------------------------------
# Prototype for editing CDR query term definitions.
#----------------------------------------------------------------------
import cgi, cdr, cdrcgi, re, string
from html import escape as html_escape

#----------------------------------------------------------------------
# Set the form variables.
#----------------------------------------------------------------------
fields  = cgi.FieldStorage()
session = cdrcgi.getSession(fields)
request = fields.getvalue(cdrcgi.REQUEST)
title   = "CDR Administration"
section = "Manage Query Term Definitions"
buttons = [cdrcgi.MAINMENU, "Log Out"]
server1 = fields.getvalue('server1')
server2 = fields.getvalue('server2')
newPath = fields.getvalue('add')
delete  = fields.getvalue('delete')
script  = "EditQueryTermDefs.py"
header  = cdrcgi.header(title, title, section, script, buttons,
                        stylesheet = """\
<style type='text/css'>
   .fb { width: 150px; }
   .path { color: green; font-weight: bold; font-family: "Courier New" }
   .path { color: navy; font-size: 1.0em; }
   .path { color: black; }
</style>""")

#----------------------------------------------------------------------
# Make sure the login was successful.
#----------------------------------------------------------------------
if not session: cdrcgi.bail('Unknown or expired CDR session.')

#----------------------------------------------------------------------
# Return to the main menu if requested.
#----------------------------------------------------------------------
if request == cdrcgi.MAINMENU:
    cdrcgi.navigateTo("Admin.py", session)

#----------------------------------------------------------------------
# Handle request to log out.
#----------------------------------------------------------------------
if request == "Log Out":
    cdrcgi.logout(session)

#----------------------------------------------------------------------
# Process an action if the user requested one.
#----------------------------------------------------------------------
if delete:
    try:
        err = cdr.delQueryTermDef(session, delete, None)
    except Exception as e:
        cdrcgi.bail("Failure deleting {!r}: {}".format(delete, e))
    if err: cdrcgi.bail(err)
if newPath:
    try:
        err = cdr.addQueryTermDef(session, newPath, None)
    except Exception as e:
        cdrcgi.bail("Failure adding {!r}: {}".format(newPath, e))
    if err: cdrcgi.bail(err)

#----------------------------------------------------------------------
# Compare the definitions with another server.
#----------------------------------------------------------------------
if request == 'Compare' and server1 and server2:
    try:
        defs1 = cdr.listQueryTermDefs('guest', tier=server1)
    except:
        cdrcgi.bail("Unable to retrieve definitions from {!r}".format(server1))
    if isinstance(defs1, (str, bytes)):
        cdrcgi.bail(defs1)
    defs1 = [d[0] for d in defs1]
    try:
        defs2 = cdr.listQueryTermDefs('guest', tier=server2)
    except:
        cdrcgi.bail("Unable to retrieve definitions from {!r}".format(server2))
    if isinstance(defs2, (str, bytes)):
        cdrcgi.bail(defs2)
    defs2 = [d[0] for d in defs2]
    defs1.sort()
    defs2.sort()
    extra1 = []
    extra2 = []
    for qdef in defs1:
        if qdef not in defs2:
            extra1.append(qdef)
    for qdef in defs2:
        if qdef not in defs1:
            extra2.append(qdef)
    html = """\
<html>
 <head>
  <title>Query Term Definitions on %s and %s</title>
 </head>
 <body>
""" % (server1, server2)
    if not extra1 and not extra2:
        cdrcgi.sendPage(html + """\
  <h2>Query Term Definitions on %s and %s</h2>
  <p>Definitions match</p>
 </body>
</html>
""" % (server1, server2))
    if extra1:
        html += """\
  <h2>On %s</h2>
  <ul>
""" % server1
        for extra in extra1:
            html += """\
   <li>%s</li>
""" % html_escape(extra)
        html += """\
  </ul>
  <br>
"""
    if extra2:
        html += """\
  <h2>On %s</h2>
  <ul>
""" % server2
        for extra in extra2:
            html += """\
   <li>%s</li>
""" % html_escape(extra)
        html += """\
  </ul>
"""
    cdrcgi.sendPage(html + """\
 </body>
</html>
""")

#----------------------------------------------------------------------
# Retrieve the lists of rules and query term definitions from the server.
#----------------------------------------------------------------------
defs = cdr.listQueryTermDefs(session)
if isinstance(defs, (str, bytes)): cdrcgi.bail(defs)
defs.sort()

#----------------------------------------------------------------------
# Create a button for deleting a specific query term definition.
#----------------------------------------------------------------------
def makeDeleteButton(path):
    onclick = 'javascript:delPath("%s");' % html_escape(path, True)
    return ("<input class='fb' type='button' onclick='%s' "
            "value='Delete Definition' />"
            % onclick.replace("'", "&apos;"))

#----------------------------------------------------------------------
# Display the existing definitions.
#----------------------------------------------------------------------
form = ["""\
  <script type='text/javascript' language='JavaScript'>
   function addPath() {
       var form = document.forms[0];
       var newPath = form.newPath.value;
       if (!newPath) {
           window.alert('No path given');
           return;
       }
       form.add.value = newPath;
       form.submit();
   }
   function delPath(p) {
       if (!window.confirm("Delete query term definition for '" + p + "'?"))
           return;
       var form = document.forms[0];
       form['delete'].value = p;
       form.submit();
   }
  </script>
  <form method='post' action='EditQueryTermDefs.py'>
   <input type='hidden' name='%s' value='%s'>
   <input type='hidden' name='add' value=''>
   <input type='hidden' name='delete' value=''>
   <input class='fb' type='submit' name='Request' value='Compare'>
   <input name='server1' value='DEV' />
   <b>with</b>
   <input name='server2' value='PROD' />
   <br /><br />
   <table>
    <tr>
     <td><input class='fb'
                type='button' onclick='javascript:addPath()'
                value='Add New Definition' /></td>
     <td><input name='newPath' size='80' value='' /></td>
    </tr>
""" % (cdrcgi.SESSION, session)]
for path, rule in defs:
    form.append("""\
    <tr>
     <td>%s</td>
     <td class='path' nowrap='nowrap'>%s</td>
    </tr>
""" % (makeDeleteButton(path), html_escape(path)))
form.append("""\
   </table>
  </form>
 </body>
<html>
""")
cdrcgi.sendPage(header + "".join(form))
