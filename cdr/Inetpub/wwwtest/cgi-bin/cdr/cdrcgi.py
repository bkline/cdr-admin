#----------------------------------------------------------------------
#
# $Id: cdrcgi.py,v 1.5 2001-12-01 17:55:45 bkline Exp $
#
# Common routines for creating CDR web forms.
#
# $Log: not supported by cvs2svn $
# Revision 1.4  2001/06/13 22:33:10  bkline
# Added logout and mainMenu functions.
#
# Revision 1.3  2001/04/08 22:52:42  bkline
# Added code for mapping to/from UTF-8.
#
# Revision 1.2  2001/03/27 21:15:27  bkline
# Paramaterized body background for HTML; added RCS Log keyword.
#
#----------------------------------------------------------------------

#----------------------------------------------------------------------
# Import external modules needed.
#----------------------------------------------------------------------
import cgi, cdr, sys, codecs, re

#----------------------------------------------------------------------
# Create some useful constants.
#----------------------------------------------------------------------
USERNAME = "UserName"
PASSWORD = "Password"
SESSION  = "Session"
REQUEST  = "Request"
DOCID    = "DocId"
FILTER   = "Filter"
FORMBG   = '/images/back.jpg'
BASE     = '/cgi-bin/cdr'
WEBSERVER= 'mmdb2.nci.nih.gov'
HEADER   = """\
<!DOCTYPE HTML PUBLIC '-//IETF//DTD HTML//EN'>
<HTML>
 <HEAD>
  <TITLE>%s</TITLE>
 </HEAD>
 <BASEFONT FACE='Arial, Helvetica, sans-serif'>
 <LINK REL='STYLESHEET' HREF='/stylesheets/dataform.css'>
 <BODY BGCOLOR='EEEEEE'>
  <FORM ACTION='/cgi-bin/cdr/%s' METHOD='POST'>
   <TABLE WIDTH='100%%' CELLSPACING='0' CELLPADDING='0' BORDER='0'>
    <TR>
     <TH NOWRAP BGCOLOR='silver' ALIGN='left' BACKGROUND='/images/nav1.jpg'>
      <FONT SIZE='6' COLOR='white'>&nbsp;%s</FONT>
     </TH>
"""
B_CELL = """\
     <TD BGCOLOR='silver'
         VALIGN='middle'
         ALIGN='right'
         WIDTH='100%'
         BACKGROUND='/images/nav1.jpg'>
"""
BUTTON = """\
      <INPUT TYPE='submit' NAME='%s' VALUE='%s'>&nbsp;
"""
SUBBANNER = """\
    </TR>
    <TR>
     <TD BGCOLOR='#FFFFCC' COLSPAN='3'>
      <FONT SIZE='-1' COLOR='navy'>&nbsp;%s<BR></FONT>
     </TD>
    </TR>
   </TABLE>
"""

#----------------------------------------------------------------------
# Display the header for a CDR web form.
#----------------------------------------------------------------------
def header(title, banner, subBanner, script = '', buttons = None, bkgd = '',
           numBreaks = 2):
    html = HEADER % (title, script, banner)
    if buttons:
        html = html + B_CELL
        for button in buttons:
            if button == "Load":
                html = html + "      <INPUT NAME='DocId' SIZE='14'>&nbsp;\n"
            html = html + BUTTON % (REQUEST, button)
        html = html + "     </TD>\n"
    html = html + SUBBANNER % subBanner
    return html + numBreaks * "   <BR>\n"

#----------------------------------------------------------------------
# Get a session ID based on current form field values.
#----------------------------------------------------------------------
def getSession(fields):

    # If we already have a Session field value, use it.
    if fields.has_key(SESSION):
        session = fields[SESSION].value
        if len(session) > 0:
            return session

    # Check for missing fields.
    if not fields.has_key(USERNAME) or not fields.has_key(PASSWORD):
        return None
    userId = fields[USERNAME].value
    password = fields[PASSWORD].value
    if len(userId) == 0 or len(password) == 0:
        return None

    # Log on to the CDR Server.
    session = cdr.login(userId, password)
    if session.find("<Err") >= 0: return None
    else:                         return session

#----------------------------------------------------------------------
# Get the name of the submitted request.
#----------------------------------------------------------------------
def getRequest(fields):

    # Make sure the request field exists.
    if not fields.has_key(REQUEST): return None
    else:                           return fields[REQUEST].value

