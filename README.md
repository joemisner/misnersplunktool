Misner Splunk Tool
==================

Misner Splunk Tool v2017.07.17
by Joe Misner  
http://tools.misner.net/  

Misner Splunk Tool connects to a Splunk Enterprise or Universal
Forwarder instance via REST API, retrieving the instance's
configurations, input status, apps, and other useful information for
troubleshooting and analysis. This tool's intention is to grant easy
access into remote Splunk instances where shell or web access may not
be available, but the splunkd management port (default 8089) is
accessible.

Edit the included file misnersplunktool.conf located in this
application's directory to specify configurations such as default
hosts, credentials, and REST endpoints. If this file is missing,
navigate to 'File > Build misnersplunktool.conf' and edit this file
with a text editor.

Tooltips have been setup throughout the tool. For additional help,
hover your mouse pointer over different areas of the tool's interface
for more information.



Building
--------

The following dependencies are required to build the application:
- Misner Splunk Tool source
- Python v2.7.13, https://www.python.org/
- Inno Setup v5.5.9, http://www.jrsoftware.org/
- Python module 'PyInstaller' v3.2.1, https://pypi.python.org/pypi/PyInstaller
- Python module 'PySide' v1.2.4, https://pypi.python.org/pypi/PySide
- Python package 'requests' v2.9.1, https://pypi.python.org/pypi/requests
- Python module 'splunk-sdk' v1.6.0, https://pypi.python.org/pypi/splunk-sdk

1. In a Command Prompt window, change to the directory containing this git project, for example:
```
cd c:\misnersplunktool\
```

2. Convert the PySide graphical user interface file `misnersplunktool.ui` into Python:
```
c:\Python27\Scripts\pyside-uic.exe -x misnersplunktool.ui -o misnersplunktoolui.py
```
  * Assumption is that Python 2.7 is installed in `c:\Python27\`

3. Package the project with all dependencies using PyInstaller:
```
c:\Python27\python.exe -O c:\Python27\Scripts\pyinstaller.exe misnersplunktool.spec -y
```
  * Assumption is that Python 2.7 is installed in `c:\Python27\`
  * Resulting package will be stored in the subdirectory `dist\Misner Splunk Tool\`

4. Compile the PyInstaller package into an installer executable using Inno Setup:
```
"c:\Program Files (x86)\Inno Setup 5\iscc.exe" innosetup.iss
```
  * Assumption is that Inno Setup 5 is installed in `c:\Program Files (x86)\Inno Setup 5\`

5. Resulting installer executable in the format `Setup_MisnerSplunkTool_xxxxxxxx.exe` is created.



Changelog
---------

2016.10.20 - initial version  
2016.10.22 - updated Cluster GUI;  
             added Management Console icon  
2016.10.23 - added Change Deployment Server functionality;  
             added Resource Usage tab  
2016.10.26 - bug fixes  
2017.01.08 - changed Configurations tab to pull from REST '/services/properties';  
             now using 'requests' for REST calls;  
             added editbox to submit data body inputs to REST;  
             added Tools menu and moved Change Deployment Server to this location;  
             added summary of Deployment Server URI, Cluster Master, and SHC Deployer to General tab  
2017.01.09 - added parsing of multiple cluster master entries in 'master_uri' for 'clustermaster:' stanzas  
2017.01.19 - changed Deployment Server settings from using splunklib.client.service.confs to rest_call to  
             URI /services/properties after finding that the rest call was accurately representing current config  
2017.01.20 - bug fixes  
2017.02.25 - added Search Head Cluster tab;  
             renamed Cluster tab to Indexer Cluster;  
             forked Splunkd class to separate module misnersplunkdwrapper.py  
2017.05.10 - initial public version  
2017.07.17 - added resizable window with auto-adjusting widgets



License
-------

Copyright (C) 2015-2017 Joe Misner <joe@misner.net>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation,
Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
