#!/usr/bin/env python

"""Publishing report menu.
"""

from cdrcgi import Controller

class Control(Controller):

    SUBTITLE = "Publishing Reports"
    SUBMIT = None

    def populate_form(self, page):
        page.body.set("class", "admin-menu")
        ol = page.B.OL()
        page.form.append(ol)
        for display, script in (
            ("Gatekeeper Status Request", "GatekeeperStatus.py"),
            ("Published Document Count (Latest Export Job - runs >4 min)",
             "CountByDoctype.py"),
            ("Publishing Job Activities", "PubStatus.py"),
            ("Publishing Job Statistics", "PubStatsByDate.py"),
        ):
            ol.append(page.B.LI(page.menu_link(script, display)))

Control().run()
