#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
os.chdir(os.path.dirname(sys.argv[0]))

sys.path.insert(1, 'modules')

import xmpp
import string
import time
import thread
import random
import types
import traceback
import getopt
import codecs
import macros

################################################################################
CONFIGURATION_FILE = 'dynamic/config.cfg'

GENERAL_CONFIG_FILE = 'config.txt'

fp = open(GENERAL_CONFIG_FILE, 'r')
GENERAL_CONFIG = eval(fp.read())
fp.close()

SERVER = GENERAL_CONFIG['SERVER']
PORT = GENERAL_CONFIG['PORT']
USERNAME = GENERAL_CONFIG['USERNAME']
PASSWORD = GENERAL_CONFIG['PASSWORD']
RESOURCE = GENERAL_CONFIG['RESOURCE']

NICKS_CACHE_FILE = 'dynamic/chatnicks.cfg'
GROUPCHAT_CACHE_FILE = 'dynamic/chatrooms.cfg'
GLOBACCESS_FILE = 'dynamic/globaccess.cfg'
ACCBYCONF_FILE = 'dynamic/accbyconf.cfg'
PLUGIN_DIR = 'plugins'

DEFAULT_NICK = GENERAL_CONFIG['DEFAULT_NICK']
ADMINS = GENERAL_CONFIG['ADMINS']
ADMIN_PASSWORD = GENERAL_CONFIG['ADMIN_PASSWORD']

AUTO_RESTART = GENERAL_CONFIG['AUTO_RESTART']

PUBLIC_LOG_DIR = GENERAL_CONFIG['PUBLIC_LOG_DIR']
PRIVATE_LOG_DIR = GENERAL_CONFIG['PRIVATE_LOG_DIR']

INITSCRIPT_FILE = GENERAL_CONFIG['INITSCRIPT_FILE']

roles={'none':0, 'visitor':0, 'participant':10, 'moderator':15}
affiliations={'none':0, 'member':0, 'admin':5, 'owner':15}
	
BOOTUP_TIMESTAMP = time.time()
################################################################################

COMMANDS = {}
MACROS = macros.Macros()

GROUPCHATS = {}

MESSAGE_HANDLERS = []
OUTGOING_MESSAGE_HANDLERS = []
JOIN_HANDLERS = []
LEAVE_HANDLERS = []
IQ_HANDLERS = []
PRESENCE_HANDLERS = []
GROUPCHAT_INVITE_HANDLERS = []

COMMAND_HANDLERS = {}

GLOBACCESS = {}
ACCBYCONF = {}

COMSET = {}

JCON = None

CONFIGURATION = {}

################################################################################
"""
optlist, args = getopt.getopt(sys.argv[1:], '', ['pid='])
for opt_tuple in optlist:
	if opt_tuple[0] == '--pid':
		pid_filename = opt_tuple[1]
		fp = open(pid_filename, 'w')
		fp.write(str(os.getpid()))
		fp.close()
"""
################################################################################

def initialize_file(filename, data=''):
	if not os.access(filename, os.F_OK):
		fp = file(filename, 'w')
		if data:
			fp.write(data)
		fp.close()

def read_file(filename):
	fp = file(filename)
	data = fp.read()
	fp.close()
	return data

def write_file(filename, data):
	fp = file(filename, 'w')
	fp.write(data)
	fp.close()
	
def check_file(gch,file):
	path='dynamic/'+gch+'/'+file
	if os.path.exists(path):
		return 1
	else:
		try:
			if not os.path.exists('dynamic/'+gch):
				os.mkdir('dynamic/'+gch)
			if os.access(path, os.F_OK):
				fp = file(path, 'w')
			else:
				fp = open(path, 'w')
			fp.write('{}')
			fp.close()
			return 1
		except:
			return 0	
	
################################################################################

initialize_file(CONFIGURATION_FILE, '{}')
try:
	CONFIGURATION = eval(read_file(CONFIGURATION_FILE))
except:
	print 'Error Parsing Configuration File'

def config_get(category, key):
	if CONFIGURATION.has_key(category):
		if CONFIGURATION[category].has_key(key):
			return CONFIGURATION[category][key]
		else:
			return None
	else:
		return None

