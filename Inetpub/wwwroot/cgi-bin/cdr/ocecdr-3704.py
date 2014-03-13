#----------------------------------------------------------------------
# $Id$
#
# Media permissions report.
#
# JIRA::OCECDR-3704
#----------------------------------------------------------------------
import cdr
import cdrcgi
import cdrdb
import cgi
import datetime
import lxml.html
import lxml.html.builder
import lxml.etree as etree

def main():
    request = Request()
    if request.action == cdrcgi.MAINMENU:
        cdrcgi.navigateTo("Admin.py", session)
    elif request.action == "Report Menu":
        cdrcgi.navigateTo("reports.py", session)
    elif request.action == "Submit":
        request.report()
    form = Form()
    form.send()

class Request:
    def __init__(self):
        self.fields = cgi.FieldStorage()
        self.action = cdrcgi.getRequest(self.fields)
        self.session = cdrcgi.getSession(self.fields)
    def report(self):
        self.cursor = cdrdb.connect("CdrGuest").cursor()
        self.option1 = self.fields.getlist("option1")
        self.option2 = self.fields.getvalue("option2")
        self.format = self.fields.getvalue("format") or "excel"
        self.req = self.get_date_range("req")
        self.exp = self.get_date_range("exp")
        if self.option1:
            if "denied" in self.option1:
                rpt = self.report_denials()
            else:
                rpt = self.report_requests()
        elif self.option2:
            rpt = self.report_approvals()
        rpt.send(self.format)
    def get_date_range(self, name):
        start = self.fields.getvalue("%s_start" % name)
        end = self.fields.getvalue("%s_end" % name)
        if start or end:
            return Request.DateRange(start, end)
    def report_denials(self):
        paths = (
            "/Media/PermissionInformation/PermissionResponse",
            "/Media/PermissionInformation/SpanishTranslationPermissionResponse"
        )
        query = cdrdb.Query("query_term", "doc_id").unique()
        query.where("path IN (?, ?)", *paths)
        query.where("value = 'Permission Denied'")
        query.execute(self.cursor)
        columns = (
            Report.Column("Media DocTitle", width="300px"),
            Report.Column("Permission Request Date", width="100px"),
            Report.Column("Permission Response (Response Date)", width="200px"),
            Report.Column("Spanish Permission Requested (Permission Response)",
                          width="200px"),
            Report.Column("Comment", width="200px")
        )
        docs = [Media(row[0], self.cursor) for row in self.cursor.fetchall()]
        rows = []
        for doc in docs:
            col1 = "%s (CDR%d)" % (doc.title, doc.doc_id)
            col2 = doc.request_date
            col3 = doc.english_response or ""
            col4 = doc.spanish_request or ""
            col5 = doc.comments
            if doc.response_date:
                col3 += " (%s)" % doc.response_date
            if doc.spanish_response:
                col4 += " (%s)" % doc.spanish_response
            rows.append((col1, col2, col3, col4, col5))
        rows.sort(lambda a,b: cmp(a[0].lower(), b[0].lower()))
        caption = "Media Permission Denials"
        opts = { "caption": caption, "sheet_name": "Denials" }
        table = Report.Table(columns, rows, **opts)
        return Report(table)
    def report_requests(self):
        columns = (
            Report.Column("Media DocTitle", width="300px"),
            Report.Column("Permission Request Date", width="100px"),
            Report.Column("Permission Response (Response Date)", width="200px"),
            Report.Column("Expiration", width="100px"),
            Report.Column("Spanish Permission Requested (Permission Response)",
                          width="200px"),
            Report.Column("Approved Use", width="300px"),
            Report.Column("Comment", width="150px")
        )
        tags = {
            "en": "PermissionRequested",
            "es": "SpanishTranslationPermissionRequested"
        }
        paths = []
        for language in self.option1:
            paths.append("/Media/PermissionInformation/%s" % tags[language])
        query = cdrdb.Query("query_term", "doc_id").unique()
        query.where("path IN (%s)" % ",".join(["?"] * len(paths)), *paths)
        query.where("value = 'Yes'")
        query.execute(self.cursor)
        docs = [Media(row[0], self.cursor) for row in self.cursor.fetchall()]
        rows = []
        for doc in docs:
            approvals = []
            for approval in doc.approved:
                approvals.append("%s (CDR%d)" % (approval.title,
                                                 approval.doc_id))
            col1 = "%s (CDR%d)" % (doc.title, doc.doc_id)
            col2 = doc.request_date
            col3 = doc.english_response or ""
            col4 = doc.expiration_date
            col5 = doc.spanish_request or ""
            col6 = "\n\n".join(approvals)
            col7 = doc.comments
            if doc.response_date:
                col3 += " (%s)" % doc.response_date
            if doc.spanish_response:
                col5 += " (%s)" % doc.spanish_response
            rows.append((col1, col2, col3, col4, col5, col6, col7))
        rows.sort(lambda a,b: cmp(a[0].lower(), b[0].lower()))
        langs = { "en": "English", "es": "Spanish" }
        langs = " and ".join([langs[key] for key in self.option1])
        caption = "%s Permission Requests" % langs
        opts = { "caption": caption, "sheet_name": "Denials" }
        table = Report.Table(columns, rows, **opts)
        return Report(table)
    def report_approvals(self):
        results = {
            "doctype": self.approvals_by_doctype,
            "summary": self.summary_approvals,
            "docid": self.approvals_by_docid
        }.get(self.option2)()
        docs = [Media(doc_id, self.cursor) for doc_id in results.doc_ids]
        columns = (
            Report.Column("Approved Use", width="300px"),
            Report.Column("Media DocTitle", width="300px"),
            Report.Column("Permission Request Date", width="100px"),
            Report.Column("Permission Granted Date", width="100px"),
            Report.Column("Expiration", width="100px"),
            Report.Column("Spanish Permission Requested (Permission Response)",
                          width="150px"),
            Report.Column("Comment", width="150px")
        )
        rows = []
        for doc in docs:
            col2 = "%s (CDR%d)" % (doc.title, doc.doc_id)
            col3 = Report.Cell(doc.request_date, classes="nowrap")
            col4 = Report.Cell(doc.response_date, classes="nowrap")
            col5 = Report.Cell(doc.expiration_date, classes="nowrap")
            col6 = doc.spanish_request
            col7 = doc.comments
            if doc.spanish_response:
                col6 += " (%s)" % doc.spanish_response
            for approval in doc.approved:
                col1 = "%s (CDR%d)" % (approval.title, approval.doc_id)
                rows.append((col1, col2, col3, col4, col5, col6, col7))
        rows.sort(lambda a,b: cmp(a[0].lower(), b[0].lower()))
        opts = { "caption": results.caption, "sheet_name": "Permissions" }
        table = Report.Table(columns, rows, **opts)
        return Report(table)
    def summary_approvals(self):
        language = self.fields.getvalue("summary")
        if not language:
            cdrcgi.bail("Summary language not specified")
        types = self.fields.getlist(language.lower())
        if not types:
            cdrcgi.bail("Summary type(s) not specified")
        args = [language]
        caption = "Media Approved For Use With %s " % language
        qry = cdrdb.Query("query_term m", "m.doc_id").unique()
        qry.join("query_term l", "l.doc_id = m.int_val")
        qry.where("m.path = "
                  "'/Media/PermissionInformation/ApprovedUse/Summary/@cdr:ref'")
        qry.where("l.path = '/Summary/SummaryMetaData/SummaryLanguage'")
        qry.where("l.value = ?", language)
        if "all" in types:
            caption += "Summaries"
        else:
            if len(types) == 1:
                caption += "%s Summaries" % types[0]
            elif len(types) == 2:
                caption += "%s and %s Summaries" % (types[0], types[1])
            else:
                caption += ", ".join(types[:-1])
                caption += ", and %s Summaries" % types[-1]
            qry.join("query_term t", "t.doc_id = l.doc_id")
            qry.where("t.path = '/Summary/SummaryMetaData/SummaryType'")
            qry.where("t.value IN (%s)" % ",".join(["?"] * len(types)), *types)
        qry.execute(self.cursor)
        return Results([row[0] for row in self.cursor.fetchall()], caption)
    def approvals_by_doctype(self):
        doctype = self.fields.getvalue("doctype")
        if not doctype:
            cdrcgi.bail("Document type(s) not specified")
        caption = "Media Approved For Use With %s" % {
            "both": "Summaries and Glossary Terms",
            "summary": "Summaries",
            "glossary": "Glossary Terms"
        }[doctype]
        query = cdrdb.Query("query_term", "doc_id").unique()
        pattern = "/Media/PermissionInformation/ApprovedUse/%s/@cdr:ref"
        doctypes = ("summary", "glossary")
        if doctype in doctypes:
            query.where("path = ?", pattern % doctype.capitalize())
        else:
            query.where("path IN (%s)" % ",".join(["?"] * len(doctypes)),
                        *[pattern % t.capitalize() for t in doctypes])
        query.execute(self.cursor)
        return Results([row[0] for row in self.cursor.fetchall()], caption)
    def approvals_by_docid(self):
        docid = self.fields.getvalue("docid")
        if not docid:
            cdrcgi.bail("Document ID not specified")
        try:
            doc_id = cdr.exNormalize(docid)[1]
        except:
            cdrcgi.bail("Invalid document ID %s" % repr(docid))
        paths = ["/Media/PermissionInformation/ApprovedUse/Glossary/@cdr:ref",
                 "/Media/PermissionInformation/ApprovedUse/Summary/@cdr:ref"]
        query = cdrdb.Query("query_term", "doc_id").unique()
        query.where("path IN (%s)" % ",".join(["?"] * len(paths)), *paths)
        query.where("int_val = ?", doc_id)
        query.execute(self.cursor)
        return Results([row[0] for row in self.cursor.fetchall()],
                       "Media Approved For Use With CDR%s" % doc_id)
    class DateRange:
        def __init__(self, start, end):
            self.start, self.end = start, end

