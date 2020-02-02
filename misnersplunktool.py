#!/usr/bin/env python3
"""
misnersplunktool.py - Misner Splunk Tool
Copyright (C) 2015-2020 Joe Misner <joe@misner.net>
http://tools.misner.net/

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

Dependencies:
- Python v3.8.1 64-bit, https://www.python.org/
- Python module 'splunk-sdk' v1.6.11, https://pypi.python.org/pypi/splunk-sdk
- Python module 'PySide2' v5.14.1, https://pypi.python.org/pypi/PySide2
- Python module 'Markdown' v3.1.1, https://pypi.python.org/pypi/Markdown
- Python module 'Pygments' v2.5.5, https://pypi.python.org/pypi/Pygments
- Python module 'networkx' v2.4, https://pypi.python.org/pypi/networkx
- Python module 'matplotlib' v3.1.2, https://pypi.python.org/pypi/matplotlib
- Python module 'misnersplunktoolui.py'
- Python module 'misnersplunktooldiscoveryreportui.py'
- Python module 'misnersplunkdwrapper.py'
"""

import sys
import os
import socket
import time
import datetime
import traceback
import math
import re
import csv
import configparser
import markdown
import networkx
import matplotlib.pyplot
from pygments import highlight
from pygments.lexers import XmlLexer, IniLexer
from pygments.formatters import HtmlFormatter
import splunklib.binding as binding
from PySide2 import QtCore, QtWidgets
from misnersplunktoolui import Ui_MainWindow
from misnersplunktooldiscoveryreportui import Ui_DiscoveryReportWindow
from misnersplunkdwrapper import Splunkd

__version__ = '2020.02.01'

SCRIPT_DIR = os.path.dirname(sys.argv[0])
CONFIG_FILENAME = 'misnersplunktool.conf'
CONFIG_DEFAULT = """\
# misnersplunktool.conf -- Misner Splunk Tool configuration file
# Place in same directory as misnersplunktool.exe to import settings

# Main configuration entries
# The default Address, Username, and Password populate these fields when the tool loads
[main]
defaultAddress=localhost:8089
defaultUsername=admin
defaultPassword=changeme

# REST API endpoints populated in the REST API tab's combo box for easy access
# Add sequential entries incrementing from 0
[endpoints]
endpoint.0=/services/server/info
endpoint.1=/services/server/settings

# Metrics and key performance indicators used by the Health Report to identify issues
[healthchecks]
version_caution=6.0  # floating point version number (only major.minor version supported)
version_warning=5.0  # floating point version number (only major.minor version supported)
uptime_caution=604800  # seconds
uptime_warning=86400  # seconds
cpu_cores_caution=12  # total
mem_capacity_caution=31744  # MB
http_ssl_caution=true  # boolean
messages_caution=true  # boolean
cpu_usage_caution=80  # percent utilization
cpu_usage_warning=90  # percent utilization
mem_usage_caution=80  # percent utilization
mem_usage_warning=90  # percent utilization
swap_usage_caution=80  # percent utilization
swap_usage_warning=90  # percent utilization
diskpartition_usage_caution=80  # percent utilization
diskpartition_usage_warning=90  # percent utilization
cluster_maintenance_caution=true  # boolean
cluster_rollingrestart_caution=true  # boolean
cluster_alldatasearchable_warning=true  # boolean
cluster_searchfactor_caution=true  # boolean
cluster_replicationfactor_caution=true  # boolean
cluster_peersnotsearchable_warning=true  # boolean
cluster_searchheadsnotconnected_warning=true  # boolean
shcluster_rollingrestart_caution=true  # boolean
shcluster_serviceready_warning=true  # boolean
shcluster_minpeersjoined_warning=true  # boolean

# Settings used to create Discovery Report topology nodes and adjacencies
# layerheight_ settings determine the y-coordinate layer height or the plotted instance role, from 0-100
# layeralignment_ settings determine if nodes on the layer are aligned to the left, center, or right
# nodecolor_ and adjcolor_ settings use hex color codes, starting with a hash
# nodedraw_ and adjdraw_ settings use boolean values of true or false to determine if they are displayed
[topology]
fontsize=8  # integer
static_width=10  # integer, width in plotted points that nodes on a left- or right-aligned layer are spaced apart
layerheight_user=100  # integer, Users
layerheight_mc=94  # integer, Management Consoles
layerheight_shcd=88  # integer, SHC Deployers
layerheight_sh=80  # integer, Search Heads
layerheight_cm=68  # integer, Cluster Masters
layerheight_idx=60  # integer, Indexers
layerheight_lm=50  # integer, License Masters
layerheight_hf=40  # integer, Heavy Forwarders
layerheight_ds=30  # integer, Deployment Servers
layerheight_uf=20  # integer, Universal Forwarders
layerheight_input=10  # integer, Non-Forwarder Inputs
layerheight_other=0  # integer, Other Instances
layeralignment_user=center
layeralignment_mc=right
layeralignment_shcd=left
layeralignment_sh=center
layeralignment_cm=left
layeralignment_idx=center
layeralignment_lm=right
layeralignment_hf=center
layeralignment_ds=left
layeralignment_uf=center
layeralignment_input=center
layeralignment_other=center
nodecolor_user=d5d8dc
nodecolor_searchhead=abebc6
nodecolor_indexer=aed6f1
nodecolor_heavyforwarder=d98880
nodecolor_universalforwarder=f5b7b1
nodecolor_mgmtconsole=abebc6
nodecolor_shcdeployer=d2b4de
nodecolor_clustermaster=fad7a0
nodecolor_deploymentserver=d7bde2
nodecolor_licensemaster=f9e79f
nodecolor_inputs=e6b0aa
nodecolor_others=d6dbdf
adjcolor_web=808b96
adjcolor_clustermgmt=f8c471
adjcolor_distsearch=82e0aa
adjcolor_mgmtconsole=82e0aa
adjcolor_bucketrep=85c1e9
adjcolor_datafwd=d98880
adjcolor_shcdeployment=bb8fce
adjcolor_deployment=c39bd3
adjcolor_license=f7dc6f
nodedraw_user=true
nodedraw_searchhead=true
nodedraw_indexer=true
nodedraw_heavyforwarder=true
nodedraw_universalforwarder=true
nodedraw_mgmtconsole=True
nodedraw_shcdeployer=true
nodedraw_clustermaster=true
nodedraw_deploymentserver=true
nodedraw_licensemaster=true
nodedraw_inputs=true
nodedraw_others=true
adjdraw_web=true
adjdraw_clustermgmt=true
adjdraw_distsearch=true
adjdraw_mgmtconsole=True
adjdraw_bucketrep=true
adjdraw_datafwdheavyforwarder=true
adjdraw_datafwduniversalforwarder=true
adjdraw_datafwdinput=true
adjdraw_shcdeployment=true
adjdraw_deployment=true
adjdraw_license=true

# splunkd locations saved in the Address combo box
# Create separate stanzas for each saved splunkd location, including the ip/host and management port
# Optionally include keys with username and/or password to populate these fields when selected
[splunkd::1.2.3.4:8089]
username=admin
password=changeme

[splunkd::splunk.myhost.com:8089]
username=admin
password=changeme
"""

ABOUT_TEXT = """
<html>
<h3>Misner Splunk Tool</h3>
Version %s
<p>
Copyright (C) 2015-2020 Joe Misner &lt;<a href="mailto:joe@misner.net">joe@misner.net</a>&gt;<br>
<a href="http://tools.misner.net/">http://tools.misner.net/</a>
<p>
Splunk is a trademark of Splunk Inc. in the United States and other
countries.
<p>
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.
<p>
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
<p>
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation,
Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
<p>
Click the "Show Details" button below for complete license information.
</html>
"""

HEALTHCHECKS = {
    'version_caution': 6.0,
    'version_warning': 5.0,
    'uptime_caution': 604800,
    'uptime_warning': 86400,
    'cpu_cores_caution': 12,
    'mem_capacity_caution': 31744,
    'http_ssl_caution': True,
    'messages_caution': True,
    'cpu_usage_caution': 80,
    'cpu_usage_warning': 90,
    'mem_usage_caution': 80,
    'mem_usage_warning': 90,
    'swap_usage_caution': 80,
    'swap_usage_warning': 90,
    'diskpartition_usage_caution': 80,
    'diskpartition_usage_warning': 90,
    'cluster_maintenance_caution': True,
    'cluster_rollingrestart_caution': True,
    'cluster_alldatasearchable_warning': True,
    'cluster_searchfactor_caution': True,
    'cluster_replicationfactor_caution': True,
    'cluster_peersnotsearchable_warning': True,
    'cluster_searchheadsnotconnected_warning': True,
    'shcluster_rollingrestart_caution': True,
    'shcluster_serviceready_warning': True,
    'shcluster_minpeersjoined_warning': True
}
TOPOLOGY = {
    'fontsize': 8,
    'static_width': 10,
    'layerheight_user': 100,
    'layerheight_mc': 94,
    'layerheight_shcd': 88,
    'layerheight_sh': 80,
    'layerheight_cm': 68,
    'layerheight_idx': 60,
    'layerheight_lm': 50,
    'layerheight_hf': 40,
    'layerheight_ds': 30,
    'layerheight_uf': 20,
    'layerheight_input': 10,
    'layerheight_other': 0,
    'layeralignment_user': 'center',
    'layeralignment_mc': 'right',
    'layeralignment_shcd': 'left',
    'layeralignment_sh': 'center',
    'layeralignment_cm': 'left',
    'layeralignment_idx': 'center',
    'layeralignment_lm': 'right',
    'layeralignment_hf': 'center',
    'layeralignment_ds': 'left',
    'layeralignment_uf': 'center',
    'layeralignment_input': 'center',
    'layeralignment_other': 'center',
    'nodecolor_user': 'd5d8dc',
    'nodecolor_searchhead': 'abebc6',
    'nodecolor_indexer': 'aed6f1',
    'nodecolor_heavyforwarder': 'd98880',
    'nodecolor_universalforwarder': 'f5b7b1',
    'nodecolor_mgmtconsole': 'abebc6',
    'nodecolor_shcdeployer': 'd2b4de',
    'nodecolor_clustermaster': 'fad7a0',
    'nodecolor_deploymentserver': 'd7bde2',
    'nodecolor_licensemaster': 'f9e79f',
    'nodecolor_inputs': 'e6b0aa',
    'nodecolor_others': 'd6dbdf',
    'adjcolor_web': '808b96',
    'adjcolor_clustermgmt': 'f8c471',
    'adjcolor_distsearch': '82e0aa',
    'adjcolor_mgmtconsole': '82e0aa',
    'adjcolor_bucketrep': '85c1e9',
    'adjcolor_datafwd': 'd98880',
    'adjcolor_shcdeployment': 'bb8fce',
    'adjcolor_deployment': 'c39bd3',
    'adjcolor_license': 'f7dc6f',
    'nodedraw_user': True,
    'nodedraw_searchhead': True,
    'nodedraw_indexer': True,
    'nodedraw_heavyforwarder': True,
    'nodedraw_universalforwarder': True,
    'nodedraw_mgmtconsole': True,
    'nodedraw_shcdeployer': True,
    'nodedraw_clustermaster': True,
    'nodedraw_deploymentserver': True,
    'nodedraw_licensemaster': True,
    'nodedraw_inputs': True,
    'nodedraw_others': True,
    'adjdraw_web': True,
    'adjdraw_clustermgmt': True,
    'adjdraw_distsearch': True,
    'adjdraw_mgmtconsole': True,
    'adjdraw_bucketrep': True,
    'adjdraw_datafwdheavyforwarder': True,
    'adjdraw_datafwduniversalforwarder': True,
    'adjdraw_datafwdinput': True,
    'adjdraw_shcdeployment': True,
    'adjdraw_deployment': True,
    'adjdraw_license': True
}