#----------------------------------------------------------------------
# Send an HTML page back to the client.
#----------------------------------------------------------------------
def sendPage(page):
    print "Content-type: text/html\n\n" + page
    sys.exit(0)

#----------------------------------------------------------------------
# Emit an HTML page containing an error message and exit.
#----------------------------------------------------------------------
def bail(message, banner = "CDR Web Interface"):
    page = header("CDR Error", banner, "An error has occured", "", [])
    page = page + "<B>%s</B></FORM></BODY></HTML>" % message
    sendPage(page)
    sys.exit(0)

#----------------------------------------------------------------------
# Encode XML for transfer to the CDR Server using utf-8.
#----------------------------------------------------------------------
def encode(xml): return unicode(xml, 'latin-1').encode('utf-8')

#----------------------------------------------------------------------
# Convert CDR Server's XML from utf-8 to latin-1 encoding.
#----------------------------------------------------------------------
decodePattern = re.compile(u"([\u0080-\uffff])")
def decode(xml): 
    return re.sub(decodePattern, 
                  lambda match: u"&#x%X;" % ord(match.group(0)[0]), 
                  unicode(xml, 'utf-8')).encode('latin-1')

#----------------------------------------------------------------------
# Log out of the CDR session and put up a new login screen.
#----------------------------------------------------------------------
def logout(session):

    # Make sure we have a session to log out of.
    if not session: bail('No session found.')

    # Create the page header.
    title   = "CDR Administration"
    section = "Login Screen"
    buttons = ["Log In"]
    hdr     = header(title, title, section, "Admin.py", buttons)

    # Perform the logout.
    error = cdr.logout(session)
    message = error or "Session Logged Out Successfully"

    # Put up the login screen.
    form = """\
        <H3>%s</H3>
           <TABLE CELLSPACING='0' 
                  CELLPADDING='0' 
                  BORDER='0'>
            <TR>
             <TD ALIGN='right'>
              <B>CDR User ID:&nbsp;</B>
             </TD>
             <TD><INPUT NAME='UserName'></TD>
            </TR>
            <TR>
             <TD ALIGN='right'>
              <B>CDR Password:&nbsp;</B>
             </TD>
             <TD><INPUT NAME='Password' 
                        TYPE='password'>
             </TD>
            </TR>
           </TABLE>
          </FORM>
         </BODY>
        </HTML>\n""" % message

    sendPage(hdr + form)

#----------------------------------------------------------------------
# Display the CDR Administation Main Menu.
#----------------------------------------------------------------------
def mainMenu(session, news = None):

    session = "?%s=%s" % (SESSION, session)
    title   = "CDR Administration"
    section = "Main Menu"
    buttons = []
    hdr     = header(title, title, section, "", buttons)

    extra = news and ("<H2>%s</H2>\n" % news) or ""
    menu = """\
     <OL>
      <LI><A HREF='%s/EditGroups.py%s'>Manage Groups</A></LI>
      <LI><A HREF='%s/EditUsers.py%s'>Manage Users</A></LI>
      <LI><A HREF='%s/EditActions.py%s'>Manage Actions</A></LI>
      <LI><A HREF='%s/EditDoctypes.py%s'>Manage Document Types</A></LI>
      <LI><A HREF='%s/EditCSSs.py%s'>Manage CSS Stylesheets</A></LI>
      <LI><A HREF='%s/EditQueryTermDefs.py%s'>Manage Query Term Definitions</A></LI>
      <LI><A HREF='%s/EditLinkControl.py%s'>Manage Linking Tables</A></LI>
      <LI><A HREF='%s/Publishing.py%s'>Publishing</A></LI>
      <LI><A HREF='%s/Reports.py%s'>Reports</A></LI>
      <LI><A HREF='%s/Mailers.py%s'>Mailers</A></LI>
      <LI><A HREF='%s/MergeProt.py%s'>Merge Protocol</A></LI>
      <LI><A HREF='%s/Logout.py%s'>Log Out</A></LI>
     </OL>
    """ % (BASE, session,
           BASE, session,
           BASE, session,
           BASE, session,
           BASE, session,
           BASE, session,
           BASE, session,
           BASE, session,
           BASE, session,
           BASE, session,
           BASE, session,
           BASE, session)

    sendPage(hdr + extra + menu + "</FORM></BODY></HTML>")