def config_set(category, key, value):
	if not CONFIGURATION.has_key(category):
		CONFIGURATION[category] = {}
	CONFIGURATION[category][key] = value
	config_string = '{\n'
	for category in CONFIGURATION.keys():
		config_string += repr(category) + ':\n'
		for key in CONFIGURATION[category].keys():
			config_string += '\t' + repr(key) + ': ' + repr(CONFIGURATION[category][key]) + '\n'
		config_string += '\n'
	config_string += '}'
	write_file(CONFIGURATION_FILE, config_string)

################################################################################

def register_message_handler(instance):
	MESSAGE_HANDLERS.append(instance)
def register_outgoing_message_handler(instance):
	OUTGOING_MESSAGE_HANDLERS.append(instance)
def register_join_handler(instance):
	JOIN_HANDLERS.append(instance)
def register_leave_handler(instance):
	LEAVE_HANDLERS.append(instance)
def register_iq_handler(instance):
	IQ_HANDLERS.append(instance)
def register_presence_handler(instance):
	PRESENCE_HANDLERS.append(instance)
def register_groupchat_invite_handler(instance):
	GROUPCHAT_INVITE_HANDLERS.append(instance)

def register_command_handler(instance, command={}, category=[], access=0, desc='', syntax='', examples=[]):
	for x in command.keys():
		comm = command[x].decode('utf-8')
		if not COMMAND_HANDLERS.has_key(x):
			COMMAND_HANDLERS[x]=x
			COMMAND_HANDLERS[x]={}
		COMMAND_HANDLERS[x][comm] = instance
		if not COMMANDS.has_key(x):
			COMMANDS[x]=x
			COMMANDS[x]={}
		COMMANDS[x][comm] = {'category': category, 'access': access, 'desc': desc, 'syntax': syntax, 'examples': examples}

def call_message_handlers(type, source, body):
	for handler in MESSAGE_HANDLERS:
		thread.start_new(handler, (type, source, body))
def call_outgoing_message_handlers(target, body):
	for handler in OUTGOING_MESSAGE_HANDLERS:
		thread.start_new(handler, (target, body))
def call_join_handlers(groupchat, nick):
	for handler in JOIN_HANDLERS:
		thread.start_new(handler, (groupchat, nick))
def call_leave_handlers(groupchat, nick):
	for handler in LEAVE_HANDLERS:
		thread.start_new(handler, (groupchat, nick))
def call_iq_handlers(iq):
	for handler in IQ_HANDLERS:
		thread.start_new(handler, (iq,))
def call_presence_handlers(prs):
	for handler in PRESENCE_HANDLERS:
		thread.start_new(handler, (prs,))
def call_groupchat_invite_handlers(source, groupchat, body):
	for handler in GROUPCHAT_INVITE_HANDLERS:
		thread.start_new(handler, (source, groupchat, body))

def call_command_handlers(command, type, source, parameters, callee):
	try:
		comset=int(COMSET[source[1]])
	except:
		comset=1
	real_access = MACROS.get_access(callee)
	if real_access < 0:
		real_access = COMMANDS[comset][command]['access']
	if COMMAND_HANDLERS[comset].has_key(command):
		if has_access(source, real_access, source[1]):
			thread.start_new(COMMAND_HANDLERS[comset][command], (type, source, parameters))
		else:
			reply(type, source, 'ага, щаззз')

################################################################################

def find_plugins():
	valid_plugins = []
	invalid_plugins = []
	possibilities = os.listdir('plugins')
	for possibility in possibilities:
		if possibility[-3:].lower() == '.py':
			try:
				fp = file(PLUGIN_DIR + '/' + possibility)
				data = fp.read(23)
				if data == '#===istalismanplugin===':
					valid_plugins.append(possibility)
				else:
					invalid_plugins.append(possibility)
			except:
				pass
	if invalid_plugins:
		print '\nfailed to load',len(invalid_plugins),'plugins:'
		invalid_plugins.sort()
		invp=', '.join(invalid_plugins)
		print invp
		print 'plugins header is not corresponding\n'
	else:
		pass
	return valid_plugins

def load_plugins():
	valid_plugins = find_plugins()
	for valid_plugin in valid_plugins:
		try:
			fp = file(PLUGIN_DIR + '/' + valid_plugin)
			exec fp in globals()
			fp.close()
		except:
			raise
	valid_plugins.sort()
	print '\nloaded',len(valid_plugins),'plugins:'
	loaded=', '.join(valid_plugins)
	print loaded,'\n'

