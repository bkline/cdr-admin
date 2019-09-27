#----------------------------------------------------------------------
# Report on lists of drug information summaries.
#
# BZIssue::4887 - New Drug Information Summary Report
#----------------------------------------------------------------------
import cdr, cgi, cdrcgi, time
from cdrapi import db
from html import escape as html_escape

#----------------------------------------------------------------------
# Set the form variables.
#----------------------------------------------------------------------
fields    = cgi.FieldStorage()
session   = cdrcgi.getSession(fields)
# audience  = fields and fields.getvalue("audience")         or "Patient"
displayType = fields and fields.getvalue("displayType")    or None
sortType  = fields and fields.getvalue("sorting")          or "I"
indication = fields and fields.getlist("indication")      or []
singleDrug = fields and fields.getvalue("singledrug")      or None
submit    = fields and fields.getvalue("SubmitButton")     or None
request   = cdrcgi.getRequest(fields)
title     = "CDR Administration"
instr     = 'Drug Indications -- %s.'
script    = "DrugIndicationsReport.py"
SUBMENU   = "Report Menu"
buttons   = (SUBMENU, cdrcgi.MAINMENU)


# -----------------------------------------------------------------
# Functions to create a dictionary with all existing US Brand Names
# The dictionary is in the following format:
#  brandnames[CDR-ID] = [TermName, [BrandName1, BrandName2, ...]]
# -----------------------------------------------------------------
def getBrandNames():
    brandNames = {}
    brandNameQuery = """
        SELECT t.doc_id as "TermId", t.value as "Term", b.value AS "BrandName"
          FROM query_term_pub t
          JOIN query_term_pub d
            ON t.doc_id = d.int_val
           AND d.path   = '/DrugInformationSummary' +
                          '/DrugInfoMetaData'       +
                          '/TerminologyLink/@cdr:ref'
          JOIN query_term_pub b
            ON t.doc_id = b.doc_id
           AND b.path   = '/Term/OtherName/OtherTermName'
          JOIN query_term_pub n
            ON t.doc_id = n.doc_id
           AND n.path   = '/Term/OtherName/OtherNameType'
           AND n.value  = 'US brand name'
           AND left(n.node_loc, 4) = left(b.node_loc, 4)
         WHERE t.path   = '/Term/PreferredName'
         ORDER BY t.value, b.value
"""

    try:
        cursor = conn.cursor()
        cursor.execute(brandNameQuery)
        rows = cursor.fetchall()
        cursor.close()
    except Exception as e:
        cdrcgi.bail('Failure retrieving brand names: %s' % e)

    for row in rows:
        brands = []
        if row[0] in brandNames:
            brandNames[row[0]][1].append(row[2])
        else:
            brandNames[row[0]] = [row[1], [row[2]]]

    return brandNames


# -----------------------------------------------------------------
# Functions to select the indication for a single Drug
# -----------------------------------------------------------------
def getIndications(drugID):
    indicationQuery = """
    SELECT q.value, t.value
          FROM query_term_pub q
          JOIN query_term_pub i
            ON i.doc_id = q.doc_id
           AND i.path   = '/DrugInformationSummary' +
                          '/DrugInfoMetaData/ApprovedIndication/@cdr:ref'
          JOIN query_term_pub t
            ON t.doc_id = i.int_val
           AND t.path   = '/Term/PreferredName'
         WHERE q.doc_id = ?
           AND q.path   = '/DrugInformationSummary' +
                          '/Title'
         ORDER BY t.value
"""

    try:
        cursor = conn.cursor()
        cursor.execute(indicationQuery, (drugID,))
        rows = cursor.fetchall()
        cursor.close()
    except Exception as e:
        cdrcgi.bail('Failure retrieving indications: %s' % e)

    indicationNames = []
    for row in rows:
        indicationNames.append(row[1])

    return (row[0], indicationNames)


