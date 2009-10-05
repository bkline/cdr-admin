#----------------------------------------------------------------------
#
# $Id: ProtPublishedCitations.py,v 1.4 2005-06-06 18:53:16 venglisc Exp $
#
# Report identifying previously published protocols that should be 
# included in a hotfix.
#
# $Log: not supported by cvs2svn $
# Revision 1.3  2005/04/12 19:06:51  venglisc
# Some more changes on the way the formatting is being handled.  Added some
# additional comments.  (Bug 1612)
#
# Revision 1.2  2005/04/11 21:12:57  venglisc
# Forgot to remove the limitation to only create output for 10 citations.
#
# Revision 1.1  2005/04/11 21:05:44  venglisc
# Initial version of Protocol Published Citation Report.
# The report displayes all citations linked to InScopeProtocols along with
# the citations formatted output.
# Due to the fact that the formatted output has to be displayed each
# individual citation will have to be filtered -- a very time consuming
# process.
# The command is run from the command line
#    $ python ProtPublishedCitations.py > filename.xls
# (Bug 1612)
#
#
#----------------------------------------------------------------------
import cdr, cdrcgi, cdrdb, pyXLWriter, sys, time

# ---------------------------------------
# Function to create a worksheet
# ---------------------------------------
def addWorksheet(workbook, title, headers, widths, headerFormat, rows):
    worksheet = workbook.add_worksheet(title)

    # Setting the worksteet format
    # ----------------------------
    worksheet.set_landscape()
    worksheet.set_margin_top(0.50)
    worksheet.set_margins_LR(0.25)
    worksheet.set_margin_bottom(0.25)
    worksheet.set_header('&RPage &P of &N', 0.25)
    worksheet.repeat_rows(3)
    worksheet.center_horizontally
    
    worksheet.write([1, 3], 'Protocol Published Citation Report',
                    workbook.add_format(bold=1))

    # Setting the format for the individual columns
    # Note: The set_column only effects the formatting after the 
    #       worksheet is written.
    # ---------------------------------------------
    defaultFormat = workbook.add_format(align='top',
                                        size=8)
    textFormat    = workbook.add_format(align='top',
                                        size=8,
                                        text_wrap=1 )
    urlFormat     = workbook.add_format(align='top',
                                        size=8,
                                        color='blue',
                                        underline=1)

    # Create the header column and set the width of each column
    # ---------------------------------------------------------
    for col in range(len(headers)):
        worksheet.set_column(col, widths[col])
        worksheet.write([3, col], headers[col], headerFormat)

        # Set the format for the entire column for the two existing empty 
        # columns
        # ----------------------------------------------------------------
        if col == 8 or col == 9:
            worksheet.set_column(col, widths[col], defaultFormat)


    # Populate the spreadsheet row by row beginning after the header row
    # ------------------------------------------------------------------
    r = 4
    for row in rows:
        c = 0
        for col in row:
            if type(col) == type(9):
                col = `col`
            elif type(col) == type(u""):
                col = col.encode('latin-1', 'replace')

            #if 0 and c == 2:
            #    worksheet.write([r, c], col, datefmt)
            if c == 0:
                if row[0] != None:
                    url = ("http://%s%s/Filter.py?DocId=CDR%s&amp;"
                           "Filter=set:QC InScopeProtocol Citation Set" % 
                        (cdrcgi.WEBSERVER, cdrcgi.BASE, row[0]))
                    worksheet.write_url([r, c], url, col, urlFormat)
                else:
                    worksheet.write([r, c], col, defaultFormat)
            elif c == 5:
                if row[5] != None:
                    url = ("http://%s%s/Filter.py?DocId=CDR%s&amp;"
                           "Filter=set:QC Citation Set" % (cdrcgi.WEBSERVER, 
                                                           cdrcgi.BASE, row[5]))
                    worksheet.write_url([r, c], url, col, urlFormat)
                else:
                    worksheet.write([r, c], col, defaultFormat)
            elif c == 6:
                if row[6] != None:
                    url = ("http://www.ncbi.nlm.nih.gov/entrez/query.fcgi"
                           "?cmd=Retrieve&amp;db=pubmed&amp;dopt=Abstract" 
                           "&amp;list_uids=%s" % (row[6]))
                    worksheet.write_url([r, c], url, col, urlFormat)
                else:
                    worksheet.write([r, c], col, defaultFormat)
            else:
                worksheet.write([r, c], col, textFormat)
            #if c == 2 or c == 6:
            #    print col
            c += 1
        #worksheet.write([r, c], url)
        r += 1
    #sys.stderr.write("Created worksheet %s\n" % title)

# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
if sys.platform == "win32":
    import os, msvcrt
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

conn = cdrdb.connect('CdrGuest')
conn.setAutoCommit()
cursor = conn.cursor()

# Creating table of all InScopeProtocol documents
# that have been published (and pushed to Cancer.gov)
# We start looking from the last successfull pushing job of the 
# full data set since there may be documents that were dropped
# because of that and did not have a removal record in the 
# pub_proc_doc table
# ------------------------------------------------------------------
cursor.execute("""\
    CREATE TABLE #t0
             (id INTEGER     NOT NULL,
             job INTEGER     NOT NULL,
        doc_type VARCHAR(32) NOT NULL,
   active_status CHAR        NOT NULL)
""")

cursor.execute("""\
    INSERT INTO #t0
         SELECT a.id, MAX(p.id), t.name, a.active_status
           FROM all_docs a
           JOIN doc_type t
             ON a.doc_type = t.id
           JOIN pub_proc_doc d
             ON d.doc_id = a.id
           JOIN pub_proc p
             ON p.id = d.pub_proc
          WHERE t.name = 'InScopeProtocol'
            AND (d.failure IS NULL OR d.failure <> 'Y')
            AND p.status = 'Success'
            AND p.pub_subset LIKE 'Push_Documents_To_Cancer.Gov%'
            AND P.id >= (SELECT max(id)
                           FROM pub_proc
                          WHERE pub_subset = 'Push_Documents_to_Cancer.Gov_Full-Load'
                            AND status = 'Success'
                        )
--       and a.id in (67564, 67560, 67568, 67603)
       GROUP BY a.id, t.name, a.active_status
""", timeout = 300)

# Create a temp table listing all documents created under #t0 along
# with it's title, primary ID, and citation link
# -----------------------------------------------------------------
cursor.execute("""\
    CREATE TABLE #t1
             (id INTEGER       NOT NULL,
             cit INTEGER       NOT NULL,
          protid NVARCHAR(32)  NOT NULL,
           phase NVARCHAR(510) NOT NULL,
           title NVARCHAR(510) NOT NULL,
          otitle NVARCHAR(510) NOT NULL,
          ptitle NVARCHAR(510) NOT NULL,
             job INTEGER       NOT NULL,
        doc_type VARCHAR(32)   NOT NULL,
   active_status CHAR          NOT NULL,
         removed CHAR          NOT NULL)
""")

cursor.execute("""\
    INSERT INTO #t1
         SELECT t.id, c.int_val, pid.value, ph.value, d.title, 
                tot.value, tpt.value, t.job, t.doc_type, 
                t.active_status, p.removed
           FROM pub_proc_doc p
           JOIN #t0 t
             ON p.doc_id = t.id
            AND p.pub_proc = t.job
           JOIN document d
             ON d.id = t.id
           JOIN query_term pid
             ON t.id = pid.doc_id
            AND pid.path = '/InScopeProtocol/ProtocolIDs/PrimaryID/IDString'
           JOIN query_term ph
             ON t.id = ph.doc_id
            AND ph.path  = '/InScopeProtocol/ProtocolPhase'
           JOIN query_term tot
             ON t.id = tot.doc_id
            AND tot.path = '/InScopeProtocol/ProtocolTitle'
           JOIN query_term ot
             ON t.id = ot.doc_id
            AND tot.node_loc = ot.node_loc
            AND ot.value in ('Original')
            AND ot.path = '/InScopeProtocol/ProtocolTitle/@Type'
           JOIN query_term tpt
             ON t.id = tpt.doc_id
            AND tpt.path = '/InScopeProtocol/ProtocolTitle'
           JOIN query_term pt
             ON t.id = pt.doc_id
            AND tpt.node_loc = pt.node_loc
            AND pt.value in ('Professional')
            AND pt.path = '/InScopeProtocol/ProtocolTitle/@Type'
           JOIN query_term c
             ON t.id = c.doc_id
            AND c.path = '/InScopeProtocol/PublishedResults/Citation/@cdr:ref'
            """, timeout = 300)

