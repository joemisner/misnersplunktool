#!/usr/bin/env python
"""
misnersplunkdwrapper.py - Misner Splunkd Wrapper
Copyright (C) 2015-2017 Joe Misner <joe@misner.net>
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
- Python v2.7.13, https://www.python.org/
- Python package 'requests' v2.9.1, https://pypi.python.org/pypi/requests
- Python module 'splunk-sdk' v1.6.0, https://pypi.python.org/pypi/splunk-sdk

Changelog:
2017.02.25 - initial version, forked from misnersplunktool.py
2017.05.10 - initial public version
2017.07.18 - added REST captures of data input ports and additional cluster values
2017.08.12 - migrated report_builder method to Splunkd class
"""

import re
import time
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import splunklib.client as client
import splunklib.data as data
import splunklib.results as results

__version__ = '2017.07.18'

SPLUNK_HOST = 'localhost'
SPLUNK_PORT = 8089
SPLUNK_USER = 'admin'
SPLUNK_PASS = 'changeme'


class Splunkd:
    """Splunkd class"""
    def __init__(self, splunk_host=SPLUNK_HOST, splunk_port=SPLUNK_PORT,
                 splunk_user=SPLUNK_USER, splunk_pass=SPLUNK_PASS):
        """Constructor"""
        self._connect(splunk_host, splunk_port, splunk_user, splunk_pass)
        self.mgmt_host, self.mgmt_port, self.mgmt_user, self.mgmt_pass =\
             splunk_host, splunk_port, splunk_user, splunk_pass

        # Define attribute defaults for this instance with the following rules:
        # Private Attributes = None, Strings = (unknown), Integers = 0, Lists = [], Dictionaries = {}, Booleans = None

        # poll_service_settings()
        self._service_settings = None
        self.host = '(unknown)'
        self.SPLUNK_HOME = '(unknown)'
        self.SPLUNK_DB = '(unknown)'
        self.server_name = '(unknown)'
        self.http_port = 0
        self.http_ssl = None
        self.http_server = None

        # poll_service_info()
        self._service_info = None
        self.version = '(unknown)'
        self.guid = '(unknown)'
        self.startup_time = 0
        self.startup_time_formatted = '(unknown)'
        self.cores = 0
        self.ram = 0
        self.roles = ['(unknown)']
        self.product = '(unknown)'
        self.mode = '(unknown)'
        self.type = '(unknown)'
        self.os = '(unknown)'

        # poll_service_messages()
        self._service_messages = None
        self.messages = []

        # get_service_confs()
        self._services_properties = None
        self.configuration_files = []
        self.deployment_server = '(unknown)'

        # get_services_admin_inputstatus()
        self._services_admin_inputstatus = None
        self.fileinput_status = []
        self.execinput_status = []
        self.modularinput_status = []
        self.rawtcp_status = []
        self.cookedtcp_status = []
        self.udphosts_status = []
        self.tcprawlistenerports_status = []
        self.tcpcookedlistenerports_status = []
        self.udplistenerports_status = []

        # poll_service_apps()
        self._service_apps = None
        self.apps = []

        # get_services_data()
        self._services_data_inputs_tcp_cooked = None
        self.receiving_ports = []
        self._services_data_inputs_tcp_raw = None
        self.rawtcp_ports = []
        self._services_data_inputs_udp = None
        self.udp_ports = []

        # get_services_kvstore()
        self._services_kvstore_status = None
        self.kvstore_port = 0

        # get_services_cluster_master()
        self._services_cluster_config = None
        self.cluster_master_uri = '(unknown)'
        self.cluster_mode = '(unknown)'
        self.cluster_site = '(unknown)'
        self.cluster_label = '(unknown)'
        self.cluster_replicationport = 0
        self.cluster_replicationfactor = 0
        self.cluster_searchfactor = 0
        self._services_shcluster_conf_deploy_fetch_url = None
        self.shcluster_deployer = '(unknown)'
        self._services_cluster_master_info = None
        self.cluster_maintenance = None
        self.cluster_rollingrestart = None
        self.cluster_initialized = None
        self.cluster_serviceready = None
        self.cluster_indexingready = None
        self._services_cluster_master_generation_master = None
        self.cluster_alldatasearchable = None
        self.cluster_searchfactormet = None
        self.cluster_replicationfactormet = None
        self._services_cluster_master_peers = None
        self.cluster_peers = []
        self.cluster_peers_searchable = 0
        self.cluster_peers_up = 0
        self._services_cluster_master_indexes = None
        self.cluster_indexes = []
        self.cluster_indexes_searchable = 0
        self._services_cluster_master_searchheads = None
        self.cluster_searchheads = []
        self.cluster_searchheads_connected = 0

        # get_services_shcluster()
        self._services_shcluster_config = None
        self.shcluster_label = '(unknown)'
        self.shcluster_replicationport = 0
        self.shcluster_replicationfactor = 0
        self._services_shcluster_status = None
        self.shcluster_captainlabel = '(unknown)'
        self.shcluster_captainuri = '(unknown)'
        self.shcluster_captainid = '(unknown)'
        self.shcluster_dynamiccaptain = None
        self.shcluster_electedcaptain = '(unknown)'
        self.shcluster_rollingrestart = None
        self.shcluster_serviceready = None
        self.shcluster_minpeersjoined = None
        self.shcluster_initialized = None
        self._services_shcluster_member_members = None
        self.shcluster_members = []

        # get_services_server_status()
        self._services_server_status_partitionsspace = None
        self.disk_partitions = []
        self._services_server_status_resourceusage_hostwide = None
        self.cpu_usage = 0
        self.mem_usage = 0
        self.swap_usage = 0
        self._services_server_status_resourceusage_splunkprocesses = None
        self.splunk_processes = []

        # refresh_config()
        self._servicesNS_admin_search_admin = None

        # report_builder()
        self.report = []

    def _connect(self, splunk_host, splunk_port, splunk_user, splunk_pass):
        """Connect to Splunk instance"""
        self.service = client.connect(host=splunk_host, port=splunk_port,
                                      username=splunk_user, password=splunk_pass)
        # NOTE: Exceptions are handled in MainWindow class to provide user feedback

    # REST API calls

    def rest_call(self, uri, method='GET', output_format='structured', body_input='', **kwargs):
        """Takes the result of a REST API call and formats the results depending on content type"""
        # Make the REST API call
        # Not using 'self.service.get/post/delete' due to Splunk SDK bug not allowing URLs with "://" in the name,
        # such as when pulling config keys for inputs.conf that have monitor:// in the stanza
        url = "https://%s:%s%s" % (self.mgmt_host, self.mgmt_port, uri)
        auth = (self.mgmt_user, self.mgmt_pass)
        if method == 'GET':
            r = requests.get(url, data=body_input, params=kwargs, auth=auth, verify=False)
        elif method == 'POST':
            r = requests.post(url, data=body_input, params=kwargs, auth=auth, verify=False)
        elif method == 'DELETE':
            r = requests.delete(url, data=body_input, params=kwargs, auth=auth, verify=False)
        else:
            raise Exception('Invalid method specified for rest_call()')

        # Handle the output
        headers = r.headers
        reason = r.reason
        status = r.status_code
        body = str(r.text.encode('ascii', 'replace'))
        if output_format == 'structured':
            if headers['content-type'][:8] == 'text/xml':
                return data.load(body)
            elif headers['content-type'][:10] == 'text/plain':
                return body
        elif output_format == 'plaintext':
            headers_plaintext = ''
            for header in headers:
                headers_plaintext += "%s: %s\n" % (header, headers[header])
            return "HTTP %s %s\n\n%s\n%s" % (status, reason, headers_plaintext, body)
        else:
            raise Exception('Invalid output_format specified for rest_call()')

    # Retrieve search results

    def _search(self, spl):
        """Perform a one-shot search"""
        if 'Universal Forwarder' in self.type:
            raise Exception('Cannot run a search on a Universal Forwarder')
        spl = 'search %s' % spl.replace('|', '&#124;')
        return results.ResultsReader(self.service.jobs.oneshot(spl))
        #for item in result: pprint(dict(item))

    # Get common information

    def poll_service_settings(self):
        """Poll splunklib.client.service.settings.content"""
        self._service_settings = self.service.settings.content
        self.host = self._service_settings['host']
        self.SPLUNK_HOME = self._service_settings['SPLUNK_HOME']
        self.SPLUNK_DB = self._service_settings['SPLUNK_DB']
        self.server_name = self._service_settings['serverName']
        self.http_port = int(self._service_settings['httpport'])
        self.http_ssl = True if self._service_settings['enableSplunkWebSSL'] == '1' else False
        self.http_server = True if self._service_settings['startwebserver'] == '1' else False

    def poll_service_info(self):
        """Poll splunklib.client.service.info"""
        self._service_info = self.service.info
        self.version = self._service_info['version']
        self.guid = self._service_info['guid']
        self.startup_time = int(self._service_info['startup_time']) if 'startup_time' in self._service_info else 0
        if self.startup_time:
            self.startup_time_formatted =\
                time.strftime("%m/%d/%Y %I:%M:%S %p", time.localtime(float(self.startup_time)))
        else:
            self.startup_time_formatted = '(unknown)'
        self.cores = int(self._service_info['numberOfCores']) if 'numberOfCores' in self._service_info else 0
        self.ram = self._service_info['physicalMemoryMB'] if 'physicalMemoryMB' in self._service_info else 0
        self.roles = self._service_info['server_roles'] if 'server_roles' in self._service_info else ['(unknown)']
        self.product = self._service_info['product_type'] if 'product_type' in self._service_info else '(unknown)'
        self.mode = self._service_info['mode'] if 'mode' in self._service_info else '(unknown)'
        if 'universal_forwarder' in self.roles:
            self.type = 'Splunk Universal Forwarder v%s' % self.version
        elif self.product == 'enterprise':
            self.type = 'Splunk Enterprise v%s' % self.version
        elif self.product == 'hunk':
            self.type = 'Splunk Hunk v%s' % self.version
        elif self.product == 'lite':
            self.type = 'Splunk Lite v%s' % self.version
        elif self.product == 'lite_free':
            self.type = 'Splunk Lite Free v%s' % self.version
        elif self.mode == 'dedicated forwarder':
            self.type = 'Splunk Forwarder v%s' % self.version
        else:
            self.type = 'Splunk v%s' % self.version
        try:
            self.os = '%s %s' % (self._service_info['os_name_extended'],
                                 self._service_info['cpu_arch'])
        except KeyError:  # In case 'os_name_extended' is not available
            if self._service_info['os_name'] == 'Windows':
                self.os = '%s %s.%s %s' % (self._service_info['os_name'],
                                           self._service_info['os_build'],
                                           self._service_info['os_version'],
                                           self._service_info['cpu_arch'])
            else:
                self.os = '%s %s %s %s' % (self._service_info['os_name'],
                                           self._service_info['os_version'],
                                           self._service_info['cpu_arch'],
                                           self._service_info['os_build'])

    def poll_service_messages(self):
        """Poll splunklib.client.service.messages"""
        self._service_messages = self.service.messages.list()
        self.messages = []
        try:
            for message in self._service_messages:
                message_dict = {
                    'time_created': time.strftime("%m/%d/%Y %I:%M:%S %p",
                                                  time.localtime(float(message.content['timeCreated_epochSecs']))),
                    'severity':     message.content['severity'].upper(),
                    'title':        message.name,
                    'description':  message.content['message']}
                self.messages.append(message_dict)
        except KeyError:
            pass  # No message entries

    def get_service_confs(self):
        """GET /services/properties"""
        self._services_properties = self.rest_call('/services/properties', count=-1)
        self.configuration_files = []
        try:
            confs = self._services_properties['feed']['entry']
            for conf in confs:
                self.configuration_files.append(conf['title'])
        except KeyError:
            pass  # No peer entries

        # Poll for Deployment Client values
        try:
            try:
                ds_disabled = self.rest_call(
                    '/services/properties/deploymentclient/target-broker:deploymentServer/disabled',
                    count=-1
                )
            except:
                ds_disabled = '0'
            try:
                ds_targeturi = self.rest_call(
                    '/services/properties/deploymentclient/target-broker:deploymentServer/targetUri',
                    count=-1
                )
            except:
                ds_targeturi = None
            if ds_disabled == '1':
                self.deployment_server = '(disabled)'
            elif not ds_targeturi or not isinstance(ds_targeturi, str):
                self.deployment_server = '(none)'
            else:
                self.deployment_server = ds_targeturi
        except KeyError:
            self.deployment_server = '(none)'

    def get_services_admin_inputstatus(self):
        """GET /services/admin/inputstatus"""
        self._services_admin_inputstatus = self.rest_call('/services/admin/inputstatus', count=-1)
        self.fileinput_status = []
        self.execinput_status = []
        self.modularinput_status = []
        self.rawtcp_status = []
        self.cookedtcp_status = []
        self.udphosts_status = []
        self.tcprawlistenerports_status = []
        self.tcpcookedlistenerports_status = []
        self.udplistenerports_status = []
        try:
            for inputtype in self._services_admin_inputstatus['feed']['entry']:
                if inputtype['title'] == 'TailingProcessor:FileStatus':
                    monitors = inputtype['content']['inputs']
                    for monitor in monitors:
                        input_dict = {'location': monitor}
                        try:
                            input_dict['type'] = monitors[monitor]['type']
                        except (KeyError, TypeError):
                            input_dict['type'] = ''
                        try:
                            input_dict['percent'] = '%g%%' % float(monitors[monitor]['percent'])
                        except (KeyError, TypeError):
                            input_dict['percent'] = ''
                        try:
                            input_dict['position'] = monitors[monitor]['file position']
                        except (KeyError, TypeError):
                            input_dict['position'] = ''
                        try:
                            input_dict['size'] = monitors[monitor]['file size']
                        except (KeyError, TypeError):
                            input_dict['size'] = ''
                        try:
                            input_dict['parent'] = monitors[monitor]['parent']
                        except (KeyError, TypeError):
                            input_dict['parent'] = ''
                        self.fileinput_status.append(input_dict)
                if inputtype['title'] == 'ExecProcessor:exec commands':
                    monitors = inputtype['content']['inputs']
                    for monitor in monitors:
                        input_dict = {'location': monitor}
                        try:
                            input_dict['exit_desc'] = monitors[monitor]['exit status description']
                        except (KeyError, TypeError):
                            input_dict['exit_desc'] = ''
                        try:
                            input_dict['closed'] = monitors[monitor]['time closed']
                        except (KeyError, TypeError):
                            input_dict['closed'] = ''
                        try:
                            input_dict['opened'] = monitors[monitor]['time opened']
                        except (KeyError, TypeError):
                            input_dict['opened'] = ''
                        try:
                            input_dict['bytes'] = monitors[monitor]['total bytes']
                        except (KeyError, TypeError):
                            input_dict['bytes'] = ''
                        self.execinput_status.append(input_dict)
                if inputtype['title'] == 'ModularInputs:modular input commands':
                    monitors = inputtype['content']['inputs']
                    for monitor in monitors:
                        input_dict = {'location': monitor}
                        try:
                            input_dict['exit_desc'] = monitors[monitor]['exit status description']
                        except (KeyError, TypeError):
                            input_dict['exit_desc'] = ''
                        try:
                            input_dict['closed'] = monitors[monitor]['time closed']
                        except (KeyError, TypeError):
                            input_dict['closed'] = ''
                        try:
                            input_dict['opened'] = monitors[monitor]['time opened']
                        except (KeyError, TypeError):
                            input_dict['opened'] = ''
                        try:
                            input_dict['bytes'] = monitors[monitor]['total bytes']
                        except (KeyError, TypeError):
                            input_dict['bytes'] = ''
                        self.modularinput_status.append(input_dict)
                if inputtype['title'] == 'Raw:tcp':
                    monitors = inputtype['content']['inputs']
                    for monitor in monitors:
                        if monitor == 'tcp':
                            continue
                        try:
                            port, source = monitor.split(':', 1)
                        except ValueError:
                            port, source = '0', monitor
                        input_dict = {'port': port, 'source': source}
                        try:
                            input_dict['exit_desc'] = monitors[monitor]['exit status description']
                        except (KeyError, TypeError):
                            input_dict['exit_desc'] = ''
                        try:
                            input_dict['closed'] = monitors[monitor]['time closed']
                        except (KeyError, TypeError):
                            input_dict['closed'] = ''
                        try:
                            input_dict['opened'] = monitors[monitor]['time opened']
                        except (KeyError, TypeError):
                            input_dict['opened'] = ''
                        try:
                            input_dict['bytes'] = monitors[monitor]['total bytes']
                        except (KeyError, TypeError):
                            input_dict['bytes'] = ''
                        self.rawtcp_status.append(input_dict)
                if inputtype['title'] == 'Cooked:tcp':
                    monitors = inputtype['content']['inputs']
                    for monitor in monitors:
                        if monitor == 'tcp':
                            continue
                        try:
                            port, source = monitor.split(':', 1)
                        except ValueError:
                            port, source = '0', monitor
                        input_dict = {'port': port, 'source': source}
                        try:
                            input_dict['exit_desc'] = monitors[monitor]['exit status description']
                        except (KeyError, TypeError):
                            input_dict['exit_desc'] = ''
                        try:
                            input_dict['closed'] = monitors[monitor]['time closed']
                        except (KeyError, TypeError):
                            input_dict['closed'] = ''
                        try:
                            input_dict['opened'] = monitors[monitor]['time opened']
                        except (KeyError, TypeError):
                            input_dict['opened'] = ''
                        try:
                            input_dict['bytes'] = monitors[monitor]['total bytes']
                        except (KeyError, TypeError):
                            input_dict['bytes'] = ''
                        self.cookedtcp_status.append(input_dict)
                if inputtype['title'] == 'UDP:hosts':
                    monitors = inputtype['content']['inputs']
                    for monitor in monitors:
                        input_dict = {'source': monitor}
                        self.udphosts_status.append(input_dict)
                if inputtype['title'] == 'tcp_raw:listenerports':
                    monitors = inputtype['content']['inputs']
                    for monitor in monitors:
                        input_dict = {'port': monitor}
                        self.tcprawlistenerports_status.append(input_dict)
                if inputtype['title'] == 'tcp_cooked:listenerports':
                    monitors = inputtype['content']['inputs']
                    for monitor in monitors:
                        input_dict = {'port': monitor}
                        self.tcpcookedlistenerports_status.append(input_dict)
                if inputtype['title'] == 'UDP:listenerports':
                    monitors = inputtype['content']['inputs']
                    for monitor in monitors:
                        input_dict = {'port': monitor}
                        self.udplistenerports_status.append(input_dict)
        except KeyError:
            pass  # No input entries

    def poll_service_apps(self):
        """Poll splunklib.client.service.apps"""
        self._service_apps = self.service.apps.list()
        self.apps = []
        try:
            if type(self._service_apps) is not list: self._service_apps = [self._service_apps]
            for app in self._service_apps:
                app_dict = {
                    'title': app.name,
                    'label': app.content['label']}
                if app.content['disabled'] == '0':
                    app_dict['disabled'] = 'No'
                else:
                    app_dict['disabled'] = 'Yes'
                try:
                    app_dict['version'] = app.content['version']
                except KeyError:
                    app_dict['version'] = 'N/A'
                try:
                    app_dict['description'] = app.content['description']
                except KeyError:
                    app_dict['description'] = 'N/A'
                self.apps.append(app_dict)
        except KeyError:
            pass  # No app entries

    def get_services_data(self):
        """GET /services/data/*"""
        self.receiving_ports = []
        try:
            self._services_data_inputs_tcp_cooked = self.rest_call('/services/data/inputs/tcp/cooked', count=-1)
            ports = self._services_data_inputs_tcp_cooked['feed']['entry']
            if type(ports) is not list: ports = [ports]
            for port in ports:
                self.receiving_ports.append(int(port['title']))
        except:
            pass

        self.rawtcp_ports = []
        try:
            self._services_data_inputs_tcp_raw = self.rest_call('/services/data/inputs/tcp/raw', count=-1)
            ports = self._services_data_inputs_tcp_raw['feed']['entry']
            if type(ports) is not list: ports = [ports]
            for port in ports:
                self.rawtcp_ports.append(int(port['title']))
        except:
            pass

        self.udp_ports = []
        try:
            self._services_data_inputs_udp = self.rest_call('/services/data/inputs/udp', count=-1)
            ports = self._services_data_inputs_udp['feed']['entry']
            if type(ports) is not list: ports = [ports]
            for port in ports:
                self.udp_ports.append(int(port['title']))
        except:
            pass

    def get_services_kvstore(self):
        """GET /services/kvstore/*"""
        try:
            self._services_kvstore_status = self.rest_call('/services/kvstore/status', count=-1)
            status_current = self._services_kvstore_status['feed']['entry']['content']['current']
            self.kvstore_port = int(status_current['port'])
        except:
            self.kvstore_port = 0

    def get_services_cluster_master(self):
        """GET /services/cluster/*"""
        try:
            self._services_cluster_config = self.rest_call('/services/cluster/config', count=-1)
            cluster_config = self._services_cluster_config['feed']['entry']['content']
            self.cluster_mode = cluster_config['mode']
            self.cluster_site = cluster_config['site']
            self.cluster_label = cluster_config['cluster_label']
            try:
                self.cluster_replicationport = int(cluster_config['replication_port'])
            except:
                pass
            try:
                self.cluster_replicationfactor = int(cluster_config['replication_factor'])
            except:
                pass
            try:
                self.cluster_searchfactor = int(cluster_config['search_factor'])
            except:
                pass

            if self.cluster_mode == 'master':
                self.cluster_master_uri = '(self)'
            elif self.cluster_mode in ['slave', 'searchhead']:
                # Get list of cluster master nodes and parse for host:port values
                resolved_masteruri = ''
                masteruri_list =\
                    self.rest_call('/services/properties/server/clustering/master_uri', count=-1).split(',')
                for masteruri in masteruri_list:
                    masteruri = masteruri.strip()  # Remove surrounding whitespace
                    if masteruri[:14] == 'clustermaster:':  # Resolve 'clustermaster:' to its stanza's master_uri value
                        masteruri = self.rest_call('/services/properties/server/%s/master_uri' % masteruri, count=-1)
                    if '://' in masteruri:  # Parse host:port from URI
                        masteruri = re.findall(r"https?://(.+)/?(.*)", masteruri)[0][0]
                    resolved_masteruri += masteruri + ', '
                self.cluster_master_uri = resolved_masteruri[:-2]  # Save, excluding final comma and space
            else:
                self.cluster_master_uri = '(none)'
        except:
            pass

        try:
            self._services_shcluster_conf_deploy_fetch_url =\
                self.rest_call('/services/properties/server/shclustering/conf_deploy_fetch_url', count=-1)
            if self._services_shcluster_conf_deploy_fetch_url:
                shcdeployer = re.findall(r"https?://(.+)/?(.*)", self._services_shcluster_conf_deploy_fetch_url)[0][0]
                self.shcluster_deployer = shcdeployer
            else:
                self.shcluster_deployer = '(none)'
        except:
            self.shcluster_deployer = '(none)'

        try:
            self._services_cluster_master_info = self.rest_call('/services/cluster/master/info', count=-1)
            cluster = self._services_cluster_master_info['feed']['entry']['content']
        except KeyError:
            self.cluster_maintenance = False
            self.cluster_rollingrestart = False
            self.cluster_initialized = False
            self.cluster_serviceready = False
            self.cluster_indexingready = False
            self.cluster_alldatasearchable = False
            self.cluster_searchfactormet = False
            self.cluster_replicationfactormet = False
            return

        self.cluster_maintenance = True if cluster['maintenance_mode'] == '1' else False
        self.cluster_rollingrestart = True if cluster['rolling_restart_flag'] == '1' else False
        self.cluster_initialized = True if cluster['initialized_flag'] == '1' else False
        self.cluster_serviceready = True if cluster['service_ready_flag'] == '1' else False
        self.cluster_indexingready = True if cluster['indexing_ready_flag'] == '1' else False

        self._services_cluster_master_generation_master = \
            self.rest_call('/services/cluster/master/generation/master', count=-1)
        generation = self._services_cluster_master_generation_master['feed']['entry']['content']
        self.cluster_alldatasearchable = True if generation['pending_last_reason'] == None else False
        self.cluster_searchfactormet = True if generation['search_factor_met'] == '1' else False
        self.cluster_replicationfactormet = True if generation['replication_factor_met'] == '1' else False

        try:
            self._services_cluster_master_peers = self.rest_call('/services/cluster/master/peers', count=-1)
            self.cluster_peers = []
            self.cluster_peers_searchable = 0
            self.cluster_peers_up = 0
        except:
            pass
        try:
            peers = self._services_cluster_master_peers['feed']['entry']
            if type(peers) is not list: peers = [peers]
            for peer in peers:
                peer_dict = {
                    'name': peer['content']['label'],
                    'site': peer['content']['site'],
                    'is_searchable': 'Yes' if peer['content']['is_searchable'] == '1' else 'No',
                    'status': peer['content']['status'],
                    'buckets': peer['content']['bucket_count'],
                    'location': peer['content']['host_port_pair'],
                    'last_heartbeat': time.strftime("%m/%d/%Y %I:%M:%S %p",
                                                    time.localtime(float(peer['content']['last_heartbeat']))),
                    'replication_port': peer['content']['replication_port'],
                    'base_gen_id': peer['content']['base_generation_id'],
                    'guid': peer['title']}
                if peer_dict['is_searchable'] == 'Yes':
                    self.cluster_peers_searchable += 1
                if peer_dict['status'] == 'Up':
                    self.cluster_peers_up += 1
                self.cluster_peers.append(peer_dict)
        except KeyError:
            pass  # No peer entries

        try:
            self._services_cluster_master_indexes = self.rest_call('/services/cluster/master/indexes', count=-1)
            self.cluster_indexes = []
            self.cluster_indexes_searchable = 0
        except:
            pass
        try:
            indexes = self._services_cluster_master_indexes['feed']['entry']
            if type(indexes) is not list: indexes = [indexes]
            for index in indexes:
                index_dict = {
                    'name': index['title'],
                    'is_searchable': 'Yes' if index['content']['is_searchable'] == '1' else 'No',
                    'buckets': index['content']['num_buckets'],
                    'cumulative_data_size': '%.2f GB' % (float(index['content']['index_size'])/1024/1024/1024)}

                # Searchable Data Copies, i.e. "2 (100:100%)"
                copy_total = len(index['content']['searchable_copies_tracker'])
                text = str(copy_total)
                copy = 0
                while copy < copy_total:
                    actual_copies = float(
                        index['content']['searchable_copies_tracker'][str(copy)]['actual_copies_per_slot']
                    )
                    expected_copies = float(
                        index['content']['searchable_copies_tracker'][str(copy)]['expected_total_per_slot']
                    )
                    if copy == 0:
                        text += ' (%.0f' % (actual_copies / expected_copies * 100)
                    else:
                        text += ':%.0f' % (actual_copies / expected_copies * 100)
                    copy += 1
                index_dict['searchable_data_copies'] = '%s%%)' % text

                # Replicated Data Copies, i.e. "3 (100:100:100%)"
                copy_total = len(index['content']['replicated_copies_tracker'])
                text = str(copy_total)
                copy = 0
                while copy < copy_total:
                    actual_copies = float(
                        index['content']['replicated_copies_tracker'][str(copy)]['actual_copies_per_slot']
                    )
                    expected_copies = float(
                        index['content']['replicated_copies_tracker'][str(copy)]['expected_total_per_slot']
                    )
                    if copy == 0:
                        text += ' (%.0f' % (actual_copies / expected_copies * 100)
                    else:
                        text += ':%.0f' % (actual_copies / expected_copies * 100)
                    copy += 1
                index_dict['replicated_data_copies'] = '%s%%)' % text

                if index_dict['is_searchable'] == 'Yes':
                    self.cluster_indexes_searchable += 1
                self.cluster_indexes.append(index_dict)
        except KeyError:
            pass  # No index entries

        try:
            self._services_cluster_master_searchheads = self.rest_call('/services/cluster/master/searchheads', count=-1)
            self.cluster_searchheads = []
            self.cluster_searchheads_connected = 0
        except:
            pass
        try:
            searchheads = self._services_cluster_master_searchheads['feed']['entry']
            if type(searchheads) is not list: searchheads = [searchheads]
            for searchhead in searchheads:
                searchhead_dict = {
                    'name': searchhead['content']['label'],
                    'site': searchhead['content']['site'],
                    'status': searchhead['content']['status'],
                    'location': searchhead['content']['host_port_pair'],
                    'guid': searchhead['title']}
                if searchhead_dict['status'] == 'Connected':
                    self.cluster_searchheads_connected += 1
                self.cluster_searchheads.append(searchhead_dict)
                #self._search('host=' + searchhead['content']['label'] + '')
        except KeyError:
            pass  # No search head entries

    def get_services_shcluster(self):
        """GET /services/shcluster/*"""
        try:
            self._services_shcluster_config = self.rest_call('/services/shcluster/config', count=-1)
            shcluster_config = self._services_shcluster_config['feed']['entry']['content']
            self.shcluster_label = shcluster_config['shcluster_label']
            try:
                self.shcluster_replicationport = int(shcluster_config['replication_port'])
            except:
                pass
            try:
                self.shcluster_replicationfactor = int(shcluster_config['replication_factor'])
            except:
                pass
        except:
            pass

        try:
            self._services_shcluster_status = self.rest_call('/services/shcluster/status', count=-1)
            captain = self._services_shcluster_status['feed']['entry']['content']['captain']

            # Get SHC status and captain details
            self.shcluster_captainlabel = captain['label']
            self.shcluster_captainuri = captain['mgmt_uri']
            self.shcluster_captainid = captain['id']
            self.shcluster_dynamiccaptain = True if captain['dynamic_captain'] == '1' else False
            self.shcluster_electedcaptain = captain['elected_captain']
            self.shcluster_rollingrestart = True if captain['rolling_restart_flag'] == '1' else False
            self.shcluster_serviceready = True if captain['service_ready_flag'] == '1' else False
            self.shcluster_minpeersjoined = True if captain['min_peers_joined_flag'] == '1' else False
            self.shcluster_initialized = True if captain['initialized_flag'] == '1' else False
        except:
            self.shcluster_dynamiccaptain = False
            self.shcluster_rollingrestart = False
            self.shcluster_serviceready = False
            self.shcluster_minpeersjoined = False
            self.shcluster_initialized = False

        try:
            self._services_shcluster_member_members = self.rest_call('/services/shcluster/member/members', count=-1)
            members = self._services_shcluster_member_members['feed']['entry']
            self.shcluster_members = []

            # Get list of SHC members
            for member in members:
                content = member['content']
                members_dict = {
                    'label': content['label'],
                    'site': content['site'],
                    'status': content['status'],
                    'artifacts': content['artifact_count'],
                    'host_port_pair': content['host_port_pair'],
                    'last_heartbeat': time.strftime("%m/%d/%Y %I:%M:%S %p",
                                      time.localtime(float(content['last_heartbeat']))),
                    'replication_port': content['replication_port'],
                    'restart_required': 'Yes' if content['advertise_restart_required'] == '1' else 'No',
                    'guid': member['title']}
                self.shcluster_members.append(members_dict)
        except:
            pass

    def get_services_server_status(self):
        """GET /services/server/status/*"""
        # Disk Partitions
        try:
            self._services_server_status_partitionsspace = self.rest_call('/services/server/status/partitions-space',
                                                                          count=-1)
            self.disk_partitions = []
            try:
                filesystems = self._services_server_status_partitionsspace['feed']['entry']
                if type(filesystems) is not list: filesystems = [filesystems]
                for mount in filesystems:
                    free = float(mount['content']['free'])
                    capacity = float(mount['content']['capacity'])
                    mount_dict = {
                        'name': mount['content']['mount_point'],
                        'type': mount['content']['fs_type'],
                        'used': '%.1f%%' % ((capacity - free) / capacity*100),
                        'total': '%.2f GB' % (float(mount['content']['capacity'])/1024)}
                    self.disk_partitions.append(mount_dict)
            except KeyError:
                pass  # No peer entries
        except KeyError:
            pass

        # Host-Wide Resource Usage
        try:
            self._services_server_status_resourceusage_hostwide = self.rest_call(
                '/services/server/status/resource-usage/hostwide',
                count=-1
            )
            cpu_usage = self._services_server_status_resourceusage_hostwide['feed']['entry']['content']['cpu_idle_pct']
            self.cpu_usage = 100 - int(float(cpu_usage))

            self.mem = self._services_server_status_resourceusage_hostwide['feed']['entry']['content']['mem']
            self.mem_used = self._services_server_status_resourceusage_hostwide['feed']['entry']['content']['mem_used']
            self.mem_usage = int(float(self.mem_used) / float(self.mem) * 100)

            self.swap = self._services_server_status_resourceusage_hostwide['feed']['entry']['content']['swap']
            self.swap_used = \
                self._services_server_status_resourceusage_hostwide['feed']['entry']['content']['swap_used']
            self.swap_usage = int(float(self.swap_used) / float(self.swap) * 100)
        except KeyError:
            pass

        # I/O Stats Resource Usage
        #try:
        #    self._services_server_status_resourceusage_iostats = self.rest_call(
        #      '/services/server/status/resource-usage/iostats',
        #      count=-1
        #    )
        #    pprint(self._services_server_status_resourceusage_iostats)
        #except KeyError:
        #    pass

        # Splunk Process Resource Usage
        try:
            self._services_server_status_resourceusage_splunkprocesses = self.rest_call(
                '/services/server/status/resource-usage/splunk-processes',
                count=-1
            )
            self.splunk_processes = []
            try:
                processes = self._services_server_status_resourceusage_splunkprocesses['feed']['entry']
                if type(processes) is not list: processes = [processes]
                for process in processes:
                    process_dict = {
                        'name': process['content']['process'],
                        'pid': process['content']['pid'],
                        'parent_pid': process['content']['ppid'],
                        'cpu': '%.0f%%' % int(float(process['content']['pct_cpu'])),
                        'mem': '%.0f%%' % int(float(process['content']['pct_memory'])),
                        'args': process['content']['args']}
                    self.splunk_processes.append(process_dict)
            except KeyError:
                pass  # No peer entries
        except KeyError:
            pass

    # Pull configuration values

    def get_configuration_kvpairs(self, filename, html=False):
        """GET /services/properties/*"""
        conf = self.rest_call('/services/properties/%s' % filename, count=-1)['feed']['entry']
        if type(conf) is not list: conf = [conf]
        data = ''
        for stanzadict in conf:
            stanza = stanzadict['title']
            if html:
                data += '<font color=\"Orange\">[%s]</font><br>' % stanza
            else:
                data += '[%s]\n' % stanza
            kvpairs = []
            try:
                keydicts = self.rest_call(stanzadict['link']['href'], count=-1)['feed']['entry']
                if type(keydicts) is not list: keydicts = [keydicts]
            except KeyError:  # Stanza contains no key=value pairs
                keydicts = []
            for keydict in keydicts:
                key = keydict['title']
                try:
                    value = keydict['content']['$text']
                except KeyError:  # Key contains no value
                    value = ''
                if key[0:4] == 'eai:':
                    continue
                if html:
                    kvpairs.append('%s = <font color=\"Green\">%s</font><br>' % (key, value))
                else:
                    kvpairs.append('%s = %s\n' % (key, value))
            kvpairs.sort()
            for kvpair in kvpairs:
                data += kvpair
            data += '<br>' if html else '\n'
        return data

    # Control process

    def refresh_config(self):
        """Performs actions similar to web server URI /debug/refresh"""
        try:
            self._servicesNS_admin_search_admin = self.rest_call('/servicesNS/admin/search/admin', count=-1)
            endpoints = [  # Manually add specified endpoints
                'admin/conf-times',
                'data/ui/manager',
                'data/ui/nav',
                'data/ui/views']
            # Add all endpoints under '/servicesNS/admin/search/admin' with _reload link
            for entry in self._servicesNS_admin_search_admin['feed']['entry']:
                # Ignore incapable endpoints
                if entry['title'] == 'fifo' and 'Windows' in self.os:  # never loads on Windows despite being advertised
                    continue
                if entry['title'] == 'auth-services':  # causes logout when refreshed
                    continue
                # Add the rest
                for link in entry['link']:
                    if link['rel'] == '_reload':
                        name = re.findall(r'/servicesNS/admin/search/(.+)/_reload', link['href'])[0]
                        endpoints.append(name)
            output = ''
            for endpoint in endpoints:
                try:
                    uri = '/servicesNS/admin/search/%s/_reload' % endpoint
                    self.service.post(uri, owner='nobody', app='search', sharing='user')
                    output += 'Refreshing %s OK\n' % endpoint.ljust(39, ' ')
                except Exception, e:
                    output += 'Refreshing %s %s\n' % (endpoint.ljust(42, ' '), e)
                except:
                    output += 'Refreshing %s %s\n' % (endpoint.ljust(42, ' '), 'unspecified error')
            output += 'DONE'
        except:
            output = "Unhandled exception while performing refresh."

        return output

    # Other

    def report_builder(self, healthchecks):
        """Executes discovery and health checks against connected instance, recording results to self.report"""
        # In the config, unspecified values will be replaced with defaults, while "False" values won't be checked
        self.report = []

        # Convenience function to add individual entries to the report
        def report_append(category, name, health, value):
            self.report.append({
                'category': category,
                'name': name,
                'health': health,
                'value': value
            })

        # Report entries, by category

        #  Server
        report_append('Server', 'Host/IP', 'N/A', self.mgmt_host)
        report_append('Server', 'Server Name', 'N/A', self.server_name)
        report_append('Server', 'GUID', 'N/A', self.guid)
        report_append('Server', 'Type', 'N/A', self.type)
        report_append('Server', 'Roles', 'N/A', ', '.join(map(str, self.roles)))
        report_append('Server', 'OS', 'N/A', self.os)
        report_append('Server', 'Web Enabled', 'N/A', str(self.http_server))

        if healthchecks['version_warning'] or healthchecks['version_caution']:
            if self.version:
                minor_version = float(self.version.split('.')[0] + '.' + self.version.split('.')[1])
                if minor_version <= healthchecks['version_warning']:
                    health = 'Warning'
                elif minor_version <= healthchecks['version_caution']:
                    health = 'Caution'
                else:
                    health = 'OK'
                    value = self.version
            else:
                health = 'Unknown'
                value = '?'
            report_append('Server', 'Version', health, value)

        if healthchecks['uptime_warning'] or healthchecks['uptime_caution']:
            if self.startup_time:
                uptime_seconds = int(time.time()) - self.startup_time
                if uptime_seconds < healthchecks['uptime_warning']:
                    health = 'Warning'
                elif uptime_seconds < healthchecks['uptime_caution']:
                    health = 'Caution'
                else:
                    health = 'OK'
                value = self.startup_time_formatted
            else:
                health = 'Unknown'
                value = '?'
            report_append('Server', 'Uptime', health, value)

        if healthchecks['http_ssl_caution']:
            if not self.http_ssl:
                if healthchecks['http_ssl_caution']:
                    health = 'Caution'
                    value = 'False'
                else:
                    health = 'OK'
                    value = 'True'
            else:
                health = 'Unknown'
                value = '?'
            report_append('Server', 'HTTP SSL', health, value)

        if healthchecks['messages_caution']:
            if self.messages:
                messages = []
                health = 'OK'
                for message in self.messages:
                    if str(message['severity']).lower != 'info':
                        health = 'Caution'
                        messages.append(message['title'])
                value = ', '.join(messages) if messages else 'None'
            else:
                health = 'OK'
                value = 'None'
            report_append('Server', 'Messages', health, value)

        # Ports
        report_append('Ports', 'Management Port', 'N/A', str(self.mgmt_port))
        report_append('Ports', 'Web Port', 'N/A', str(self.http_port))
        report_append('Ports', 'Receiving Ports', 'N/A', ', '.join(map(str, self.receiving_ports)))
        report_append('Ports', 'TCP Input Ports', 'N/A', ', '.join(map(str, self.rawtcp_ports)))
        report_append('Ports', 'UDP Input Ports', 'N/A', ', '.join(map(str, self.udp_ports)))
        report_append('Ports', 'Replication Port', 'N/A', str(self.cluster_replicationport))
        report_append('Ports', 'KV Store Port', 'N/A', str(self.kvstore_port))

        #  Resources
        if healthchecks['cpu_cores_caution']:
            if self.cores:
                health = 'Caution' if self.cores < healthchecks['cpu_cores_caution'] else 'OK'
                value = str(self.cores)
            else:
                health = 'Unknown'
                value = '?'
            report_append('Resources', 'CPU Cores', health, value)

        if healthchecks['mem_capacity_caution']:
            if self.ram:
                health = 'Caution' if self.ram < healthchecks['mem_capacity_caution'] else 'OK'
                value = "%s MB" % self.ram
            else:
                health = 'Unknown'
                value = '?'
            report_append('Resources', 'RAM Size', health, value)

        if healthchecks['cpu_usage_warning'] or healthchecks['cpu_usage_caution']:
            if self.cpu_usage:
                if self.cpu_usage >= healthchecks['cpu_usage_warning']:
                    health = 'Warning'
                elif self.cpu_usage >= healthchecks['cpu_usage_caution']:
                    health = 'Caution'
                else:
                    health = 'OK'
                value = "%i%%" % self.cpu_usage
            else:
                health = 'Unknown'
                value = '?'
            report_append('Resources', 'CPU Usage', health, value)

        if healthchecks['mem_usage_warning'] or healthchecks['mem_usage_caution']:
            if self.mem_usage:
                if self.mem_usage >= healthchecks['mem_usage_warning']:
                    health = 'Warning'
                elif self.mem_usage >= healthchecks['mem_usage_caution']:
                    health = 'Caution'
                else:
                    health = 'OK'
                value = "%i%%" % self.mem_usage
            else:
                health = 'Unknown'
                value = '?'
            report_append('Resources', 'RAM Usage', health, value)

        if healthchecks['swap_usage_warning'] or healthchecks['swap_usage_caution']:
            if self.swap_usage:
                if self.swap_usage >= healthchecks['swap_usage_warning']:
                    health = 'Warning'
                elif self.swap_usage >= healthchecks['swap_usage_caution']:
                    health = 'Caution'
                else:
                    health = 'OK'
                value = "%i%%" % self.swap_usage
            else:
                health = 'Unknown'
                value = '?'
            report_append('Resources', 'Swap Usage', health, value)

        if healthchecks['diskpartition_usage_warning'] or healthchecks['diskpartition_usage_caution']:
            if self.disk_partitions:
                mounts = []
                health = 'OK'
                for mount in self.disk_partitions:
                    name = mount['name']
                    percent_used = float(mount['used'][:-1])
                    if percent_used >= healthchecks['diskpartition_usage_warning'] and health in ['OK', 'Caution']:
                        health = 'Warning'
                    elif percent_used >= healthchecks['diskpartition_usage_caution'] and health == 'OK':
                        health = 'Caution'
                    mounts.append("'%s': %i%%" % (name, percent_used))
                value = ', '.join(mounts) if mounts else 'None'
            else:
                health = 'Unknown'
                value = '?'
            report_append('Resources', 'Disk Usage', health, value)

        # Deployment
        report_append('Deployment', 'Client of Deployment Server', 'N/A', self.deployment_server)
        report_append('Deployment', 'Cluster Master', 'N/A', self.cluster_master_uri)
        report_append('Deployment', 'Fetch from SHC Deployer', 'N/A', self.shcluster_deployer)

        # Indexer Cluster
        if 'cluster_master' in self.roles:
            report_append('Cluster', 'IC Label', 'N/A', self.cluster_label)
            report_append('Cluster', 'IC Mode', 'N/A', self.cluster_mode)
            report_append('Cluster', 'IC Site', 'N/A', self.cluster_site)

            if healthchecks['cluster_maintenance_caution']:
                if self.cluster_maintenance:
                    report_append('Cluster', 'IC Maintenance Mode', 'Caution', 'True')
                else:
                    report_append('Cluster', 'IC Maintenance Mode', 'OK', 'False')

            if healthchecks['cluster_rollingrestart_caution']:
                if self.cluster_rollingrestart:
                    report_append('Cluster', 'IC Rolling Restart', 'Caution', 'True')
                else:
                    report_append('Cluster', 'IC Rolling Restart', 'OK', 'False')

            if healthchecks['cluster_alldatasearchable_warning']:
                if not self.cluster_alldatasearchable:
                    report_append('Cluster', 'IC All Data Searchable', 'Warning', 'False')
                else:
                    report_append('Cluster', 'IC All Data Searchable', 'OK', 'True')

            report_append('Cluster', 'IC Search Factor', 'N/A', str(self.cluster_searchfactor))
            if healthchecks['cluster_searchfactor_caution']:
                if not self.cluster_searchfactormet:
                    report_append('Cluster', 'IC Search Factor Met', 'Caution', 'False')
                else:
                    report_append('Cluster', 'IC Search Factor Met', 'OK', 'True')

            report_append('Cluster', 'IC Rep Factor', 'N/A', str(self.cluster_replicationfactor))
            if healthchecks['cluster_replicationfactor_caution']:
                if not self.cluster_replicationfactormet:
                    report_append('Cluster', 'IC Rep Factor Met', 'Caution', 'False')
                else:
                    report_append('Cluster', 'IC Rep Factor Met', 'OK', 'True')

            if healthchecks['cluster_peersnotsearchable_warning'] and self.cluster_peers:
                if self.cluster_peers_searchable < len(self.cluster_peers):
                    health = 'Warning'
                else:
                    health = 'OK'
                report_append('Cluster', 'IC Searchable Peers', health,
                              "%s of %s" % (self.cluster_peers_searchable, len(self.cluster_peers)))

            if healthchecks['cluster_searchheadsnotconnected_warning'] and self.cluster_searchheads:
                if self.cluster_searchheads_connected < len(self.cluster_searchheads):
                    health = 'Warning'
                else:
                    health = 'OK'
                report_append('Cluster', 'IC Connected Search Heads', health,
                              "%s of %s" % (self.cluster_searchheads_connected,
                                            len(self.cluster_searchheads)))

        # Search Head Cluster
        if 'shc_member' in self.roles:
            report_append('Cluster', 'SHC Label', 'N/A', self.shcluster_label)
            report_append('Cluster', 'SHC Rep Factor', 'N/A', str(self.shcluster_replicationfactor))

            if healthchecks['shcluster_rollingrestart_caution']:
                if self.shcluster_rollingrestart:
                    report_append('Cluster', 'SHC Rolling Restart', 'Caution', 'True')
                else:
                    report_append('Cluster', 'SHC Rolling Restart', 'OK', 'False')

            if healthchecks['shcluster_serviceready_warning']:
                if not self.shcluster_serviceready:
                    report_append('Cluster', 'SHC Service Ready', 'Warning', 'False')
                else:
                    report_append('Cluster', 'SHC Service Ready', 'OK', 'True')

            if healthchecks['shcluster_minpeersjoined_warning']:
                if not self.shcluster_minpeersjoined:
                    report_append('Cluster', 'SHC Minimum Peers Joined', 'Warning', 'False')
                else:
                    report_append('Cluster', 'SHC Minimum Peers Joined', 'OK', 'True')

        # Counts
        report_append('Counts', 'Messages', 'N/A', str(len(self.messages)))
        report_append('Counts', 'Apps', 'N/A', str(len(self.apps)))