def load_initscript():
	print 'Exec Init Script\n'
	fp = file(INITSCRIPT_FILE)
	exec fp in globals()
	fp.close()
	
def get_comset():
	possibilities = os.listdir('dynamic')
	for possibility in possibilities:
		try:
			files = os.listdir('dynamic/'+possibility)
			for x in files:
				if x == 'config.cfg':
					cfgfile='dynamic/'+possibility+'/config.cfg'
					try:
						cfg = eval(read_file(cfgfile))
						if cfg.has_key('comset'):
							comset=cfg['comset']
							COMSET[possibility]=possibility
							COMSET[possibility]=comset
							comset_ontopres(possibility)
					except:
						pass
		except:
			pass
	
def comset_ontopres(groupchat):	
	if groupchat in GROUPCHATS.keys():		
		comset=COMSET[groupchat]
		nick = get_nick(groupchat)
		if comset==1:
			comm=u'помощь'
			desc=u'в данной конференции включен первый набор команд - русские без экранирования'
		elif comset==2:
			comm=u'helpme'
			desc=u'в данной конференции включен второй набор команд - английские без экранирования'
		elif comset==3:
			comm=u'!help'
			desc=u'в данной конференции включен третий набор команд - английские, экранированные симвоволом (!)'
		presence=xmpp.protocol.Presence(groupchat+'/'+nick)
		presence.setStatus(u'напишите "'+comm+u'" и следуйте указаниям, чтобы понять что к чему!\n'+desc)
		presence.setTag('x',namespace=xmpp.NS_MUC).addChild('history',{'maxchars':'0','maxstanzas':'0'})
		JCON.send(presence)
			
################################################################################

def get_conf_jid(gc, nick):
	if gc.has_key(nick):
		info = gc[nick]
		if info.has_key('jid') and info['jid']:
			return info['jid']
	return ''
	
def get_jid(source, parameter):
	groupchat = source[1]
	parameter = parameter.strip()
	jid = ''
	if parameter == '':
		parameter = source[2]
	if GROUPCHATS.has_key(groupchat):
		jid = get_conf_jid(GROUPCHATS[groupchat], parameter)
#	jid = get_true_jid(source)
	return jid

def get_true_jid(jid):
	true_jid = ''
	if type(jid) is types.ListType:
		jid = jid[0]
	if type(jid) is types.InstanceType:
		jid = unicode(jid) # str(jid)
	stripped_jid = string.split(jid, '/', 1)[0]
	resource = ''
	if len(string.split(jid, '/', 1)) == 2:
		resource = string.split(jid, '/', 1)[1]
	if GROUPCHATS.has_key(stripped_jid):
		if GROUPCHATS[stripped_jid].has_key(resource):
			true_jid = string.split(unicode(GROUPCHATS[stripped_jid][resource]['jid']), '/', 1)[0]
		else:
			true_jid = stripped_jid
	else:
		true_jid = stripped_jid
	return true_jid
	
def get_groupchat(jid):
	if type(jid) is types.ListType:
		jid = jid[1]
	jid = string.split(unicode(jid), '/')[0] # str(jid)
	if GROUPCHATS.has_key(jid):
		return jid
	else:
		return None

def get_nick(groupchat):
	try:
		nicks_string = read_file(NICKS_CACHE_FILE)
	except:
		fp = file(NICKS_CACHE_FILE, 'w')
		fp.write('{}')
		fp.close()
		nicks_string = '{}'
		print 'Initializing ' + NICKS_CACHE_FILE
	nicks = eval(nicks_string)
	if nicks.has_key(groupchat):
		return nicks[groupchat]
	else:
		return DEFAULT_NICK

def set_nick(groupchat, nick=None):
	nicks = eval(read_file(NICKS_CACHE_FILE))
	if nick:
		nicks[groupchat] = nick
	elif groupchat:
		del nicks[groupchat]
	fp = file(NICKS_CACHE_FILE, 'w')
	fp.write(str(nicks))
	fp.close()
	

################################################################################

