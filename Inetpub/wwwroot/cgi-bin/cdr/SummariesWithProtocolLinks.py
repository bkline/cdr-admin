#----------------------------------------------------------------------
#
# $Id: SummariesWithProtocolLinks.py
#
# Report on lists of summaries.
#
# $Log: not supported by cvs2svn $
#----------------------------------------------------------------------
import cgi, cdr, cdrcgi, re, string, cdrdb, time, xml.dom.minidom

#----------------------------------------------------------------------
# Set the form variables.
#----------------------------------------------------------------------
fields    = cgi.FieldStorage()
session   = cdrcgi.getSession(fields)
lang      = fields and fields.getvalue("lang")             or None
groups    = fields and fields.getvalue("grp")              or []
statuses    = fields and fields.getvalue("status")         or []
submit    = fields and fields.getvalue("SubmitButton")     or None
request   = cdrcgi.getRequest(fields)
title     = "CDR Administration"
instr     = "Summaries With Protocol Links/Refs Report"
script    = "SummariesWithProtocolLinks.py"
SUBMENU   = "Report Menu"
buttons   = (SUBMENU, cdrcgi.MAINMENU)

#---------------------------
# DEBUG SETTINGS
#---------------------------
#lang = 'English'
#groups.append('Adult Treatment')
#statuses.append('Closed')
#statuses.append('Active')
#session   = '471F2BE9-7A98C6-248-1RFI84EWTK9Z'
#---------------------------

class dataRow:
    def __init__(self,cdrid,summaryTitle,summarySecTitle,ref,protCDRID,status):
        self.cdrid = cdrid
        self.summaryTitle = summaryTitle
        self.summarySecTitle = summarySecTitle
        self.ref = ref
        self.protCDRID = protCDRID
        self.linkcdrid = cdr.normalize(protCDRID)
        self.status = status
        self.protocolLink = ''
        self.fullProtocolLink = ''
        self.text = ''
        self.refTextStart = 0
        self.refTextSize = 0
    
    def addProtocolLink(self,parentElem):
        self.text = ''
        self.addText(parentElem,0)
        self.fullProtocolLink = self.text
        self.protocolLink = self.reduceTo(self.fullProtocolLink,200)

    def addText(self,parentElem,bInLink):
        binlink = 0
        for parentChildNode in parentElem.childNodes:
            if parentChildNode.nodeType == xml.dom.minidom.Node.ELEMENT_NODE:
                if parentChildNode.attributes.length > 0:
                    for (name,value) in parentChildNode.attributes.items():
                        if self.ref == 'LINK':
                            if name == 'cdr:ref':
                                if value == self.linkcdrid:
                                    binlink = 1
                                    href = "<a target='_blank' href = %s/QcReport.py?DocId=%s&Session=%s>" % (cdrcgi.BASE,self.linkcdrid,session)
                                    self.refTextStart = len(self.text)
                                    self.refTextSize = len(href)
                                    self.text += href
                        elif self.ref == 'REF':
                            if name == 'cdr:href':
                                if value == self.linkcdrid:
                                    binlink = 1
                                    href = "<a target='_blank' href = %s/QcReport.py?DocId=%s&Session=%s>" % (cdrcgi.BASE,self.linkcdrid,session)
                                    self.refTextStart = len(self.text)
                                    self.refTextSize = len(href)
                                    self.text += href
                                
            if parentChildNode.nodeType == xml.dom.minidom.Node.TEXT_NODE:
                self.text += parentChildNode.nodeValue + " "
                if bInLink == 1:
                    bInLink = 0
                    self.refTextSize += len(parentChildNode.nodeValue)
                    self.text += "</a>"
            self.addText(parentChildNode,binlink)
            binlink = 0

    def reduceTo(self,text,count):
        startIndex = self.refTextStart - count
        if startIndex < 0:
            startIndex = 0;
        endIndex = self.refTextStart + self.refTextSize + count
        if endIndex > len(text) - 1:
            endIndex = len(text) - 1

        returnText = ''
        if startIndex > 0:
           returnText = '...'
        returnText += text[startIndex:endIndex]
        if endIndex < len(text) - 1:
            returnText += '...'

        return returnText
