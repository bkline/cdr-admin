#----------------------------------------------------------------------
#
# $Id$
#
# Report on Drug/Agent terms.
#
# BZIssue::1191
# BZIssue::5011
#
#----------------------------------------------------------------------
import cdrdb, ExcelWriter, sys, time, lxml.etree as etree

if sys.platform == "win32":
    import os, msvcrt
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

def findActiveProtocols():
    cursor.execute("""\
SELECT doc_id 
  INTO #active_protocols 
  FROM query_term 
 WHERE path = '/InScopeProtocol/ProtocolAdminInfo/CurrentProtocolStatus'
   AND value IN ('Active', 'Approved-not yet active')""")

def getPrimaryIds():
    ids = {}
    cursor.execute("""\
SELECT i.doc_id, i.value
  FROM query_term i
  JOIN #active_protocols a
    ON a.doc_id = i.doc_id
 WHERE i.path = '/InScopeProtocol/ProtocolIDs/PrimaryID/IDString'""")
    for docId, primaryId in cursor.fetchall():
        ids[docId] = primaryId
    return ids

def getInterventions():
    interventions = {}
    cursor.execute("""\
SELECT i.doc_id, i.int_val
  FROM query_term i
  JOIN #active_protocols a
    ON a.doc_id = i.doc_id
 WHERE i.path = '/InScopeProtocol/ProtocolDetail/StudyCategory/Intervention'
              + '/InterventionNameLink/@cdr:ref'""")
    for protocolId, interventionId in cursor.fetchall():
        if interventionId not in interventions:
            interventions[interventionId] = set([protocolId])
        else:
            interventions[interventionId].add(protocolId)
    return interventions

class Term:
    def __init__(self, id, protocolIds, primaryIds):
        self.id         = id
        self.name       = u""
        self.otherNames = []
        self.protocols  = []
        cursor.execute("SELECT xml FROM document WHERE id = ?", id)
        tree = etree.XML(cursor.fetchall()[0][0].encode('utf-8'))
        for node in tree.findall('PreferredName'):
            self.name = node.text
        for node in tree.findall('OtherName/OtherTermName'):
            self.otherNames.append(node.text)
        self.otherNames.sort(lambda a,b: cmp(a.upper(), b.upper()))
        if protocolIds:
            for protocolId in protocolIds:
                primaryId = primaryIds.get(protocolId,
                                           "[NO PRIMARY ID FOR CDR%d]" %
                                           protocolId)
                self.protocols.append(primaryId)
        self.protocols.sort(lambda a,b: cmp(a.upper(), b.upper()))

conn = cdrdb.connect('CdrGuest')
cursor = conn.cursor()
cursor.execute("""\
    SELECT DISTINCT doc_id
               FROM query_term
              WHERE path = '/Term/SemanticType/@cdr:ref'
                AND int_val = (SELECT doc_id
                                 FROM query_term
                                WHERE path = '/Term/PreferredName'
                                  AND value = 'Drug/agent')
           ORDER BY doc_id""")
rows = cursor.fetchall()
terms = []
findActiveProtocols()
primaryIds = getPrimaryIds()
interventions = getInterventions()
for row in rows:
    termId = row[0]
    protocolIds = interventions.get(termId)
    if protocolIds:
        terms.append(Term(termId, protocolIds, primaryIds))
t = time.strftime("%Y%m%d%H%M%S")
terms.sort(lambda a,b: cmp(len(b.protocols), len(a.protocols)))
print "Content-type: application/vnd.ms-excel"
print "Content-Disposition: attachment; filename=DrugAgentReport-%s.xls" % t
print 

workbook = ExcelWriter.Workbook()
worksheet = workbook.addWorksheet("Terms")
align = ExcelWriter.Alignment('Center')
font = ExcelWriter.Font('white', bold=True)
interior = ExcelWriter.Interior('blue')
headerStyle = workbook.addStyle(alignment=align, font=font, interior=interior)
centerStyle = workbook.addStyle(alignment=align)
worksheet.addCol(1, 300)
worksheet.addCol(2, 400)
worksheet.addCol(3, 100)
worksheet.addCol(4, 150)
row = worksheet.addRow(1, headerStyle)
row.addCell(1, "Preferred Name")
row.addCell(2, "Other Names")
row.addCell(3, "Count of Protocols")
row.addCell(4, "Primary Protocol IDs")
rowNum = 2
leftAlign = workbook.addStyle(alignment=ExcelWriter.Alignment('Left'))
for term in terms:
    row = worksheet.addRow(rowNum)
    row.addCell(1, term.name, leftAlign)
    row.addCell(3, len(term.protocols))
    i = 0
    totalRows = max(len(term.otherNames), len(term.protocols))
    while i < totalRows:
        if i:
            rowNum += 1
            row = worksheet.addRow(rowNum)
        if i < len(term.otherNames):
            row.addCell(2, term.otherNames[i], style=leftAlign)
        if i < len(term.protocols):
            row.addCell(4, term.protocols[i], style=leftAlign)
        i += 1
    rowNum += 1
workbook.write(sys.stdout, True)