# ---------------------------------------------------
#
# ---------------------------------------------------
def createByIndication2(rows, type, names):
    """Return the HTML code to display the Summary Board Header with ID"""
    html = """
    <table>
     <col class="col3">
     <col class="col3">
     <col class="col4">
     <tr>
      <th>Approved Indication</th>
      <th>Drug Name</th>
      <th>Brand Name(s)</th>
     </tr>
"""

    last = ''
    i = 0
    for row in rows:
        i += 1
        html += """
     <tr class='%s'>
      <td valign="top" class="indrow">""" % (i % 2 == 0 and 'even' or 'odd')
        if last == row[1]:
            html += "&nbsp;"
        else:
            html += " %s" % row[1]
        last = row[1]

        html += """</td>
      <td valign="top">
       <span class="indrow">%s (<a href="/cgi-bin/cdr/QcReport.py?Session=guest&\
DocType=DrugInformationSummary&\
DocId=CDR%d&DocVersion=-1">CDR%d</a>)</span><br>
      </td>
""" % (row[2], row[0], row[0])

        query = """
        select int_val
          from query_term_pub
         WHERE doc_id = ?
           AND path = '/DrugInformationSummary' +
                      '/DrugInfoMetaData' +
                      '/TerminologyLink/@cdr:ref'
"""

        cursor.execute(query, (row[0],))
        row = cursor.fetchone()

        html += """
      <td>"""

        if row[0] in names:
            for brand in names[row[0]][1]:
                html += """
       <span class='indrow'>%s</span><br>""" % brand
        else:
            html += "&nbsp;"

        html += """
      </td>
     </tr>"""

    html += """
    </table>
"""

    return html


# ---------------------------------------------------
#
# ---------------------------------------------------
def createByIndication3(rows, type, names):
    """Return the HTML code to display the Summary Board Header with ID"""

    allIndications = {}
    last = 'x'
    i = 0
    html = ""

    # We need to sort the display by indication and also the drug
    # names for each indication.
    # Creating a dictionary from the rows given to list
    #   {indication:[[CDR-ID, Drug1], [CDR-ID, Drug2], ...]}
    # ------------------------------------------------------------
    for row in rows:
        allIndications.setdefault(row[1], []).append([row[0], row[2]])
        i += 1

    html += "<p><b>Indication : Drug</b></p>"

    for indication in sorted(allIndications.keys()):
        html += """\n<span class='indlabel'>%s</span><br>""" % indication

        drugs = sorted(allIndications[indication], key=lambda i: i[1])

        for drug in drugs:
            html += """
       <div class="drug">%s (<a href="/cgi-bin/cdr/QcReport.py?Session=guest&\
DocType=DrugInformationSummary&\
DocId=CDR%d&DocVersion=-1">CDR%d</a>)</div>
""" % (drug[1], drug[0], drug[0])

            if type == 'brand':
                query = """
            select int_val
              from query_term_pub
             WHERE doc_id = ?
               AND path = '/DrugInformationSummary' +
                          '/DrugInfoMetaData' +
                          '/TerminologyLink/@cdr:ref'
"""

                cursor.execute(query, (drug[0],))
                row = cursor.fetchone()

                if row[0] in names:
                    for brand in names[row[0]][1]:
                        html += """
           <div class="brand"><span class='indrow'>%s</span><br></div>""" % brand
                else:
                    html += "&nbsp;"

        html += "\n<br>"
    return html


# ---------------------------------------------------
#
# ---------------------------------------------------
def createByIndication(rows, type, name):
    """The report with brand names is displayed in table
       format, the report without brand names as a list.
       Selecting the module to create the two report types."""

    if type == 'brand':
       html = createByIndication2(rows, type, name)
    else:
       html = createByIndication3(rows, type, name)

    return html


# ---------------------------------------------------
#
# ---------------------------------------------------
def createByIndication1(rows, type, names):
    """Return the HTML code to display the Summary Board Header with ID"""

    last = 'x'
    i = 0
    html = ""
    sortrows = sorted(rows, key=lambda i: i[2])

    for row in rows:
        i += 1
        if last == row[1]:
            html += ""
        else:
            html += """
    <br><b>Indication: </b>%s<br>""" % row[1]
        last = row[1]

        html += """
       <div class="drug">%s (<a href="/cgi-bin/cdr/QcReport.py?Session=guest&\
DocType=DrugInformationSummary&\
DocId=CDR%d&DocVersion=-1">CDR%d</a>)</div>
""" % (row[2], row[0], row[0])

        if type == 'brand':
            query = """
        select int_val
          from query_term_pub
         WHERE doc_id = ?
           AND path = '/DrugInformationSummary' +
                      '/DrugInfoMetaData' +
                      '/TerminologyLink/@cdr:ref'
"""

            cursor.execute(query, (row[0],))
            row = cursor.fetchone()

            if row[0] in names:
                for brand in names[row[0]][1]:
                    html += """
       <div class="brand"><span class='indrow'>%s</span><br></div>""" % brand
            else:
                html += "&nbsp;"

    return html