#----------------------------------------------------------------------
# If the user only picked one summary group, put it into a list so we
# can deal with the same data structure whether one or more were
# selected. Ditto for statuses.
#----------------------------------------------------------------------
if type(groups) in (type(""), type(u"")):
    groups = [groups]
if type(statuses) in (type(""), type(u"")):
    statuses = [statuses]

#----------------------------------------------------------------------
# Handle navigation requests.
#----------------------------------------------------------------------
if request == cdrcgi.MAINMENU:
    cdrcgi.navigateTo("Admin.py", session)
elif request == SUBMENU:
    cdrcgi.navigateTo("reports.py", session)

#----------------------------------------------------------------------
# Build date string for header.
#----------------------------------------------------------------------
dateString = time.strftime("%B %d, %Y")

#----------------------------------------------------------------------
# If we don't have a request, put up the form.
#----------------------------------------------------------------------
if not lang:
    jscript = """
<style type="text/css">
body {
    font-family: sans-serif;
    font-size: 11pt;
    }
legend  {
    font-weight: bold;
    color: teal;
    font-family: sans-serif;
    }
fieldset {
    width: 500px;
    margin-left: auto;
    margin-right: auto;
    display: block;
    }
</style>

<script language='JavaScript' src='/js/scriptaculous/prototype.js'></script>
<script language='JavaScript' src='/js/scriptaculous/scriptaculous.js'></script>
<script type="text/javascript">

Event.observe(window, 'load', function(){
    checkAllEnglish(0);
    checkAllSpanish(0);
    checkAllStatus(0);
    $('All English').checked = 1;
    $('All Status').checked = 1;
    $('English').checked = 1;
});

function isEnglishItemChecked(){
    return ($('All English').checked ||
    $('Adult Treatment').checked ||
    $('Genetics').checked ||
    $('Complementary and Alternative Medicine').checked  ||
    $('Pediatric Treatment').checked ||
    $('Screening and Prevention').checked ||
    $('Supportive Care').checked);
}

function isSpanishItemChecked(){
    return($('All Spanish').checked ||
    $('Spanish Adult Treatment').checked ||
    $('Spanish Pediatric Treatment').checked ||
    $('Spanish Supportive Care').checked);
}

function isStatusItemChecked(){
    return($('All Status').checked ||
    $('Active').checked ||
    $('Approved-not yet active').checked ||
    $('Temporarily closed').checked ||
    $('Closed').checked ||
    $('Completed').checked ||
    $('Withdrawn').checked ||
    $('Withdrawn from PDQ').checked);
}

function checkAllEnglish(checked){
    $('All English').checked = checked;
    $('Adult Treatment').checked = checked;
    $('Genetics').checked = checked;
    $('Complementary and Alternative Medicine').checked = checked;
    $('Pediatric Treatment').checked = checked;
    $('Screening and Prevention').checked = checked;
    $('Supportive Care').checked = checked;    
}

function checkAllSpanish(checked){
    $('All Spanish').checked = checked;
    $('Spanish Adult Treatment').checked = checked;
    $('Spanish Pediatric Treatment').checked = checked;
    $('Spanish Supportive Care').checked = checked;
}

function checkAllStatus(checked){
    $('All Status').checked = checked;
    $('Active').checked = checked;
    $('Approved-not yet active').checked = checked;
    $('Temporarily closed').checked = checked;
    $('Closed').checked = checked;
    $('Completed').checked = checked;
    $('Withdrawn').checked = checked;
    $('Withdrawn from PDQ').checked = checked;
}

function englishItemClicked(){
    $('All English').checked = 0;
    $('English').checked = 1;
    $('Spanish').checked = 0;
    checkAllSpanish(0);
    if (!isEnglishItemChecked())
        $('All English').checked = 1;
}

function spanishItemClicked(){
    $('All Spanish').checked = 0;
    $('Spanish').checked = 1;
    $('English').checked = 0;
    checkAllEnglish(0);
    if (!isSpanishItemChecked())
        $('All Spanish').checked = 1;
}

function statusItemClicked(){
    $('All Status').checked = 0;
    if (!isStatusItemChecked())
        $('All Status').checked = 1;
}

function langClicked(lang){
    checkAllEnglish(0);
    checkAllSpanish(0);
    if (lang == 'English'){
        $('All English').disabled = 0;
        $('All English').checked = 1;
    }
    else{
        $('All Spanish').disabled = 0;
        $('All Spanish').checked = 1;
    }
}

function allEnglishClicked(){
    checkAllEnglish(0);
    checkAllSpanish(0);
    $('English').checked = 1;
    $('All English').checked = 1;
}

function allSpanishClicked(){
    checkAllEnglish(0);
    checkAllSpanish(0);
    $('Spanish').checked = 1;
    $('All Spanish').checked = 1;
}

function allStatusClicked(){
    checkAllStatus(0);
    $('All Status').checked = 1;
}

</script>
"""
    header = cdrcgi.header(title, title, instr + ' - ' + dateString, 
                           script,
                           ("Submit",
                            SUBMENU,
                            cdrcgi.MAINMENU),
                           numBreaks = 1,stylesheet = jscript)
    form   = """\
   <input type='hidden' name='%s' value='%s'>
 
   <fieldset>
    <legend>&nbsp;Select Language and PDQ Summaries&nbsp;</legend>
    <table>
   <tr>
     <td width=100>
      <input id='English' name='lang' type='radio' value='English' onClick="langClicked('English');" CHECKED><b>English</b></input>
     </td>
     <td>
      <b>Select PDQ Summaries: (one or more)</b>
     </td>
    </tr>
    <tr>
     <td></td>
     <td>
      <input type='checkbox' id='All English' name='grp' 
       value='All English' onClick="allEnglishClicked();" CHECKED>
       <b>All English</b></input><br>
      <input type='checkbox' id='Adult Treatment' name='grp' 
       value='Adult Treatment' onClick="englishItemClicked();">
       <b>Adult Treatment</b></input><br>
      <input type='checkbox' id='Genetics' name='grp' 
       value='Genetics' onClick="englishItemClicked();">
       <b>Cancer Genetics</b></input><br>
      <input type='checkbox' name='grp' 
       id='Complementary and Alternative Medicine' onClick="englishItemClicked();"
       value='Complementary and Alternative Medicine'>
       <b>Complementary and Alternative Medicine</b></input><br>
      <input type='checkbox' id='Pediatric Treatment' name='grp' 
       value='Pediatric Treatment' onClick="englishItemClicked();">
       <b>Pediatric Treatment</b></input><br>
      <input type='checkbox' id='Screening and Prevention' name='grp' 
       value='Screening and Prevention' onClick="englishItemClicked();">
       <b>Screening and Prevention</b></input><br>
      <input type='checkbox' id='Supportive Care' name='grp' 
       value='Supportive Care' onClick="englishItemClicked();">
       <b>Supportive and Palliative Care</b><br></input>
     </td>
    </tr>
    </table>
    </fieldset>

    <fieldset>
    <table>
    <tr>
     <td width=100>
      <input id='Spanish' name='lang' type='radio' 
       value='Spanish' onClick="langClicked('Spanish');"><b>Spanish</b></input>
     </td>
     <td>
      <b>Select PDQ Summaries: (one or more)</b>
     </td>
    </tr>
    <tr>
     <td></td>
     <td>
      <input type='checkbox' id='All Spanish' name='grp' 
       value='All Spanish' onClick="allSpanishClicked();">
       <b>All Spanish</b></input><br>
      <input type='checkbox' id='Spanish Adult Treatment' name='grp' 
       value='Spanish Adult Treatment' onClick="spanishItemClicked();">
       <b>Adult Treatment</b></input><br>
      <input type='checkbox' id='Spanish Pediatric Treatment' name='grp' 
       value='Spanish Pediatric Treatment' onClick="spanishItemClicked();">
       <b>Pediatric Treatment</b></input><br>
      <input type='checkbox' id='Spanish Supportive Care' name='grp' 
       value='Spanish Supportive Care' onClick="spanishItemClicked();">
       <b>Supportive and Palliative Care</b></input><br>
     </td>
    </tr>
    </table>
    </fieldset>

    <br>
    <fieldset>
    <legend>&nbsp;Select Trial Status: (one or more)&nbsp;</legend>
    <table>
    <tr>
     <td width=100></td>
     <td>
      <input type='checkbox' id='All Status' name='status' 
       value='All Status' onClick="allStatusClicked();" CHECKED>
       <b>All Status</b></input><br>
      <input type='checkbox' id='Active' name='status' 
       value='Active' onClick="statusItemClicked();">
       <b>Active</b></input><br>
      <input type='checkbox' id='Approved-not yet active' name='status' 
       value='Approved-not yet active' onClick="statusItemClicked();">
       <b>Approved-not yet active</b><br>
      <input type='checkbox' id='Temporarily closed' name='status' 
       value='Temporarily closed' onClick="statusItemClicked();">
       <b>Temporarily closed</b></input><br>
       <input type='checkbox' id='Closed' name='status' 
        value='Closed' onClick="statusItemClicked();">
       <b>Closed</b></input><br>
       <input type='checkbox' id='Completed' name='status' 
        value='Completed' onClick="statusItemClicked();">
       <b>Completed</b></input><br>
       <input type='checkbox' id='Withdrawn' name='status' 
        value='Withdrawn' onClick="statusItemClicked();">
       <b>Withdrawn</b></input><br>
       <input type='checkbox' id='Withdrawn from PDQ' name='status' 
        value='Withdrawn from PDQ' onClick="statusItemClicked();">
       <b>Withdrawn from PDQ</b></input><br>
     </td>
    </tr>    
   </table>
   </fieldset>

  </form>
 </body>
</html>
""" % (cdrcgi.SESSION, session)
    cdrcgi.sendPage(header + form)

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