def fatal_error(txt):
    """Prints error to syserr in standard Unix format with filename, to main window if it exists, as well as to file
     error.log in the current directory, then quits"""
    try:
        main_window.critical_msg(txt)
    except NameError:
        pass
    try:
        with open(os.path.join(SCRIPT_DIR, 'error.log'), 'a') as error_log:
            current_local = time.strftime("%m/%d/%Y %I:%M:%S %p", time.localtime())
            error_log_text = "%s - %s\n" % (current_local, txt)
            error_log.write(error_log_text)
    except:
        pass
    exitcode = "\n%s: error: %s" % (os.path.basename(sys.argv[0]), txt)
    sys.exit(exitcode)


def unhandled_exception(etype, value, tb):
    exc = traceback.format_exception(etype, value, tb)
    msg = "Unhandled exception, exiting application.\n\n%s" % ''.join(exc)
    fatal_error(msg)
sys.excepthook = unhandled_exception


def human_time(*args, **kwargs):
    """Convert datetime.timedelta to human readable value"""
    secs  = float(datetime.timedelta(*args, **kwargs).total_seconds())
    units = [("day", 86400), ("hr", 3600), ("min", 60), ("sec", 1)]
    parts = []
    for unit, mul in units:
        if secs / mul >= 1 or mul == 1:
            if mul > 1:
                n = int(math.floor(secs / mul))
                secs -= n * mul
            else:
                n = secs if secs != int(secs) else int(secs)
            parts.append("%s %s%s" % (n, unit, "" if n == 1 else "s"))
    return " ".join(parts)


def pretty_time_delta(seconds):
    """Returns time delta in easily readable format"""
    output = '-' if seconds < 0 else ''
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        output += ' %d day%s' % (days, 's' if days > 1 else '')
    if hours > 0:
        output += ' %d hr%s' % (hours, 's' if hours > 1 else '')
    if minutes > 0:
        output += ' %d min%s' % (minutes, 's' if minutes > 1 else '')
    if seconds > 0:
        output += ' %d sec%s' % (seconds, 's' if seconds > 1 else '')
    return output.strip()


