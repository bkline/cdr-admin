#----------------------------------------------------------------------
#
# $Id: SummariesTocReport.py,v 1.3 2007-11-03 14:15:07 bkline Exp $
#
# Report on lists of summaries.
#
# $Log: not supported by cvs2svn $
# Revision 1.2  2004/08/16 20:03:24  venglisc
# Added CSS to display the TOC levels indented.  Added help message.
# (Bug 1231)
#
# Revision 1.1  2004/07/13 20:11:36  venglisc
# Initial version of program to display a list of Summary Section Titles by
# summary board (Bug 1231).
# The user interface has been "borrowed" from SummariesLists.py.
#
#
#----------------------------------------------------------------------
import cgi, cdr, cdrcgi, re, string, cdrdb, time

#----------------------------------------------------------------------
# Set the form variables.
#----------------------------------------------------------------------
fields    = cgi.FieldStorage()
session   = cdrcgi.getSession(fields)
boolOp    = fields and fields.getvalue("Boolean")          or "AND"
audience  = fields and fields.getvalue("audience")         or None
lang      = fields and fields.getvalue("lang")             or None
showId    = fields and fields.getvalue("showId")           or "N"
tocLevel  = fields and fields.getvalue("tocLevel")         or "3"
groups    = fields and fields.getvalue("grp")              or []
submit    = fields and fields.getvalue("SubmitButton")     or None
request   = cdrcgi.getRequest(fields)
title     = "CDR Administration"
instr     = "Summaries TOC Lists"
script    = "SummariesTocReport.py"
SUBMENU   = "Report Menu"
buttons   = (SUBMENU, cdrcgi.MAINMENU)

# Functions to replace sevaral repeated HTML snippets
# ===================================================
def boardHeader(header):
    """Return the HTML code to display the Summary Board Header"""
    html = """\
  <U><H4>%s</H4></U>
""" % board_type
    return html

def summaryRow(id, summary, toc):
    """Return the HTML code to display a Summary row"""
    response = cdr.filterDoc('guest', ['name:Summaries TOC Report'], id, 
                             parm = filterParm)
    html = unicode(response[0], "utf-8")
    html += """\
"""
    return html

#----------------------------------------------------------------------
# If the user only picked one summary group, put it into a list so we
# can deal with the same data structure whether one or more were
# selected.
#----------------------------------------------------------------------
if type(groups) in (type(""), type(u"")):
    groups = [groups]

#----------------------------------------------------------------------
# Handle navigation requests.
#----------------------------------------------------------------------
if request == cdrcgi.MAINMENU:
    cdrcgi.navigateTo("Admin.py", session)
elif request == SUBMENU:
    cdrcgi.navigateTo("reports.py", session)

#----------------------------------------------------------------------
# Set up a database connection and cursor.
#----------------------------------------------------------------------
try:
    conn = cdrdb.connect("CdrGuest")
    cursor = conn.cursor()
except cdrdb.Error, info:
    cdrcgi.bail('Database connection failure: %s' % info[1][0])

#----------------------------------------------------------------------
# Build date string for header.
#----------------------------------------------------------------------
dateString = time.strftime("%B %d, %Y")