statusPick=''
for i in range(len(statuses)):
    statusPick += "'" + statuses[i] + "',"

#------------------------------------
# build the query
#------------------------------------
def getQuerySegment(lang,ref):
    query = [u"""SELECT qt.doc_id as cdrid, title.value as summaryTitle, secTitle.value as summarySecTitle,'"""]

    query.append(ref)
    
    query.append(u"""' as ref, qt.int_val as protCDRID, qstatus.value as status,secTitle.node_loc as TitleNodeLoc,
      len(secTitle.node_loc) as TitleNodeLocLen,qt.node_loc as LinkNodeLoc 
      FROM query_term qt
      JOIN query_term title ON qt.doc_id = title.doc_id
      JOIN query_term qstatus ON qt.int_val = qstatus.doc_id
      JOIN query_term secTitle ON qt.doc_id = secTitle.doc_id
      JOIN query_term lang ON qt.doc_id = lang.doc_id """)
    
    if lang == 'English':
        query.append(u""" JOIN query_term board ON qt.doc_id = board.doc_id """)
    else:
        query.append(u""" JOIN query_term qtrans ON qtrans.doc_id = qt.doc_id
                     JOIN query_term board ON qtrans.int_val = board.doc_id """)
    if ref == 'LINK':
        query.append(u""" WHERE qt.path like '/summary/%ProtocolLink/@cdr:ref' """)
    else:
        query.append(u""" WHERE qt.path like '/summary/%ProtocolRef/@cdr:href' """)

    if lang == 'Spanish':
        query.append(u""" AND qtrans.path = '/Summary/TranslationOf/@cdr:ref' """)

    query.append(u"""\
    AND title.path = '/Summary/SummaryTitle'
    AND qstatus.path = '/InScopeProtocol/ProtocolAdminInfo/CurrentProtocolStatus' 
    AND secTitle.path like '/Summary/%SummarySection/Title' 
    AND LEFT(secTitle.node_loc,len(secTitle.node_loc)-4) =  LEFT(qt.node_loc,len(secTitle.node_loc)-4) 
    AND board.path = '/Summary/SummaryMetaData/PDQBoard/Board/@cdr:ref' """)

    allStr = "All " + lang
    if boardPick.find(allStr) == -1:
        query.append(u""" AND board.value in (""")
        query.append(boardPick[:-2])
        query.append(u""") """)

    if statusPick.find("All Status") == -1:
        query.append(u""" AND qstatus.value in (""")
        query.append(statusPick[:-1])
        query.append(u""") """)
    
    query.append(u"""
    AND lang.path = '/Summary/SummaryMetaData/SummaryLanguage'
    AND lang.value = '""")

    query.append(lang)
    
    query.append(u"""'
    AND EXISTS (SELECT 'x'
                   FROM doc_version v
                  WHERE v.id = qt.doc_id AND v.val_status = 'V' 
                    AND v.publishable = 'Y') 
     AND qt.doc_id not in (select doc_id 
                             from doc_info 
                            where doc_status = 'I' 
                              and doc_type = 'Summary')
    """)

    query = u"".join(query)
    return query
      
