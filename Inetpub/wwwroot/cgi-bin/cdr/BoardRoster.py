#----------------------------------------------------------------------
#
# $Id$
#
# Report to display the Board Roster with or without assistant
# information.
#
# BZIssue::4909 - Board Roster Report Change
# BZIssue::4979 - Error in Board Roster Report
# BZIssue::5023 - Changes to Board Roster Report
# 
#----------------------------------------------------------------------
import cgi, cdr, cdrcgi, cdrdb, re, time

#----------------------------------------------------------------------
# Set the form variables.
#----------------------------------------------------------------------
fields     = cgi.FieldStorage()
boardId    = fields and fields.getvalue("board")  or None
otherInfo  = fields and fields.getvalue("oinfo")  or 'No'
assistant  = fields and fields.getvalue("ainfo")  or 'No'
subgroup   = fields and fields.getvalue("sginfo") or 'No'
phone      = fields and fields.getvalue("pinfo")  or 'No'
fax        = fields and fields.getvalue("finfo")  or 'No'
cdrid      = fields and fields.getvalue("cinfo")  or 'No'
email      = fields and fields.getvalue("einfo")  or 'No'
startDate  = fields and fields.getvalue("dinfo")  or 'No'
blankCol   = fields and fields.getvalue("blank")  or 'No'
govEmp     = fields and fields.getvalue("govemp")  or 'No'
### recHonor   = fields and fields.getvalue("honoraria")  or 'No'
flavor     = fields and fields.getvalue("sheet")  or 'full'
session    = cdrcgi.getSession(fields)
request    = cdrcgi.getRequest(fields)
title      = "PDQ Board Roster Report"
instr      = "Report on PDQ Board Roster"
script     = "BoardRoster.py"
SUBMENU    = "Report Menu"
buttons    = ("Submit", SUBMENU, cdrcgi.MAINMENU)
header     = cdrcgi.header(title, title, instr, script, buttons, 
                           method = 'GET', 
                           stylesheet = """
    <script type='text/javascript'>
     function doSummarySheet(box) {
         if (box == 'summary')
             {
             if (document.getElementById('summary').checked == true)
                 {
                 document.getElementById('summary').checked = true;
                 }
             else
                 {
                 document.getElementById('summary').checked = false;
                 }
             }
         else
             {
             document.getElementById('summary').checked = true;
             }

         document.getElementById('contact').checked   = false;
         document.getElementById('assistant').checked = false;
         document.getElementById('subgroup').checked  = false;
         var form = document.forms[0];
         {
             form.einfo.value = form.einfo.checked ? 'Yes' : 'No';
             form.sheet.value = form.sheet.checked ? 'summary' : 'full';
             form.pinfo.value = form.pinfo.checked ? 'Yes' : 'No';
             form.cinfo.value = form.cinfo.checked ? 'Yes' : 'No';
             form.dinfo.value = form.dinfo.checked ? 'Yes' : 'No';
             form.finfo.value = form.finfo.checked ? 'Yes' : 'No';
             form.blank.value = form.blank.checked ? 'Yes' : 'No';
             form.govemp.value = form.govemp.checked ? 'Yes' : 'No';
             /*form.honoraria.value = form.honoraria.checked ? 'Yes' : 'No';*/
         }
     }
     function doFullReport() {
         document.getElementById('summary').checked = false;
         var form = document.forms[0];
         {
             form.oinfo.value  = form.oinfo.checked  ? 'Yes' : 'No';
             form.ainfo.value  = form.ainfo.checked  ? 'Yes' : 'No';
             form.sginfo.value = form.sginfo.checked ? 'Yes' : 'No';
             form.sheet.value  = form.sheet.checked  ? 'summary' : 'full';
         }
     }
    </script>
    <style type="text/css">
     td       { font-size: 12pt; }
     .label   { font-weight: bold; }
     .label2  { font-size: 11pt;
                font-weight: bold; }
     .select:hover { background-color: #FFFFCC; }
     .grey    {background-color: #BEBEBE; }
     .topspace { margin-top: 24px; }

    </style>
""")
boardId    = boardId and int(boardId) or None
dateString = time.strftime("%B %d, %Y")

filterType= {'summary':'name:PDQBoardMember Roster Summary',
             'full'   :'name:PDQBoardMember Roster'}
allRows   = []