#----------------------------------------------------------------------
# Determine whether query contains unescaped wildcards.
#----------------------------------------------------------------------
def getQueryOp(query):
    escaped = 0
    for char in query:
        if char == '\\':
            escaped = not escaped
        elif not escaped and char in "_%": return "LIKE"
    return "="

#----------------------------------------------------------------------
# Escape single quotes in string.
#----------------------------------------------------------------------
def getQueryVal(val):
    return val.replace("'", "''")

#----------------------------------------------------------------------
# Query components.
#----------------------------------------------------------------------
class SearchField:
    def __init__(self, var, selectors):
        self.var       = var
        self.selectors = selectors

#----------------------------------------------------------------------
# Generate picklist for document publication status valid values.
#----------------------------------------------------------------------
def pubStatusList(conn, fName):
    return """\
      <SELECT NAME='%s'>
       <OPTION VALUE='' SELECTED>&nbsp;</OPTION>
       <OPTION VALUE='A'>Ready For Publication &nbsp;</OPTION>
       <OPTION VALUE='I'>Not Ready For Publication &nbsp;</OPTION>
      </SELECT>
""" % fName

#----------------------------------------------------------------------
# Generate picklist for countries.
#----------------------------------------------------------------------
def countryList(conn, fName):
    try:
        cursor = conn.cursor()
        query  = """\
  SELECT d.id, d.title
    FROM document d
    JOIN doc_type t
      ON t.id = d.doc_type
   WHERE t.name = 'GeographicEntity'
ORDER BY d.title
"""
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        cursor = None
    except cdrdb.Error, info:
        bail('Failure retrieving country list from CDR: %s' % info[1][0])
    html = """\
      <SELECT NAME='%s'>
       <OPTION VALUE='' SELECTED>&nbsp;</OPTION>
""" % fName
    for row in rows:
        html += """\
       <OPTION VALUE='CDR%010d'>%s &nbsp;</OPTION>
""" % (row[0], row[1])
    html += """\
      </SELECT>
"""
    return html
        
#----------------------------------------------------------------------
# Generate picklist for states.
#----------------------------------------------------------------------
def stateList(conn, fName):
    try:
        cursor = conn.cursor()
        query  = """\
SELECT DISTINCT c.id, 
                c.title, 
                state_name.value,
                frag_id.value,
                short_name.value
           FROM document c
           JOIN doc_type t
             ON (t.id = c.doc_type)
           JOIN query_term state_name
             ON (state_name.doc_id = c.id)
           JOIN query_term frag_id
             ON (frag_id.doc_id = c.id
            AND frag_id.node_loc = LEFT(state_name.node_loc, 4))
LEFT OUTER JOIN query_term short_name
             ON short_name.doc_id = c.id
          WHERE t.name = 'GeographicEntity'
            AND state_name.path = '/GeographicEntity/PoliticalUnit' +
                                  '/PoliticalUnitFullName'
            AND frag_id.path    = '/GeographicEntity/PoliticalUnit/@cdr:id'
            AND short_name.path = '/GeographicEntity/CountryShortName'
       ORDER BY state_name.value
"""
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        cursor = None
    except cdrdb.Error, info:
        bail('Failure retrieving state list from CDR: %s' % info[1][0])
    html = """\
      <SELECT NAME='%s'>
       <OPTION VALUE='' SELECTED>&nbsp;</OPTION>
""" % fName
    for row in rows:
        cName = row[4] and row[4] or row[1]
        html += """\
       <OPTION VALUE='CDR%010d#%s'>%s [%s]&nbsp;</OPTION>
""" % (row[0], row[3], row[2], cName)
    html += """\
      </SELECT>
"""
    return html