# -------------------------------------------------------------
# Put all the pieces together for the SELECT statement
# -------------------------------------------------------------

query = getQuerySegment(lang,'LINK') + " UNION " + getQuerySegment(lang,'REF') + " ORDER BY cdrid,status,LinkNodeLoc,TitleNodeLocLen desc"

#cdrcgi.bail(query)

if not query:
    cdrcgi.bail('No query criteria specified')

dataRows = []
cdrids = []

def checkElement(cdrid,node,parentElem,ref,lastSECTitle):
    for dataRow in dataRows:
        if dataRow.cdrid == cdrid:
            if dataRow.summarySecTitle == lastSECTitle:
                Linkcdrid = cdr.normalize(dataRow.protCDRID)
                if node.attributes.length > 0:
                    for (name,value) in node.attributes.items():
                        if ref == 'LINK':
                            if name == 'cdr:ref':
                                if value == Linkcdrid:
                                    if node.childNodes:
                                        for nodeChild in node.childNodes:
                                            if nodeChild == xml.dom.minidom.Node.TEXT_NODE:
                                                if len(nodeChild.Value) == 0:
                                                    nodeChild.Value = 'Protocol Link'
                                    else:
                                        textNode = dom.createTextNode('Protocol Link')
                                        node.appendChild(textNode)
                                    if len(dataRow.protocolLink) == 0:
                                        dataRow.addProtocolLink(parentElem)
                                        return
                        elif ref == 'REF':
                            if name == 'cdr:href':
                                if value == Linkcdrid:
                                    if node.childNodes:
                                        for nodeChild in node.childNodes:
                                            if nodeChild == xml.dom.minidom.Node.TEXT_NODE:
                                                if len(nodeChild.Value) == 0:
                                                    nodeChild.Value = 'Protocol Ref'
                                    else:
                                        textNode = dom.createTextNode('Protocol Ref')
                                        node.appendChild(textNode)
                                    if len(dataRow.protocolLink) == 0:
                                        dataRow.addProtocolLink(parentElem)
                                        return
    return