def get_access_levels():
	global GLOBACCESS
	initialize_file(GLOBACCESS_FILE, '{}')
	GLOBACCESS = eval(read_file(GLOBACCESS_FILE))
	for jid in ADMINS:
		level = 100
		GLOBACCESS[jid] = level
		write_file(GLOBACCESS_FILE, str(GLOBACCESS))
	

def change_access_temp(gch, source, level=0):
	global ACCBYCONF
	jid = get_true_jid(source)
	try:
		level = int(level)
	except:
		level = 0
	if not ACCBYCONF.has_key(gch):
		ACCBYCONF[gch] = gch
		ACCBYCONF[gch] = {}
	if not ACCBYCONF[gch].has_key(jid):
		ACCBYCONF[gch][jid]=jid
	ACCBYCONF[gch][jid]=level
	
def change_access_perm(gch, source, level=0):
	global ACCBYCONF
	jid = get_true_jid(source)
	try:
		level = int(level)
	except:
		level = 0
	temp_access = eval(read_file(ACCBYCONF_FILE))
	if not temp_access.has_key(gch):
		temp_access[gch] = gch
		temp_access[gch] = {}
	if not temp_access[gch].has_key(jid):
		temp_access[gch][jid]=jid
	temp_access[gch][jid]=level
	write_file(ACCBYCONF_FILE, str(temp_access))
	if not ACCBYCONF.has_key(gch):
		ACCBYCONF[gch] = gch
		ACCBYCONF[gch] = {}
	if not ACCBYCONF[gch].has_key(jid):
		ACCBYCONF[gch][jid]=jid
	ACCBYCONF[gch][jid]=level
	
def change_access_perm_glob(source, level=0):
	global GLOBACCESS
	jid = get_true_jid(source)
	temp_access = eval(read_file(GLOBACCESS_FILE))
	if level:
		temp_access[jid] = level
	else:
		del temp_access[jid]
	write_file(GLOBACCESS_FILE, str(temp_access))

def user_level(source, gch):
	global ACCBYCONF
	global GLOBACCESS
	ACCFILE = eval(read_file(ACCBYCONF_FILE))
	jid = get_true_jid(source)
	if GLOBACCESS.has_key(jid):
		return GLOBACCESS[jid]
	if ACCFILE.has_key(gch):
		if ACCFILE[gch].has_key(jid):
			return ACCFILE[gch][jid]
	if ACCBYCONF.has_key(gch):
		if ACCBYCONF[gch].has_key(jid):
			return ACCBYCONF[gch][jid]
	return 0

def has_access(source, required_level, gch):
	jid = get_true_jid(source)
	if user_level(jid,gch) >= int(required_level):
		return 1
	return 0
	
################################################################################

def join_groupchat(groupchat, nick=None):
	if nick:
		set_nick(groupchat, nick)
	else:
		nick = get_nick(groupchat)
	presence=xmpp.protocol.Presence(groupchat+'/'+nick)
	presence.setStatus(u'напишите (wait) и следуйте указаниям, чтобы понять что к чему!')
	presence.setTag('x',namespace=xmpp.NS_MUC).addChild('history',{'maxchars':'0','maxstanzas':'0'})
	JCON.send(presence)
	if not GROUPCHATS.has_key(groupchat):
		GROUPCHATS[groupchat] = {}
		write_file(GROUPCHAT_CACHE_FILE, str(GROUPCHATS.keys()))
	if not COMSET.has_key(groupchat):
		CFGPATH='dynamic/'+groupchat+'/config.cfg'
		if check_file(groupchat,'config.cfg'):
			cfg = eval(read_file(CFGPATH))
			if not cfg.has_key('comset'):
				cfg['comset']=1
				write_file(CFGPATH, str(cfg))
				COMSET[groupchat]=groupchat
				COMSET[groupchat]=1
		else:
			print u'бяка'
		
def leave_groupchat(groupchat):
	JCON.send(xmpp.Presence(groupchat, 'unavailable'))
	if GROUPCHATS.has_key(groupchat):
		del GROUPCHATS[groupchat]
		write_file(GROUPCHAT_CACHE_FILE, str(GROUPCHATS.keys()))

def msg(target, body):
	msg = xmpp.Message(target, body)
	if GROUPCHATS.has_key(target):
		msg.setType('groupchat')
	else:
		msg.setType('chat')
	JCON.send(msg)
	call_outgoing_message_handlers(target, body)