# We can only run one report at a time: Full or Summary
# -----------------------------------------------------
if flavor == 'summary' and (otherInfo == 'Yes' or assistant == 'Yes'):
    cdrcgi.bail("Please uncheck 'Create Summary Sheet' to run 'Full' report")

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
# Look up title of a board, given its ID.
#----------------------------------------------------------------------
def getBoardName(id):
    try:
        cursor.execute("SELECT title FROM document WHERE id = ?", id)
        rows = cursor.fetchall()
        if not rows:
            cdrcgi.bail('Failure looking up title for CDR%s' % id)
        return cleanTitle(rows[0][0])
    except Exception, e:
        cdrcgi.bail('Looking up board title: %s' % str(e))

#----------------------------------------------------------------------
# Remove cruft from a document title.
#----------------------------------------------------------------------
def cleanTitle(title):
    semicolon = title.find(';')
    if semicolon != -1:
        title = title[:semicolon]
    return title.strip()

#----------------------------------------------------------------------
# Build a picklist for PDQ Boards.
# This function serves two purposes:
# a)  create the picklist for the selection of the board
# b)  create a dictionary in subsequent calls to select the board
#     ID based on the board selected in the first call.
#----------------------------------------------------------------------
def getBoardPicklist():
    picklist = "<SELECT NAME='board' onchange='javascript:doSummarySheet(\"summary\")'>\n"
    sel      = " SELECTED"
    try:
        cursor.execute("""\
SELECT DISTINCT board.id, board.title
           FROM document board
           JOIN query_term org_type
             ON org_type.doc_id = board.id
          WHERE org_type.path = '/Organization/OrganizationType'
            AND org_type.value IN ('PDQ Editorial Board',
                                   'PDQ Advisory Board')
       ORDER BY board.title""")
        for id, title in cursor.fetchall():
            title = cleanTitle(title)
            picklist += "<OPTION%s value='%d'>%s</OPTION>\n" % (sel, id, title)
            sel = ""
    except cdrdb.Error, info:
        cdrcgi.bail('Database query failure: %s' % info[1][0])
    return picklist + "</SELECT>\n"

#----------------------------------------------------------------------
# Get the information for the Board Manager
#----------------------------------------------------------------------
def getBoardManagerInfo(orgId):
    try:
        cursor.execute("""\
SELECT path, value
 FROM query_term
 WHERE path like '/Organization/PDQBoardInformation/BoardManager%%'
 AND   doc_id = ?
 ORDER BY path""", orgId)

    except cdrdb.Error, info:
        cdrcgi.bail('Database query failure for BoardManager: %s' % info[1][0])
    return cursor.fetchall()

#----------------------------------------------------------------------
# Extract the relevant information from the HTML snippet (which is
# created using the filter modules)
# The phone, fax, email information has been wrapped with the 
# respective elements in the filter for the summary sheet flavor
#----------------------------------------------------------------------
def extractSheetInfo(boardInfo):
    #cdrcgi.bail(boardInfo)
    myName  = boardInfo.split('<b>')[1].split('</b>')[0]
    #myTitle = boardInfo.split('<br>')[1]
    if boardInfo.find('<Phone>') > -1:
        try:
            myPhone = boardInfo.split('<Phone>')[1].split('</Phone>')[0]
        except:
            cdrcgi.bail(boardInfo)
    else:
        myPhone = ''

    if boardInfo.find('<Email>') > -1:
        try:
            myEmail = boardInfo.split('<Email>')[1].split('</Email>')[0]
        except:
            cdrcgi.bail(boardInfo)
    else:
        myEmail = ''

    if boardInfo.find('<Fax>') > -1:
        try:
            myFax   = boardInfo.split('<Fax>')[1].split('</Fax>')[0]
        except:
            cdrcgi.bail(boardInfo)
    else:
        myFax   = ''
    
    return [myName, myPhone, myFax, myEmail]


