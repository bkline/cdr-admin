#----------------------------------------------------------------------
#
# $Id: CountrySearch.py,v 1.4 2009-05-18 15:44:10 venglisc Exp $
#
# Duplicate-checking interface for Country documents.
#
# $Log: not supported by cvs2svn $
# Revision 1.3  2007/06/12 19:10:02  venglisc
# Modified to use the updated 'Country QC Report Filter' to display the
# QC filter. (Bug 3308)
#
# Revision 1.2  2002/02/28 15:54:41  bkline
# Modified display filter title.
#
# Revision 1.1  2002/02/14 19:36:35  bkline
# Broken out from original GeographicEntity search pages.
#
#----------------------------------------------------------------------
import cgi, cdr, cdrcgi, re, cdrdb

#----------------------------------------------------------------------
# Get the form variables.
#----------------------------------------------------------------------
fields  = cgi.FieldStorage()
session = cdrcgi.getSession(fields)
country = fields and fields.getvalue("Country")         or None
submit  = fields and fields.getvalue("SubmitButton")    or None
help    = fields and fields.getvalue("HelpButton")      or None

if help: 
    cdrcgi.bail("Sorry, help for this interface has not yet been developed.")

#----------------------------------------------------------------------
# Connect to the CDR database.
#----------------------------------------------------------------------
try:
    conn = cdrdb.connect('CdrGuest')
except cdrdb.Error, info:
    cdrcgi.bail('Failure connecting to CDR: %s' % info[1][0])

#----------------------------------------------------------------------
# Display the search form.
#----------------------------------------------------------------------
if not submit:
    fields = (('Country Name',            'Country'),)
    buttons = (('submit', 'SubmitButton', 'Search'),
               ('submit', 'HelpButton',   'Help'),
               ('reset',  'CancelButton', 'Clear'))
    page = cdrcgi.startAdvancedSearchPage(session,
                                          "Country Search Form",
                                          "CountrySearch.py",
                                          fields,
                                          buttons,
                                          'Country',
                                          conn)
    page += """\
  </FORM>
 </BODY>
</HTML>
"""
    # Converting string to Unicode before sending to sendPage()
    # ---------------------------------------------------------
    page = page.decode('utf-8')
    cdrcgi.sendPage(page)

#----------------------------------------------------------------------
# Define the search fields used for the query.
#----------------------------------------------------------------------
searchFields = (cdrcgi.SearchField(country,
                            ("/Country/CountryFullName",
                             "/Country/CountryShortName",
                             "/Country/CountryAlternateName")),)

#----------------------------------------------------------------------
# Construct the query.
#----------------------------------------------------------------------
(query, strings) = cdrcgi.constructAdvancedSearchQuery(searchFields, None, 
                                                       "Country")
#cdrcgi.bail(query)
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
    cdrcgi.bail('Failure retrieving Country documents: %s' % info[1][0])

#----------------------------------------------------------------------
# Create the results page.
#----------------------------------------------------------------------
html = cdrcgi.advancedSearchResultsPage("Country", rows, strings, 
                                        'name:Country QC Report Filter')

#----------------------------------------------------------------------
# Send the page back to the browser.
#----------------------------------------------------------------------
cdrcgi.sendPage(html)