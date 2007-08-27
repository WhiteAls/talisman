#===istalismanplugin===
# -*- coding: utf-8 -*-
####### It is translated and modified by Als #######


def handler_access_login(type, source, parameters):
	if type == 'public':
		reply(type, source, u'тормоз, это надо было делать в привате')
	elif type == 'private':
		jid = get_true_jid(source)
		if parameters.strip() == ADMIN_PASSWORD:
			change_access_temp(source[1], jid, 100)
			reply(type, source, u'угу, точняк')
		else:
			reply(type, source, u'пшёл вон, я хз кто ты >)')

def handler_access_logout(type, source, parameters):
	jid = get_true_jid(source)
	change_access_temp(source[1], jid, 10)
	reply(type, source, u'бб')

def handler_access_view_access(type, source, parameters):
	if not parameters.strip():
		reply(type, source, str(user_level(source[1]+'/'+source[2], source[1])))
	else:
		reply(type, source, str(user_level(source[1]+'/'+parameters,source[1])))

def handler_access_set_access(type, source, parameters):
	splitdata = string.split(parameters)
	nicks=GROUPCHATS[source[1]].keys()
	if not splitdata[0] in nicks:
		reply(type, source, u'а он тут? :-O')
		return
	tjidto=get_true_jid(source[1]+'/'+splitdata[0])
	tjidsource=get_true_jid(source)
	groupchat=source[1]
	jidacc=user_level(source, groupchat)
	if tjidsource in ADMINS:
		pass
	elif int(splitdata[1]) > int(jidacc):
		reply(type, source, u'ага, щаззз')
		return
	if len(splitdata) == 2:
		change_access_temp(source[1], tjidto, splitdata[1])
		reply(type, source, u'дал временно')
	elif len(splitdata) == 3:
		change_access_perm(source[1], tjidto, splitdata[1])
		reply(type, source, u'дал навсегда')
	else:
		reply(type, source, u'чё-то ты не правильно пишешь...')
		
		
def handler_access_set_access_glob(type, source, parameters):
	splitdata = string.split(parameters)
	tjidto=get_true_jid(source[1]+'/'+splitdata[0])
	change_access_perm_glob(tjidto, splitdata[1])
	reply(type, source, u'дал')

def handler_access_unset_access_glob(type, source, parameters):
	splitdata = string.split(parameters)
	tjidto=get_true_jid(source[1]+'/'+splitdata[0])
	change_access_perm_glob(tjidto)
	reply(type, source, u'снял')


register_command_handler(handler_access_login, {1: 'логин', 2: 'login', 3: '!login'}, ['доступ','админ','все'], 0, 'Залогиниться как админ.', 'login <пароль>', ['login мой_пароль'])
register_command_handler(handler_access_login, {1: 'логаут', 2: 'logout', 3: '!logout'}, ['доступ','админ','все'], 0, 'Разлогиниться.', 'logout', ['logout'])
register_command_handler(handler_access_view_access, {1: 'доступ', 2: 'acc', 3: '!acc'}, ['доступ','админ','все'], 0, 'Показывает уровень доступа определённого ника.', 'acc [ник]', ['acc', 'acc guy'])
register_command_handler(handler_access_set_access, {1: 'дать_доступ', 2: 'giveacc', 3: '!giveacc'}, ['доступ','админ','все'], 15, 'Устанавливает уровень доступа для определённого ника на определённый уровень. Если указываеться третий параметр, то изменение происходит навсегда, иначе установленный уровень будет действовать до выхода бота из конфы.', 'giveacc <ник> <уровень> [навсегда]', ['giveacc guy 100', 'giveacc guy 100 что-нить там'])
register_command_handler(handler_access_set_access_glob, {1: 'globacc', 2: 'globacc', 3: '!globacc'}, ['доступ','суперадмин','все'], 100, 'Устанавливает уровень доступа для определённого ника на определённый уровень ГЛОБАЛЬНО.', 'globacc <ник> <уровень>', ['globacc gay 100'])
register_command_handler(handler_access_unset_access_glob, {1: 'unglobacc', 2: 'unglobacc', 3: '!unglobacc'}, ['доступ','суперадмин','все'], 100, 'Снимает глобальный уровень доступа с ЖИДА.', 'unglobacc <жид> ', ['globacc guy'])