def checkChildren(cdrid,parentElem,lastSECTitle):
    parentNodeName = parentElem.nodeName
    for node in parentElem.childNodes:
        nodeValue = node.nodeValue
        nodeName = node.nodeName
        if node.nodeType == xml.dom.minidom.Node.ELEMENT_NODE:
            if nodeName == 'ProtocolLink':
                checkElement(cdrid,node,parentElem,'LINK',lastSECTitle)
            elif nodeName == 'ProtocolRef':
                checkElement(cdrid,node,parentElem,'REF',lastSECTitle)
            elif nodeName == 'Title':
                if parentNodeName == 'SummarySection':
                    for chNode in node.childNodes:
                        if chNode.nodeType == xml.dom.minidom.Node.TEXT_NODE:
                            lastSECTitle = chNode.nodeValue
            
        checkChildren(cdrid,node,lastSECTitle)
    return

def updateRefs(cdrid,dom):
    docElem = dom.documentElement
    checkChildren(cdrid,docElem,'')
    return

#----------------------------------------------------------------------
# Submit the query to the database.
#----------------------------------------------------------------------
try:
    conn = cdrdb.connect('CdrGuest')
    cursor = conn.cursor()
    cursor.execute(query,timeout=300)
    rows = cursor.fetchall()
except cdrdb.Error, info:
    cdrcgi.bail('Failure retrieving Summary documents: %s' % info[1][0])
     
if not rows:
    cdrcgi.bail('No Records Found for Selection')

LastLinkNodeLoc = ''

for cdrid,summaryTitle,summarySecTitle,ref,protCDRID,status,TitleNodeLoc,TitleNodeLocLen,LinkNodeLoc in rows:
    if LinkNodeLoc != LastLinkNodeLoc:
        dataRows.append(dataRow(cdrid,summaryTitle,summarySecTitle,ref,protCDRID,status))
        if cdrid not in cdrids:
            cdrids.append(cdrid)
    LastLinkNodeLoc = LinkNodeLoc