# Create a temp table with all the existing latest valid versions
# ----------------------------------------------------------------------
cursor.execute("""\
         CREATE TABLE #t2 (cit  INTEGER  NOT NULL, 
                           pmid INTEGER  NOT NULL)
""")

cursor.execute("""\
    INSERT INTO #t2
         SELECT DISTINCT doc_id, int_val
           FROM query_term q
          WHERE exists (SELECT 'x'
                          FROM #t1 t
                         WHERE t.cit = q.doc_id
                       )
            AND q.path = '/Citation/PubmedArticle/MedlineCitation/PMID'
""", timeout = 300)

# Create a temp table listing all OtherID protocol names
# ------------------------------------------------------
cursor.execute("""\
         CREATE TABLE #t3 (id  INTEGER     NOT NULL, 
                      otherid  VARCHAR(50) NOT NULL)
""")

cursor.execute("""\
    INSERT INTO #t3
         SELECT q.doc_id, q.value
           FROM query_term q
           JOIN #t0 t0
             ON q.doc_id = t0.id
          WHERE path = '/InScopeProtocol/ProtocolIDs/OtherID/IDString'
          ORDER BY q.doc_id, q.value
""", timeout = 300)

# Create the list of InScopeProtocols for which we find a publishable
# version whose version number is greater than the version number that
# has been published.
# ---------------------------------------------------------------------
cursor.execute("""\
         SELECT t1.id, t1.protid, t1.phase, t1.ptitle, t1.otitle, 
                t1.cit, t2.pmid
           FROM #t1 t1
LEFT OUTER JOIN #t2 t2
             ON t1.cit = t2.cit
          ORDER BY t1.protid
""", timeout = 300)

rows = cursor.fetchall()

# Filter the Citation document to extract the formatted citation
# for each document
# --------------------------------------------------------------
for row in rows:
    response = []
    response = cdr.filterDoc('guest', ['set:Format Citation'], row[5])
    row.append(response[0])

# Select the protocol OtherIDs and concatenate them to the primary
# protocol ID
# --------------------------------------------------------------------
for row in rows:
    query = """\
         SELECT otherid
           FROM #t3
          WHERE id = %s
""" % row[0]
    cursor.execute(query)
    names = cursor.fetchall()

    otherNames = ''
    for name in names:
        otherNames += '; ' + name[0]
    row[1] += otherNames

t = time.strftime("%Y%m%d%H%M%S")

workbook = pyXLWriter.Writer(sys.stdout)

format = workbook.add_format()
format.set_bold();
format.set_color('white')
format.set_bg_color('blue')
format.set_align('top')

# Create worksheet listing all updated InScopeProtocols
# -----------------------------------------------------
titles  = ('InScopeProtocol Citations', 'Summary Titles')
colheaders = ['DocID',    'Protocol IDs', 'Phase', 
           'HP Title', 'Original Title', 
           'CID', 'PMID', 
           'Formatted Citation', 'Kp/Rm', 'Comment']
widths  = (6, 15, 10, 20, 20, 6, 8, 25, 6, 10)
addWorksheet(workbook, titles[0], colheaders, widths, format, rows)

workbook.close()