def reply(ltype, source, body):
	if type(body) is types.StringType:
		body = body.decode('utf-8', 'backslashreplace')
	if ltype == 'public':
		if len(body)>1000:
			body=body[:1000]+u'[...]'
		msg(source[1], source[2] + ': ' + body)
	elif ltype == 'private':
		msg(source[0], body)

def isadmin(jid):
	admin_list = ADMINS
	if type(jid) is types.ListType:
		jid = jid[0]
	jid = str(jid)
	stripped_jid = string.split(jid, '/', 1)[0]
	resource = ''
	if len(string.split(jid, '/', 1)) == 2:
		resource = string.split(jid, '/', 1)[1]
	if stripped_jid in admin_list:
		return 1
	elif GROUPCHATS.has_key(stripped_jid):
		if GROUPCHATS[stripped_jid].has_key(resource):
			if string.split(str(GROUPCHATS[stripped_jid][resource]['jid']), '/', 1)[0] in admin_list:
				return 1
	return 0

################################################################################
def findPresenceItem(node):
	for p in [x.getTag('item') for x in node.getTags('x')]:
		if p != None:
			return p
	return None

def messageCB(con, msg):
	msgtype = msg.getType()
	body = msg.getBody()
	fromjid = msg.getFrom()
	cbody = ''
	rcmd = ''
	try:
		comset=int(COMSET[fromjid.getStripped()])
	except:
		comset=1
	if body:
		rcmd = body.split(' ')[0]
		cbody = MACROS.expand(body, [fromjid, fromjid.getStripped(), fromjid.getResource()])
	command = ''
	parameters = ''
	mynick = get_nick(fromjid.getStripped())
	if cbody and string.split(cbody):
		if mynick and cbody[0:len(mynick)+1] == mynick+':':
			nbody=cbody[len(mynick)+1:].strip().split();
			if nbody:
				command = nbody[0]
				parameters = ' '.join(nbody[1:])
		else:
			command = string.lower(string.split(cbody)[0])
			if cbody.count(' '):
				parameters = cbody[(cbody.find(' ') + 1):]
	if not msg.timestamp:
		if msgtype == 'groupchat':
				call_message_handlers('public', [fromjid, fromjid.getStripped(), fromjid.getResource()], body)
				if command in COMMANDS[comset]:
					call_command_handlers(command, 'public', [fromjid, fromjid.getStripped(), fromjid.getResource()], unicode(parameters), rcmd)
		else:
			call_message_handlers('private', [fromjid, fromjid.getStripped(), fromjid.getResource()], body)
			if command in COMMANDS[comset]:
				call_command_handlers(command, 'private', [fromjid, fromjid.getStripped(), fromjid.getResource()], parameters, rcmd)
	for x_node in msg.getTags('x', {}, 'jabber:x:conference'):
		inviter_jid = None
		muc_inviter_tag = msg.getTag('x', {}, 'http://jabber.org/protocol/muc#user')
		if muc_inviter_tag:
			if muc_inviter_tag.getTag('invite'):
				if muc_inviter_tag.getTag('invite').getAttr('from'):
					inviter_jid = xmpp.JID(muc_inviter_tag.getTag('invite').getAttr('from'))
		if not inviter_jid:
			inviter_jid = fromjid
		call_groupchat_invite_handlers([inviter_jid, inviter_jid.getStripped(), inviter_jid.getResource()], x_node.getAttr('jid'), body)

def presenceCB(con, prs):
	call_presence_handlers(prs)
	xtype = prs.getType()
	groupchat = prs.getFrom().getStripped()
	nick = prs.getFrom().getResource()
	
	if groupchat in GROUPCHATS:
		if xtype == 'available' or xtype == None:
			if not GROUPCHATS[groupchat].has_key(nick):
				item = findPresenceItem(prs)
				if item == None:
					jid = groupchat+'/'+nick
				else:
					jid = item['jid']
					if jid != None:
						call_join_handlers(groupchat, nick)