# ---------------------------------------------------
#
# ---------------------------------------------------
def createByDrug(rows, type, names):
    """Return the HTML code to display the Summary Board Header with ID"""
    html = """
    <table>
     <col class="cdrid">
     <col class="col1">
     <col class="col2">
     <tr>
      <th>CDR ID</th>"""

    if type == 'brand':
        html += """
      <th>Drug Name (Brand name)</th>"""
    else:
        html += """
      <th>Drug Name</th>"""

    html += """
      <th>Approved Indication</th>
     </tr>
"""

    allDrugs = {}
    last = 'x'
    i = 0

    # Create a dictionary of the format
    # D = { CDR-ID : [ Drug, [Indication1, Indication2, ...]]}
    # --------------------------------------------------------
    for row in rows:
        if row[0] in allDrugs:
            allDrugs[row[2]][1].append(row[1])
        else:
            allDrugs[row[2]] = [row[0], [row[1]]]

    # Create the HTML output for each row
    # -----------------------------------
    for drug in sorted(allDrugs.keys()):
        i += 1
        html += """
     <tr class='%s'>
      <td valign="top" class="indrow"><a href="/cgi-bin/cdr/QcReport.py?Session=guest&\
DocType=DrugInformationSummary&\
DocId=CDR%d&DocVersion=-1">CDR%d</a></td>
      <td valign="top" class="indrow">%s""" % (i % 2 == 0 and 'even' or 'odd',
                                               allDrugs[drug][0],
                                               allDrugs[drug][0], drug)

        # Add the brand names
        # -------------------
        query = """
    select q.int_val, i.value
      from query_term_pub q
      JOIN query_term_pub i
        ON i.doc_id = q.doc_id
       AND i.path = '/DrugInformationSummary' +
                    '/DrugInfoMetaData'       +
                    '/ApprovedIndication'
     WHERE q.doc_id = ?
       AND q.path = '/DrugInformationSummary' +
                  '/DrugInfoMetaData' +
                  '/TerminologyLink/@cdr:ref'
     ORDER BY i.value
"""

        cursor.execute(query, (allDrugs[drug][0],))
        bRows = cursor.fetchall()
        #cdrcgi.bail(bRows)

        if type == 'brand':
            if bRows[0][0] in names:
                html += " <span class='brand'>(%s)</span>" %\
                            ', '.join(x for x in names[bRows[0][0]][1])

        html += """
      </td>
      <td>"""
        for ind in bRows:
            html += """
        <span class='indrow'>%s<br></span>""" % ind[1]

        html += """
      </td>"""

        html += """
     </tr>"""

    html += """
    </table>
"""

    return html


# =====================================================================
# Main starts here
# =====================================================================
# Handle navigation requests.
#----------------------------
if request == cdrcgi.MAINMENU:
    cdrcgi.navigateTo("Admin.py", session)
elif request == SUBMENU:
    cdrcgi.navigateTo("reports.py", session)

#----------------------------------------------------------------------
# Set up a database connection and cursor.
#----------------------------------------------------------------------
try:
    conn = db.connect(user="CdrGuest")
    cursor = conn.cursor()
except Exception as e:
    cdrcgi.bail('Database connection failure: %s' % e)

#----------------------------------------------------------------------
# Build date string for header.
#----------------------------------------------------------------------
dateString = time.strftime("%B %d, %Y")
instr = instr % dateString

# -------------------------------------------------------------
# Select all indications for the plain report and the select
# text box.
# -------------------------------------------------------------
iQuery = """\
         SELECT DISTINCT value
           FROM query_term_pub
          WHERE path = '/DrugInformationSummary' +
                      '/DrugInfoMetaData/ApprovedIndication'
          ORDER BY value
"""

if not iQuery:
    cdrcgi.bail('iQuery: No query criteria specified')

### # -------------------------------------------------------------
### # Create a drop-down list for Drug Names
### # -------------------------------------------------------------
### dQuery = """\
###          SELECT distinct q.doc_id, q.value
###            FROM query_term q
###            JOIN active_doc d
###              ON d.id = q.doc_id
###            JOIN query_term i
###              ON i.doc_id = d.id
###             AND i.path = '/DrugInformationSummary' +
###               '/DrugInfoMetaData/ApprovedIndication/@cdr:ref'
###           WHERE q.path = '/DrugInformationSummary/Title'
###           ORDER BY q.value
### """
###
### if not dQuery:
###     cdrcgi.bail('dQuery: No query criteria specified')