#----------------------------------------------------------------------
# Add the specific information to the boardInfo records
#----------------------------------------------------------------------
def addSpecificContactInfo(boardIds, boardInfo):
    newBoardInfo = []
    try:
        cursor.execute("""\
    SELECT g.doc_id, g.value AS GE, h.value, q.value as SpPhone, 
           f.value as SpFax, e.value as SpEmail
      FROM query_term g
LEFT OUTER JOIN query_term h
        ON g.doc_id = h.doc_id
       AND h.path = '/PDQBoardMemberInfo/GovernmentEmployee/@HonorariaDeclined'
LEFT OUTER JOIN query_term f
        ON g.doc_id = f.doc_id
       AND f.path = '/PDQBoardMemberInfo/BoardMemberContact' +
                    '/SpecificBoardMemberContact/BoardContactFax'
LEFT OUTER JOIN query_term e
        ON g.doc_id = e.doc_id
       AND e.path = '/PDQBoardMemberInfo/BoardMemberContact/' +
                    'SpecificBoardMemberContact/BoardContactEmail'
LEFT OUTER JOIN query_term q
        ON g.doc_id = q.doc_id
       AND q.path = '/PDQBoardMemberInfo/BoardMemberContact' +
                    '/SpecificBoardMemberContact/BoardContactPhone'
     WHERE g.doc_id IN (%s)
       AND g.path = '/PDQBoardMemberInfo/GovernmentEmployee'
  ORDER BY q.path""" % ','.join(["'%d'" % id for id in boardIds]))
    except cdrdb.Error, info:
        cdrcgi.bail('Database query failure for SpecificInfo: %s' % info[1][0]+
                    '<br>Board has No Board Members')

    rows = cursor.fetchall()

    # Add the specific info to the boardInfo records
    # ----------------------------------------------
    for member in boardInfo:
        memCount = len(member)
        for cdrId, ge, honor, phone, fax, email in rows:
            if member[4] == cdrId:
                member = member + [ge, honor or None, phone or None, 
                                   fax or None, email or None]
        if memCount == len(member):
            member = member + [None, None, None, None, None]
        newBoardInfo.append(member)
    return newBoardInfo


# ---------------------------------------------------------------------
# A non-government employee may decline to receive a honorarium.  
# Returning the appropriate value for the person.
# ---------------------------------------------------------------------
def checkHonoraria(govEmployee, declined = u''):
    if govEmployee == 'Yes':
        return u''
    elif govEmployee == u'Unknown':
        return u''
    elif govEmployee == 'No':
        if declined == 'Yes':
            return u'*'
        else:
            return u''


#----------------------------------------------------------------------
# Once the information for all board members has been collected create
# the HTML table to be displayed
#----------------------------------------------------------------------
def makeSheet(rows):
    # Create the table and table headings
    # ===================================
    rowCount = 0
    html = """
        <tr class="theader">"""
    for k, v in [('Name', 'Yes'), ('Phone', phone), ('Fax', fax), 
              ('Email', email), ('CDR-ID', cdrid), 
              ('Start Date', startDate), ('Gov. Empl.', govEmp),
              ### ('Rec. Honor.', recHonor), 
              ('&nbsp;', blankCol)]:
        if v == 'Yes':
            rowCount += 1
            html += """
         <th class="thcell">%s</th>""" % k

    html += """
        </tr>"""

    # Populate the table with data rows
    # =================================
    # for row in name, phone, fax, email, cdrid, termStardDate, 
    # govEmpl, recHonor, spPhone, ...
    # ----------------------------------------------------------
    for row in rows:
       html += """
        <tr>
         <td class="name">%s</td>""" % row[0]
       # Phone, Fax, Email may also have specific info
       # ---------------------------------------------
       if phone == 'Yes':
           html += """
         <td class="phone">%s""" % row[1]
           if row[1] and row[8]:
               html += "<br>%s</td>" % row[8]
           elif not row[1] and row[8]:
               html += "%s</td>" % row[8]
           else:
               html += "</td>"

       if fax   == 'Yes':
           html += """
         <td class="fax">%s""" % row[2]
           if row[2] and row[9]:
               html += "<br>%s</td>" % row[9]
           elif not row[2] and row[9]:
               html += u"%s</td>" % row[9]
           else:
               html += u"</td>"

       if email == 'Yes':
           html += u"""
         <td class="email">
          <a href="mailto:%s">%s</a>
         """ % (row[3], row[3])
           if row[3] and row[10]:
               html += u"""<br>
          <a href="mailto:%s">%s</a>
         """ % (row[10], row[10])
           elif not row[3] and row[10]:
               html += u"""
          <a href="mailto:%s">%s</a>
         </td>""" % (row[10], row[10])
           else:
               html += "</td>"

       # If the CDR-ID is to be printed
       # ------------------------------
       if cdrid == 'Yes':
           html += u"""
         <td class="cdrid">%s</td>""" % row[4]
       if startDate == 'Yes':
           html += u"""
         <td class="cdrid">%s</td>""" % row[5]

       # If the Government Employee column is printed
       # --------------------------------------------
       if govEmp == 'Yes':
           if row[7] is None:
               declined = u''
           else:
               declined = row[7]

           # The field Govt Employee is mandatory but was empty for
           # some documents during testing.
           # ------------------------------------------------------
           if row[6] is None: row[6] = u'Unknown'

           html += u"""
         <td class="cdrid">%s<sup><b>%s</b></sup></td>""" % (row[6],
                                               checkHonoraria(row[6], declined))
       ### if recHonor == 'Yes':
       ###     html += u"""
       ###   <td class="cdrid">%s</td>""" % (not(row[7]) and u'Yes' or u'No')

       # If a blank column is printed
       # ----------------------------
       if blankCol == 'Yes':
           html += u"""
         <td class="blank">&nbsp;</td>"""
       html += u"""
        </tr>"""

    return (html, rowCount)