#----------------------------------------------------------------------
# If we don't have a request, put up the form.
#----------------------------------------------------------------------
if not lang:
    header = cdrcgi.header(title, title, instr, script,
                           ("Submit",
                            SUBMENU,
                            cdrcgi.MAINMENU),
                           numBreaks = 1)
    form   = """\
   <input type='hidden' name='%s' value='%s'>
   <table border='0'>
    <tr>
     <td colspan='3'>
      %s<br><br>
     </td>
    </tr>
   </table>
 
   <table border="0">
    <tr>
     <td>
      <table border="0">
       <tr>
        <td nowrap>
         <input name='audience' type='radio' value='Health Professional' CHECKED>
         <b>Health Professional</b>
        </td>
        <td nowrap>
         <input name='showId' type='radio' value='Y'>
	 <b>With CDR ID</b>
        </td>
       </tr>
       <tr>
        <td nowrap>
         <input name='audience' type='radio' value='Patient'>
          <b>Patient</b>
        </td>
        <td nowrap>
         <input name='showId' type='radio' value='N' CHECKED>
	 <b>Without CDR ID</b>
        </td>
       </tr>
      </table>
     </td>
     <td valign='center'>
      <table border="0">
       <tr>
        <td>
         <input name='tocLevel' type='text' size='1' value='3' CHECKED>
	</td>
	<td>
         <b>TOC Levels Displayed</b> 
        </td>
        <td>(QC Report uses "3"; <br>leave blank to see all levels)</td>
       </tr>
      </table>
     </td>
    </tr>
   </table>

   <table>
    <tr>
     <td width="320">
      <hr width="50%%"/>
     </td>
    </tr>
   </table>

   <table border = '0'>
    <tr>
     <td width=100>
      <input name='lang' type='radio' value='English' CHECKED><b>English</b>
     </td>
     <td valign='top'>
      <b>Select PDQ Summaries: (one or more)</b>
     </td>
    </tr>
    <tr>
     <td></td>
     <td>
      <input type='checkbox' name='grp' value='All English' CHECKED>
       <b>All English</b><br>
      <input type='checkbox' name='grp' value='Adult Treatment'>
       <b>Adult Treatment</b><br>
      <input type='checkbox' name='grp' value='Genetics'>
       <b>Cancer Genetics</b><br>
      <input type='checkbox' name='grp'
             value='Complementary and Alternative Medicine'>
       <b>Complementary and Alternative Medicine</b><br>
      <input type='checkbox' name='grp' value='Pediatric Treatment'>
       <b>Pediatric Treatment</b><br>
      <input type='checkbox' name='grp' value='Screening and Prevention'>
       <b>Screening and Prevention</b><br>
      <input type='checkbox' name='grp' value='Supportive Care'>
       <b>Supportive Care</b><br><br>
     </td>
    </tr>
    <tr>
     <td width=100>
      <input name='lang' type='radio' value='Spanish'><b>Spanish</b>
     </td>
     <td valign='top'>
      <b>Select PDQ Summaries: (one or more)</b>
     </td>
    </tr>
    <tr>
     <td></td>
     <td>
      <input type='checkbox' name='grp' value='All Spanish'>
       <b>All Spanish</b><br>
      <input type='checkbox' name='grp' value='Spanish Adult Treatment'>
       <b>Adult Treatment</b><br>
      <input type='checkbox' name='grp' value='Spanish Pediatric Treatment'>
       <b>Pediatric Treatment</b><br>
      <input type='checkbox' name='grp' value='Spanish Supportive Care'>
       <b>Supportive Care</b><br>
     </td>
    </tr>
   </table>

  </form>
 </body>
</html>
""" % (cdrcgi.SESSION, session, dateString)
    cdrcgi.sendPage(header + form)

#----------------------------------------------------------------------
# Language variable has been selected
# Building individual Queries
# - English, HP, with CDR ID
# - English, HP, without CDR ID
# - English, Patient, with CDR ID ...
#----------------------------------------------------------------------

#----------------------------------------------------------------------
# Create the selection criteria based on the groups picked by the user
# But the decision will be based on the content of the board instead
# of the SummaryType.
# Based on the SummaryType selected on the form the boardPick list is
# being created including the Editorial and Advisory board for each
# type.  These board IDs can then be decoded into the proper 
# heading to be used for each selected summary type.
# --------------------------------------------------------------------
boardPick = ''
for i in range(len(groups)):
  # if i+1 == len(groups):
  if groups[i] == 'Adult Treatment' and lang == 'English':
      boardPick += """'CDR0000028327', 'CDR0000035049', """
  elif groups[i] == 'Spanish Adult Treatment' and lang == 'Spanish':
      boardPick += """'CDR0000028327', 'CDR0000035049', """
  elif groups[i] == 'Complementary and Alternative Medicine':
      boardPick += """'CDR0000256158', """
  elif groups[i] == 'Genetics':
      boardPick += """'CDR0000032120', 'CDR0000257061', """
  elif groups[i] == 'Screening and Prevention':
      boardPick += """'CDR0000028536', 'CDR0000028537', """
  elif groups[i] == 'Pediatric Treatment' and lang == 'English':
      boardPick += """'CDR0000028557', 'CDR0000028558', """
  elif groups[i] == 'Spanish Pediatric Treatment' and lang == 'Spanish':
      boardPick += """'CDR0000028557', 'CDR0000028558', """
  elif groups[i] == 'Supportive Care' and lang == 'English':
      boardPick += """'CDR0000028579', 'CDR0000029837', """
  elif groups[i] == 'Spanish Supportive Care' and lang == 'Spanish':
      boardPick += """'CDR0000028579', 'CDR0000029837', """
  else:
      boardPick += """'""" + groups[i] + """', """