#----------------------------------------------------------------------
# Generate the top portion of an advanced search form.
#----------------------------------------------------------------------
def startAdvancedSearchPage(session, title, script, fields, buttons, subtitle,
                            conn):

    html = """\
<!DOCTYPE HTML PUBLIC '-//IETF//DTD HTML//EN'>
<HTML>
 <HEAD>
  <TITLE>%s</TITLE>
  <META         HTTP-EQUIV  = "Content-Type"
                CONTENT     = "text/html; charset=iso-8859-1">
  <STYLE        TYPE        = "text/css">
   <!--
    .Page { font-family: Arial, Helvietica, sans-serif; color: #000066 }
   -->
  </STYLE>
 </HEAD>
 <BODY          BGCOLOR     = "#CCCCFF">
  <FORM         METHOD      = "POST"
                ACTION      = "%s/%s">
   <INPUT       TYPE        = "hidden"
                NAME        = "%s"
                VALUE       = "%s">
   <TABLE       WIDTH       = "100%%"
                BORDER      = "0"
                CELLSPACING = "0">
    <TR         BGCOLOR     = "#6699FF">
     <TD        NOWRAP
                HEIGHT      = "26"
                COLSPAN     = "2">
      <FONT     SIZE        = "+2"
                CLASS       = "Page">CDR Advanced Search</FONT>
     </TD>
    </TR>
    <TR         BGCOLOR     = "#FFFFCC">
     <TD        NOWRAP
                COLSPAN     = "2">
      <FONT     SIZE        = "+1"
                CLASS       = "Page">%s</FONT>
     </TD>
    <TR>
    <TR>
     <TD        NOWRAP
                COLSPAN     = "2">&nbsp;</TD>
    </TR>
""" % (title, BASE, script, SESSION, session, subtitle)

    for field in fields:
        if len(field) == 2:
            html += """\
    <TR>
     <TD        NOWRAP
                ALIGN       = "right"
                CLASS       = "Page">%s &nbsp; </TD>
     <TD        WIDTH       = "55%%"
                ALIGN       = "left">
      <INPUT    TYPE        = "text"
                NAME        = "%s"
                SIZE        = "60">
     </TD>
    </TR>
""" % field
        else:
            html += """\
    <TR>
     <TD        NOWRAP
                ALIGN       = "right"
                CLASS       = "Page">%s &nbsp; </TD>
     <TD        WIDTH       = "55%%"
                ALIGN       = "left">
%s
     </TD>
    </TR>
""" % (field[0], field[2](conn, field[1]))

    html += """\
    <TR>
     <TD        NOWRAP
                WIDTH       = "15%"
                CLASS       = "Page"
                VALIGN      = "top"
                ALIGN       = "right">Search Connector &nbsp; </TD>
     <TD        WIDTH       = "30%"
                ALIGN       = "left">
      <SELECT   NAME        = "Boolean"
                SIZE        = "1">
       <OPTION  SELECTED>AND</OPTION>
       <OPTION>OR</OPTION>
      </SELECT>
     </TD>
    </TR>
    <TR>
     <TD        WIDTH       = "15%">&nbsp;</TD>
     <TD        WIDTH       = "55%">&nbsp;</TD>
    </TR>
   </TABLE>
   <TABLE       WIDTH       = "100%"
                BORDER      = "0">
    <TR>
     <TD        COLSPAN     = "2">&nbsp; </TD>
"""

    for button in buttons:
        html += """\
     <TD        WIDTH       = "13%%"
                ALIGN       = "center">
      <INPUT    TYPE        = "%s"
                NAME        = "%s"
                VALUE       = "%s">
     </TD>
""" % button

    html += """\
     <TD        WIDTH       = "33%">&nbsp;</TD>
    </TR>
   </TABLE>
   <BR>
"""

    return html

#----------------------------------------------------------------------
# Construct query for advanced search page.
#----------------------------------------------------------------------
def constructAdvancedSearchQuery(searchFields, boolOp, docType):
    where   = ""
    strings = ""
    aliases = 0
    qtUsed  = 0
    boolOp  = boolOp == "AND" and " AND " or " OR "
    for searchField in searchFields:
        if searchField.var:
            queryOp  = getQueryOp(searchField.var)
            queryVal = getQueryVal(searchField.var)
            if strings: strings += ' '
            strings += queryVal.strip()
            if where:
                where += boolOp
            else:
                where = "WHERE ("
            if type(searchField.selectors) == type(""):
                where += "(document.%s %s '%s')" % (searchField.selectors,
                                                   queryOp,
                                                   queryVal)
                continue
            part = "("
            partOp = ""
            qtUsed = 1
            if boolOp == " AND ":
                aliases += 1
                alias = "q%d" % aliases
            for selector in searchField.selectors:
                pathOp = selector.find("%") == -1 and "=" or "LIKE"
                part += partOp
                if boolOp == " AND ":
                    part += "(%s.path %s '%s' "\
                            "AND %s.value %s '%s' "\
                            "AND %s.doc_id = document.id)" % (
                            alias, pathOp, selector,
                            alias, queryOp, queryVal,
                            alias)
                else:
                    part += "(q.path %s '%s' AND q.value %s '%s')" % (
                              pathOp,
                              selector,
                              queryOp,
                              queryVal)
                partOp = " OR "
            where += part + ")"
    if not where:
        return (None, None)
    if type(docType) == type(""):
        where += ") AND (document.doc_type = doc_type.id "\
                  " AND doc_type.name = '%s') " % docType
        query = 'SELECT DISTINCT document.id, document.title '\
                           'FROM document, doc_type'
    else:
        where += ") AND (document.doc_type = doc_type.id "\
                  " AND doc_type.name IN ("
        sep = ""
        for dt in docType:
            where += "%s'%s'" % (sep, dt)
            sep = ","
        where += "))"
        query = 'SELECT DISTINCT document.id, document.title, doc_type.name '\
                           'FROM document, doc_type'
        
    if boolOp == " AND ":
        for a in range(aliases):
            query += ", query_term q%d" % (a + 1)
    elif qtUsed:
        query += ", query_term q"
        where += "AND document.id = q.doc_id "
    query += " " + where + "ORDER BY document.title"
    return (query, strings)