for cdrid in cdrids:
    docId = cdr.normalize(cdrid)
    doc = cdr.getDoc(session, docId, checkout = 'N')
    if doc.startswith("<Errors"):
        cdrcgi.bail("<error>Unable to retrieve %s : %s" % (cdrid, doc))
    filter = ['name:Revision Markup Filter']
    doc = cdr.filterDoc(session,filter,docId=docId)
    dom = xml.dom.minidom.parseString(doc[0])
    updateRefs(cdrid,dom)

cursor.close()
cursor = None

# out put the results table
header = cdrcgi.rptHeader(title, instr) 
form   = [u"""\
 <style type="text/css">
table
{
    font-family: Verdana, Tahoma, sans-serif;
    font-size: 8pt;
    text-align: top;
}
th.cdrTable
{
    font-family: Verdana, Tahoma, sans-serif;
    font-size: 8pt;
    text-align: top;
    color: white;
    background: #664;
}
td.cdrTableEven
{
    font-family: Verdana, Tahoma, sans-serif;
    font-size: 8pt;
    text-align: top;
    color: black;
    background: #FFC;
}
td.cdrTableOdd
{
    font-family: Verdana, Tahoma, sans-serif;
    font-size: 8pt;
    text-align: top;
    color: #220;
    background: #FFE;
}
a:link 
{
    color: red; 
    text-decoration: none;
    font-weight: bold;
} /* unvisited link */
a:active 
{
    color: red; 
    text-decoration: none;
    font-weight: bold;
}
a:visited 
{
    color: red;
    text-decoration: none;
    font-weight: bold;
} /* visited link */
a:hover 
{
    color: white; 
    background-color:red; 
    text-decoration: underline;
    font-weight: bold;
} /* mouse over link */

a.selected:link 
{
    color: purple;
    font-style:italic;
    text-decoration: none;
    font-weight: bold;
} /* unvisited link */
a.selected:active 
{
    color: blue;
    font-style:italic;
    text-decoration: none;
    font-weight: bold;
}
a.selected:visited 
{
    color: purple;
    font-style:italic;
    text-decoration: none;
    font-weight: bold;
} /* visited link */
a.selected:hover 
{
    color: white; 
    background-color:purple;
    font-style:italic;
    text-decoration: underline;
    font-weight: bold;
} /* mouse over link */

  </style>
  
   <input type='hidden' name='%s' value='%s'>
    <p style="text-align: center; font-family: Verdana, Tahoma, sans-serif; font-size: 12pt; font-weight: bold; color: #553;">
    Summaries with Protocol Links/Refs Report<br>
    <span style="text-align: center; font-family: Verdana, Tahoma, sans-serif; font-size: 11pt; font-weight: normal; color: #553;">%s</span>
    </p>
   
   <table>
   <tr>
   <th  class="cdrTable">cdrid</th>
   <th  class="cdrTable">Summary Title</th>
   <th  class="cdrTable">Summary Sec Title</th>
   <th  class="cdrTable">Protocol Link/Ref</th>
   <th  class="cdrTable">CDRID</th>
   <th  class="cdrTable">Status</th>
   </tr>
   """ % (cdrcgi.SESSION, session, dateString)]
cssClass = 'cdrTableEven'
for dataRow in dataRows:
    form.append(u"<tr>")
    form.append(u"""<td class="%s">%s</td><td class="%s">%s</td><td class="%s">%s</td>"""
                %(cssClass,dataRow.cdrid,cssClass,dataRow.summaryTitle,cssClass,dataRow.summarySecTitle))
    form.append(u"""<td class="%s"><b>%s :</b> %s</td>""" % (cssClass,dataRow.ref,dataRow.protocolLink))
    form.append(u"""<td class="%s">%s</td><td class="%s">%s</td>""" % (cssClass,dataRow.protCDRID,cssClass,dataRow.status))
    form.append(u"</tr>")
    if cssClass == 'cdrTableEven':
        cssClass = 'cdrTableOdd'
    else:
        cssClass = 'cdrTableEven'
    
form.append(u"""</table>
  </form>
 </body>
</html>
""")
form = u"".join(form)
cdrcgi.sendPage(header + form)