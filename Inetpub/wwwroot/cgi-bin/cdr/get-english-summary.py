#!/usr/bin/env python

"""Fetch an English summary ready for translation
"""

from html import escape as html_escape
from re import findall, split, sub
from sys import stdout
from lxml import etree, html
from cdrapi.docs import Doc
from cdrcgi import Controller, HTMLPage


class Control(Controller):
    """Access to the database, form creation."""

    SUBTITLE = "Fetch English Summary For Translation"
    LOGNAME = "get-english-summary"
    CHANGES = "SummarySection[SectMetaData/SectionType='Changes to summary']"
    INSTRUCTIONS = (
        "Document ID is required, and must be an integer.  Version is "
        "optional, and can be a positive or negative integer (negative "
        "number counts back from the most recent version, so -1 means "
        "last version, -2 is the one before that, etc.).  If the "
        "version is omitted, the current working copy of the document "
        "is retrieved.  You can also give 'last' for the most recent "
        "version, or 'pub' for the latest publishable version.  The "
        "default output is the display of the document in the browser; "
        "select the 'raw' output option to get the XML document itself, "
        "which you can save to your local file system and pass on to "
        "Trados for translation."
    )
    STRIP = (
        "BoardMember",
        "Comment",
        "ComprehensiveReview",
        "DateLastModified",
        "MediaLink",
        "PMID",
        "PdqKey",
        "RelatedDocuments",
        "ReplacementFor",
        "SectMetaData",
        "TypeOfSummaryChange",
    )
    RAW = (
        "ContentType: text/xml;charset=utf-8\n"
        "Content-disposition: attachment; filename={}\n\n{}"
    )
    CSS = (
        ".tag { color: blue; font-weight: bold }",
        ".name { color: brown }",
        ".value { color: red }",
        "body { background: white; }",
        "pre { font-size: 13px; }",
    )

    def populate_form(self, page):
        """Show the fields and the instruction.

        Pass:
            page - canvas on which we draw
        """

        fieldset = page.fieldset("Instructions")
        fieldset.append(page.B.P(self.INSTRUCTIONS))
        page.form.append(fieldset)
        fieldset = page.fieldset("Document Selection")
        fieldset.append(page.text_field("id", label="Document ID"))
        fieldset.append(page.text_field("version"))
        page.form.append(fieldset)
        fieldset = page.fieldset("Output")
        label = "Display (for viewing)"
        opts = dict(value="display", label=label, checked=True)
        fieldset.append(page.radio_button("fmt", **opts))
        opts = dict(value="raw", label="Raw (for import into Trados)")
        fieldset.append(page.radio_button("fmt", **opts))
        page.form.append(fieldset)
        page.add_script("jQuery(function(){jQuery('id').focus();}")

    def show_report(self):
        """Not a standard report, so we override the base class version."""

        args = self.id, self.version, self.fmt
        self.logger.info("doc id=%r version=%r format=%r", *args)
        if self.raw:
            ver = f"V{self.doc.version:d}" if self.doc.version else ""
            name = f"{self.doc.cdr_id}{ver}.xml"
            raw = self.RAW.format(name, self.xml)
            stdout.buffer.write(raw.encode("utf-8"))
        else:
            subtitle = f"CDR Document {self.doc.cdr_id}"
            if self.doc.version:
                subtitle += f" (version {self.doc.version})"
            buttons = (
                HTMLPage.button(self.SUBMENU),
                HTMLPage.button(self.ADMINMENU),
                HTMLPage.button(self.LOG_OUT),
            )
            opts = dict(
                subtitle=subtitle,
                session=self.session,
                action=self.script,
                buttons=buttons,
            )
            class Page(HTMLPage):
                """Customized for raw HTML block."""
                def __init__(self, pre, title, **opts):
                    self.__pre = pre
                    HTMLPage.__init__(self, title, **opts)
                def tostring(self):
                    opts = dict(self.STRING_OPTS, encoding="unicode")
                    string = html.tostring(self.html, **opts)
                    return string.replace("@@PRE@@", self.__pre)
            page = Page(self.display, self.TITLE, **opts)
            page.form.append(page.B.PRE("@@PRE@@"))
            page.add_css("\n".join(self.CSS))
            page.send()

    @staticmethod
    def markup_tag(match):
        """Replace XML tags with placeholders.

        This is a callback used by `display()` below, so what we can apply
        color formatting to make the XML tags easier to find and read in
        the display (i.e., not raw) version of the document.

        Pass:
          match - regex SRE_Match object

        Return:
          replacement Unicode string with placeholders for tags
        """

        s = match.group(1)
        if s.startswith("/"):
            return "</@@TAG-START@@{}@@END-SPAN@@>".format(s[1:])
        trailingSlash = ""
        if s.endswith("/"):
            s = s[:-1]
            trailingSlash = "/"
        pieces = split("\\s", s, 1)
        if len(pieces) == 1:
            return "<@@TAG-START@@{}@@END-SPAN@@{}>".format(s, trailingSlash)
        tag, attrs = pieces
        pieces = ["<@@TAG-START@@{}@@END-SPAN@@".format(tag)]
        for attr, delim in findall("(\\S+=(['\"]).*?\\2)", attrs):
            name, value = attr.split("=", 1)
            pieces.append(" @@NAME-START@@{}=@@END-SPAN@@"
                          "@@VALUE-START@@{}@@END-SPAN@@".format(name, value))
        pieces.append(trailingSlash)
        pieces.append(">")
        return "".join(pieces)

    @property
    def display(self):
        """Colorized markup to show the document prior to download."""

        if not hasattr(self, "_display"):
            xml = sub("<([^>]+)>", Control.markup_tag, self.xml)
            doc = html_escape(xml)
            doc = doc.replace("@@TAG-START@@", '<span class="tag">')
            doc = doc.replace("@@NAME-START@@", '<span class="name">')
            doc = doc.replace("@@VALUE-START@@", '<span class="value">')
            doc = doc.replace("@@END-SPAN@@", "</span>")
            self._display = doc
        return self._display

    @property
    def fmt(self):
        "One of 'raw' or 'display' (validated)."""

        if not hasattr(self, "_fmt"):
            self._fmt = self.fields.getvalue("fmt")
            if self._fmt not in ("raw", "display"):
                self.bail()
        return self._fmt

    @property
    def raw(self):
        """True if we send raw bytes. Else send display version."""
        return self.fmt == "raw"

    @property
    def doc(self):
        """`Doc` object for the requested CDR document."""

        if not hasattr(self, "_doc"):
            self._doc = Doc(self.session, id=self.id, version=self.version)
        return self._doc

    @property
    def id(self):
        """Integer for the CDR document ID."""
        return int(self.fields.getvalue("id"))

    @property
    def version(self):
        """Which version to get."""

        if not hasattr(self, "_version"):
            self._version = self.fields.getvalue("version", "").strip()
            if self._version:
                try:
                    self._version = int(self._version)
                except:
                    self.bail("version must be an integer")
                if self._version < 0:
                    try:
                        doc = Doc(self.session, id=self.id, version="last")
                    except:
                        self.bail(f"CDR{self.id} not versioned")
                    self._version = doc.version + self._version + 1
                    if self._version < 1:
                        self.bail(f"invalid version number for CDR{self.id}")
        return self._version

    @property
    def xml(self):
        """Filtered and stripped serialized document."""

        if not hasattr(self, "_xml"):
            try:
                xml = etree.tostring(self.doc.resolved, encoding="utf-8")
                parser = etree.XMLParser(remove_blank_text=True)
                root = etree.fromstring(xml, parser)
                first = True
                for node in root.findall("SummaryMetaData/MainTopics"):
                    if first:
                        first = False
                    else:
                        parent = node.getparent()
                        parent.remove(node)
                for node in root.xpath(self.CHANGES):
                    parent = node.getparent()
                    parent.remove(node)
                etree.strip_elements(root, with_tail=False, *self.STRIP)
                etree.strip_attributes(root, "PdqKey")
                opts = dict(pretty_print=True, encoding="unicode")
                self._xml = etree.tostring(root, **opts)
            except:
                logger.exception("failure processing XML")
                bail("failure processing XML")
        return self._xml


if __name__ == "__main__":
    Control().run()
