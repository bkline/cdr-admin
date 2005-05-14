#----------------------------------------------------------------------
#
# $Id: DrugAgentReport2.py,v 1.1 2005-03-24 21:15:04 bkline Exp $
#
# Request #1602 (second report on Drug/Agent terms).
#
# $Log: not supported by cvs2svn $
#----------------------------------------------------------------------
import cdrdb, pyXLWriter, sys, time

if sys.platform == "win32":
    import os, msvcrt
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

class Term:
    def __init__(self, id):
        self.id         = id
        self.name       = u""
        self.otherNames = []
        cursor.execute("""\
            SELECT value
              FROM query_term
             WHERE path = '/Term/PreferredName'
               AND doc_id = ?""", id)
        rows = cursor.fetchall()
        if rows:
            self.name = rows[0][0]
        cursor.execute("""\
   SELECT DISTINCT n.value, t.value
              FROM query_term n
              JOIN query_term t
                ON n.doc_id = t.doc_id
               AND LEFT(n.node_loc, 4) = LEFT(t.node_loc, 4)
             WHERE n.path = '/Term/OtherName/OtherTermName'
               AND t.path = '/Term/OtherName/OtherNameType'
               AND n.doc_id = ?""", id)
        for row in cursor.fetchall():
            self.otherNames.append(row)
        self.otherNames.sort(lambda a,b: cmp(a[0].upper(), b[0].upper()))

conn = cdrdb.connect('CdrGuest')
cursor = conn.cursor()
cursor.execute("CREATE TABLE #t1 (doc_id INTEGER)")
conn.commit()
cursor.execute("CREATE TABLE #t2 (doc_id INTEGER)")
conn.commit()
cursor.execute("""\
        INSERT INTO #t1 (doc_id)
    SELECT DISTINCT doc_id
               FROM query_term
              WHERE path = '/Term/SemanticType/@cdr:ref'
                AND int_val = (SELECT doc_id
                                 FROM query_term
                                WHERE path = '/Term/PreferredName'
                                  AND value = 'Drug/agent')""")
cursor.execute("""
        INSERT INTO #t1 (doc_id)
    SELECT DISTINCT doc_id
               FROM query_term
              WHERE path = '/Term/SemanticType/@cdr:ref'
                AND int_val = (SELECT doc_id
                                 FROM query_term
                                WHERE path = '/Term/PreferredName'
                                  AND value = 'Drug/agent')""")
conn.commit()
cursor.execute("""\
       INSERT INTO #t2
            SELECT doc_id
              FROM query_term
             WHERE path = '/InScopeProtocol/ProtocolAdminInfo'
                        + '/CurrentProtocolStatus'
               AND value IN ('Active', 'Approved-not yet active')""")
conn.commit()
cursor.execute("""\
   SELECT DISTINCT u.int_val
              FROM query_term u
              JOIN #t1
                ON #t1.doc_id = u.int_val
              JOIN #t2
                ON #t2.doc_id = u.doc_id
             WHERE u.path = '/InScopeProtocol/ProtocolDetail/StudyCategory'
                           + '/Intervention/InterventionNameLink/@cdr:ref'
          ORDER BY u.int_val""")
terms = []
for row in cursor.fetchall():
    terms.append(Term(row[0]))
t = time.strftime("%Y%m%d%H%M%S")
terms.sort(lambda a,b: cmp(a.name, b.name))
print "Content-type: application/vnd.ms-excel"
print "Content-Disposition: attachment; filename=DrugAgentReport-%s.xls" % t
print 

workbook = pyXLWriter.Writer(sys.stdout)
worksheet = workbook.add_worksheet("Terms")

format = workbook.add_format()
format.set_bold();
format.set_color('white')
format.set_bg_color('blue')
format.set_align('center')

worksheet.set_column(0, 50)
worksheet.set_column(1, 50)
worksheet.set_column(2, 18)
worksheet.write([0, 0], "Preferred Name", format)
worksheet.write([0, 1], "Other Names", format)
worksheet.write([0, 2], "Other Name Type", format)
row = 1

def fix(name):
    return (name.replace(u'\u2120', u'(SM)')
                .replace(u'\u2122', u'(TM)')
                .encode('latin-1', 'ignore'))
for term in terms:
    worksheet.write([row, 0], fix(term.name))
    for i in range(len(term.otherNames)):
        name = fix(term.otherNames[i][0])
        nameType = fix(term.otherNames[i][1])
        worksheet.write([row, 1], name)
        worksheet.write([row, 2], nameType)
        row += 1
    if not term.otherNames:
        row += 1
workbook.close()