class MainWindow(QtWidgets.QMainWindow):
    """Object class for the main window"""
    def __init__(self):
        """Executed when the MainWindow() object is created"""
        # GUI Setup
        #  Basics
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.show()
        self.disconnect()

        #  General tab
        self.ui.tableMessages.setColumnWidth(0, 140)  # Time Created
        self.ui.tableMessages.setColumnWidth(1, 55)   # Severity
        self.ui.tableMessages.setColumnWidth(2, 150)  # Title
        self.ui.tableMessages.setColumnWidth(3, 340)  # Description
        self.ui.tableMessages.sortByColumn(0, QtCore.Qt.AscendingOrder)

        #  Report tab
        self.ui.tableReport.setColumnWidth(0, 80)   # Category
        self.ui.tableReport.setColumnWidth(1, 170)  # Name
        self.ui.tableReport.setColumnWidth(2, 80)   # Health
        self.ui.tableReport.setColumnWidth(3, 340)  # Value

        #  Input Status tab
        self.ui.tableFileStatus.setColumnWidth(0, 420)  # Location
        self.ui.tableFileStatus.setColumnWidth(1, 100)  # Type
        self.ui.tableFileStatus.setColumnWidth(2, 50)   # Percent
        self.ui.tableFileStatus.setColumnWidth(3, 70)   # Position
        self.ui.tableFileStatus.setColumnWidth(4, 70)   # Size
        self.ui.tableFileStatus.setColumnWidth(5, 400)  # Parent
        self.ui.tableFileStatus.sortByColumn(0, QtCore.Qt.AscendingOrder)

        self.ui.tableTCP.setColumnWidth(0, 70)   # TCP Type
        self.ui.tableTCP.setColumnWidth(1, 50)   # Port
        self.ui.tableTCP.setColumnWidth(2, 300)  # Source
        self.ui.tableTCP.setColumnWidth(3, 150)  # Time Opened
        self.ui.tableTCP.sortByColumn(0, QtCore.Qt.AscendingOrder)

        self.ui.tableUDP.setColumnWidth(0, 300)  # Source
        self.ui.tableUDP.sortByColumn(0, QtCore.Qt.AscendingOrder)

        self.ui.tableModular.setColumnWidth(0, 420)  # Location
        self.ui.tableModular.setColumnWidth(1, 110)  # Exit Status
        self.ui.tableModular.setColumnWidth(2, 150)  # Opened
        self.ui.tableModular.setColumnWidth(3, 150)  # Closed
        self.ui.tableModular.setColumnWidth(4, 70)   # Total Bytes
        self.ui.tableModular.sortByColumn(0, QtCore.Qt.AscendingOrder)

        self.ui.tableExec.setColumnWidth(0, 420)  # Location
        self.ui.tableExec.setColumnWidth(1, 110)  # Exit Status
        self.ui.tableExec.setColumnWidth(2, 150)  # Opened
        self.ui.tableExec.setColumnWidth(3, 150)  # Closed
        self.ui.tableExec.setColumnWidth(4, 70)   # Total Bytes
        self.ui.tableExec.sortByColumn(0, QtCore.Qt.AscendingOrder)

        #  Apps tab
        self.ui.tableApps.setColumnWidth(0, 50)   # Active
        self.ui.tableApps.setColumnWidth(1, 180)  # Title
        self.ui.tableApps.setColumnWidth(2, 50)   # Version
        self.ui.tableApps.setColumnWidth(3, 180)  # Label
        self.ui.tableApps.setColumnWidth(4, 300)  # Description
        self.ui.tableApps.sortByColumn(1, QtCore.Qt.AscendingOrder)

        #  Indexer Cluster tab
        #   Peers tab
        self.ui.tableClusterPeers.setColumnWidth(0, 200)  # Peer Name
        self.ui.tableClusterPeers.setColumnWidth(1, 50)   # Site
        self.ui.tableClusterPeers.setColumnWidth(2, 100)  # Fully Searchable
        self.ui.tableClusterPeers.setColumnWidth(3, 50)   # Status
        self.ui.tableClusterPeers.setColumnWidth(4, 50)   # Buckets
        self.ui.tableClusterPeers.setColumnWidth(5, 120)  # Location
        self.ui.tableClusterPeers.setColumnWidth(6, 150)  # Last Heartbeat
        self.ui.tableClusterPeers.setColumnWidth(7, 100)  # Replication Port
        self.ui.tableClusterPeers.setColumnWidth(8, 110)  # Base Generation ID
        self.ui.tableClusterPeers.setColumnWidth(9, 250)  # GUID
        self.ui.tableClusterPeers.sortByColumn(0, QtCore.Qt.AscendingOrder)
        #   Indexes tab
        self.ui.tableClusterIndexes.setColumnWidth(0, 150)  # Index Name
        self.ui.tableClusterIndexes.setColumnWidth(1, 100)  # Fully Searchable
        self.ui.tableClusterIndexes.setColumnWidth(2, 150)  # Searchable Data Copies
        self.ui.tableClusterIndexes.setColumnWidth(3, 150)  # Replicated Data Copies
        self.ui.tableClusterIndexes.setColumnWidth(4, 50)   # Buckets
        self.ui.tableClusterIndexes.setColumnWidth(5, 150)  # Cumulative Raw Data Size
        self.ui.tableClusterIndexes.sortByColumn(0, QtCore.Qt.AscendingOrder)
        #   Search Heads tab
        self.ui.tableClusterSearchHeads.setColumnWidth(0, 200)  # Search Head Name
        self.ui.tableClusterSearchHeads.setColumnWidth(1, 50)   # Site
        self.ui.tableClusterSearchHeads.setColumnWidth(2, 100)  # Status
        self.ui.tableClusterSearchHeads.setColumnWidth(3, 150)  # Location
        self.ui.tableClusterSearchHeads.setColumnWidth(4, 250)  # GUID
        self.ui.tableClusterSearchHeads.sortByColumn(0, QtCore.Qt.AscendingOrder)

        #  Search Head Cluster tab
        self.ui.tableSHClusterMembers.setColumnWidth(0, 200)  # Peer Name
        self.ui.tableSHClusterMembers.setColumnWidth(1, 50)   # Site
        self.ui.tableSHClusterMembers.setColumnWidth(2, 50)   # Status
        self.ui.tableSHClusterMembers.setColumnWidth(3, 60)   # Artifacts
        self.ui.tableSHClusterMembers.setColumnWidth(4, 120)  # Location
        self.ui.tableSHClusterMembers.setColumnWidth(5, 150)  # Last Heartbeat
        self.ui.tableSHClusterMembers.setColumnWidth(6, 100)  # Replication Port
        self.ui.tableSHClusterMembers.setColumnWidth(7, 100)  # Restart Required
        self.ui.tableSHClusterMembers.setColumnWidth(8, 250)  # GUID
        self.ui.tableSHClusterMembers.sortByColumn(0, QtCore.Qt.AscendingOrder)

        # Resource Usage tab
        self.ui.progressResourceUsageCPU.setStyleSheet(
            "QProgressBar { border: 2px solid grey; border-radius: 0px; text-align: center; } "
            "QProgressBar::chunk {background-color: #3add36; width: 1px;}")
        self.ui.progressResourceUsageMemory.setStyleSheet(
            "QProgressBar { border: 2px solid grey; border-radius: 0px; text-align: center; } "
            "QProgressBar::chunk {background-color: #3add36; width: 1px;}")
        self.ui.progressResourceUsageSwap.setStyleSheet(
            "QProgressBar { border: 2px solid grey; border-radius: 0px; text-align: center; } "
            "QProgressBar::chunk {background-color: #3add36; width: 1px;}")
        self.ui.tableResourceUsageProcesses.setColumnWidth(0, 70)   # Process
        self.ui.tableResourceUsageProcesses.setColumnWidth(1, 40)   # PID
        self.ui.tableResourceUsageProcesses.setColumnWidth(2, 40)   # PPID
        self.ui.tableResourceUsageProcesses.setColumnWidth(3, 40)   # CPU
        self.ui.tableResourceUsageProcesses.setColumnWidth(4, 40)   # RAM
        self.ui.tableResourceUsageProcesses.setColumnWidth(5, 200)  # Args
        self.ui.tableResourceUsageProcesses.sortByColumn(1, QtCore.Qt.AscendingOrder)
        self.ui.tableResourceUsageDisks.setColumnWidth(0, 170)  # Mount
        self.ui.tableResourceUsageDisks.setColumnWidth(1, 50)   # Type
        self.ui.tableResourceUsageDisks.setColumnWidth(2, 40)   # Used
        self.ui.tableResourceUsageDisks.setColumnWidth(3, 60)   # Total
        self.ui.tableResourceUsageDisks.sortByColumn(0, QtCore.Qt.AscendingOrder)

        # Signals and Slots
        #  Menubar
        self.ui.actionBuildMisnersplunktoolConf.triggered.connect(self.actionBuildMisnersplunktoolConf_triggered)
        self.ui.actionSaveReport.triggered.connect(self.actionSaveReport_triggered)
        #self.ui.actionSaveSplunkInstanceCredentials.triggered.connect(
        #  self.actionSaveSplunkInstanceCredentials_triggered
        #)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionRestartSplunkd.triggered.connect(self.actionRestartSplunkd_clicked)
        self.ui.actionRefreshConfigurations.triggered.connect(self.actionRefreshConfigurations_clicked)
        self.ui.actionChangeDeploymentServer.triggered.connect(self.actionChangeDeploymentServer_clicked)
        self.ui.actionDiscoveryReport.triggered.connect(self.actionDiscoveryReport_clicked)
        self.ui.actionHelp.triggered.connect(self.actionHelp_triggered)
        self.ui.actionAbout.triggered.connect(self.actionAbout_triggered)
        #  Top
        self.ui.comboAddress.activated.connect(self.comboAddress_activated)
        self.ui.comboAddress.lineEdit().returnPressed.connect(self.buttonToggle_clicked)
        self.ui.editUsername.returnPressed.connect(self.buttonToggle_clicked)
        self.ui.editPassword.returnPressed.connect(self.buttonToggle_clicked)
        self.ui.buttonToggle.clicked.connect(self.buttonToggle_clicked)
        self.ui.buttonPoll.clicked.connect(self.poll)
        #  General tab
        self.ui.buttonRestartSplunkd.clicked.connect(self.actionRestartSplunkd_clicked)
        self.ui.buttonRefreshConfigurations.clicked.connect(self.actionRefreshConfigurations_clicked)
        #  Report tab
        #  Configuration tab
        self.ui.comboConfig.activated.connect(self.comboConfig_activated)

        #  Input Status tab
        #  Apps tab
        #  Cluster tab
        self.ui.checkClusterDataSearchable.clicked.connect(self.checkCluster_clicked)
        self.ui.checkClusterSearchFactorMet.clicked.connect(self.checkCluster_clicked)
        self.ui.checkClusterReplicationFactorMet.clicked.connect(self.checkCluster_clicked)
        self.ui.checkClusterMaintenanceMode.clicked.connect(self.checkCluster_clicked)
        self.ui.checkClusterRollingRestartFlag.clicked.connect(self.checkCluster_clicked)
        self.ui.checkClusterInitializedFlag.clicked.connect(self.checkCluster_clicked)
        self.ui.checkClusterServiceReadyFlag.clicked.connect(self.checkCluster_clicked)
        self.ui.checkClusterIndexingReadyFlag.clicked.connect(self.checkCluster_clicked)
        #  Cluster tab
        self.ui.checkSHClusterInitializedFlag.clicked.connect(self.checkSHCluster_clicked)
        self.ui.checkSHClusterServiceReadyFlag.clicked.connect(self.checkSHCluster_clicked)
        self.ui.checkSHClusterMinimumPeersJoinedFlag.clicked.connect(self.checkSHCluster_clicked)
        self.ui.checkSHClusterDynamicCaptain.clicked.connect(self.checkSHCluster_clicked)
        self.ui.checkSHClusterRollingRestartFlag.clicked.connect(self.checkSHCluster_clicked)
        #  REST API tab
        self.ui.comboRestURI.lineEdit().returnPressed.connect(self.buttonRestSend_clicked)
        self.ui.buttonRestSend.clicked.connect(self.buttonRestSend_clicked)

        # Load defaults
        #self.poll_interval = POLL_INTERVAL

        # Load misnersplunktool.conf configurations
        # Build health checks dictionary of defaults, in case values in configuration are not present
        self.healthchecks = HEALTHCHECKS
        self.topology = TOPOLOGY
        try:
            self.pull_configs()
        except:
            msg = "Error while pulling configurations from misnersplunktool.conf\n" \
                  "Check formatting in file. If error persists, delete the file and restart."
            self.critical_msg(msg)
            fatal_error(msg)

    def resizeEvent(self, event):
        """Resizes widgets as window size changes"""
        # MainWindow
        self.ui.comboAddress.resize(self.ui.centralwidget.width() - 458, self.ui.comboAddress.height())
        self.ui.labelUsername.move(self.ui.centralwidget.width() - 389, self.ui.labelUsername.y())
        self.ui.editUsername.move(self.ui.centralwidget.width() - 389, self.ui.editUsername.y())
        self.ui.labelPassword.move(self.ui.centralwidget.width() - 269, self.ui.labelPassword.y())
        self.ui.editPassword.move(self.ui.centralwidget.width() - 269, self.ui.editPassword.y())
        self.ui.buttonToggle.move(self.ui.centralwidget.width() - 149, self.ui.buttonToggle.y())
        self.ui.buttonPoll.move(self.ui.centralwidget.width() - 61, self.ui.buttonPoll.y())
        self.ui.labelOS.resize(self.ui.centralwidget.width() - 608, self.ui.labelOS.height())
        self.ui.labelSystem.resize(self.ui.centralwidget.width() - 608, self.ui.labelSystem.height())
        self.ui.labelHealth.move(self.ui.centralwidget.width() - 29, self.ui.labelHealth.y())

        t = self.ui.tabWidgetMain
        t.resize(self.ui.centralwidget.width() - 18, self.ui.centralwidget.height() - 115)

        # General tab
        self.ui.boxDeployment.resize(t.width() - 290, self.ui.boxDeployment.height())
        self.ui.labelDeploymentServer.resize(t.width() - 510, self.ui.labelDeploymentServer.height())
        self.ui.labelClusterMaster.resize(t.width() - 510, self.ui.labelClusterMaster.height())
        self.ui.labelSHCDeployer.resize(t.width() - 510, self.ui.labelSHCDeployer.height())
        self.ui.boxMessages.resize(t.width() - 20, t.height() - 126)
        self.ui.tableMessages.resize(t.width() - 40, t.height() - 156)

        # Report tab
        self.ui.tableReport.resize(t.width() - 20, t.height() - 40)

        # Configuration tab
        self.ui.editConfig.resize(t.width() - 20, t.height() - 70)

        # Input Status tab
        self.ui.tabWidgetInputStatus.resize(t.width() - 20, t.height() - 40)
        self.ui.tableFileStatus.resize(t.width() - 40, t.height() - 80)
        self.ui.tableTCP.resize(t.width() - 40, t.height() - 80)
        self.ui.tableUDP.resize(t.width() - 40, t.height() - 80)
        self.ui.tableModular.resize(t.width() - 40, t.height() - 80)
        self.ui.tableExec.resize(t.width() - 40, t.height() - 80)

        # Apps tab
        self.ui.tableApps.resize(t.width() - 20, t.height() - 40)

        # Indexer Cluster tab
        self.ui.tabWidgetCluster.resize(t.width() - 20, t.height() - 110)
        self.ui.tableClusterPeers.resize(t.width() - 40, t.height() - 150)
        self.ui.tableClusterIndexes.resize(t.width() - 40, t.height() - 150)
        self.ui.tableClusterSearchHeads.resize(t.width() - 40, t.height() - 150)

        # Search Head Cluster tab
        self.ui.tableSHClusterMembers.resize(t.width() - 20, t.height() - 110)

        # Resource Usage tab
        self.ui.tableResourceUsageProcesses.resize(self.ui.tableResourceUsageProcesses.width(), t.height() - 90)
        self.ui.tableResourceUsageDisks.resize(t.width() - 380, t.height() - 90)

        # REST API tab
        self.ui.comboRestURI.resize(t.width() - 210, self.ui.comboRestURI.height())
        self.ui.editRestBodyInput.resize(t.width() - 210, self.ui.editRestBodyInput.height())
        self.ui.buttonRestSend.move(t.width() - 81, self.ui.buttonRestSend.y())
        self.ui.editRestResult.resize(t.width() - 20, t.height() - 90)

    def statusbar_msg(self, msg):
        """Sends a message to the statusbar"""
        self.ui.statusbar.showMessage(msg)
        QtCore.QCoreApplication.processEvents()

    def question_msg_yesno(self, msg):
        dialog_answer = QtWidgets.QMessageBox.question(self, "Misner Splunk Tool", msg,
                                                       QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if dialog_answer == QtWidgets.QMessageBox.StandardButton.Yes:
            return True
        else:
            return False

    def information_msg(self, msg):
        """Creates an information dialog"""
        QtWidgets.QMessageBox.information(self, "Misner Splunk Tool", msg)

    def warning_msg(self, msg):
        """Creates a warning dialog"""
        QtWidgets.QMessageBox.warning(self, "Misner Splunk Tool", msg)

    def critical_msg(self, msg):
        """Creates a critical dialog"""
        QtWidgets.QMessageBox.critical(self, "Misner Splunk Tool", msg)

    def pull_configs(self):
        """Pull in configurations from flat configuration file misnersplunktool.conf"""
        for section in config.sections():
            if section[0:9] == 'splunkd::':
                self.ui.comboAddress.addItem(section[9:])

        # Pull REST API endpoints
        if config.has_section('endpoints'):
            endpoint_number = 0
            while config.has_option('endpoints', 'endpoint.%s' % endpoint_number):
                uri = config.get('endpoints', 'endpoint.%s' % endpoint_number)
                self.ui.comboRestURI.addItem(uri)
                endpoint_number += 1

        def fixtype(object):
            """Returns the object as the correct type: a boolean, integer, floating point, or string"""
            if object.lower() == 'true':
                return True
            elif object.lower() == 'false':
                return False
            try:
                return int(object)
            except ValueError:
                try:
                    return float(object)
                except ValueError:
                    return str(object)

        # Pull health check values
        if config.has_section('healthchecks'):
            for option in config.options('healthchecks'):
                value = config.get('healthchecks', option)
                try:  # Remove comments from key=value pair
                    if '#' in value:
                        value = re.findall(r"^([\.\w]+)\s*#.*$", value)[0]
                except:  # Some bad formatting broke the regex parser
                    msg = "Error while pulling configurations from misnersplunktool.conf\n" \
                          "Check formatting of [healthchecks] option %s within this file." % option
                    self.critical_msg(msg)
                    fatal_error(msg)

                self.healthchecks[option] = fixtype(value.strip())

        # Pull topology values
        if config.has_section('topology'):
            for option in config.options('topology'):
                value = config.get('topology', option)
                try:  # Remove comments from key=value pair
                    if '#' in value:
                        value = re.findall(r"^([\.\w]+)\s*#.*$", value)[0]
                except:  # Some bad formatting broke the regex parser
                    msg = "Error while pulling configurations from misnersplunktool.conf\n" \
                          "Check formatting of [topology] option %s within this file." % option
                    self.critical_msg(msg)
                    fatal_error(msg)

                self.topology[option] = fixtype(value.strip())

        # Pull other config values
        if config.has_option('main', 'defaultAddress'):
            self.ui.comboAddress.setEditText(config.get('main', 'defaultAddress'))
        if config.has_option('main', 'defaultUsername'):
            self.ui.editUsername.setText(config.get('main', 'defaultUsername'))
        if config.has_option('main', 'defaultPassword'):
            self.ui.editPassword.setText(config.get('main', 'defaultPassword'))
        if config.has_option('main', 'pollInterval'):
            try:
                self.poll_interval = config.getint('main', 'pollInterval')
            except:
                self.warning_msg("Bad poll interval value in configuration, must be an integer")

    def connect(self):
        """Connect to Splunkd"""
        splunk_host = self.ui.comboAddress.currentText().strip()
        splunk_user = self.ui.editUsername.text().strip()
        splunk_pass = self.ui.editPassword.text().strip()

        # Check address, username, and password fields
        if not splunk_host:
            self.warning_msg("Missing Splunk address")
            return
        if not splunk_user:
            self.warning_msg("Missing Splunk username")
            return
        if not splunk_pass:
            self.warning_msg("Missing Splunk password")
            return
        if ':' in splunk_host:
            splunk_host, splunk_port = self.ui.comboAddress.currentText().split(':')
            splunk_port = int(splunk_port)
        else:
            splunk_port = 8089
        if not 0 < splunk_port < 65536:
            self.warning_msg("Invalid port specified")
            return

        # Create Splunk instance
        host = "'%s:%s'" % (splunk_host, splunk_port)
        self.statusbar_msg("Connecting to host %s..." % host)
        try:
            self.splunkd = Splunkd(splunk_host, splunk_port, splunk_user, splunk_pass)
        except binding.AuthenticationError:
            self.warning_msg("Authentication error connecting to host %s" % host)
            return
        except socket.gaierror:
            self.warning_msg("Unable to connect to host %s" % host)
            return
        except socket.error as error:
            self.warning_msg("Unable to connect to host %s:\n"
                             "%s" % (host, error))
            return
        finally:
            self.statusbar_msg('Connection failed')
        self.statusbar_msg('Connected')

        # Toggle GUI fields
        self.ui.comboAddress.setEnabled(False)
        self.ui.editUsername.setEnabled(False)
        self.ui.editPassword.setEnabled(False)
        self.ui.tabWidgetMain.setEnabled(True)
        self.ui.buttonPoll.setEnabled(True)
        self.ui.buttonToggle.setText('Disconnect')

        # Poll Splunk instance
        self.poll()
        self.setWindowTitle('%s - Misner Splunk Tool' % self.splunkd.server_name)
        if 'cluster_master' in self.splunkd.roles:
            self.ui.tabCluster.setEnabled(True)
        else:
            self.ui.tabCluster.setEnabled(False)
        if 'shc_member' in self.splunkd.roles:
            self.ui.tabSHCluster.setEnabled(True)
        else:
            self.ui.tabSHCluster.setEnabled(False)

    def disconnect(self):
        """Disconnect from Splunkd"""
        # Destroy the splunkd instance
        try:
            del self.splunkd
        except AttributeError:
            pass

        # Toggle GUI fields
        self.setWindowTitle('Misner Splunk Tool')
        self.ui.comboAddress.setEnabled(True)
        self.ui.editUsername.setEnabled(True)
        self.ui.editPassword.setEnabled(True)
        self.ui.tabWidgetMain.setEnabled(False)
        self.ui.buttonPoll.setEnabled(False)
        self.ui.buttonToggle.setText('Connect')

        # Reset labels
        #  Top
        self.ui.labelRole.setPixmap(":/blank.png")
        self.ui.labelRole.setToolTip(None)
        self.ui.labelHealth.setPixmap(":/health_unknown.png")
        self.ui.labelHealth.setToolTip(None)
        self.ui.labelHost.setText('(none)')
        self.ui.labelType.setText('(none)')
        self.ui.labelGUID.setText('(none)')
        self.ui.labelOS.setText('(none)')
        self.ui.labelOS.setToolTip('(none)')
        self.ui.labelSystem.setText('(none)')
        self.ui.labelUptime.setText('(none)')
        self.ui.labelUptime.setToolTip(None)
        #  General tab
        self.ui.tableMessages.setRowCount(0)
        self.ui.labelRestartRequired.setText('?')
        self.ui.labelDeploymentServer.setText('(none)')
        self.ui.labelDeploymentServer.setToolTip(None)
        self.ui.labelClusterMasterHeader.setText('Cluster Master:')
        self.ui.labelClusterMaster.setText('(none)')
        self.ui.labelClusterMaster.setToolTip(None)
        self.ui.labelSHCDeployer.setText('(none)')
        self.ui.labelSHCDeployer.setToolTip(None)
        #  Report tab
        self.ui.tableReport.setRowCount(0)
        #  Configuration tab
        self.ui.editConfig.setHtml(None)
        #  Input Status tab
        self.ui.tableFileStatus.setRowCount(0)
        self.ui.tableTCP.setRowCount(0)
        self.ui.tableUDP.setRowCount(0)
        self.ui.tableModular.setRowCount(0)
        self.ui.tableExec.setRowCount(0)
        self.ui.tableApps.setRowCount(0)
        #  Indexer Cluster tab
        self.ui.checkClusterDataSearchable.setChecked(False)
        self.ui.checkClusterSearchFactorMet.setChecked(False)
        self.ui.checkClusterReplicationFactorMet.setChecked(False)
        self.ui.labelClusterPeersSearchable.setText('? searchable')
        self.ui.labelClusterPeersNotSearchable.setText('? not searchable')
        self.ui.labelClusterIndexesSearchable.setText('? searchable')
        self.ui.labelClusterIndexesNotSearchable.setText('? not searchable')
        self.ui.labelClusterPeersUp.setText('?/? Peers Up')
        self.ui.labelClusterSearchHeadsUp.setText('?/? Search Heads Up')
        self.ui.checkClusterMaintenanceMode.setChecked(False)
        self.ui.checkClusterRollingRestartFlag.setChecked(False)
        self.ui.checkClusterInitializedFlag.setChecked(False)
        self.ui.checkClusterServiceReadyFlag.setChecked(False)
        self.ui.checkClusterIndexingReadyFlag.setChecked(False)
        self.ui.tableClusterPeers.setRowCount(0)
        self.ui.tableClusterIndexes.setRowCount(0)
        self.ui.tableClusterSearchHeads.setRowCount(0)
        #  Search Head Cluster tab
        self.ui.checkSHClusterInitializedFlag.setChecked(False)
        self.ui.checkSHClusterServiceReadyFlag.setChecked(False)
        self.ui.checkSHClusterMinimumPeersJoinedFlag.setChecked(False)
        self.ui.checkSHClusterDynamicCaptain.setChecked(False)
        self.ui.checkSHClusterRollingRestartFlag.setChecked(False)
        self.ui.labelSHClusterCaptain.setText('(none)')
        self.ui.labelSHClusterCaptainElected.setText('(none)')
        self.ui.tableSHClusterMembers.setRowCount(0)
        #  Resource Usage tab
        self.ui.progressResourceUsageCPU.setValue(0)
        self.ui.progressResourceUsageMemory.setValue(0)
        self.ui.labelResourceUsageMemory.setText('(none)')
        self.ui.labelResourceUsageSwapHeader.setText('Swap:')
        self.ui.progressResourceUsageSwap.setValue(0)
        self.ui.labelResourceUsageSwap.setText('(none)')
        self.ui.tableResourceUsageProcesses.setRowCount(0)
        self.ui.tableResourceUsageDisks.setRowCount(0)
        #  REST API tab
        self.ui.editRestResult.setHtml(None)

        self.statusbar_msg('Disconnected')

    def poll(self):
        """Poll for new Splunkd values"""
        # Check connection with splunkd
        try:
            self.splunkd.service.settings
        except binding.AuthenticationError:
            self.disconnect()
            self.critical_msg('Splunk connection reset')
            return
        except socket.error as e:
            self.disconnect()
            self.critical_msg("Socket error while attempting to poll splunkd:\n"
                              "%s" % e)
            return
        except:
            self.disconnect()
            self.critical_msg('Unknown error while attempting to poll splunkd')
            return

        # Poll splunkd
        try:
            self.statusbar_msg('Polling service info...')
            self.splunkd.poll_service_info()
            self.statusbar_msg('Polling settings...')
            self.splunkd.poll_service_settings()
            self.statusbar_msg('Polling messages...')
            self.splunkd.poll_service_messages()
            self.statusbar_msg('Polling configurations...')
            self.splunkd.get_service_confs()
            self.statusbar_msg('Polling input status...')
            self.splunkd.get_services_admin_inputstatus()
            self.statusbar_msg('Polling apps...')
            self.splunkd.poll_service_apps()
            self.statusbar_msg('Polling data collection info...')
            self.splunkd.get_services_data()
            self.statusbar_msg('Polling KV store info...')
            self.splunkd.get_services_kvstore()
            self.statusbar_msg('Polling cluster master info...')
            self.splunkd.get_services_cluster()
            self.statusbar_msg('Polling search head cluster info...')
            self.splunkd.get_services_shcluster()
            self.statusbar_msg('Polling deployment info...')
            self.splunkd.get_services_deployment()
            self.statusbar_msg('Polling licensing info...')
            self.splunkd.get_services_licenser()
            self.statusbar_msg('Polling distributed search info...')
            self.splunkd.get_services_search()
            self.statusbar_msg('Polling health...')
            self.splunkd.get_services_server_health_details()
            self.statusbar_msg('Polling introspection...')
            self.splunkd.get_services_server_status()
        except socket.error as e:
            self.disconnect()
            self.critical_msg("Socket error while attempting to poll splunkd:\n"
                              "%s" % e)
            return

        # Build instance report
        self.statusbar_msg('Building report...')
        self.splunkd.report_builder(self.healthchecks)

        # Setup Splunk icon
        self.statusbar_msg('Populating GUI, Splunk icon...')
        roles = ['Server Roles:']
        for role in self.splunkd.roles:
            roles.append(role)
        self.ui.labelRole.setToolTip('\n'.join(roles))
        role_icons = {  # Map this instance's 'guessed' primary role to an appropriate icon
            "Cluster Master": ':/masternode.png',
            "Deployer (SHC)": ':/deploymentserver.png',
            "Deployment Server": ':/deploymentserver.png',
            "Forwarder": ':/forwarder.png',
            "Heavy Forwarder": ':/heavyforwarder.png',
            "Indexer (Cluster Slave)": ':/indexer.png',
            "Indexer (Standalone)": ':/indexer.png',
            "License Master": ':/licenseserver.png',
            "Management Console": ':/managementconsole.png',
            "Search Head (Standalone)": ':/searchhead.png',
            "Search Head (SHC Member)": ':/searchhead.png',
            "Search Head (SHC Captain)": ':/searchhead.png',
            "Universal Forwarder": ':/forwarder.png'
        }
        self.ui.labelRole.setPixmap(role_icons[self.splunkd.primary_role])

        # Setup health icon
        self.statusbar_msg('Populating GUI, health icon...')
        health = ['Splunkd Health = ' + self.splunkd.health_splunkd_overall + '\n\nFeatures:']
        features = self.splunkd.health_splunkd_features
        for feature in features:
            health.append(feature + " = " + features[feature])
        self.ui.labelHealth.setToolTip('\n'.join(health))
        health_icons = {  # Map this instance's splunkd health to an appropriate icon
            "green": ':/health_green.png',
            "yellow": ':/health_yellow.png',
            "red": ':/health_red.png',
            "unknown": ':/health_unknown.png'
        }
        self.ui.labelHealth.setPixmap(health_icons[self.splunkd.health_splunkd_overall])

        # Fill in top labels
        self.statusbar_msg('Populating GUI, top labels...')
        self.ui.labelHost.setText(self.splunkd.host)
        self.ui.labelType.setText(self.splunkd.type)
        self.ui.labelGUID.setText(self.splunkd.guid)
        self.ui.labelOS.setText(self.splunkd.os)
        self.ui.labelOS.setToolTip(self.splunkd.os)
        self.ui.labelSystem.setText("%s core%s, %s MB RAM" % (self.splunkd.cores if self.splunkd.cores > 0 else '?',
                                                              '' if self.splunkd.cores == 1 else 's',
                                                              self.splunkd.ram if self.splunkd.ram > 0 else '?'))
        if self.splunkd.startup_time:
            uptime = pretty_time_delta(int(time.time()) - self.splunkd.startup_time)
        else:
            uptime = '(unknown)'
        self.ui.labelUptime.setText(uptime)
        self.ui.labelUptime.setToolTip('splunkd start time: %s' % self.splunkd.startup_time_formatted)

        # Fill in General tab
        self.statusbar_msg('Populating GUI, General tab...')
        restart_required = 'Yes' if self.splunkd.service.restart_required else 'No'
        self.ui.labelRestartRequired.setText(restart_required)
        if 'Enterprise' in self.splunkd.type:
            self.ui.buttonRefreshConfigurations.setEnabled(True)
        else:
            self.ui.buttonRefreshConfigurations.setEnabled(False)
        self.ui.labelDeploymentServer.setText(self.splunkd.deployment_server)
        self.ui.labelDeploymentServer.setToolTip(self.splunkd.deployment_server)

        if self.splunkd.cluster_mode == 'master':
            self.ui.labelClusterMasterHeader.setText('Cluster Master:')
        elif self.splunkd.cluster_mode == 'slave':
            self.ui.labelClusterMasterHeader.setText('Peer of Cluster Master:')
        elif self.splunkd.cluster_mode == 'searchhead':
            self.ui.labelClusterMasterHeader.setText('Search Head of Cluster Master(s):')
        else:
            self.ui.labelClusterMasterHeader.setText('Cluster Master:')
        self.ui.labelClusterMaster.setText(self.splunkd.cluster_master_uri)
        self.ui.labelClusterMaster.setToolTip(self.splunkd.cluster_master_uri)

        self.ui.labelSHCDeployer.setText(self.splunkd.shcluster_deployer)
        self.ui.labelSHCDeployer.setToolTip(self.splunkd.shcluster_deployer)

        self.table_builder(
            self.ui.tableMessages,
            self.splunkd.messages,
            ['time_created', 'severity', 'title', 'description']
        )
        self.ui.tableMessages.resizeRowsToContents()

        # Fill in Report tab
        self.statusbar_msg('Populating GUI, Report tab...')
        self.table_builder(
            self.ui.tableReport,
            self.splunkd.report,
            ['category', 'name', 'health', 'value'],
            sorting=False
        )

        # Fill in Configuration tab
        self.statusbar_msg('Populating GUI, Configuration tab...')
        self.ui.comboConfig.clear()
        self.ui.comboConfig.addItems(self.splunkd.configuration_files)
        self.ui.comboConfig.setCurrentIndex(self.ui.comboConfig.findText('server'))
        self.ui.editConfig.setHtml(None)
        self.comboConfig_activated()

        # Fill in Input Status tab
        self.statusbar_msg('Populating GUI, Input Status tab...')
        #  Input Status > File Status
        self.table_builder(
            self.ui.tableFileStatus,
            self.splunkd.fileinput_status,
            ['location', 'type', 'percent', 'position', 'size', 'parent']
        )

        #  Input Status > TCP
        tcp_monitors = []
        for monitor in self.splunkd.rawtcp_status:
            monitor['tcptype'] = 'Raw'
            tcp_monitors.append(monitor)
        for monitor in self.splunkd.cookedtcp_status:
            monitor['tcptype'] = 'Cooked'
            tcp_monitors.append(monitor)
        self.table_builder(
            self.ui.tableTCP,
            tcp_monitors,
            ['tcptype', 'port', 'source', 'opened']
        )

        #  Input Status > UDP
        self.table_builder(
            self.ui.tableUDP,
            self.splunkd.udphosts_status,
            ['source']
        )

        #  Input Status > Modular
        self.table_builder(
            self.ui.tableModular,
            self.splunkd.modularinput_status,
            ['location', 'exit_desc', 'opened', 'closed', 'bytes']
        )

        #  Input Status > Exec
        self.table_builder(
            self.ui.tableExec,
            self.splunkd.execinput_status,
            ['location', 'exit_desc', 'opened', 'closed', 'bytes']
        )

        # Fill in Apps tab
        self.statusbar_msg('Populating GUI, Apps tab...')
        self.table_builder(
            self.ui.tableApps,
            self.splunkd.apps,
            ['disabled', 'title', 'version', 'label', 'description']
        )

        # Fill in Indexer Cluster tab
        self.statusbar_msg('Populating GUI, Indexer Cluster tab...')
        self.checkCluster_clicked()
        if 'cluster_master' in self.splunkd.roles:
            peers_unsearchable = len(self.splunkd.cluster_peers) - self.splunkd.cluster_peers_searchable
            self.ui.labelClusterPeersSearchable.setText('%s searchable' % self.splunkd.cluster_peers_searchable)
            self.ui.labelClusterPeersNotSearchable.setText('%s not searchable' % peers_unsearchable)
            indexes_unsearchable = len(self.splunkd.cluster_indexes) - self.splunkd.cluster_indexes_searchable
            self.ui.labelClusterIndexesSearchable.setText('%s searchable' % self.splunkd.cluster_indexes_searchable)
            self.ui.labelClusterIndexesNotSearchable.setText('%s not searchable' % indexes_unsearchable)
            self.ui.labelClusterPeersUp.setText('%s/%s Peers Up' % (self.splunkd.cluster_peers_up,
                                                                    len(self.splunkd.cluster_peers)))
            self.ui.labelClusterSearchHeadsUp.setText('%s/%s Search Heads Up'
                                                      % (self.splunkd.cluster_searchheads_connected,
                                                         len(self.splunkd.cluster_searchheads)))

            self.table_builder(
                self.ui.tableClusterPeers,
                self.splunkd.cluster_peers,
                ['name', 'site', 'is_searchable', 'status', 'buckets', 'location', 'last_heartbeat',
                      'replication_port', 'base_gen_id', 'guid']
            )

            self.table_builder(
                self.ui.tableClusterIndexes,
                self.splunkd.cluster_indexes,
                ['name', 'is_searchable', 'searchable_data_copies', 'replicated_data_copies',
                      'buckets', 'cumulative_data_size']
            )

            self.table_builder(
                self.ui.tableClusterSearchHeads,
                self.splunkd.cluster_searchheads,
                ['name', 'site', 'status', 'location', 'guid']
            )

        # Fill in Search Head Cluster tab
        self.statusbar_msg('Populating GUI, SH Cluster tab...')
        self.checkSHCluster_clicked()
        if 'shc_member' in self.splunkd.roles:
            self.ui.labelSHClusterCaptain.setText(self.splunkd.shcluster_captainlabel)
            self.ui.labelSHClusterCaptainElected.setText(self.splunkd.shcluster_electedcaptain)

            self.table_builder(
                self.ui.tableSHClusterMembers,
                self.splunkd.shcluster_members,
                ['label', 'site', 'status', 'artifacts', 'location', 'last_heartbeat', 'replication_port',
                      'restart_required', 'guid']
            )

        # Fill in Resource Usage tab
        self.statusbar_msg('Populating GUI, Resource Usage tab...')
        if self.splunkd.cpu_usage:
            self.ui.progressResourceUsageCPU.setValue(self.splunkd.cpu_usage)
        if self.splunkd.mem_usage:
            self.ui.progressResourceUsageMemory.setValue(self.splunkd.mem_usage)
            self.ui.labelResourceUsageMemory.setText('%.1f / %.1f GB' % (float(self.splunkd.mem_used) / 1024,
                                                                         float(self.splunkd.mem) / 1024))
        if self.splunkd.swap_usage:
            # On Windows systems, the 'swap' variable is actually Commit Charge
            swap_header = 'Commit:' if 'Windows' in self.splunkd.os else 'Swap:'
            self.ui.labelResourceUsageSwapHeader.setText(swap_header)
            self.ui.progressResourceUsageSwap.setValue(self.splunkd.swap_usage)
            self.ui.labelResourceUsageSwap.setText('%.1f / %.1f GB' % (float(self.splunkd.swap_used) / 1024,
                                                                       float(self.splunkd.swap) / 1024))
        if self.splunkd.splunk_processes:
            self.table_builder(
                self.ui.tableResourceUsageProcesses,
                self.splunkd.splunk_processes,
                ['name', 'pid', 'parent_pid', 'cpu', 'mem', 'args']
            )
        if self.splunkd.disk_partitions:
            self.table_builder(
                self.ui.tableResourceUsageDisks,
                self.splunkd.disk_partitions,
                ['name', 'type', 'used', 'total']
            )

        # Update status bar with latest poll
        current_local = time.strftime("%m/%d/%Y %I:%M:%S %p", time.localtime())
        self.statusbar_msg("Last poll completed %s" % current_local)

    @staticmethod
    def table_builder(table, collection, fields, sorting=True):
        table.setRowCount(0)
        table.setRowCount(len(collection))
        table.setSortingEnabled(False)  # Fixes bug where rows don't repopulate after a sort
        row = 0
        for entry in collection:
            column = 0
            for field in fields:
                table.setItem(row, column, QtWidgets.QTableWidgetItem())
                table.item(row, column).setText(entry[field])
                column += 1
            row += 1
        if sorting:
            table.setSortingEnabled(True)  # Fixes bug where rows don't repopulate after a sort

    # Qt slots

    def actionBuildMisnersplunktoolConf_triggered(self):
        """File > Configuration > Build misnersplunktool.conf"""
        filename = config_file.replace('/', '\\')
        message = "This will replace '%s' with defaults. Are you sure?" % filename
        if self.question_msg_yesno(message):
            try:
                with open(config_file, 'w') as f:
                    f.write(CONFIG_DEFAULT)
            except:
                self.warning_msg("Unable to write default configuration to '%s'" % filename)

    def actionSaveReport_triggered(self):
        """File > Save Report"""
        # Throw an error if we haven't successfully connected to a Splunk instance yet
        try:
            self.splunkd.report
        except AttributeError:
            self.warning_msg("No collected reporting data to save.")
            return

        local_datetime_full = time.strftime("%m/%d/%Y %I:%M:%S %p", time.localtime())
        local_datetime_short = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        server = self.splunkd.server_name if self.splunkd.server_name else self.splunkd.mgmt_host
        default_filename = "%s %s" % (local_datetime_short, server)

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Report", os.path.join(SCRIPT_DIR, default_filename),
                                                        "CSV (Comma delimited) (*.csv);;All Files (*.*)")
        if not filename:
            return

        try:
            # Build report text
            report = ""
            report += "# Misner Splunk Tool v%s by Joe Misner - http://tools.misner.net/\n" % __version__
            report += "# Instance Report produced %s\n" % local_datetime_full
            report += "Category,Name,Health,Value\n"
            for entry in self.splunkd.report:
                report += "%s,%s,%s,%s\n" % (entry['category'], entry['name'], entry['health'],
                                             str(entry['value']).replace(',', ';'))

            # Save file
            with open(filename, 'w') as f:
                f.write(report)
            self.information_msg("Report saved to location:\n%s" % filename.replace('/', '\\'))
        except:
            exc = traceback.format_exception(*sys.exc_info())
            msg = "Exception while building report:\n\n%s" % ''.join(exc)
            self.warning_msg(msg)

    def actionSaveCurrentTab_triggered(self):
        """File > Save > Current Tab"""
        # TO-DO: Implement save or print function for current tab
        current_tab = self.ui.tabWidgetMain.tabText(self.ui.tabWidgetMain.currentIndex())
        if current_tab == "Report":
            if not self.splunkd.report:
                self.warning_msg("No collected data to print.")
        else:
            self.warning_msg("Printing functionality not created for currently selected tab.")

    def actionSaveSplunkInstanceCredentials_triggered(self):
        """File > Configuration > Save Splunk Instance Credentials"""
        filename = config_file.replace('/', '\\')
        address = self.ui.comboAddress.strip()
        username = self.ui.editUsername.strip()
        password = self.ui.editPassword.strip()
        section = '[splunkd::%s]' % address
        try:
            if not config.has_section(section):
                config.add_section(section)
            config.set(section, 'username', username)
            config.set(section, 'password', password)
            with open(config_file, 'wb') as f:
                config.write(f)
        except:
            self.warning_msg("Unable to add Splunk instance credentials to '%s'" % filename)

    def actionHelp_triggered(self):
        """Help > Help dialog box"""
        help_window.show()

    def actionAbout_triggered(self):
        """Help > About dialog box"""
        try:
            with open(os.path.join(SCRIPT_DIR, 'LICENSE.txt'), 'r', encoding='utf-8') as f:
                license = f.read()
        except:
            license = "Unable to read LICENSE.txt file"

        dialog = QtWidgets.QMessageBox(self)
        dialog.setIconPixmap(':/favorites.png')
        dialog.setWindowTitle("About")
        dialog.setText(ABOUT_TEXT % __version__)
        dialog.setDetailedText(license)
        dialog.exec_()

    def buttonToggle_clicked(self):
        """Toggle the Connect/Disconnect button"""
        try:
            self.splunkd
        except AttributeError:
            self.connect()
        else:
            self.disconnect()

    def comboAddress_activated(self):
        """Select a hostname configured in misnersplunktool.conf, and fill in the username and password if available"""
        section = 'splunkd::%s' % self.ui.comboAddress.currentText()
        if config.has_option(section, 'username'):
            self.ui.editUsername.setText(config.get(section, 'username'))
        if config.has_option(section, 'password'):
            self.ui.editPassword.setText(config.get(section, 'password'))

    def actionRestartSplunkd_clicked(self):
        """Restart splunkd process"""
        # Check connection with splunkd
        try:
            self.splunkd.service.settings
        except AttributeError:
            self.warning_msg("Not connected to splunkd")
            return
        except binding.AuthenticationError:
            self.disconnect()
            self.critical_msg('Splunk connection reset')
            return

        # Restart splunkd
        try:
            message = "Are you sure you want to restart splunkd on '%s'?" % self.splunkd.host
            if self.question_msg_yesno(message):
                self.splunkd.service.restart()
                self.disconnect()
        except:
            self.critical_msg("Error while attempting to restart splunkd")

    def actionRefreshConfigurations_clicked(self):
        """Refresh configurations, working similar to the web port's /debug/refresh endpoint"""
        # Check connection with splunkd
        try:
            self.splunkd.service.settings
        except AttributeError:
            self.warning_msg("Not connected to splunkd")
            return
        except binding.AuthenticationError:
            self.disconnect()
            self.critical_msg('Splunk connection reset')
            return

        # Refresh configurations
        try:
            message = "Are you sure you want to refresh configurations on '%s'?" % self.splunkd.host
            if not self.question_msg_yesno(message):
                return
            self.statusbar_msg("Refreshing configurations...")
            output = self.splunkd.refresh_config()
            self.statusbar_msg("")
            dialog = QtWidgets.QMessageBox(self)
            dialog.setIcon(QtWidgets.QMessageBox.Information)
            dialog.setWindowTitle("Misner Splunk Tool")
            dialog.setText("Configuration refresh complete.\n\n"
                           "See details below for reload results against each entity.")
            dialog.setDetailedText(output)
            dialog.exec_()
        except Exception as e:
            self.critical_msg("Unable to refresh configuration:\n"
                              "%s" % e)
        except:
            self.critical_msg("Unable to refresh configuration:\n"
                              "Unknown error")

    def comboConfig_activated(self):
        """Poll configuration from splunkd"""
        # Check connection with splunkd
        try:
            self.splunkd.service.settings
        except binding.AuthenticationError:
            self.disconnect()
            self.critical_msg('Splunk connection reset')
            return

        self.ui.editConfig.setHtml('Please wait...')

        # Pull config
        filename = self.ui.comboConfig.currentText()
        self.statusbar_msg("Polling configuration values for '%s'..." % filename)
        data = self.splunkd.get_configuration_kvpairs(filename)

        # Use Pygments to perform syntax highlighting and translate into HTML, then display results
        html = highlight(data, IniLexer(), HtmlFormatter(full=True, style='colorful'))
        self.ui.editConfig.setHtml(html)
        self.statusbar_msg("Poll for '%s' configuration values complete" % filename)

    def actionChangeDeploymentServer_clicked(self):
        """Update which Deployment Server the connected Splunk instance is a client of"""
        # Check connection with splunkd
        try:
            self.splunkd.service.settings
        except AttributeError:
            self.warning_msg("Not connected to splunkd")
            return
        except binding.AuthenticationError:
            self.disconnect()
            self.critical_msg('Splunk connection reset')
            return

        # Change deployment server
        message = "Enter new Deployment Server URI (i.e. 1.2.3.4:8089)"
        new_deployment_server, dialog_not_cancelled = QtWidgets.QInputDialog.getText(self, "Misner Splunk Tool", message)
        if dialog_not_cancelled:  # OK was pushed on dialog
            if new_deployment_server:  # Deployment server specified in Input Dialog
                disabled = '0'
                targeturi = new_deployment_server
                message = "Perform the following actions?\n" \
                          "\n" \
                          "- Enable deployment client.\n" \
                          "- Set deployment server URI to '%s'.\n" \
                          "- Restart splunkd on '%s'"\
                          % (new_deployment_server, self.splunkd.host)
            else:  # Deployment server blank in Input Dialog
                disabled = '1'
                targeturi = ''
                message = "Perform the following actions?\n" \
                          "\n" \
                          "- Disable deployment client.\n" \
                          "- Set deployment server URI to blank.\n" \
                          "- Restart splunkd on '%s'"\
                          % self.splunkd.host

            if self.question_msg_yesno(message):
                try:
                    uri = '/services/properties/deploymentclient/target-broker:deploymentServer'
                    body_input = "disabled=%s&targetUri=%s" % (disabled, targeturi)
                    result = self.splunkd.rest_call(uri, method='POST', body_input=body_input)
                    result_type = result['response']['messages']['msg']['type']
                    result_msg = result['response']['messages']['msg']['$text']

                    if result_type != 'INFO':
                        message = "Error while attempting to modify deployment server URI:\n" \
                                  "%s" % result_msg
                        self.critical_msg(message)
                        return
                    elif 'modified 0 key' in result_msg:
                        message = "Splunkd reports no changes made to deployment server URI:\n" \
                                  "%s" % result_msg
                        self.critical_msg(message)
                        return

                    self.splunkd.service.restart()
                    self.disconnect()
                    self.statusbar_msg('Disconnected while splunkd is restarting, try reconnecting in a few moments')
                except:
                    self.critical_msg("Error while attempting to restart splunkd")
            else:
                self.poll()

    def actionDiscoveryReport_clicked(self):
        """Shows DiscoveryReportWindow()"""
        discoveryreport_window.show()

    def checkCluster_clicked(self):
        """Returns any clicked check boxes in Indexer Cluster tab back to actual values"""
        self.ui.checkClusterDataSearchable.setChecked(self.splunkd.cluster_alldatasearchable)
        self.ui.checkClusterSearchFactorMet.setChecked(self.splunkd.cluster_searchfactormet)
        self.ui.checkClusterReplicationFactorMet.setChecked(self.splunkd.cluster_replicationfactormet)
        self.ui.checkClusterMaintenanceMode.setChecked(self.splunkd.cluster_maintenance)
        self.ui.checkClusterRollingRestartFlag.setChecked(self.splunkd.cluster_rollingrestart)
        self.ui.checkClusterInitializedFlag.setChecked(self.splunkd.cluster_initialized)
        self.ui.checkClusterServiceReadyFlag.setChecked(self.splunkd.cluster_serviceready)
        self.ui.checkClusterIndexingReadyFlag.setChecked(self.splunkd.cluster_indexingready)

    def checkSHCluster_clicked(self):
        """Returns any clicked check boxes in Search Head Cluster tab back to actual values"""
        self.ui.checkSHClusterInitializedFlag.setChecked(self.splunkd.shcluster_initialized)
        self.ui.checkSHClusterServiceReadyFlag.setChecked(self.splunkd.shcluster_serviceready)
        self.ui.checkSHClusterMinimumPeersJoinedFlag.setChecked(self.splunkd.shcluster_minpeersjoined)
        self.ui.checkSHClusterDynamicCaptain.setChecked(self.splunkd.shcluster_dynamiccaptain)
        self.ui.checkSHClusterRollingRestartFlag.setChecked(self.splunkd.shcluster_rollingrestart)

    def buttonRestSend_clicked(self):
        """Sends custom REST API call to splunkd"""
        # Check connection with splunkd
        try:
            self.splunkd.service.settings
        except binding.AuthenticationError:
            self.disconnect()
            self.critical_msg('Splunk connection reset')
            return

        # Send REST API call
        method = self.ui.comboRestMethod.currentText()
        combobox_text = self.ui.comboRestURI.currentText()
        uri = combobox_text
        body_input = self.ui.editRestBodyInput.text()
        parameters = {}

        try:
            if '?' in uri:
                uri, parameter_string = uri.split('?')
                for parameter in parameter_string.split('&'):
                    key, value = parameter.split('=')
                    parameters[key] = value
        except ValueError:
            self.warning_msg("Unable to parse parameters in URI, check formatting")
            return

        # Send REST API query, then use Pygments to perform syntax highlighting, translate into HTML, and display result
        try:
            result = self.splunkd.rest_call(uri, method, output_format='plaintext', body_input=body_input, **parameters)
            html = highlight(result, XmlLexer(), HtmlFormatter(full=True, style='colorful'))
            self.ui.editRestResult.setHtml(html)
        except:
            return

        # Add to combobox history
        item_total = self.ui.comboRestURI.count()
        items = []
        for item in range(0, item_total):
            items.append(self.ui.comboRestURI.itemText(item))
        if combobox_text not in items:
            self.ui.comboRestURI.addItem(combobox_text)


