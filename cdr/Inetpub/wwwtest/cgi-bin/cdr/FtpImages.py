#----------------------------------------------------------------------
# $Id: FtpImages.py,v 1.1 2004-11-01 21:29:48 venglisc Exp $
#
# Ftp files from the CIPSFTP server from the ciat/qa/Images directory
# and place them on the CIPS network.
#
# $Log: not supported by cvs2svn $
#----------------------------------------------------------------------
import cgi, cdr, cdrcgi, re, string, os, ftplib, shutil

#----------------------------------------------------------------------
# Set the form variables.
#----------------------------------------------------------------------
defTarget = "Images_from_Cipsftp"
defSource = "CDR_Images"
fields    = cgi.FieldStorage()
session   = cdrcgi.getSession(fields) or "guest"
request   = cdrcgi.getRequest(fields) # or "Get Images"
baseDir   = 'qa/ciat/Images/'
sourceDir = fields and fields.getvalue("SourceDir") or defSource
targetDir = fields and fields.getvalue("TargetDir") or defTarget
title     = "CDR Administration"
section   = "FTP Images from CIPSFTP"
buttons   = ["Get Images", cdrcgi.MAINMENU, "Log Out"]
script    = "FtpImages.py"
ftphost   = "cipsftp.nci.nih.gov"
ftpuser   = "cdrdev"
ftppwd    = "***REMOVED***"
ftpDone   = None

#----------------------------------------------------------------------
# Make sure we're logged in.
#----------------------------------------------------------------------
if not session: cdrcgi.bail('Unknown or expired CDR session.')

#----------------------------------------------------------------------
# Handle request to log out.
#----------------------------------------------------------------------
if request == "Log Out": 
    cdrcgi.logout(session)

#----------------------------------------------------------------------
# Return to the main menu if requested.
#----------------------------------------------------------------------
if request == cdrcgi.MAINMENU:
    cdrcgi.navigateTo("Admin.py", session)

#----------------------------------------------------------------------
# Handle request to delete the user.
#----------------------------------------------------------------------
if request == "Get Images" and ftpDone != 'Y':
    if not sourceDir or not targetDir:
        cdrcgi.bail("Both document IDs are required.")
    netwkDir  = "\\\\imbncipf01\\public\\CDR Images\\" + targetDir
    ftp = ftplib.FTP(ftphost)
    try: 
       ftp.login(ftpuser, ftppwd)
       ftp.cwd(baseDir + sourceDir)
       for name in ftp.nlst():
           if name.endswith('.jpg') or name.endswith('.gif') \
	                            or name.endswith('.psd'):
               bytes = []
               ftp.retrbinary('RETR ' + name, lambda a: bytes.append(a))
               f = open(os.path.join('..', '..', 'cdr', targetDir, name), 'wb')
               # f = open(os.path.join(netwkDir, name), 'wb')
               f.write("".join(bytes))
               f.close()
	       # Delete the file if it was transferred from default directory
	       # ------------------------------------------------------------
	       if sourceDir == 'CDR_Images':
	          ftp.delete(name)
               #print "%d chunks for %s" % (len(bytes), name)
       ftp.quit()
       ftpDone = 'Y'
    except ftplib.error_reply, info:
       cdrcgi.bail("Unexpected Error: %s" % info)
    except ftplib.error_perm, info:
       cdrcgi.bail("Invalid Username/password: %s" % info)
    except ftplib.error_proto, info:
       cdrcgi.bail("Server Error: %s" % info)
    #except:
    #   cdrcgi.bail("Notify Programming staff")
    

#----------------------------------------------------------------------
# Display confirmation message when FTP is done.
#----------------------------------------------------------------------
if ftpDone == 'Y':
   header  = cdrcgi.header(title, title, section, script, buttons)
   form = """\
<H3>FTP Completed</H3>
<INPUT TYPE='hidden' NAME='%s' VALUE='%s' >
""" % (cdrcgi.SESSION, session)
   cdrcgi.sendPage(header + form + "</BODY></HTML>")


#----------------------------------------------------------------------
# Display the form for merging two protocol documents.
#----------------------------------------------------------------------
header  = cdrcgi.header(title, title, section, script, buttons)
form = """\
<H2>FTP Image (jpg, gif) or Photoshop Files from CIPSFTP</H2>
<TABLE border='0'>
 <TR>
  <TD NOWRAP>
   <B>Directory on FTP Server</B>
   </BR>Default: /qa/ciat/Images/CDR_Images
  </TD>
  <TD>&nbsp;&nbsp;</TD>
  <TD NOWRAP>
   <B>Directory on CDR Server</B>
   </BR>Default: /cdr/Images_from_CIPSFTP
  </TD>
 </TR>
 <TR>
  <TD><INPUT NAME='SourceDir' size='40' value='CDR_Images'></TD>
  <TD>&nbsp;&nbsp;</TD>
  <TD><INPUT NAME='TargetDir' size='40' value='Images_from_CIPSFTP'></TD>
 </TR>
</TABLE>
<INPUT TYPE='hidden' NAME='%s' VALUE='%s' >
""" % (cdrcgi.SESSION, session)
cdrcgi.sendPage(header + form + "</FORM></BODY></HTML>")