#----------------------------------------------------------------------
# If we don't have a request, put up the form.
#----------------------------------------------------------------------
if not boardId:
    form   = """\
  <input TYPE='hidden' NAME='%s' VALUE='%s'>

  <table>
   <tr>
    <td class="label">PDQ Board:&nbsp;</TD>
    <td>%s</td>
   </tr>
   <tr>
    <td> </td>
    <td class="select">
     <input type='checkbox' name='oinfo' id='contact'
            onclick='jacascript:doFullReport()'>
     <label for="contact">Show All Contact Information</label>
    </td>
   </tr>
   <tr>
    <td> </td>
    <td class="select">
     <input type='checkbox' name='sginfo' id='subgroup'
            onclick='javascript:doFullReport()'>
     <label for="subgroup">Show Subgroup Information</label>
    </td>
   </tr>
   <tr>
    <td> </td>
    <td class="select">
     <input type='checkbox' name='ainfo' id='assistant'
            onclick='javascript:doFullReport()'>
     <label for="assistant">Show Assistant Information</label>
    </td>
   </tr>
   <tr>
    <td colspan="2">
     <div style="height: 10px"> </div>
    </td>
   </tr>
   <tr>
    <td> </td>
    <td class="grey">
     <div style="height: 10px"> </div>
     <input TYPE='checkbox' NAME='sheet' id='summary'
            onclick='javascript:doSummarySheet("summary")'>
      <label for="summary" class="select">
       <strong>Create Summary Sheet</strong>
      </label>
     <table>
      <tr>
       <th><span style="margin-left: 20px"> </span></th>
       <th class="label2">Include Columns</th>
      <tr>
       <td><span style="margin-left: 20px"> </span></td>
       <td class="select">
        <input type='checkbox' name='pinfo' 
               onclick='javascript:doSummarySheet()' id='E1' CHECKED>
        <label for="E1">Phone</label>
       </td>
      </tr>
      <tr>
       <td> </td>
       <td class="select">
        <input type='checkbox' name='finfo' 
               onclick='javascript:doSummarySheet()' id='E2'>
        <label for="E2">Fax</label>
       </td>
      </tr>
      <tr>
       <td> </td>
       <td class="select">
        <input type='checkbox' name='einfo' 
               onclick='javascript:doSummarySheet()' id='E3'>
        <label for="E3">Email</label>
       </td>
      </tr>
      <tr>
       <td> </td>
       <td class="select">
        <input type='checkbox' name='cinfo' 
               onclick='javascript:doSummarySheet()' id='E4'>
        <label for="E4">CDR-ID</label>
       </td>
      </tr>
      <tr>
       <td> </td>
       <td class="select">
        <input type='checkbox' name='dinfo' 
               onclick='javascript:doSummarySheet()' id='E5'>
        <label for="E5">Start Date</label>
       </td>
      </tr>
      <tr>
       <td> </td>
       <td class="select">
        <input type='checkbox' name='govemp' 
               onclick='javascript:doSummarySheet()' id='E7'>
        <label for="E7">Government Employee</label>
       </td>
      </tr>
      <!--
      <tr>
       <td> </td>
       <td class="select">
        <input type='checkbox' name='honoraria' 
               onclick='javascript:doSummarySheet()' id='E8'>
        <label for="E8">Receives Honoraria</label>
       </td>
      </tr>
      -->
      <tr>
       <td> </td>
       <td class="select">
        <input type='checkbox' name='blank' 
               onclick='javascript:doSummarySheet()' id='E6'>
        <label for="E6">Blank Column</label>
       </td>
      </tr>
     </table>
    </td>
   </tr>
   </table>
  </form>
 </body>
</html>
""" % (cdrcgi.SESSION, session, getBoardPicklist())
    cdrcgi.sendPage(header + form)

