#----------------------------------------------------------------------
#
# $Id$
#
# Compare filters between the current tier and the production tier.
#
# OCECDR-3623
#
#----------------------------------------------------------------------
import cdr, cdrdb, cgi, cdrcgi, os, tempfile, re, shutil, glob

#----------------------------------------------------------------------
# Make sure we're not on the production server.
#----------------------------------------------------------------------
if cdr.isProdHost():
    cdrcgi.bail("Can't compare the production server to itself")

#----------------------------------------------------------------------
# Create a temporary working area.
#----------------------------------------------------------------------
def makeTempDir():
    tempfile.tempdir = "d:\\tmp"
    where = tempfile.mktemp("diff")
    abspath = os.path.abspath(where)
    print abspath
    try: os.mkdir(abspath)
    except: cdrcgi.bail("Cannot create directory %s" % abspath)
    try: os.chdir(abspath)
    except: 
        cleanup(abspath)
        cdrcgi.bail("Cannot cd to %s" % abspath)
    return abspath

#----------------------------------------------------------------------
# Get the filters from the local tier.
#----------------------------------------------------------------------
def getLocalFilters(tmpDir):
    try: os.mkdir(cdr.h.tier)
    except: 
        cleanup(tmpDir)
        cdrcgi.bail("Cannot create directory %s" % cdr.h.tier)
    try:
        conn = cdrdb.connect('CdrGuest')
        curs = conn.cursor()
        curs.execute("""\
            SELECT d.title, d.xml
              FROM document d
              JOIN doc_type t
                ON t.id = d.doc_type
             WHERE t.name = 'Filter'""", timeout=300)
        rows = curs.fetchall()
    except Exception, e:
        cleanup(tmpDir)
        cdrcgi.bail('Database failure: %s' % e)
    for row in rows:
        try:
            title = row[0].replace(" ", "@@SPACE@@") \
                          .replace(":", "@@COLON@@") \
                          .replace("/", "@@SLASH@@") \
                          .replace("*", "@@STAR@@")
            xml = row[1].replace("\r", "")
            filename = "%s/@@MARK@@%s@@MARK@@" % (cdr.h.tier, title)
            open(filename, "w").write(xml.encode('utf-8'))
        except:
            cleanup(tmpDir)
            cdrcgi.bail("Failure writing %s" % filename);

#----------------------------------------------------------------------
# Make a copy of the filters on the production server.
#----------------------------------------------------------------------
def getProdFilters(tmpDir):
    try:
        os.mkdir("PROD")
    except:
        cleanup(tmpDir)
        cdrcgi.bail("Cannot create directory PROD")
    for oldpath in glob.glob("d:/cdr/prod-filters/*"):
        try:
            newpath = "PROD/%s" % os.path.basename(oldpath)
            shutil.copy(oldpath, newpath)
        except:
            cleanup(tmpDir)
            cdrcgi.bail("Failure writing %s" % newpath)

#----------------------------------------------------------------------
# Don't leave dross around if we can help it.
#----------------------------------------------------------------------
def cleanup(abspath):
    try:
        os.chdir("..")
        cdr.runCommand("rm -rf %s" % abspath)
    except:
        pass

#----------------------------------------------------------------------
# Undo our homemade encoding.
#----------------------------------------------------------------------
def unEncode(str):
    return str.replace("@@SPACE@@", " ") \
              .replace("@@COLON@@", ":") \
              .replace("@@SLASH@@", "/") \
              .replace("@@STAR@@", "*")  \
              .replace("@@MARK@@", "")
 
#----------------------------------------------------------------------
# Create a banner for the report on a single filter.
#----------------------------------------------------------------------
def makeBanner(name):
    line = "*" * 79 + "\n"
    name = (" %s " % name).center(79, "*")
    return "\n\n%s%s\n%s\n" % (line * 2, name, line * 2)

#----------------------------------------------------------------------
# Get the filters.
#----------------------------------------------------------------------
workDir = makeTempDir()
getLocalFilters(workDir)
getProdFilters(workDir)

#----------------------------------------------------------------------
# Compare the filters.
#----------------------------------------------------------------------
result  = cdr.runCommand("diff -aur PROD %s" % cdr.h.tier)
lines   = result.output.splitlines()
pattern = re.compile("diff -aur PROD/@@MARK@@(.*?)@@MARK@@")
for i in range(len(lines)):
    match = pattern.match(lines[i])
    if match:
        lines[i] = makeBanner(unEncode(match.group(1)))
report = cgi.escape(unEncode("\n".join(lines)))
cleanup(workDir)

print """\
Content-type: text/html; charset: utf-8

<!DOCTYPE HTML PUBLIC '-//IETF//DTD HTML//EN'>
<html>
 <head>
  <title>Filter Comparison Results</title>
 </head>
 <body>
  <h3>The following filters differ between PROD and %s</h3>
  <pre>%s</pre>
 </body>
</html>""" % (cdr.h.tier, report)
