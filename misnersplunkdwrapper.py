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
        if self._service_settings['enableSplunkWebSSL'] == '1':
            self.http_ssl = True
        else:
            self.http_ssl = False
        if self._service_settings['startwebserver'] == '1':
            self.http_server = True
        else:
            self.http_server = False

    def poll_service_info(self):
        """Poll splunklib.client.service.info"""
        self._service_info = self.service.info
        self.version = self._service_info['version']
        self.guid = self._service_info['guid']
        self.startup_time = int(self._service_info['startup_time']) if 'startup_time' in self._service_info else None
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
            self._services_data_inputs_tcp_cooked = None

        self.rawtcp_ports = []
        try:
            self._services_data_inputs_tcp_raw = self.rest_call('/services/data/inputs/tcp/raw', count=-1)
            ports = self._services_data_inputs_tcp_raw['feed']['entry']
            if type(ports) is not list: ports = [ports]
            for port in ports:
                self.rawtcp_ports.append(int(port['title']))
        except:
            self._services_data_inputs_tcp_raw = None

        self.udp_ports = []
        try:
            self._services_data_inputs_udp = self.rest_call('/services/data/inputs/udp', count=-1)
            ports = self._services_data_inputs_udp['feed']['entry']
            if type(ports) is not list: ports = [ports]
            for port in ports:
                self.udp_ports.append(int(port['title']))
        except:
            self._services_data_inputs_udp = None

    def get_services_kvstore(self):
        """GET /services/kvstore/*"""
        try:
            self._services_kvstore_status = self.rest_call('/services/kvstore/status', count=-1)
            status_current = self._services_kvstore_status['feed']['entry']['content']['current']
            self.kvstore_port = int(status_current['port'])
        except:
            self._services_data_inputs_tcp_cooked = None
            self.kvstore_port = False

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
                self.cluster_replicationport = None
            try:
                self.cluster_replicationfactor = int(cluster_config['replication_factor'])
            except:
                self.cluster_replicationfactor = None
            try:
                self.cluster_searchfactor = int(cluster_config['search_factor'])
            except:
                self.cluster_searchfactor = None

            # Get list of cluster master nodes and parse for host:port values
            resolved_masteruri = ''
            masteruri_list = self.rest_call('/services/properties/server/clustering/master_uri', count=-1).split(',')
            for masteruri in masteruri_list:
                masteruri = masteruri.strip()  # Remove surrounding whitespace
                if masteruri[:14] == 'clustermaster:':  # Resolve 'clustermaster:' to its stanza's master_uri value
                    masteruri = self.rest_call('/services/properties/server/%s/master_uri' % masteruri, count=-1)
                if '://' in masteruri:  # Parse host:port from URI
                    masteruri = re.findall(r"https?://(.+)/?(.*)", masteruri)[0][0]
                resolved_masteruri += masteruri + ', '
            self.cluster_master_uri = resolved_masteruri[:-2]  # Save, excluding final comma and space
        except:
            self._services_cluster_config = None
            self.cluster_master_uri = None
            self.cluster_mode = None
            self.cluster_site = None
            self.cluster_label = None
            self.cluster_replicationport = None
            self.cluster_replicationfactor = None
            self.cluster_searchfactor = None

        try:
            self._services_shcluster_conf_deploy_fetch_url =\
                self.rest_call('/services/properties/server/shclustering/conf_deploy_fetch_url', count=-1)
            if self._services_shcluster_conf_deploy_fetch_url:
                shcdeployer = re.findall(r"https?://(.+)/?(.*)", self._services_shcluster_conf_deploy_fetch_url)[0][0]
                self.shcluster_deployer = shcdeployer
            else:
                self.shcluster_deployer = False
        except:
            self._services_shcluster_conf_deploy_fetch_url = None
            self.shcluster_deployer = False

        try:
            self._services_cluster_master_info = self.rest_call('/services/cluster/master/info', count=-1)
            cluster = self._services_cluster_master_info['feed']['entry']['content']
        except KeyError:
            self._services_cluster_master_info = None
            self.cluster_maintenance = False
            self.cluster_rollingrestart = False
            self.cluster_initialized = False
            self.cluster_serviceready = False
            self.cluster_indexingready = False
            self._services_cluster_master_generation_master = None
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

        self._services_cluster_master_peers = self.rest_call('/services/cluster/master/peers', count=-1)
        self.cluster_peers = []
        self.cluster_peers_searchable = 0
        self.cluster_peers_up = 0
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

        self._services_cluster_master_indexes = self.rest_call('/services/cluster/master/indexes', count=-1)
        self.cluster_indexes = []
        self.cluster_indexes_searchable = 0
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

        self._services_cluster_master_searchheads = self.rest_call('/services/cluster/master/searchheads', count=-1)
        self.cluster_searchheads = []
        self.cluster_searchheads_connected = 0
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
                self.shcluster_replicationport = None
            try:
                self.shcluster_replicationfactor = int(shcluster_config['replication_factor'])
            except:
                self.shcluster_replicationfactor = None
        except:
            self._services_shcluster_config = None
            self.shcluster_label = None
            self.shcluster_replicationport = None
            self.shcluster_replicationfactor = None

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
            self._services_shcluster_status = None
            self.shcluster_captainlabel = None
            self.shcluster_captainuri = None
            self.shcluster_captainid = None
            self.shcluster_dynamiccaptain = False
            self.shcluster_electedcaptain = None
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
            self._services_shcluster_member_members = None
            self.shcluster_members = None

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
            self._services_server_status_partitionsspace = None
            self.disk_partitions = None

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
            self._services_server_status_resourceusage_hostwide = None
            self.cpu_usage = None
            self.mem_usage = None
            self.swap_usage = None

        # I/O Stats Resource Usage
        #try:
        #    self._services_server_status_resourceusage_iostats = self.rest_call(
        #      '/services/server/status/resource-usage/iostats',
        #      count=-1
        #    )
        #    pprint(self._services_server_status_resourceusage_iostats)
        #except KeyError:
        #    self._services_server_status_resourceusage_iostats = None

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
            self._services_server_status_resourceusage_splunkprocesses = None
            self.splunk_processes = None

    # Control process

    def refresh_config(self):
        """Performs actions similar to web server URI /debug/refresh"""
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
        return output

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