#----------------------------------------------------------------------
# Submit the queriew to the database.
#----------------------------------------------------------------------
try:
    ind_cursor = conn.cursor()
    ind_cursor.execute(iQuery)
    iRows = ind_cursor.fetchall()
    ind_cursor.close()
except Exception as e:
    cdrcgi.bail('Failure retrieving initial indications: %s' % e)

#----------------------------------------------------------------------
# If we don't have a request, put up the form.
#----------------------------------------------------------------------
if not displayType:
    header = cdrcgi.header(title, title, instr,
                           script,
                           ("Submit",
                            SUBMENU,
                            cdrcgi.MAINMENU),
                           numBreaks = 1,
                           stylesheet = """
   <STYLE type="text/css">
    TD      { font-size:  12pt;
              padding-right:     5px; }
    DL      { margin-left: 0; padding-left: 0 }
   </STYLE>
""")
    form   = """\
   <input type='hidden' name='%s' value='%s'>

   <!-- fieldset>
    <legend>&nbsp;Select Drug Name&nbsp;</legend>
    <select name="singledrug" id="singledrug">
     <option value="" selected='selected'>Select Drug Name</option>
""" % (cdrcgi.SESSION, session)

###     for row in dRows:
###         form += """<option value='%s'>%s</option>
### """ % (row[0], row[1])

    form  += """\
    </select>
   </fieldset -->

   <fieldset>
    <legend>&nbsp;Select Report Type&nbsp;</legend>
    <!-- input name='displayType' type='radio' id="single" value='single'>
    <label for="single">Single Drug with Indication(s)</label>
    <br -->
    <input name='displayType' type='radio' id="drug" value='drug'
           checked='checked'>
    <label for="drug">Indications and Drug Names only</label>
    <br>
    <input name='displayType' type='radio' id="brand" value='brand'>
    <label for="brand">Indications and Drug Names (with Brand Name(s))</label>
    <br>
    <hr width="25%">
    <input name='displayType' type='radio' id="plain" value='plain'>
    <label for="plain">Indications only</label>
   </fieldset>

   <fieldset>
    <legend>&nbsp;Select Display Type for Indication(s)&nbsp;</legend>
    <input name='sorting' type='radio' id='sortD'
           value='D'>
    <label for='sortD'>Display Indication(s) for each Drug</label>
    <br>
    <input name='sorting' type='radio' id='sortI'
           value='I' checked='checked'>
    <label for='sortI'>Display Drug(s) for each Indication</label>
   </fieldset>

   <fieldset>
    <legend>&nbsp;Select Approved Indication(s)&nbsp;</legend>
    <select name="indication" id="indication" size="10"
            multiple="multiple">
     <option value='all' selected='selected'>all indications</option>
"""

    for row in iRows:
        form += """<option value="%s">%s</option>
""" % (html_escape(row[0], True), row[0])

    form += """\
    </select>
   </fieldset>

  </form>
 </body>
</html>
"""
    cdrcgi.sendPage(header + form)

if not iRows:
    cdrcgi.bail('No Records Found for Selection: %s ' % displayType   + "; ")

