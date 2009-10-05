#----------------------------------------------------------------------
#
# $Id: OrgSearch2.py,v 1.10 2004-02-03 14:40:14 bkline Exp $
#
# Prototype for duplicate-checking interface for Organization documents.
#
# $Log: not supported by cvs2svn $
# Revision 1.9  2003/12/09 19:13:26  bkline
# Bumped up the timeout value for the query.
#
# Revision 1.8  2003/08/25 20:19:05  bkline
# Added support for searching on FormerName element.
#
# Revision 1.7  2002/08/08 12:16:29  bkline
# Changed path for AlternateName.
#
# Revision 1.6  2002/06/28 20:13:57  bkline
# Plugged in QcReport.py for Organization advanced search.
#
# Revision 1.5  2002/06/04 20:19:34  bkline
# Fixed typos in query_term paths.
#
# Revision 1.4  2002/05/08 17:41:50  bkline
# Updated to reflect Volker's new filter names.
#
# Revision 1.3  2002/02/20 03:59:34  bkline
# Modified code to match changes in schemas.
#
# Revision 1.2  2002/02/14 19:37:23  bkline
# Modified search elements to match schema changes; fixed display filter.
#
# Revision 1.1  2001/12/01 18:11:44  bkline
# Initial revision
#
# Revision 1.1  2001/07/17 19:17:43  bkline
# Initial revision
#
#----------------------------------------------------------------------
import cgi, cdr, cdrcgi, re, cdrdb

#----------------------------------------------------------------------
# Get the form variables.
#----------------------------------------------------------------------
fields  = cgi.FieldStorage()
session = cdrcgi.getSession(fields)
boolOp  = fields and fields.getvalue("Boolean")         or "AND"
orgName = fields and fields.getvalue("OrgName")         or None
orgType = fields and fields.getvalue("OrgType")         or None
street  = fields and fields.getvalue("Street")          or None
city    = fields and fields.getvalue("City")            or None
state   = fields and fields.getvalue("State")           or None
country = fields and fields.getvalue("Country")         or None
zip     = fields and fields.getvalue("ZipCode")         or None
submit  = fields and fields.getvalue("SubmitButton")    or None
help    = fields and fields.getvalue("HelpButton")      or None

if help: 
    cdrcgi.bail("Sorry, help for this interface has not yet been developed.")

#----------------------------------------------------------------------
# Generate picklist for countries.
#----------------------------------------------------------------------
def orgTypeList(conn, fName):
    query  = """\
  SELECT DISTINCT value, value
    FROM query_term
   WHERE path = '/Organization/OrganizationType'
     AND value IS NOT NULL
     AND value <> ''
ORDER BY value"""
    pattern = "<option value='%s'>%s &nbsp;</option>"
    return cdrcgi.generateHtmlPicklist(conn, fName, query, pattern)

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
    fields = (('Organization Name',       'OrgName'),
              ('Organization Type',       'OrgType', orgTypeList),
              ('Street',                  'Street'),
              ('City',                    'City'),
              ('State',                   'State', cdrcgi.stateList),
              ('Country',                 'Country', cdrcgi.countryList),
              ('ZIP Code',                'ZipCode'))
    buttons = (('submit', 'SubmitButton', 'Search'),
               ('submit', 'HelpButton',   'Help'),
               ('reset',  'CancelButton', 'Clear'))
    page = cdrcgi.startAdvancedSearchPage(session,
                                          "Organization Search Form",
                                          "OrgSearch2.py",
                                          fields,
                                          buttons,
                                          'Organization',
                                          conn)
    page += """\
  </FORM>
 </BODY>
</HTML>
"""
    cdrcgi.sendPage(page)

#----------------------------------------------------------------------
# Define the search fields used for the query.
#----------------------------------------------------------------------
searchFields = (cdrcgi.SearchField(orgName,
                            ("/Organization/OrganizationNameInformation/"
                             "OfficialName/Name",
                             "/Organization/OrganizationNameInformation/"
                             "ShortName/Name",
                             "/Organization/OrganizationNameInformation/"
                             "AlternateName",
                             "/Organization/OrganizationNameInformation/"
                             "FormerName")),
                cdrcgi.SearchField(orgType,
                            ("/Organization/OrganizationType",)),
                cdrcgi.SearchField(street,
                            ("/Organization/OrganizationLocations/"
                             "OrganizationLocation/Location/PostalAddress/"
                             "Street",)),
                cdrcgi.SearchField(city,
                            ("/Organization/OrganizationLocations/"
                             "OrganizationLocation/Location/PostalAddress/"
                             "City",)),
                cdrcgi.SearchField(state,
                            ("/Organization/OrganizationLocations/"
                             "OrganizationLocation/Location/PostalAddress/"
                             "PoliticalSubUnit_State/@cdr:ref",)),
                cdrcgi.SearchField(country,
                            ("/Organization/OrganizationLocations/"
                             "OrganizationLocation/Location/PostalAddress/"
                             "Country/@cdr:ref",)),
                cdrcgi.SearchField(zip,
                            ("/Organization/OrganizationLocations/"
                             "OrganizationLocation/Location/PostalAddress/"
                             "PostalCode_ZIP",)))

#----------------------------------------------------------------------
# Construct the query.
#----------------------------------------------------------------------
(query, strings) = cdrcgi.constructAdvancedSearchQuery(searchFields, boolOp, 
                                                       "Organization")
if not query:
    cdrcgi.bail('No query criteria specified')
#cdrcgi.bail("QUERY: [%s]" % query)

#----------------------------------------------------------------------
# Submit the query to the database.
#----------------------------------------------------------------------
try:
    cursor = conn.cursor()
    cursor.execute(query, timeout = 300)
    rows = cursor.fetchall()
    cursor.close()
    cursor = None
except cdrdb.Error, info:
    cdrcgi.bail('Failure retrieving Organization documents: %s' % info[1][0])

#----------------------------------------------------------------------
# Create the results page.
#----------------------------------------------------------------------
html = cdrcgi.advancedSearchResultsPage("Organization", rows, strings, 
                                        None, session)

#----------------------------------------------------------------------
# Send the page back to the browser.
#----------------------------------------------------------------------
cdrcgi.sendPage(html)