class Form(cdrcgi.Page):
    def __init__(self):
        self.cursor = cdrdb.connect("CdrGuest").cursor()
        self._fields = cgi.FieldStorage()
        self._session = self._fields.getvalue("Session")
        settings = {
            "subtitle": "Media Permissions Report",
            "action": "ocecdr-3704.py",
            "buttons": (u"Submit", u"Report Menu", cdrcgi.MAINMENU),
            "session": self._session
        }
        cdrcgi.Page.__init__(self, "CDR Administration", **settings)
        self.add_script("CdrCalendar.setReadOnly = false;")
        self.option1()
        self.option2()
        self.common()
    def option1(self):
        self.add("<fieldset>")
        self.add(self.B.LEGEND("OPTION 1: Global Version"))
        choices = (
            ("Permission Requested (English)", "en"),
            ("Permission Requested (Spanish)", "es"),
            ("Show All Denied Permission Requested (English and Spanish)",
             "denied")
        )
        for label, value in choices:
            self.add_checkbox("option1", label, value)
        self.add("</fieldset>")
        self.add_script("""\
function check_option1(id) {
    switch (id) {
    case 'denied':
        jQuery('#option1-en').prop('checked', false);
        jQuery('#option1-es').prop('checked', false);
        break;
    default:
        jQuery('#option1-denied').prop('checked', false);
    }
    clear_option_2();
}
function clear_option_1() {
    jQuery('#option1-en').prop('checked', false);
    jQuery('#option1-es').prop('checked', false);
    jQuery('#option1-denied').prop('checked', false);
}
""")

    def common(self):
        self.add("<fieldset>")
        self.add(self.B.LEGEND("Common Options"))
        self.add("<fieldset>")
        self.add(self.B.LEGEND("Optional Date Range for Permission Request"))
        self.add_date_field("req_start", "Start Date")
        self.add_date_field("req_end", "End Date")
        self.add("</fieldset>")
        self.add("<fieldset>")
        self.add(self.B.LEGEND("Optional Date Range for Permission Expiration"))
        self.add_date_field("exp_start", "Start Date")
        self.add_date_field("exp_end", "End Date")
        self.add("</fieldset>")
        self.add("<fieldset>")
        self.add(self.B.LEGEND("Output Format"))
        self.add_radio("format", "Excel Workbook", "excel", checked=True)
        self.add_radio("format", "Web Page ", "html")
        self.add("</fieldset>")
        self.add("</fieldset>")
    def option2(self):
        self.add("<fieldset>")
        self.add(self.B.LEGEND("OPTION 2: Specific Version"))
        choices = (
            ("Choose Document Type", "doctype"),
            ("Select Summary Language and Summary Type", "summary"),
            ("Enter the CDR ID of a certain summary or glossary term", "docid")
        )
        for label, value in choices:
            self.add_radio("option2", label, value)
        self.doctype_block()
        self.summary_block()
        self.docid_block()
        self.add("</fieldset>")
        self.add_script("""\
function check_option2(id) {
    var options = ['doctype', 'summary', 'docid'];
    for (var i = 0; i < options.length; ++i) {
        if (options[i] == id)
            jQuery('#' + options[i] + '_block').show();
        else
            jQuery('#' + options[i] + '_block').hide();
    }
    clear_option_1();
}
function clear_option_2() {
    var options = ['doctype', 'summary', 'docid'];
    for (var i = 0; i < options.length; ++i) {
        jQuery('#option2-' + options[i]).prop('checked', false);
        jQuery('#' + options[i] + '_block').hide();
    }
}
""")
    def doctype_block(self):
        self.add('<fieldset id="doctype_block" class="hidden">')
        self.add(self.B.LEGEND("Document Type(s)"))
        choices = (
            ("Summaries", "summary"),
            ("Glossary Terms", "glossary"),
            ("Both Summaries and Glossary Terms", "both")
        )
        for label, value in choices:
            self.add_radio("doctype", label, value)
        self.add("</fieldset>")
    def summary_block(self):
        self.add('<fieldset id="summary_block" class="hidden">')
        self.add(self.B.LEGEND("Select PDQ Summaries"))
        for language in ("English", "Spanish"):
            self.add_radio("summary", language, language, wrapper=None)
        for language in ("English", "Spanish"):
            lang = language.lower()
            self.add('<fieldset id="%s_block" class="hidden">' % lang)
            self.add(self.B.LEGEND("%s Summary Types" % language))
            self.add_checkbox(lang, "All", "all")
            query = cdrdb.Query("query_term t", "t.value").unique()
            query.join("query_term l", "t.doc_id = l.doc_id")
            query.where("t.path = '/Summary/SummaryMetaData/SummaryType'")
            query.where("l.path = '/Summary/SummaryMetaData/SummaryLanguage'")
            query.where("l.value = ?", language)
            query.order("t.value")
            for row in query.execute(self.cursor).fetchall():
                if row[0]:
                    self.add_checkbox(lang, row[0], row[0],
                                      widget_class="summary-type")
            self.add("</fieldset>")
        self.add("</fieldset>")
        self.add_script("""\
function check_summary(id) {
    var options = ['English', 'Spanish'];
    for (var i = 0; i < options.length; ++i) {
        if (options[i] == id)
            jQuery('#' + options[i].toLowerCase() + '_block').show();
        else
            jQuery('#' + options[i].toLowerCase() + '_block').hide();
    }
}
function check_english(id) { check_lang(id); }
function check_spanish(id) { check_lang(id); }
function check_lang(id) {
    switch (id) {
    case 'all':
        jQuery('.summary-type').prop('checked', false);
        break;
    default:
        jQuery('#english-all').prop('checked', false);
        jQuery('#spanish-all').prop('checked', false);
    }
}
""")
    def docid_block(self):
        self.add('<fieldset id="docid_block" class="hidden">')
        self.add(self.B.LEGEND("CDR Document ID"))
        self.add_text_field("docid", "CDR ID")
        self.add("</fieldset>")