class DiscoveryReportWindow(QtWidgets.QMainWindow):
    """Object class for the main window"""
    def __init__(self):
        """Executed when the DiscoveryReportWindow() object is created"""
        # GUI Setup
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_DiscoveryReportWindow()
        self.ui.setupUi(self)
        self.setFixedSize(self.size())
        self.ui.tableInstances.setColumnWidth(0, 150)  # Address
        self.ui.tableInstances.setColumnWidth(1, 150)  # Status
        self.ui.labelHelp.linkActivated.connect(self.labelHelp_linkActivated)
        self.ui.buttonCsvBrowse.clicked.connect(self.buttonCsvBrowse_clicked)
        self.ui.buttonReset.clicked.connect(self.buttonReset_clicked)
        self.ui.buttonToggle.clicked.connect(self.buttonToggle_clicked)
        self.ui.buttonTopology.clicked.connect(self.buttonTopology_clicked)
        self.ui.buttonSaveReport.clicked.connect(self.buttonSaveReport_clicked)

        # Threading Setup
        self.threadWorker = DiscoveryReportWorker()
        self.threadWorker.signalUpdateProgress[int].connect(self.threadWorker_updateprogress)
        self.threadWorker.signalUpdateTable[dict].connect(self.threadWorker_updatetable)
        self.threadWorker.signalPollingComplete[dict].connect(self.threadWorker_complete)

        self.cleanup()

    def closeEvent(self, event):
        """Executed when the DiscoveryReportWindow() object is closed"""
        self.cleanup()

    def statusbar_msg(self, msg):
        """Sends a message to the statusbar"""
        self.ui.statusbar.showMessage(msg)

    def information_msg(self, msg):
        """Creates an information dialog"""
        QtWidgets.QMessageBox.information(self, "Discovery Report", msg)

    def warning_msg(self, msg):
        """Creates a warning dialog"""
        QtWidgets.QMessageBox.warning(self, "Discovery Report", msg)

    def critical_msg(self, msg):
        """Creates a critical dialog"""
        QtWidgets.QMessageBox.critical(self, "Discovery Report", msg)

    def cleanup(self):
        """Clear widgets and associated objects from this window"""
        self.ui.editCsvFilename.setText(None)
        self.ui.tableInstances.setRowCount(0)
        self.ui.buttonCsvBrowse.setEnabled(True)
        self.ui.buttonTopology.setEnabled(False)
        self.ui.buttonSaveReport.setEnabled(False)
        self.ui.buttonReset.setEnabled(True)
        self.ui.buttonToggle.setEnabled(True)
        self.ui.buttonToggle.setText('Start')
        self.ui.progressBar.setValue(0)
        self.statusbar_msg(None)
        self.filename = None
        self.instances = None
        self.splunkd_polls = None
        self.threadWorker.quit()
        self.threadWorker.stop_execution = True

    def labelHelp_linkActivated(self):
        help_window.show()

    def buttonCsvBrowse_clicked(self):
        """Selects the CSV file completed with Splunk instances and loads into memory, checking for syntax errors"""
        try:
            # Open file dialog to have user locate the CSV file
            self.filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select CSV File", os.path.dirname(sys.argv[0]),
                                                                 "Comma-Separated Value Files (*.csv)")
            if not self.filename:
                return
            self.ui.editCsvFilename.setText(self.filename.replace('/', '\\'))
            with open(self.filename, 'rb') as f:
                reader = csv.reader(f)
                csvfile = list(reader)

            # Build self.instances list made up of each Splunk instance in the CSV file
            self.instances = []
            line_number = 0
            for line in csvfile:
                line_number += 1
                if not line:  # Blank line
                    continue
                if line[0][0] == '#':  # Comments
                    continue
                if line[0] == 'address':  # CSV header
                    continue
                if len(line) != 4:  # Not 4 comma-separated values
                    self.critical_msg("Error on line %s of '%s':\n\nMust have four comma-separated values."
                                      % (line_number, self.filename))
                    self.cleanup()
                    return
                self.instances.append({
                    'address': line[0],
                    'port': int(line[1]),
                    'username': line[2],
                    'password': line[3].strip()
                })

            # Load instances into the Discovery Report window's table
            table = self.ui.tableInstances
            table.setRowCount(len(self.instances))
            row_number = 0
            for instance in self.instances:
                # Address column
                host_port_pair = '%s:%s' % (instance['address'], instance['port'])
                table.setItem(row_number, 0, QtWidgets.QTableWidgetItem())
                table.item(row_number, 0).setText(host_port_pair)
                # Status column
                table.setItem(row_number, 1, QtWidgets.QTableWidgetItem())
                table.item(row_number, 1).setText("Pending")
                row_number += 1
        except:
            self.critical_msg("Unspecified error while loading file '%s'" % self.filename)
            self.cleanup()

    def buttonReset_clicked(self):
        """Reset the Discovery Report window"""
        self.cleanup()

    def buttonToggle_clicked(self):
        """Start or stop execution of the discovery report"""
        if self.threadWorker.isRunning():
            # Cancel execution of discovery report
            self.statusbar_msg("Stopping discovery thread...")
            self.ui.buttonToggle.setEnabled(False)
            self.threadWorker.mutex.lock()
            self.threadWorker.stop_execution = True
            self.threadWorker.mutex.unlock()
        else:
            # Begin execution of discovery report
            if not self.instances:
                self.critical_msg("CSV file has not been selected.")
                return
            self.statusbar_msg("Executing discovery report...")
            self.ui.buttonCsvBrowse.setEnabled(False)
            self.ui.buttonReset.setEnabled(False)
            self.ui.buttonToggle.setText("Stop")
            self.threadWorker.mutex.lock()
            self.threadWorker.stop_execution = False
            self.threadWorker.mutex.unlock()
            self.threadWorker.signalInstanceData.emit(self.instances)
            self.threadWorker.start()

    def buttonTopology_clicked(self):
        """Build topology from report adjacency data, then display window for adjustment and saving"""
        try:
            # Create instances and dictionaries needed for topology building
            Graph = networkx.Graph()         # Object containing visual topology (nodes, adjacencies, locations, etc)
            topology = main_window.topology  # Topology configuration
            pos = {}    # Positions of each node on the topology, representing x=0-100,y=0-100
            labels = {  # Labels given to each node
                'webuser': "Web User"
            }
            nodes = {   # Splunkd instances categorized by their discovered primary role
                'user': frozenset({'webuser'}),
                'sh': set(),
                'idx': set(),
                'hf': set(),
                'uf': set(),
                'mc': set(),
                'shcd': set(),
                'cm': set(),
                'ds': set(),
                'lm': set(),
                'input': set(),
                'other': set()
            }

            # Build invisible corner nodes to make sure matplotlib.pyplot displays a proportionate topology in 100x100
            Graph.add_nodes_from({'cornernw', 'cornerne', 'cornersw', 'cornerse'}, color='#ffffff')
            pos.update({'cornernw': (-10, 110), 'cornerne': (110, 110), 'cornersw': (-10, -10), 'cornerse': (110, -10)})

            # Iterate through splunkd instances
            instances = {}
            for instance in self.splunkd_polls:
                clean_name = str.lower(self.splunkd_polls[instance].server_name).split('.')[0]
                instances[clean_name] = self.splunkd_polls[instance]
                primary_role = instances[clean_name].primary_role
                all_roles = instances[clean_name].roles
                labels[clean_name] = "%s\n%s" % (clean_name, primary_role)

                # Add to nodes dictionary based on primary role
                if primary_role[0:11] == "Search Head":
                    nodes['sh'].add(clean_name)
                elif primary_role[0:7] == "Indexer":
                    nodes['idx'].add(clean_name)
                elif primary_role == "Heavy Forwarder":
                    nodes['hf'].add(clean_name)
                elif primary_role == "Universal Forwarder":
                    nodes['uf'].add(clean_name)
                elif primary_role == "Management Console":
                    nodes['mc'].add(clean_name)
                elif primary_role == "Deployer (SHC)":
                    nodes['shcd'].add(clean_name)
                elif primary_role == "Cluster Master":
                    nodes['cm'].add(clean_name)
                elif primary_role == "Deployment Server":
                    nodes['ds'].add(clean_name)
                elif primary_role == "License Master":
                    nodes['lm'].add(clean_name)
                elif primary_role == "Forwarder":
                    nodes['uf'].add(clean_name)

                # Add additional roles to label
                if ('universal_forwarder' in all_roles) and ("Universal Forwarder" not in labels[clean_name]):
                    labels[clean_name] += "\nUniversal Forwarder"
                if ('management_console' in all_roles) and ("Management Console" not in labels[clean_name]):
                    labels[clean_name] += "\nManagement Console"
                if ('cluster_slave' in all_roles) and ("Indexer" not in labels[clean_name]):
                    labels[clean_name] += "\nIndexer (Cluster Slave)"
                if ('indexer' in all_roles) and ("Indexer" not in labels[clean_name]):
                    labels[clean_name] += "\nIndexer (Standalone)"
                if ('shc_deployer' in all_roles) and ("Deployer (SHC)" not in labels[clean_name]):
                    labels[clean_name] += "\nDeployer (SHC)"
                if ('shc_captain' in all_roles) and ("Search Head" not in labels[clean_name]):
                    labels[clean_name] += "\nSearch Head (SHC Captain)"
                if ('shc_member' in all_roles) and ("Search Head" not in labels[clean_name]):
                    labels[clean_name] += "\nSearch Head (SHC Member)"
                if ('cluster_master' in all_roles) and ("Cluster Master" not in labels[clean_name]):
                    labels[clean_name] += "\nCluster Master"
                if ('search_head' in all_roles) and ("Search Head" not in labels[clean_name]):
                    labels[clean_name] += "\nSearch Head (Standalone)"
                if ('deployment_server' in all_roles) and ("Deployment Server" not in labels[clean_name]):
                    labels[clean_name] += "\nDeployment Server"
                if ('heavyweight_forwarder' in all_roles) and ("Heavy Forwarder" not in labels[clean_name]):
                    labels[clean_name] += "\nHeavy Forwarder"
                if ('license_master' in all_roles) and ("License Master" not in labels[clean_name]):
                    labels[clean_name] += "\nLicense Master"

            ent_nodes = set().union(nodes['sh'], nodes['idx'], nodes['hf'], nodes['mc'],
                                    nodes['shcd'], nodes['cm'], nodes['ds'], nodes['uf'])

            # Add nodes to graph
            if topology['nodedraw_user']:
                Graph.add_nodes_from(nodes['user'], color='#' + topology['nodecolor_user'])
            if topology['nodedraw_searchhead']:
                Graph.add_nodes_from(nodes['sh'], color='#' + topology['nodecolor_searchhead'])
            if topology['nodedraw_indexer']:
                Graph.add_nodes_from(nodes['idx'], color='#' + topology['nodecolor_indexer'])
            if topology['nodedraw_heavyforwarder']:
                Graph.add_nodes_from(nodes['hf'], color='#' + topology['nodecolor_heavyforwarder'])
            if topology['nodedraw_universalforwarder']:
                Graph.add_nodes_from(nodes['uf'], color='#' + topology['nodecolor_universalforwarder'])
            if topology['nodedraw_mgmtconsole']:
                Graph.add_nodes_from(nodes['mc'], color='#' + topology['nodecolor_mgmtconsole'])
            if topology['nodedraw_shcdeployer']:
                Graph.add_nodes_from(nodes['shcd'], color='#' + topology['nodecolor_shcdeployer'])
            if topology['nodedraw_clustermaster']:
                Graph.add_nodes_from(nodes['cm'], color='#' + topology['nodecolor_clustermaster'])
            if topology['nodedraw_deploymentserver']:
                Graph.add_nodes_from(nodes['ds'], color='#' + topology['nodecolor_deploymentserver'])
            if topology['nodedraw_licensemaster']:
                Graph.add_nodes_from(nodes['lm'], color='#' + topology['nodecolor_licensemaster'])
            if topology['nodedraw_inputs']:
                Graph.add_nodes_from(nodes['input'], color='#' + topology['nodecolor_inputs'])

            # Function used to add adjacencies and discover new Splunk instances
            def add_adjacency(discovered_node, dn_role, dn_color, adj_node, adj_color):
                if discovered_node[0] == '(' and discovered_node[-1:] == ')':
                    return
                discovered_node = discovered_node.split(':')[0]  # Return address without port

                # If IP address, try and resolve to host
                ipaddr_regex = r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
                if re.findall(ipaddr_regex, discovered_node):
                    try:
                        discovered_node = socket.gethostbyaddr(discovered_node)[0].lower().split('.')[0]  # Resolved by DNS, return hostname without suffix
                    except:
                        pass  # Not found by DNS, return IP
                else:
                    discovered_node = discovered_node.lower().split('.')[0]  # Not an IP, return hostname without suffix

                if discovered_node not in Graph.nodes:
                    nodes[dn_role].add(discovered_node)
                    labels[discovered_node] = "%s\nDiscovered Node" % discovered_node
                    Graph.add_node(discovered_node, color='#' + topology[dn_color])
                Graph.add_edge(discovered_node, adj_node, color='#' + topology[adj_color])

            # Map adjacencies between nodes
            #  Web Access to Search Heads
            if topology['adjdraw_web']:
                for sh in nodes['sh']:
                    if sh not in instances:
                        continue
                    if instances[sh].http_server:
                        if (nodes['user'] in Graph.nodes) and (sh in Graph.nodes):
                            Graph.add_edge(nodes['user'], sh, color='#' + topology['adjcolor_web'])
            #  Distributed Search from Search Heads
            if topology['adjdraw_distsearch']:
                for sh in nodes['sh']:
                    if sh not in instances:
                        continue
                    for peer in instances[sh].distributedsearch_peers:
                        add_adjacency(peer['peerName'], 'idx', 'nodecolor_indexer', sh, 'adjcolor_distsearch')
            #  Data Forwarding from Heavy Forwarder
            if topology['adjdraw_datafwdheavyforwarder']:
                for hf in nodes['hf']:
                    if hf not in instances:
                        continue
                    for server in instances[hf].forward_servers:
                        add_adjacency(server['title'], 'idx', 'nodecolor_indexer', hf, 'adjcolor_datafwd')
            #  Data Forwarding from Universal Forwarder
            if topology['adjdraw_datafwduniversalforwarder']:
                for uf in nodes['uf']:
                    if uf not in instances:
                        continue
                    for server in instances[uf].forward_servers:
                        add_adjacency(server['title'], 'idx', 'nodecolor_indexer', uf, 'adjcolor_datafwd')
            #  Data Forwarding from Inputs
            if topology['adjdraw_datafwdinput']:
                for ipt in nodes['input']:
                    if ipt not in instances:
                        continue
                    for server in instances[ipt].forward_servers:
                        add_adjacency(server['title'], 'idx', 'nodecolor_indexer', ipt, 'adjcolor_datafwd')
            #  Cluster Management
            if topology['adjdraw_clustermgmt']:
                for cm in nodes['cm']:
                    if cm not in instances:
                        continue
                    for peer in instances[cm].cluster_peers:
                        add_adjacency(peer['location'], 'idx', 'nodecolor_indexer', cm, 'adjcolor_clustermgmt')
            #  Bucket Replication
            if topology['adjdraw_bucketrep']:
                for idx in nodes['idx']:
                    if idx not in instances:
                        continue
                    for peer in instances[idx].cluster_peers:
                        add_adjacency(peer['location'], 'idx', 'nodecolor_indexer', idx, 'adjcolor_bucketrep')
            #  SHC Deployer
            if topology['adjdraw_shcdeployment']:
                for sh in nodes['sh']:
                    if sh not in instances:
                        continue
                    deployer = instances[sh].shcluster_deployer
                    add_adjacency(deployer, 'shcd', 'nodecolor_shcdeployer', sh, 'adjcolor_shcdeployment')
            #  Since potentially discovered nodes below don't have a clear Splunk role, discover them last
            #  Distributed Search from Management Console
            if topology['adjdraw_mgmtconsole']:
                for mc in nodes['mc']:
                    for peer in instances[mc].distributedsearch_peers:
                        add_adjacency(peer['peerName'], 'other', 'nodecolor_others', mc, 'adjcolor_mgmtconsole')
            #  Deployment Server
            if topology['adjdraw_deployment']:
                for ds in nodes['ds']:
                    for client in instances[ds].deployment_clients:
                        dns_mgmt_pair = '%s:%s' % (client['dns'], client['mgmt'])
                        add_adjacency(dns_mgmt_pair, 'other', 'nodecolor_others', ds, 'adjcolor_deployment')
            #  License
            if topology['adjdraw_license']:
                for slave in ent_nodes:
                    license_master = instances[slave].license_master
                    add_adjacency(license_master, 'other', 'nodecolor_others', slave, 'adjcolor_license')

            # Return error if not enough nodes to paint
            if len(Graph.nodes) <= 1:
                self.warning_msg("Not enough nodes found to build topology.")
                return

            # Function used to compute positions where nodes are placed on each layer
            def layer_positions(layernodes, layerheight=0, bufferwidth=10, xalignment='justify'):
                if not layernodes:
                    return {}
                positions = {}
                # If statically separated nodes are too wide, justify instead
                if (topology['static_width'] * len(layernodes)) > 100 - (bufferwidth * 2):
                    xalignment = 'justify'
                if xalignment == 'left':  # left-aligned and statically separated
                    xpos = bufferwidth
                    for node in layernodes:
                        positions[node] = (xpos, layerheight)
                        xpos += topology['static_width']
                if xalignment == 'right':  # right-aligned and statically separated
                    xpos = 100 - bufferwidth
                    for node in layernodes:
                        positions[node] = (xpos, layerheight)
                        xpos -= topology['static_width']
                if xalignment in ('center', 'justify'):  # center-aligned and evenly justified
                    nodewidth = (100 - (bufferwidth * 2)) / len(layernodes)
                    xpos = bufferwidth + (nodewidth / 2)
                    for node in layernodes:
                        positions[node] = (xpos, layerheight)
                        xpos += nodewidth
                return positions

            # Determine x-coordinate positions of nodes, along with y-coordinate layer height
            pos.update(layer_positions(sorted(nodes['user']), layerheight=topology['layerheight_user'],
                                       xalignment=topology['layeralignment_user']))
            pos.update(layer_positions(sorted(nodes['mc']), layerheight=topology['layerheight_mc'],
                                       xalignment=topology['layeralignment_mc']))
            pos.update(layer_positions(sorted(nodes['shcd']), layerheight=topology['layerheight_shcd'],
                                       xalignment=topology['layeralignment_shcd']))
            pos.update(layer_positions(sorted(nodes['sh']), layerheight=topology['layerheight_sh'],
                                       xalignment=topology['layeralignment_sh']))
            pos.update(layer_positions(sorted(nodes['cm']), layerheight=topology['layerheight_cm'],
                                       xalignment=topology['layeralignment_cm']))
            pos.update(layer_positions(sorted(nodes['idx']), layerheight=topology['layerheight_idx'],
                                       xalignment=topology['layeralignment_idx']))
            pos.update(layer_positions(sorted(nodes['lm']), layerheight=topology['layerheight_lm'],
                                       xalignment=topology['layeralignment_lm']))
            pos.update(layer_positions(sorted(nodes['hf']), layerheight=topology['layerheight_hf'],
                                       xalignment=topology['layeralignment_hf']))
            pos.update(layer_positions(sorted(nodes['ds']), layerheight=topology['layerheight_ds'],
                                       xalignment=topology['layeralignment_ds']))
            pos.update(layer_positions(sorted(nodes['uf']), layerheight=topology['layerheight_uf'],
                                       xalignment=topology['layeralignment_uf']))
            pos.update(layer_positions(sorted(nodes['input']), layerheight=topology['layerheight_input'],
                                       xalignment=topology['layeralignment_input']))
            pos.update(layer_positions(sorted(nodes['other']), layerheight=topology['layerheight_other'],
                                       xalignment=topology['layeralignment_other']))

            # Draw topology
            node_colors = [Graph.nodes[n]['color'] for n in Graph.nodes()]
            edge_colors = [Graph[a][b]['color'] for a, b in Graph.edges()]
            networkx.draw(Graph, pos=pos, labels=labels, with_labels=True, font_size=topology['fontsize'],
                          alpha=0.8, node_color=node_colors, edge_color=edge_colors)

            # Open new window displaying topology, with option to save
            matplotlib.pyplot.get_current_fig_manager().canvas.set_window_title('Topology')
            matplotlib.pyplot.show()
        except:
            exc = traceback.format_exception(*sys.exc_info())
            msg = "Exception while building topology:\n\n%s" % ''.join(exc)
            self.warning_msg(msg)

    def buttonSaveReport_clicked(self):
        """Save the discovered data as a CSV file"""
        # Build report
        try:
            # Build report text
            local_datetime_full = time.strftime("%m/%d/%Y %I:%M:%S %p", time.localtime())
            local_datetime_short = time.strftime("%Y%m%d-%H%M%S", time.localtime())
            report = ""
            report += "# Misner Splunk Tool v%s by Joe Misner - http://tools.misner.net/\n" % __version__
            report += "# Discovery Report produced %s\n" % local_datetime_full

            # Get "category / name" columns from a successful splunkd's report to build the header, then break
            header = []
            for instance in self.splunkd_polls:
                if self.splunkd_polls[instance].report:
                    for entry in self.splunkd_polls[instance].report:
                        header.append('%s: %s' % (entry['category'], entry['name']))
                    report += "%s\n" % ','.join(header)
                    break

            # Return error if not enough nodes to paint
            if not header:
                self.warning_msg("No successful splunkd polls retrieved to generate a report.")
                return

            # Pull values from each instance into a comma-separated string
            for instance in self.splunkd_polls:
                entries = []
                for entry in self.splunkd_polls[instance].report:
                    entries.append(str(entry['value']).replace(',', ';'))
                report += "%s\n" % ','.join(entries)

            # Get destination filename from user for the completed report
            default_filename = "%s Discovery Report" % local_datetime_short
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Discovery Report",
                                                            os.path.join(SCRIPT_DIR, default_filename),
                                                            "CSV (Comma delimited) (*.csv);;All Files (*.*)")

            # If user cancels the Save Discovery Report dialog, report data is discarded
            if not filename:
                return

            # Save file
            with open(filename, 'w') as f:
                f.write(report)
                self.information_msg("Report saved to location:\n%s" % filename.replace('/', '\\'))
        except:
            exc = traceback.format_exception(*sys.exc_info())
            msg = "Exception while building report:\n\n%s" % ''.join(exc)
            self.warning_msg(msg)

    def threadWorker_updateprogress(self, progress):
        """Update the statusbar with a message from the worker thread"""
        if progress == 0:
            self.statusbar_msg("Cancelled")
            self.ui.buttonReset.setEnabled(True)
        else:
            instance_count = len(self.instances)
            percent = int((float(progress) - 1) / instance_count * 100) if instance_count > 0 else 0
            self.ui.progressBar.setValue(percent)
            self.statusbar_msg("Running discovery report (instance %s of %s)..." % (progress, instance_count))


    def threadWorker_updatetable(self, msg):
        """Update the table's status column with a message from the worker thread"""
        try:
            self.ui.tableInstances.item(msg['row'], 1).setText(msg['text'])
        except AttributeError:  # table was likely reset
            pass

    def threadWorker_complete(self, splunkd_polls):
        """Called when the worker thread is done polling Splunk instances"""
        # splunkd_polls is a list of dictionaries, one for each polled Splunk instance
        # Save to instance attribute for use later when creating a Topology
        self.splunkd_polls = splunkd_polls

        # Notify user that polling is complete
        self.ui.buttonReset.setEnabled(True)
        self.ui.buttonToggle.setEnabled(False)
        self.ui.buttonTopology.setEnabled(True)
        self.ui.buttonSaveReport.setEnabled(True)
        self.ui.progressBar.setValue(100)
        self.statusbar_msg("Complete")
        self.information_msg("Discovery Report generation complete.")


