Misner Splunk Tool
==================

Misner Splunk Tool v2018.07.12  
by Joe Misner  
http://tools.misner.net/

Misner Splunk Tool connects to a Splunk Enterprise or Universal
Forwarder instance via REST API, retrieving the instance's
configurations, input status, apps, and other useful information for
troubleshooting and analysis. This tool's intention is to grant easy
access into remote Splunk instances where shell or web access may not
be available, but the splunkd management port (default 8089) is
accessible.

Tooltips have been setup throughout the tool. For additional help,
hover your mouse pointer over different areas of the tool's interface
for more information.



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

### Discovery Report ###

This comprehensive tool connects to multiple Splunk instances, creating
a combined report of polled values across a deployment. The contents of
this report is identical to the Report tab of an individual instance,
multiplied by all Splunk instances listed. Usage of this report is
beneficial to document configurations, locate discrepancies, and
understand adjacencies, among other uses in the discovery process of a
Splunk environment. In addition to a saved report, the combined instance
adjacency data can generate a visual topology of the deployment.

**Execution**

To run this tool, a CSV file first needs to be completed. The format of
this file must be as per the following example:

    address,port,username,password
    1.2.3.4,8089,admin,changeme
    splunk.myhost.com,8089,admin,changeme

This example is included in the "discovery.csv" file located in the
Misner Splunk Tool installation directory. This file may be modified and
selected in the Discovery Report, or copied to another location where
multiple CSV files in this format can be kept for different Splunk
deployments.

After a properly formatted CSV file is chosen, each instance listed in
the file is loaded into the Discovery Report window. When the Start
button is clicked, a separate thread sequentially polls each Splunk
instance and gathers data. Once all instances are polled, you may click
Save Report to save this completed Discovery Report on disk. The
completed Discovery Report is also in CSV format, and can be loaded into
spreadsheet software for filtering.

**Topology**

In addition to the saved CSV report, clicking the Topology button will
generate a visual topology based on the polled data of each instance.
The Splunk instances are plotted in layers, by default in this order:

- Users
- Management Consoles
- SHC Deployers
- Search Heads
- Cluster Masters
- Indexers
- License Masters
- Heavy Forwarders
- Deployment Servers
- Universal Forwarders
- Non-Forwarder Inputs
- Other Instances

This primary role of a Splunk instance is a guess, based on the provided
roles which the instance is currently participating in, and may not be
accurate per the design of the deployment. Any new instances that were
discovered while polling the initial Splunk instances are also plotted,
and are given the label "Discovered Node" on the topology.

Instance node and adjacency colors among many other options are all
customizable in the Misner Splunk Tool configuration. These options
allow for tweaking to paint the topology to suit your needs.

After the topology is built, the window can be used to stretch, zoom,
and pan the image as needed. The topology can then be saved to disk by
clicking the floppy disk icon, and choosing a format such as PDF or PNG.

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
This table can be exported to CSV by going to the "File > Save Instance
Report" menu.

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



Building
--------

The following dependencies are required to build the application:

- Misner Splunk Tool source
- Python 64-bit v2.7.15, https://www.python.org/
- Inno Setup v5.5.9, http://www.jrsoftware.org/
- Python module 'PyInstaller' v3.4.dev0, https://pypi.python.org/pypi/PyInstaller
- Python module 'PySide2' v5.11, https://pypi.python.org/pypi/PySide2
- Python package 'requests' v2.19.1, https://pypi.python.org/pypi/requests
- Python module 'splunk-sdk' v1.6.5, https://pypi.python.org/pypi/splunk-sdk
- Python module 'Markdown' v2.6.11, https://pypi.python.org/pypi/Markdown
- Python module 'Pygments' v2.2.0, https://pypi.python.org/pypi/Pygments
- Python module 'networkx' v2.1, https://pypi.python.org/pypi/networkx
- Python module 'matplotlib' v2.2.2, https://pypi.python.org/pypi/matplotlib

Steps to build installer for Windows:

1. In a Command Prompt window, change to the directory containing this git project, for example:
    ```
    cd c:\misnersplunktool\
    ```

2. Convert the PySide2 graphical user interface files into Python code:
    ```
    c:\Python27\Scripts\pyside2-uic.exe -x misnersplunktool.ui -o misnersplunktoolui.py
	c:\Python27\Scripts\pyside2-uic.exe -x misnersplunktooldiscoveryreport.ui -o misnersplunktooldiscoveryreportui.py
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

Steps to build portable executable for Windows:

1. In a Command Prompt window, change to the directory containing this git project, for example:
    ```
    cd c:\misnersplunktool\
    ```

2. Convert the PySide2 graphical user interface files into Python code:
    ```
    c:\Python27\Scripts\pyside2-uic.exe -x misnersplunktool.ui -o misnersplunktoolui.py
	c:\Python27\Scripts\pyside2-uic.exe -x misnersplunktooldiscoveryreport.ui -o misnersplunktooldiscoveryreportui.py
    ```
    * Assumption is that Python 2.7 is installed in `c:\Python27\`

3. Package the project with all dependencies using PyInstaller:
    ```
    c:\Python27\python.exe -O c:\Python27\Scripts\pyinstaller.exe misnersplunktool_onefile.spec -y
    ```
    * Assumption is that Python 2.7 is installed in `c:\Python27\`

4. Resulting portable executable `misnersplunktool.exe` is created in the subdirectory `dist\`.



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

2017.10.10

 * fixed Save Report broken after migrating report_builder method
 * Help dialog replaced with modal window displaying README.md markdown

2017.10.12

 * added Adjacencies category in Report tab, listing all known Splunk instances directly interfacing with the current instance
 * merged Deployment category in Report tab into the Adjacencies category
 * added syntax highlighting to Configuration and REST API tab's code using Pygments

2017.10.15

 * fixed report code related to adjacencies causing a crash
 * added Discovery Report tool for creating a combined report of multiple Splunk instances at once

2017.10.25

 * added Topology view to Discovery Report tool
 * fixed Tools menu code not checking for inactive splunkd connection and causing a crash
 * disabled QWebView right-click menu which incorrectly displayed a "Reload" action
 * misc code cleanup

2018.07.11

 * ported from PySide to PySide2 (Qt4 to Qt5)
 * updated dependencies, including switch to 64-bit Python interpreter and PyInstaller v3.4.dev0 for better Qt5 hooks support
 * removed QtWebKit dependency in Qt, which was switched to the much larger QtWebEngine that was not necessary for this app

2018.07.12

 * fixed Discovery Report Topology execution and handling of discovered nodes
 * added additional roles as viewable on Discovery Report Topology nodes
 * updated order of guessing instance's Splunk role, standalone search head going above license master and deployment server
 * updated Disk Usage in report to show total capacity along with usage



License
-------

Copyright (C) 2015-2018 Joe Misner <joe@misner.net>

See LICENSE.txt in this application's installation directory for
complete license information.

Splunk is a trademark of Splunk Inc. in the United States and other
countries.

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
