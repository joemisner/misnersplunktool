Misner Splunk Tool
==================

Misner Splunk Tool v2017.08.12
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



Usage
-----

### Configuration ###

Configuration values for the Misner Splunk Tool are stored in the file
`misnersplunktool.conf` located in the installation directory of this
tool. This file is similar in formatting to Splunk configuration files,
and contains instructions on values that may be changed from defaults.
This includes listing multiple Splunkd instances and their credentials,
default REST API endpoints, and health check metrics that will show as
Caution or Warning in the Report tab.

If this file is missing on startup, a default file will be created. To
reset values back to defaults, choose the "File > Build
misnersplunktool.conf" menu option.

### Tools ###

The "Tools" menu contains the following options:

**Restart splunkd**

Instructs the Splunk daemon to restart. Similar to executing the Splunk
CLI `restart` command.

**Refresh Configurations**

Mimics the script executed when visiting the `/debug/refresh` URI on
this Splunk instance's web server. When used, this function will execute
all endpoints with `_reload` links, and return similar output to the
above URI.

Only works on Splunk Enterprise instances.

**Change Deployment Server**

This is useful for remote Universal Forwarder installations, allowing
you to enable the deployment client, change the deployment server URI,
and restart splunkd on the current instance.

### Tabs ###

This tool is divided into multiple tabs, each with a corresponding
feature:

**General**

High-level overview of this Splunk instance, including process controls,
deployment information, and current messages.

**Report**

Gathers polled values into a report that contains discovery and health
information on a single table. Health values are determined by the
metrics listed in the configuration file, or defaults if not defined.
This table can be exported to CSV by going to the "File > Save Report"
menu.

See the `misnersplunktool.conf` configuration to make changes to values
that flag a value into Caution or Warning status.

**Configuration**

Contains a dropdown for selecting a Splunk configuration file, polled
using the `/services/properties` REST API endpoint. This endpoint by
experience returns values that closely resembles the Splunk CLI `btool`.
Choosing a configuration in the dropdown immediately polls the instance
for the current running configurations, not just the startup
configurations listed in the .conf file on disk.

**Input Status**

Pulls data from the `/services/admin/inputstatus` REST API endpoint and
filters the results into sorted tables. Eases troubleshooting in
locating faults during onboarding and analysis of ingested data on
forwarders.

**Apps**

Lists the Apps installed on this instance. Useful in troubleshooting
whether an app has been deployed and enabled on a remote Splunk
instance.

**Indexer Cluster**

Data on this tab closely resembles the Indexer Clustering page under
the Splunk Web GUI's settings, returning health and status information
of the indexer cluster. Useful if the web interface and Management
Console are unavailable.

This tab is enabled on Cluster Master instances only.

**SH Cluster**

Data on this tab closely resembles the `show shcluster-status` command
on the Splunk CLI, returning health and status information of the search
head cluster. Useful if CLI access and the Management Console are
unavailable.

This tab is enabled on Search Head Cluster Member instances only.

**Resource Usage**

Returns resource usage of the Splunk instance's processes as well as
it's host system.

This tab returns data only on Splunk versions 6.3 and up, and not all
data is available depending on version and instance type.

**REST API**

Returns a simple interface for executing REST API methods against the
currently connected Splunk instance. GET, POST, and DELETE methods are
supported.

See the [REST API Reference Manual](http://docs.splunk.com/Documentation/Splunk/latest/RESTREF/RESTprolog)
for more information.



Changelog
---------

2016.10.20
 * initial version

2016.10.22
 * updated Cluster GUI
 * added Management Console icon

2016.10.23
 * added Change Deployment Server functionality
 * added Resource Usage tab

2016.10.26
 * bug fixes

2017.01.08
 * changed Configurations tab to pull from REST '/services/properties'
 * now using 'requests' for REST calls
 * added editbox to submit data body inputs to REST
 * added Tools menu and moved Change Deployment Server to this location
 * added summary of Deployment Server URI, Cluster Master, and SHC Deployer to General tab

2017.01.09
 * added parsing of multiple cluster master entries in 'master_uri' for 'clustermaster:' stanzas

2017.01.19
 * changed Deployment Server settings from using splunklib.client.service.confs to rest_call to URI /services/properties after finding that the rest call was accurately representing current config

2017.01.20
 * bug fixes

2017.02.25
 * added Search Head Cluster tab
 * renamed Cluster tab to Indexer Cluster
 * forked Splunkd class to separate module misnersplunkdwrapper.py

2017.05.10
 * initial public version

2017.07.17
 * added resizable window with auto-adjusting widgets

2017.07.18
 * added Report tab, containing Discovery and Health reports
 * added File > Save functionality, currently for saving reports to CSV

2017.07.26
 * updated health report to display metric status even when not in alarm
 * modified Report tab, combining Discovery and Health report functionality
 * modified Save Report to use current datetime and server name as default filename

2017.08.11
 * changed the Report's status column to health
 * added capturing of unhandled exceptions for debugging

2017.08.12
 * unhandled exceptions get written to error.log in app directory
 * migrated report_builder method to Splunkd class
 * fixed report code related to SHC counts causing a crash
 * misc code cleanup



License
-------

Copyright (C) 2015-2017 Joe Misner <joe@misner.net>

Splunk is a trademark of Splunk Inc. in the United States and other countries.

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
