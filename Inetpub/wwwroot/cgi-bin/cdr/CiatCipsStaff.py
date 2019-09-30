#!/usr/bin/env python

"""Main menu for CIAT/CIPS staff.
"""

from cdrcgi import Controller

class Control(Controller):

    SUBTITLE = "CIAT/OCC Staff"
    SUBMIT = None

    def populate_form(self, page):
        """Add the menu items for CIAT."""
        page.body.set("class", "admin-menu")
        ol = page.B.OL()
        page.form.append(ol)
        for display, script in (
            ("Advanced Search", "AdvancedSearch.py"),
            ("Audio Download", "FtpAudio.py"),
            ("Audio Import", "ocecdr-3373.py"),
            ("Audio Request Spreadsheet", "ocecdr-3606.py"),
            ("Audio Review Glossary Term", "GlossaryTermAudioReview.py"),
            ("Batch Job Status", "getBatchStatus.py"),
            ("Create World Server Translated Summary",
             "post-translated-summary.py"),
            ("Glossary Translation Job Queue", "glossary-translation-jobs.py"),
            ("Mailers", "Mailers.py"),
            ("Media Translation Job Queue", "media-translation-jobs.py"),
            ("Replace CWD with Older Version", "ReplaceCWDwithVersion.py"),
            ("Replace Doc with New Doc", "ReplaceDocWithNewDoc.py"),
            ("Reports", "Reports.py"),
            ("Summary Translation Job Queue", "translation-jobs.py"),
            ("Update Mapping Table", "EditExternMap.py"),
            ("Update Pre-Medline Citations", "UpdatePreMedlineCitations.py"),
        ):
            ol.append(page.B.LI(page.menu_link(script, display)))


Control().run()
