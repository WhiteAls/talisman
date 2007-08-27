#===istalismanplugin===
# -*- coding: utf-8 -*-
####### by Als #######

idle_pending=[]
def handler_idle(type, source, parameters):
	idle_iq = xmpp.Iq('get')
	id='idle'+str(random.randrange(1000, 9999))
	globals()['idle_pending'].append(id)
	idle_iq.setID(id)
	idle_iq.addChild('query', {}, [], 'jabber:iq:last');
	if parameters:
		param = parameters.strip()
		idle_iq.setTo(param)
	else:
		param=SERVER
		idle_iq.setTo(param)
	JCON.SendAndCallForResponse(idle_iq, handler_idle_answ, {'type': type, 'source': source, 'param': param})
	
		
def handler_idle_answ(coze, res, type, source, param):
	id=res.getID()
	if id in globals()['idle_pending']:
		globals()['idle_pending'].remove(id)
	else:
		print 'ooops!'
		return
	rep =''
	if res:
		if res.getType()=='error':
			reply(type,source,u'там или нету жабер сервера или он упал или он запрещает смотреть эту инфу')
			return
		elif res.getType() == 'result':
			sec = ''
			props = res.getPayload()
			if not props:
				reply(type,source,u'там или упал жабер сервер или его вообще нету')
				return 
			for p in props:
				sec=p.getAttrs()['seconds']
				if not sec == '0':
					seconds = int(sec) % 60
					minutes = int(sec) / 60
					hours = minutes / 60
					minutes %= 60
					days = hours / 24
					mounth = days /30
					hours %= 24
					if mounth:
						rep += str(mounth) + u' мес '
					else:
						if days: rep += str(days) + u' дн '
					if hours: rep += str(hours) + u' час '
					if minutes: rep += str(minutes) + u' мин '
					rep += str(seconds) + u' сек'
					rep = param+u' работает уже '+rep
	else:
		rep = u'глюк'
	reply(type, source, rep)
	
def handler_userinfo_message(type, source, body):
	if type == 'public':
		if GROUPCHATS.has_key(source[1]) and GROUPCHATS[source[1]].has_key(source[2]):
			GROUPCHATS[source[1]][source[2]]['idle'] = time.time()	
	
def handler_userinfo_idle(type, source, parameters):
	if GROUPCHATS.has_key(source[1]):
		if not parameters:
			reply(type,source,u'и что я должен сказать? ;)')
			return
		nick = parameters.strip()
		if nick==source[2]:
			reply(type,source,u'и что я должен сказать? ;)')
			return
		if GROUPCHATS[source[1]].has_key(nick):
			groupchat = source[1]
			idletime = int(time.time() - GROUPCHATS[groupchat][nick]['idle'])
			rep = ''
			seconds = int(idletime) % 60
			minutes = int(idletime) / 60
			hours = minutes / 60
			minutes %= 60
			days = hours / 24
			mounth = days /30
			hours %= 24
			if mounth:
				rep += str(mounth) + u' мес '
			else:
				if days: rep += str(days) + u' дн '
			if hours: rep += str(hours) + u' час '
			if minutes: rep += str(minutes) + u' мин '
			rep += str(seconds) + u' сек'
			reply(type, source, nick+u' заснул '+rep+u' назад')
		else:
			reply(type,source,u'а он тут? :-O')



register_message_handler(handler_userinfo_message)
register_command_handler(handler_idle, {1: 'аптайм', 2: 'uptm', 3: '!uptime'}, ['инфо','мук','все'], 10, 'Показывает аптайм определённого сервера.', 'uptm <сервер>', ['uptm jabber.aq'])
register_command_handler(handler_userinfo_idle, {1: 'жив', 2: 'sleep', 3: '!idle'}, ['инфо','мук','все'], 10, 'Показывает сколько времени неактивен юзер.', 'sleep <ник>', ['sleep guy'])