#						time.sleep(0.5)
						if user_level(jid,groupchat) == 0:
							role = item['role']
							aff = item['affiliation']
							if role in roles.keys():
								accr = roles[role]
							else:
								accr = 0
							if aff in affiliations.keys():
								acca = affiliations[aff]
							else:
								acca = 0
							access = int(accr)+int(acca)
							change_access_temp(groupchat, jid, access)

				GROUPCHATS[groupchat][nick] = {'jid': jid, 'idle': time.time()}


		elif xtype == 'unavailable':
			if GROUPCHATS[groupchat].has_key(nick):
				call_leave_handlers(groupchat, nick)
				del GROUPCHATS[groupchat][nick]
		elif xtype == 'error':
			try:
				code = prs.asNode().getTag('error').getAttr('code')
			except:
				code = None
			if code == '409': # name conflict
				join_groupchat(groupchat, nick + '_')
				time.sleep(0.5)

def iqCB(con, iq):
	global JCON
	if iq.getTags('query', {}, xmpp.NS_VERSION):
		result = iq.buildReply('result')
		query = result.getTag('query')
		query.setTagData('name', 'Тао-Альфа-Лямбда-Ипсилон-Сигма-Мю-Альфа-Ню')
		query.setTagData('version', '')
		query.setTagData('os', os.name)
		JCON.send(result)
	else:
		call_iq_handlers(iq)
	

def dcCB():
	print 'DISCONNECTED'
	if AUTO_RESTART:
		print 'WAITING FOR RESTART...'
		time.sleep(5) # sleep for (240) 5 seconds - by als
		print 'RESTARTING'
		os.execl(sys.executable, sys.executable, sys.argv[0])
	else:
		sys.exit(0)

################################################################################

def start():
	global JCON
	JCON = xmpp.Client(server=SERVER, port=PORT, debug=[])

	get_access_levels()
#	load_plugins()
	load_initscript()

	con=JCON.connect()
	if not con:
		print 'COULDN\'T CONNECT\nSleep for 30 seconds'
		time.sleep(30)
		sys.exit(1)
	else:
		print 'Connection Established'
	if con!='tls':
		print "Warning: unable to estabilish secure connection - TLS failed!"
		
	print 'Using',JCON.isConnected()
		
	auth=JCON.auth(USERNAME, PASSWORD, RESOURCE)
	if not auth:
		print 'Auth Error. Incorrect login/password?\nError: ', JCON.lastErr, JCON.lastErrCode
		sys.exit(1)
	else:
		print 'Logged In'
	if auth<>'sasl':
		print 'Warning: unable to perform SASL auth. Old authentication method used!'


	JCON.RegisterHandler('message', messageCB)
	JCON.RegisterHandler('presence', presenceCB)
	JCON.RegisterHandler('iq', iqCB)
	JCON.RegisterDisconnectHandler(dcCB)
	JCON.UnregisterDisconnectHandler(JCON.DisconnectHandler)
	print 'Handlers Registered'
#	JCON.getRoster()
	JCON.sendInitPresence(requestRoster=0)
	print 'Entering Rooms'

	initialize_file(GROUPCHAT_CACHE_FILE, '[]')
	groupchats = eval(read_file(GROUPCHAT_CACHE_FILE))
	MACROS.init()
	for groupchat in groupchats:
		join_groupchat(groupchat)
		time.sleep(0.5)
		
	time.sleep(2)
	load_plugins()
	get_comset()

	print '\nOk, i\'m ready to work :)'

	while 1:
		JCON.Process(10)

if __name__ == "__main__":
	try:
		start()
	except KeyboardInterrupt:
		print '\nINTERUPT (Ctrl+C)'
		for gch in GROUPCHATS.keys():
			msg(gch,u'я получил Сtrl+C из консоли -> выключаюсь')
		sys.exit(1)
	except:
		if AUTO_RESTART:
			if sys.exc_info()[0] is not SystemExit:
				traceback.print_exc()
			try:
				JCON.disconnected()
			except IOError:
				# IOError is raised by default DisconnectHandler
				pass
			try:
				time.sleep(3)
			except KeyboardInterrupt:
				print '\nINTERUPT (Ctrl+C)'
				for gch in GROUPCHATS.keys():
					msg(gch,u'я получил Сtrl+C из консоли -> выключаюсь')
				sys.exit(1)

			print 'RESTARTING'
			os.execl(sys.executable, sys.executable, sys.argv[0])
		else:
			raise

#EOF