#----------------------------------------------------------------------
# Get the board's name from its ID.
#----------------------------------------------------------------------
boardName = getBoardName(boardId)

#----------------------------------------------------------------------
# Object for one PDQ board member.
#----------------------------------------------------------------------
class BoardMember:
    now = time.strftime("%Y-%m-%d")
    def __init__(self, docId, eic_start, eic_finish, term_start, name):
        self.id        = docId
        self.name      = cleanTitle(name)
        self.isEic     = (eic_start and eic_start <= BoardMember.now and
                          (not eic_finish or eic_finish > BoardMember.now))
        self.eicSdate  = eic_start
        self.eicEdate  = eic_finish
        self.termSdate = term_start
    def __cmp__(self, other):
        if self.isEic == other.isEic:
            return cmp(self.name.upper(), other.name.upper())
        elif self.isEic:
            return -1
        return 1
    
#----------------------------------------------------------------------
# Select the list of board members associated to a board (passed in
# by the selection of the user) along with start/end dates.
#----------------------------------------------------------------------
try:
    cursor.execute("""\
 SELECT DISTINCT member.doc_id, eic_start.value, eic_finish.value, 
                 term_start.value, person_doc.title
            FROM query_term member
            JOIN query_term curmemb
              ON curmemb.doc_id = member.doc_id
             AND LEFT(curmemb.node_loc, 4) = LEFT(member.node_loc, 4)
            JOIN query_term person
              ON person.doc_id = member.doc_id
            JOIN document person_doc
              ON person_doc.id = person.doc_id
 LEFT OUTER JOIN query_term eic_start
              ON eic_start.doc_id = member.doc_id
             AND LEFT(eic_start.node_loc, 4) = LEFT(member.node_loc, 4)
             AND eic_start.path   = '/PDQBoardMemberInfo/BoardMembershipDetails'
                              + '/EditorInChief/TermStartDate'
 LEFT OUTER JOIN query_term eic_finish
              ON eic_finish.doc_id = member.doc_id  
             AND LEFT(eic_finish.node_loc, 4) = LEFT(member.node_loc, 4)
             AND eic_finish.path  = '/PDQBoardMemberInfo/BoardMembershipDetails'
                              + '/EditorInChief/TermEndDate'
 LEFT OUTER JOIN query_term term_start
              ON term_start.doc_id = member.doc_id
             AND LEFT(term_start.node_loc, 4) = LEFT(member.node_loc, 4)
             AND term_start.path = '/PDQBoardMemberInfo/BoardMembershipDetails'
                              + '/TermStartDate'
           WHERE member.path  = '/PDQBoardMemberInfo/BoardMembershipDetails'
                              + '/BoardName/@cdr:ref'
             AND curmemb.path = '/PDQBoardMemberInfo/BoardMembershipDetails'
                              + '/CurrentMember'
             AND person.path  = '/PDQBoardMemberInfo/BoardMemberName/@cdr:ref'
             AND curmemb.value = 'Yes'
             AND person_doc.active_status = 'A'
             AND member.int_val = ?""", boardId, timeout = 300)
    rows = cursor.fetchall()
    boardMembers = []
    boardIds     = []
    for docId, eic_start, eic_finish, term_start, name in rows:
        boardMembers.append(BoardMember(docId, eic_start, eic_finish, 
                                               term_start, name))
        boardIds.append(docId)
    boardMembers.sort()

except cdrdb.Error, info:
    cdrcgi.bail('Database query failure: %s' % info[1][0])