#----------------------------------------------------------------------
# Create the results page.
#----------------------------------------------------------------------
#    UL             { margin-left:    0;
#                     padding-left:   0;
#                     margin-top:    10px;
#                     margin-bottom: 30px; }
header    = cdrcgi.rptHeader(title, stylesheet = """\
   <STYLE type="text/css">
    TABLE         { margin-top:    10px;
                    margin-bottom: 30px; }

    table         { border-collapse: collapse;
                    width: 90%; }

    table, th, tr, td
                  { border: 1px solid black; }
    .full         { border: none; }

    th            { height: 50px;
                    background-color: #00FF77;
                    color: navy; }
    td            { text-align: left;
                    vertical-align: top; }
    .col1         { width: 45%; }
    .col2         { width: 45%; }
    .col3         { width: 40%; }
    .col4         { width: 20%; }
    tr.even       { background-color: white; }
    tr.odd        { background-color: #DDFFDD; }

    .date         { font-size: 12pt; }
    .sectionHdr   { font-size: 12pt;
                    font-weight: bold;
                    text-decoration: underline; }
    td.report     { font-size: 11pt;
                    padding-right: 15px;
                    vertical-align: top; }
    td, th        { padding-right: 5pt;
                    padding-left:  5pt; }
    .cdrid        { width: 10%;
    .cdrid          text-align: right }
    div.es        { height: 10px; }
    .header       { font-size: 12pt;
                    font-weight: bold; }
    .indlabel     { font-weight: bold; }
    .indrow       { font-size: 12pt;
                    font-weight: normal; }
    .drug         { text-indent: 2em;
                    margin: 0px; }
    .brand        { text-indent: 4em;
                    margin: 0px;
                    font-style: italic; }
    li            { display: list-item;
                    list-style-type: none;
                    margin-left: 2em; }
    a:link        { text-decoration: underline; }
    a:visited     { text-decoration: underline; }
    a:hover       { background: #FFFFAA; }
   </STYLE>
""")

footer = """\
 </BODY>
</HTML>
"""

# -------------------------
# Display the Report Title
# -------------------------
report    = """\
   <INPUT TYPE='hidden' NAME='%s' VALUE='%s'>
  <H3>Approved Indications for Drug Information Summaries<br>
  <span class="date">(%s)</span>
  </H3>
""" % (cdrcgi.SESSION, session, dateString)

# -------------------------------------------------------------------
# Decision if the CDR IDs are displayed along with the summary titles
# - The report without CDR ID is displayed as a none-bulleted list.
# - The report with    CDR ID is displayed in a table format.
# -------------------------------------------------------------------

# In the simple case we only want a list of the indications
# ---------------------------------------------------------
if displayType == 'plain':
    report += """
    <span class="header">Full List of Drug Indications</span>

    <table class="full">
"""

    for row in iRows:
        report += """\
     <tr class="full">
      <td class="full">
       <li class='indrow'>%s</li>
      </td>
     </tr>
""" % row[0]

    report += """
    </table>
"""
    # Send the page back to the browser.
    #----------------------------------------------------------------------
    cdrcgi.sendPage(header + report + footer)

elif displayType == 'single':
    if not singleDrug:
        cdrcgi.bail("Error:  No drug name selected.")

    drugName, drugIndications = getIndications(singleDrug)

    report += """
    <span class="header">Drug Name: %s (<a href="/cgi-bin/cdr/QcReport.py?\
Session=guest&\
DocType=DrugInformationSummary&\
DocId=CDR%s&DocVersion=-1">CDR%s</a>)

    <table>
""" % (drugName, singleDrug, singleDrug)

    for indication in drugIndications:
        report += """<tr><td><li class='indrow'>%s</li></td></tr>
""" % indication

    report += """
    </table>
"""
    # Send the page back to the browser.
    #----------------------------------------------------------------------
    cdrcgi.sendPage(header + report + footer)


else:
    # Creating the four different reports by indication/drug displayed
    # with/without brandnames
    # ----------------------------------------------------------------
    if type(indication) == type(''): indication = [indication]

    brandNames = getBrandNames()

    q_path = "/DrugInformationSummary/DrugInfoMetaData/ApprovedIndication"
    fields = 'q.doc_id', 'q.value AS "Indication"', 't.value AS "DrugName"'
    query = db.Query("query_term_pub q", *fields)
    query.join("query_term_pub t", "t.doc_id = q.doc_id",
               "t.path = '/DrugInformationSummary/Title'")
    query.where(query.Condition("q.path", q_path))
    if "all" not in indication:
        query.where(query.Condition("q.value", indication, "IN"))
    if sortType == "I":
        query.order("q.value")
    else:
        query.order("t.value", "q.value")

    #----------------------------------------------------------------------
    # Submit the query to the database.
    #----------------------------------------------------------------------
    try:
        rows = query.execute(cursor).fetchall()
    except Exception as e:
        cdrcgi.bail('Failure retrieving indications2: %s' % e)

    # Sorting report by indication
    # ----------------------------
    if sortType == 'I':
        report += createByIndication(rows, displayType, brandNames)
        # report += createByIndication2(rows, displayType, brandNames)
    else:
        report += createByDrug(rows, displayType, brandNames)


# Send the page back to the browser.
#----------------------------------------------------------------------
cdrcgi.sendPage(header + report + footer)