class DiscoveryReportWorker(QtCore.QThread):
    """Executes the Discovery Report on it's own worker thread"""
    # Class attribute used for cross-thread communications
    signalInstanceData = QtCore.Signal(list)
    signalUpdateProgress = QtCore.Signal(int)
    signalUpdateTable = QtCore.Signal(dict)
    signalPollingComplete = QtCore.Signal(dict)
    mutex = QtCore.QMutex()

    def __init__(self):
        """Constructor"""
        QtCore.QThread.__init__(self)
        self.signalInstanceData[list].connect(self.signalInstanceData_write)
        self.stop_execution = True
        self.instances = []

    def signalInstanceData_write(self, instances):
        """Capture list of Splunk instances to iterate through from the main thread"""
        self.instances = instances

    def run(self):
        """Worker thread started"""
        self.poll()

    def poll(self):
        """Execute the discovery report, polling all Splunk instances"""
        # Iterate through instances
        splunkd_polls = {}
        for instance in self.instances:
            if self.stop_execution:
                self.signalUpdateProgress.emit(0)
                return

            # Setup before polling
            instance_number = self.instances.index(instance) + 1
            self.signalUpdateProgress.emit(instance_number)
            splunk_host = instance['address']
            splunk_port = instance['port']
            splunk_user = instance['username']
            splunk_pass = instance['password']

            def instance_status(msg):
                """Update Discovery Report window's table with Splunk instance's polling status"""
                row_number = instance_number - 1
                self.signalUpdateTable.emit({'row': row_number, 'text': msg})

            # Connect to Splunk instance
            instance_status("Connecting...")
            try:
                splunkd = Splunkd(splunk_host, splunk_port, splunk_user, splunk_pass)
            except binding.AuthenticationError:
                instance_status("Failed: Authentication error")
                continue
            except socket.gaierror:
                instance_status("Failed: Unable to connect")
                continue
            except socket.error as error:
                instance_status("Failed: Unable to connect (%s)" % error)
                continue
            except:
                instance_status("Failed: Unable to connect (unknown exception)")
                continue
            instance_status("Connected")

            # Poll Splunk instance
            try:
                instance_status('Polling service info...')
                splunkd.poll_service_info()
                instance_status('Polling settings...')
                splunkd.poll_service_settings()
                instance_status('Polling messages...')
                splunkd.poll_service_messages()
                instance_status('Polling configurations...')
                splunkd.get_service_confs()
                instance_status('Polling input status...')
                splunkd.get_services_admin_inputstatus()
                instance_status('Polling apps...')
                splunkd.poll_service_apps()
                instance_status('Polling data collection info...')
                splunkd.get_services_data()
                instance_status('Polling KV store info...')
                splunkd.get_services_kvstore()
                instance_status('Polling cluster master info...')
                splunkd.get_services_cluster()
                instance_status('Polling search head cluster info...')
                splunkd.get_services_shcluster()
                instance_status('Polling deployment info...')
                splunkd.get_services_deployment()
                instance_status('Polling licensing info...')
                splunkd.get_services_licenser()
                instance_status('Polling distributed search info...')
                splunkd.get_services_search()
                instance_status('Polling introspection...')
                splunkd.get_services_server_status()
            except socket.error as e:
                instance_status("Failed: Socket error while attempting to poll splunkd:\n%s" % e)
                continue

            # Build instance report
            instance_status('Building instance report...')
            try:
                splunkd.report_builder(main_window.healthchecks)
            except:
                instance_status("Failed: Unable to build instance report")
                continue

            # Success
            host_port_pair = "%s:%s" % (splunk_host, splunk_port)
            splunkd_polls[host_port_pair] = splunkd
            instance_status("Complete")

        # Notify main thread that polling is complete, sending over the data from all instances
        self.signalPollingComplete.emit(splunkd_polls)
        self.quit()