class Results:
    def __init__(self, doc_ids, caption):
        self.doc_ids = doc_ids
        self.caption = caption

class Report(cdrcgi.Report):
    def __init__(self, table):
        title = "Media Permissions Report"
        options = {
            "banner": title,
            "subtitle": "Report Generated %s" % datetime.date.today()
        }
        cdrcgi.Report.__init__(self, title, [table], **options)

class Table(Report.Table):
    def __init__(self, columns, rows, caption):
        Raport.Table.__init__(self, columns, rows, caption=caption,
                              sheet_name="Permissions")

class Media:
    def __init__(self, doc_id, cursor):
        qry = cdrdb.Query("document", "title", "xml").where("id = ?", doc_id)
        rows = qry.execute(cursor).fetchall()
        if not rows:
            cdrcgi.bail("Media document %s not found" % doc_id)
        self.title = rows[0][0].split(";")[0]
        self.doc_id = doc_id
        self.approved = []
        self.english_request = self.spanish_request = None
        self.english_response = self.spanish_response = None
        self.request_date = self.response_date = self.expiration_date = None
        self.comments = []
        tree = etree.XML(rows[0][1].encode("utf-8"))
        for node in tree.findall("PermissionInformation/*"):
            if node.tag == "PermissionRequested":
                self.english_request = node.text
            elif node.tag == "PermissionRequestDate":
                self.request_date = node.text
            elif node.tag == "PermissionResponse":
                self.english_response = node.text
            elif node.tag == "PermissionResponseDate":
                self.response_date = node.text
            elif node.tag == "PermissionExpirationDate":
                self.expiration_date = node.text
            elif node.tag == "SpanishTranslationPermissionRequested":
                self.spanish_request = node.text
            elif node.tag == "SpanishTranslationPermissionResponse":
                self.spanish_response = node.text
            elif node.tag == "Comment":
                self.comments.append(node.text)
            elif node.tag == "ApprovedUse":
                for child in node:
                    ref = child.get("{cips.nci.nih.gov/cdr}ref")
                    try:
                        doc_id = cdr.exNormalize(ref)[1]
                        self.approved.append(Approval(doc_id, cursor))
                    except:
                        pass

class Approval:
    def __init__(self, doc_id, cursor):
        query = cdrdb.Query("document", "title").where("id = ?", doc_id)
        self.doc_id = doc_id
        self.title = query.execute(cursor).fetchall()[0][0].split(";")[0]

main()