# ---------------------------------------------------------------
# Create the HTML Output Page
# ---------------------------------------------------------------
html = """\
<!DOCTYPE HTML PUBLIC '-//W3C//DTD HTML 4.01 Transitional//EN'
                      'http://www.w3.org/TR/html4/loose.dtd'>
<html>
 <head>
  <title>PDQ Board Member Roster Report - %s</title>
  <meta http-equiv='Content-Type' content='text/html; charset=UTF-8'>
  <style type='text/css'>
   h1       { font-family: Arial, sans-serif; 
              font-size: 16pt;
              text-align: center; 
              font-weight: bold; }
   h2       { font-family: Arial, sans-serif; 
              font-size: 14pt;
              text-align: center; 
              font-weight: bold; }
   p        { font-family: Arial, sans-serif; 
              font-size: 12pt; }
   #summary td, #summary th
            { border: 1px solid black; }
   #hdg     { font-family: Arial, sans-serif; 
              font-size: 16pt;
              font-weight: bold; 
              text-align: center; 
              padding-bottom: 20px;
              border: 0px; }
   #summary { border: 0px; }

   /* The Board Member Roster information is created via a global */
   /* template for Persons.  The italic display used for the QC   */
   /* report does therefore need to be suppressed here.           */
   /* ----------------------------------------------------------- */
   I        { font-family: Arial, sans-serif; font-size: 12pt; 
              font-style: normal; }
   span.SectionRef { text-decoration: underline; font-weight: bold; }

   .theader { background-color: #CFCFCF; }
   .name    { font-weight: bold; 
              vertical-align: top; }
   .phone, .email, .fax, .cdrid
            { vertical-align: top; }
   .blank   { width: 100px; }
   #main    { font-family: Arial, Helvetica, sans-serif;
              font-size: 12pt; }
  </style>
 </head>  
 <body id="main">
""" % boardName

if flavor == 'full':
    html += """
   <h1>%s<br><span style="font-size: 12pt">%s</span></h1>
""" % (boardName, dateString)   

count = 0
for boardMember in boardMembers:
    response = cdr.filterDoc('guest',
                             ['set:Denormalization PDQBoardMemberInfo Set',
                              'name:Copy XML for Person 2',
                              filterType[flavor]],
                             boardMember.id,
                             parm = [['otherInfo', otherInfo],
                                     ['assistant', assistant],
                                     ['subgroup',  subgroup],
                                     ['eic',
                                      boardMember.isEic and 'Yes' or 'No']])
    if type(response) in (str, unicode):
        cdrcgi.bail("%s: %s" % (boardMember.id, response))

    # If we run the full report we just attach the resulting HTML 
    # snippets to the previous output.  
    # For the summary sheet we still need to extract the relevant
    # information from the HTML snippet
    #
    # We need to wrap each person in a table in order to prevent
    # page breaks within address blocks after the convertion to 
    # MS-Word.
    # -----------------------------------------------------------
    if flavor == 'full':
        html += u"""
        <table width='100%%'>
         <tr>
          <td>%s<td>
         </tr>
        </table>""" % unicode(response[0], 'utf-8')
    else:
        row = extractSheetInfo(response[0])
        row = row + [boardMember.id] + [boardMember.termSdate]
        allRows.append(row)
 
# Create the HTML table for the summary sheet
# -------------------------------------------
if flavor == 'summary':
    allRows = addSpecificContactInfo(boardIds, allRows)
    out  = makeSheet(allRows)
    html += u"""\
       <table id="summary" cellspacing="0" cellpadding="5">
        <tr>
         <td id="hdg" colspan="%d">%s<br>
           <span style="font-size: 12pt">%s</span>
         </td>
        </tr>
        %s
       </table>
""" % (out[1], boardName, dateString, out[0])   

    if govEmp == 'Yes':
        html += u"""\
       <b>* - Honoraria Declined</b>
       <br/>"""

boardManagerInfo = getBoardManagerInfo(boardId)

html += u"""
  <br>
  <table width='100%%'>
   <tr>
    <td>
     <b><u>Board Manager Information</u></b><br>
     <b>%s</b><br>
     Office of Cancer Content Management (OCCM)<br>
     Office of Communications and Education<br>
     National Cancer Institute<br>
     9609 Medical Center Drive, MSC 9760<br>
     Rockville, MD 20850<br><br>
     <table border="0" width="100%%" cellspacing="0" cellpadding="0">
      <tr>
       <td width="35%%">Phone</td>
       <td width="65%%">%s</td>
      </tr>
      <tr>
       <td>Fax</td>
       <td>240-276-7679</td>
      </tr>
      <tr>
       <td>Email</td>
       <td><a href="mailto:%s">%s</a></td>
      </tr>
     </table>
       </td>
   </tr>
  </table>
 </body>   
</html>    
""" % (boardManagerInfo and boardManagerInfo[0][1] or 'No Board Manager', 
       boardManagerInfo and boardManagerInfo[2][1] or 'TBD',
       boardManagerInfo and boardManagerInfo[1][1] or 'TBD', 
       boardManagerInfo and boardManagerInfo[1][1] or 'TBD')

# The users don't want to display the country if it's the US.
# Since the address is build by a common address module we're
# better off removing it in the final HTML output
# ------------------------------------------------------------
cdrcgi.sendPage(html.replace('U.S.A.<br>', ''))