# --------------------------------------------------------------
# Define the Headings under which the summaries should be listed
# --------------------------------------------------------------
q_case = """\
       CASE WHEN board.value = 'CDR0000028327'  THEN 'Adult Treatment'
            WHEN board.value = 'CDR0000035049'  THEN 'Adult Treatment'
            WHEN board.value = 'CDR0000032120'  THEN 'Cancer Genetics'
            WHEN board.value = 'CDR0000257061'  THEN 'Cancer Genetics'
            WHEN board.value = 'CDR0000256158'  THEN 'Complementary and Alternative Medicine'
            WHEN board.value = 'CDR0000028557'  THEN 'Pediatric Treatment'
            WHEN board.value = 'CDR0000028558'  THEN 'Pediatric Treatment'
            WHEN board.value = 'CDR0000028536'  THEN 'Screening and Prevention'
            WHEN board.value = 'CDR0000028537'  THEN 'Screening and Prevention'
            WHEN board.value = 'CDR0000028579'  THEN 'Supportive Care'
            WHEN board.value = 'CDR0000029837'  THEN 'Supportive Care'
            ELSE board.value END
"""

# ------------------------------------------------------------------------
# Create the selection criteria for the summary language (English/Spanish)
# ------------------------------------------------------------------------
q_lang = """\
AND    lang.path = '/Summary/SummaryMetaData/SummaryLanguage'
AND    lang.value = '%s'
""" % lang

# ---------------------------------------------------------------------
# Define the selection criteria parts that are different for English or
# Spanish documents:
# q_fields:  Fields to be selected, i.e. the Spanish version needs to 
#            display the English translation
# q_join:    The Spanish version has to evaluate the board and language
#            elements differently
# q_board:   Don't restrict on selected boards if All English/Spanish
#            has been selected as well
# --------------------------------------------------------------------
if lang == 'English': 
    q_fields = """
                'dummy1', 'dummy2', title.value EnglTitle, 
"""
    q_join = """
JOIN  query_term board
ON    qt.doc_id = board.doc_id
JOIN  query_term lang
ON    qt.doc_id    = lang.doc_id
"""
    q_trans = ''
    if groups.count('All English'):
        q_board = ''
    else:
        q_board = """\
AND    board.value in (%s)
""" % boardPick[:-2]
else:
    q_fields = """
                qt.value CDRID, qt.int_val ID, translation.value EnglTitle, 
"""
    q_join = """
JOIN  query_term board
ON    qt.int_val = board.doc_id
JOIN  query_term translation
ON    qt.int_val = translation.doc_id
JOIN  query_term lang
ON    qt.doc_id    = lang.doc_id
"""
    q_trans = """
AND   translation.path = '/Summary/SummaryTitle'
AND   qt.path          = '/Summary/TranslationOf/@cdr:ref'
"""
    if groups.count('All Spanish'):
        q_board = ''
    else:
        q_board = """\
AND    board.value in (%s)
""" % boardPick[:-2]

# ---------------------------------------------------
# Create selection criteria for HP or Patient version
# ---------------------------------------------------
if audience == 'Patient':
    q_audience = """\
AND audience.value = 'Patients'
"""
else:
    q_audience = """\
AND audience.value = 'Health professionals'
"""

