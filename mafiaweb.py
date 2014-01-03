#!/usr/bin/env python
# -*- coding: utf-8 -*- 
'''
Created on Dec 31, 2013

@author: zhong
'''
import random
import pickle
import traceback
import os

""" Basic blog using webpy 0.3 """
import web
import models

### Url mappings

urls = (
    '/favicon.ico','favicon',
    '/', 'Login',
    '/admin', 'Admin',
    '/restore', 'Restore',
    '/game/(\w+)', 'Game',
    '/message/(\w+)', 'Message'
)

class favicon: 
    def GET(self): 
        f = open("static/favicon.ico", 'rb') 
        return f.read() 

### Templates
render = web.template.render('templates', base='base', globals = {'models':models})

class Login:
    def GET(self):
        form = web.form.Form(
            web.form.Textbox('username', description = u"用户名"),
            web.form.Textbox('nickname', description = u"昵称"),
            web.form.Button('Login', description = u"登录"),
        )
        return render.login(form)
    
    def POST(self):
        global s
        if s is None:
            return "Game has not started yet."
        else:
            for p in s.context.players:
                if p.username == web.input()['username'].strip():
                    nickname = web.input()['nickname'].strip()
                    if nickname != '':
                        p.nickname = nickname
                    raise web.seeother('/game/%s' % web.input()['username'])
                    break
            else:
                return "User not found."

class Admin:
    def GET(self):
        form = web.form.Form(
            web.form.Textbox('players', description = u"全部玩家用户名，逗号分隔"),
            web.form.Textbox('killer_num', description = u"杀手人数"),
            web.form.Textbox('police_num', description = u"警察人数"),
            web.form.Textbox('civilian_num', description = u"平民人数"),
            web.form.Radio('civilian_all_die_winner', ['killer', 'police'], description = u"平民全部牺牲情况下的获胜方"),
            web.form.Button('submit', description = u"创建游戏"),
        )
        return render.admin(form)
    
    def POST(self):
        global s
        usernames = [n.strip() for n in web.input()['players'].split(',')]
        killer_num = int(web.input()['killer_num'])
        police_num = int(web.input()['police_num'])
        civilian_num = int(web.input()['civilian_num'])
        assert len(usernames) == killer_num + police_num + civilian_num
        identities = [models.KILLER] * killer_num + [models.POLICE] * police_num + [models.CIVILIAN] * civilian_num
        random.shuffle(identities)
        
        context = models.Context([models.Player(username, identity) for username, identity in zip(usernames, identities)])
        context.civilian_all_die_winner = models.POLICE if web.input()['civilian_all_die_winner'] == 'police' else 'killer'
        
        s = models.GameStart(context).pre()
            
        raise web.seeother('/')
    
class Restore:
    def GET(self):
        
        form = web.form.Form(
            web.form.Dropdown('status', args = [filename for filename in os.listdir('status') if 'pickle' in filename]),
            web.form.Button('Restore', description = u"恢复状态"),
        )
        return render.restore(form)
    
    def POST(self):
        global s
        filename = web.input()['status']
        s = pickle.load(open('status/%s'%filename)).pre()   
        raise web.seeother('/')     

class Message:
    def GET(self, username):
        global s
        return render.message(username, s)

class Game:
    def GET(self, username):
        global s
        return render.game(username, s)
    
    def POST(self, username):
        global s
        if str(id(s)) == web.input()['sid']:
            kwargs = {'actor' : s.context.get_player(username)}
            if 'target' in web.input():
                target_text = web.input()['target']
                if target_text == 'None':
                    target = None
                else:
                    target = s.context.get_player(target_text)
            if 'words' in web.input():
                kwargs['words'] = web.input()['words']
                    
            if getattr(s, 'cancel', None) is not None and 'target' in web.input() and target is None:
                s = s.cancel(**kwargs)
            else:
                if 'target' in locals():
                    kwargs['target'] = target
                try:
                    s = s.act(**kwargs)
                except:
                    traceback.print_exc()
                    pass
                #TODO
        else:
            actor = s.context.get_player(username)
            actor.message.add("warn", u"您刚刚的操作已过期，请重试")
        raise web.seeother('/game/%s' % username)

s = None

if __name__ == '__main__':
    app = web.application(urls, globals())
    app.run()