#----------------------------------------------------------------------
# Construct top of HTML page for advanced search results.
#----------------------------------------------------------------------
def advancedSearchResultsPageTop(docType, nRows, strings):
    return """\
<!DOCTYPE HTML PUBLIC '-//IETF//DTD HTML//EN'>
<HTML>
 <HEAD>
  <TITLE>CDR %s Search Results</TITLE>
  <META   HTTP-EQUIV = "Content-Type" 
             CONTENT = "text/html; charset=iso-8859-1">
  <STYLE        TYPE = "text/css">
   <!--
    .Page { font-family: Arial, Helvetica, sans-serif; color: #000066 }
    :link { color: navy }
    :link:visited { color: navy }
   -->
  </STYLE>
 </HEAD>
 <BODY       BGCOLOR = "#CCCCFF">
  <TABLE       WIDTH = "100%%" 
              BORDER = "0" 
         CELLSPACING = "0" 
               CLASS = "Page">
   <TR       BGCOLOR = "#6699FF"> 
    <TD       NOWRAP 
              HEIGHT = "26" 
             COLSPAN = "4">
     <FONT      SIZE = "+2" 
               CLASS = "Page">CDR Advanced Search Results</FONT>
    </TD>
   </TR>
   <TR       BGCOLOR = "#FFFFCC"> 
    <TD       NOWRAP 
             COLSPAN = "4">
     <SPAN     CLASS = "Page">
      <FONT     SIZE = "+1">%s</FONT>
     </SPAN>
    </TD>
   </TR>
   <TR> 
    <TD       NOWRAP 
             COLSPAN = "4"
              HEIGHT = "20">&nbsp;</TD>
   </TR>
   <TR> 
    <TD       NOWRAP
             COLSPAN = "4"
               CLASS = "Page">
     <FONT     COLOR = "#000000">%d documents match '%s'</FONT>
    </TD>
   </TR>
   <TR> 
    <TD       NOWRAP
             COLSPAN = "4"
               CLASS = "Page">&nbsp;</TD>
   </TR>
""" % (docType, docType, nRows, strings)

#----------------------------------------------------------------------
# Construct HTML page for advanced search results.
#----------------------------------------------------------------------
def advancedSearchResultsPage(docType, rows, strings, filter):
    html = advancedSearchResultsPageTop(docType, len(rows), strings)

    for i in range(len(rows)):
        docId = "CDR%010d" % rows[i][0]
        title = rows[i][1]
        dtcol = "<TD>&nbsp;</TD>"
        filt  = filter
        if len(rows[i]) > 2:
            dt = rows[i][2]
            filt = filter[dt]
            dtcol = """\
    <TD       VALIGN = "top">%s</TD>
""" % dt
        html += """\
   <TR>
    <TD       NOWRAP
               WIDTH = "10"
              VALIGN = "top">
     <DIV      ALIGN = "right">%d.</DIV>
    </TD>
    <TD        WIDTH = "75%%">%s</TD>
%s
    <TD        WIDTH = "20"
              VALIGN = "top">
     <A         HREF = "%s?DocId=%s&Filter=%s">%s</A>
    </TD>
   </TR>
""" % (i + 1, cgi.escape(title, 1), dtcol, '/cgi-bin/cdr/Filter.py', 
       docId, filt, docId)
    return html + "  </TABLE>\n </BODY>\n</HTML>\n"