class HelpWindow(QtWidgets.QTextEdit):
    """Object class for the help window"""
    def __init__(self):
        """Executed when the HelpWindow() object is created"""
        # GUI Setup
        QtWidgets.QTextEdit.__init__(self)
        self.setWindowTitle("Help - README.md")
        self.setWindowIcon(main_window.windowIcon())
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.resize(500, 400)

        # Retrieve markdown text from the README.md file in the script directory
        try:
            with open(os.path.join(SCRIPT_DIR, 'README.md'), 'r', encoding='utf-8') as f:
                readme_file = f.read()
            html = markdown.markdown(readme_file)
        except:
            html = "<html>Unable to read README.md file</html>"
        self.setHtml(html)


if __name__ == '__main__':
    # Pull available configs from misnertraptool.conf
    config = configparser.ConfigParser(allow_no_value=True)
    config_file = os.path.join(SCRIPT_DIR, CONFIG_FILENAME)
    if os.path.isfile(config_file):  # Read in configuration file if it exists
        try:
            config.read(config_file)
        except configparser.ParsingError as e:
            pass
    else:  # If configuration file is missing, build a default file
        try:
            with open(config_file, 'w') as f:
                f.write(CONFIG_DEFAULT)
            config.read(config_file)
        except:
            pass

    # PySide GUI
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    help_window = HelpWindow()
    discoveryreport_window = DiscoveryReportWindow()

    sys.exit(app.exec_())
