#!/usr/bin/env python

# Copyright (C) 2012 University of Southern California
# This software is licensed under the GPLv3 license, included in
# ./GPLv3-LICENSE.txt in the source distribution

import errno
import glob
import logging
import os
import re
import stat
import sys
import time

from magi.util import config
from magi.util.agent import SharedServer, agentmethod
from magi.util.execl import run, pipeIn
from magi.util.processAgent import initializeProcessAgent


log = logging.getLogger(__name__)

class ApacheAgent(SharedServer):
	"""
		Provides interface for starting and stopping a shared instance of the Apache server
	"""

	def __init__(self):
		SharedServer.__init__(self)

		# List of variables that the user can set
		self.configVariables = {
			'StartServers': 5,
			'MaxClients': 200,
			'MaxRequestsPerChild': 120,
			'Timeout': 300,
			'KeepAlive': 'On',
			'MaxKeepAliveRequests': 100,
			'KeepAliveTimeout': 30
		}

		# List of modules we need to load for things to work
		self.loadModules = ["fastcgi", "mime"] #enable gnutls if ssl required
		
		self.apacheRootDir = None
		self.configfile = None
		
		self.siteConf = siteConfTemplate \
						.replace("{scripts_dir}", self.getScriptsDir()) \
						.replace("{logs_dir}", config.getTempDir()) 
						#magi log dir is not world writable
		
		
		self.terminateserver()

		self.configure()
		
		#self.setConfig(None)
		
		# GTL - there is a race condition somewhere. Sleep a few seconds, 
		# so we loose the race.
		time.sleep(2)
	
	def runserver(self):
		""" subclass implementation """
		run("apache2ctl start", close_fds=True)
		log.info('Apache started.')
		return True

	def terminateserver(self):
		""" subclass implementation """
		run("apache2ctl stop", close_fds=True)
		log.info('Apache stopped.')
		return True
	
	def enableModule(self, module):
		cmd = "a2enmod %s" %module
		run(cmd, close_fds=True)
		log.info("Module '%s' enabled" %module)
	
	def enableSite(self, site):
		cmd = "a2ensite %s" %site
		run(cmd, close_fds=True)
		log.info("Site '%s' enabled" %site)
		
	def getApacheRootDir(self):
		if self.apacheRootDir is not None:
			return self.apacheRootDir
		
		apacheRootOptionPattern = re.compile(r'HTTPD_ROOT="(.*)"')
		for line in pipeIn("apache2ctl -V", close_fds=True):
			match = apacheRootOptionPattern.search(line)
			if match is not None:
				self.apacheRootDir = match.group(1)
				return self.apacheRootDir
			
		raise OSError(errno.ENOENT, "Unable to locate apache root dir")
	
	def getConfigFile(self):
		if self.configfile is not None:
			return self.configfile
		
		configOptionPattern = re.compile(r'SERVER_CONFIG_FILE="(.*)"')
		for line in pipeIn("apache2ctl -V", close_fds=True):
			match = configOptionPattern.search(line)
			if match is not None:
				filename = match.group(1)
				self.configfile = os.path.join(self.getApacheRootDir(), filename)
				return self.configfile

		raise OSError(errno.ENOENT, "Unable to locate apache config file")

	def getScriptsDir(self):
		return os.path.join(os.path.dirname(__file__), 'htdocs')
	
	def configure(self):
		
		#enable all the required modules
		for module in self.loadModules:
			self.enableModule(module)
			
		#disable existing sites
		for f in glob.glob(os.path.join(self.getApacheRootDir(), 'sites-enabled', '*')):
			os.remove(f)
			
		#create magi site config
		siteConfFile = os.path.join(self.getApacheRootDir(), 'sites-available', 'magi')
		with open(siteConfFile, 'w') as siteConfFileObj:
			siteConfFileObj.write(self.siteConf)
		
		#Apache 2.4 requires .conf to be appended to site configuration file
		#try:
		#	os.remove(siteConfFile+".conf")	
		#except OSError:
		#	pass
		#os.symlink(siteConfFile, siteConfFile+".conf")
		
		#enable only magi site
		self.enableSite('magi')
		
		# GTL HACK - setup.py installs all py files are read/write no execute. 
		# But we have scripts in htdocs which are scripts and must be executable. 
		# So we change them by hand here, in a not standard place. 
		# GTL TODO force sdist (setup.py) to keep file permissions in htdocs dir. 
		for f in glob.glob(os.path.join(self.getScriptsDir(), '*.py')):
			# ugo --> r-x
			os.chmod(f, stat.S_IEXEC | stat.S_IREAD | stat.S_IXGRP | stat.S_IRGRP | stat.S_IXOTH | stat.S_IROTH)

	
	@agentmethod(kwargs="any key/value arguments for apache conf file")
	def setConfig(self, msg, **kwargs):
		"""
			Set configuration values in the apache.conf file, doesn't
			take effect until the next time apache is actually stopped and started
		"""
		for k, v in kwargs.iteritems():
			if k not in self.configVariables:
				log.error("Trying to write config variable %s, doesn't exist" % k)
				continue
			self.configVariables[k] = str(v)
		
		# Modify the config file
		try:
			confFile = self.getConfigFile()
			log.info("Writing our apache configuration to %s" % confFile)
			with open(confFile, 'w') as conf:
				for k, v in self.configVariables.iteritems():
					conf.write("%s %s\n" % (k,v))
		except Exception, e:
			log.error("Failed to update config file: %s", e, exc_info=1)

			
siteConfTemplate = """
<VirtualHost *:80>

        DocumentRoot {scripts_dir}

        <Directory "{scripts_dir}">
		        Options FollowSymLinks ExecCGI
                AllowOverride None
                Order allow,deny
                Allow from all
                SetHandler fastcgi-script
        </Directory>

        ErrorLog {logs_dir}/apache_error.log

        LogLevel info
        CustomLog {logs_dir}/apache.log combined

</VirtualHost>
"""
#Require all granted

def getAgent(**kwargs):
	agent = ApacheAgent()
	agent.setConfiguration(None, **kwargs)
	return agent

if __name__ == "__main__":
	agent = ApacheAgent()
	kwargs = initializeProcessAgent(agent, sys.argv)
	agent.setConfiguration(None, **kwargs)
	agent.run()