# -------------------------------------------------------------
# Put all the pieces together for the SELECT statement
# -------------------------------------------------------------
query = """\
SELECT DISTINCT qt.doc_id, title.value DocTitle, 
%s
%s
FROM  query_term qt
%s
JOIN  query_term title
ON    qt.doc_id    = title.doc_id
JOIN  query_term audience
ON    qt.doc_id    = audience.doc_id
WHERE title.path   = '/Summary/SummaryTitle'
%s
AND   board.path   = '/Summary/SummaryMetaData/PDQBoard/Board/@cdr:ref'
%s
AND   audience.path = '/Summary/SummaryMetaData/SummaryAudience'
%s
%s
AND EXISTS (SELECT 'x' FROM doc_version v
            WHERE  v.id = qt.doc_id
            AND    v.val_status = 'V'
            AND    v.publishable = 'Y')
AND qt.doc_id not in (select doc_id 
                       from doc_info 
                       where doc_status = 'I' 
                       and doc_type = 'Summary')
ORDER BY 6, 2
""" % (q_fields, q_case, q_join, q_trans, q_board, q_audience, q_lang)

if not query:
    cdrcgi.bail('No query criteria specified')   

#----------------------------------------------------------------------
# Submit the query to the database.
#----------------------------------------------------------------------
try:
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    cursor = None
except cdrdb.Error, info:
    cdrcgi.bail('Failure retrieving Summary documents: %s' %
                info[1][0])
     
if not rows:
    cdrcgi.bail('No Records Found for Selection: %s ' % lang+"; "+audience+"; "+groups[0] )

#cdrcgi.bail("Result: [%s]" % rows)
#----------------------------------------------------------------------
# Create the results page.
#----------------------------------------------------------------------
instr     = 'Section Titles for %s Summaries -- %s.' % (lang, dateString)
header    = cdrcgi.header(title, title, instr, script, buttons, 
                          stylesheet = """\
   <STYLE type="text/css">
    UL             { margin: 0pt; }
    UL UL          { margin-left: 30pt; }
    UL UL UL       { margin-left: 30pt; }
    UL UL UL UL    { margin-left: 30pt; }
    UL UL UL UL UL { margin-left: 30pt; }
    LI      { font-style: normal;
	      font-family: Arial;
              font-weight: normal; 
	      font-size: 12pt;
              list-style-type: none; }
    H5      { font-weight: bold;
	      font-family: Arial;
              font-size: 13pt; 
	      margin: 0pt; }
   </STYLE>
""")

# -------------------------
# Display the Report Title
# -------------------------
if lang == 'English':
    report    = """\
   <INPUT TYPE='hidden' NAME='%s' VALUE='%s'>
  </FORM>
  <H3>PDQ %s Summaries</H3>
""" % (cdrcgi.SESSION, session, audience)
else:
    report    = """\
   <INPUT TYPE='hidden' NAME='%s' VALUE='%s'>
  </FORM>
  <H3>PDQ %s %s Summaries</H3>
""" % (cdrcgi.SESSION, session, lang, audience)

board_type = rows[0][5]

# -------------------------------------------------------------------
# Decision if the CDR IDs are displayed along with the summary titles
# - The report without CDR ID is displayed as a bulleted list.
# - The report with    CDR ID is displayed in a table format.
# -------------------------------------------------------------------
# ------------------------------------------------------------------------
# Display Summary Title including CDR ID
# ------------------------------------------------------------------------
filterParm = []
filterParm = [['showLevel', tocLevel], ['showId', showId ]]
report += """\
  <U><H4>%s</H4></U>
""" % board_type

for row in rows:
    # If we encounter a new board_type we need to create a new
    # heading
    # ----------------------------------------------------------
    if row[5] == board_type:
       if lang == 'English':
          report += summaryRow(row[0], row[1], toc = tocLevel)
       else:
          report += summaryRow(row[0], row[1], toc = tocLevel)

    # For the Treatment Summary Type we need to check if this is an 
    # adult or pediatric summary
    # -------------------------------------------------------------
    else:
       board_type = row[5]
       report += boardHeader(board_type)
       if lang == 'English':
          report += summaryRow(row[0], row[1], toc = tocLevel)
       else:
          report += summaryRow(row[0], row[1], toc = tocLevel)
footer = """\
 </BODY>
</HTML> 
"""     

#----------------------------------------------------------------------
# Send the page back to the browser.
#----------------------------------------------------------------------
cdrcgi.sendPage(header + report + footer)
