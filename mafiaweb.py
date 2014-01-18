#!/usr/bin/env python
# -*- coding: utf-8 -*- 
'''
Created on Dec 31, 2013

@author: zhong
'''
import random
import pickle
import os
import json

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
    '/process/(\w+)', 'Process',
    '/message/(\w+)', 'Message',
    '/update', 'Update',
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
        context.civilian_all_die_winner = models.POLICE if web.input()['civilian_all_die_winner'] == 'police' else models.KILLER
        
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

class Update:
    def POST(self):
        global s
        web.header('Content-Type', 'application/json')

        if s is None:
            messages = None
            new_message_count = 0
            players = None
            form = get_form(None, None)
            new_sid = 0
        else:
            username = web.input()['username']
            message_count = int(web.input()['message_count'])
            sid = int(web.input()['sid'])
            
            player = s.context.get_player(username)
            if player is None:
                messages = None
                new_message_count = 0
                players = None
                form = get_form(s, None)
                new_sid = 0
            else:
                messages = get_messages(s, player, message_count)
                new_message_count = len(player.message.data)
            
                new_sid = id(s)
                if new_sid == sid:
                    players = form = None
                else:
                    players = get_players(s, player)
                    form = get_form(s, player)
            
        return json.dumps(
            ((messages, new_message_count), 
             players, form, new_sid)
        )

formrender = web.template.render('templates')

def get_messages(s, player, message_count):
    if message_count < len(player.message.data):
        return str(formrender.messages(s, player, message_count))
    else:
        return None
    
def get_players(s, player):
    return str(formrender.players(s, player))
    
def get_form(s, player):

    if s is None:
        return '<h1>游戏尚未开始</h1> <a href="/admin">Admin</a> &nbsp; <a href="/restore">Restore</a>'
    elif player is None:
        return '<h1>该用户不在游戏中</h1> <a href="/admin">Admin</a> &nbsp; <a href="/restore">Restore</a>'
    elif isinstance(s, models.KillStatus):
        if player in s.actors:
            return str(formrender.kill(s))
        else:
            return str(formrender.wait(s, secret = True))
    elif isinstance(s, models.InvestigateStatus):
        if player in s.actors:
            return str(formrender.investigate(s))
        else:
            return str(formrender.wait(s, secret = True))
    elif isinstance(s, models.TalkStatus):
        if player in s.actors:
            return str(formrender.talk(s))
        else:
            return str(formrender.wait(s, secret = False))
    elif isinstance(s, models.VoteStatus):
        if player in s.actors:
            return str(formrender.vote(s))
        else:
            return str(formrender.wait(s, secret = False))
    elif isinstance(s, models.LastWordsStatus):
        if player in s.actors:
            return str(formrender.lastwords(s))
        else:
            return str(formrender.wait(s, secret = False))
    elif isinstance(s, models.GameOver):
        return '<h1>游戏结束</h1> <a href="/admin">Admin</a> &nbsp; <a href="/restore">Restore</a>'
    else:
        return None
    
class Process:
    def POST(self, username):
        global s
        actor = s.context.get_player(username)
        if str(id(s)) == web.input()['sid']:
            kwargs = {'actor':actor}
            if 'target' in web.input():
                target_text = web.input()['target']
                if target_text == 'None':
                    kwargs['target'] = None
                else:
                    kwargs['target'] = s.context.get_player(target_text[5:]) # perfix is user:
                    
            if 'words' in web.input():
                kwargs['words'] = web.input()['words']
                    
            if web.input()['type'] == 'submit':
                s = s.act(**kwargs)
            elif web.input()['type'] == 'cancel':
                s = s.cancel(actor = actor)
        else:
            actor.message.add("warn", u"您刚刚的操作已过期，请重试")
        return json.dumps(""); # Create a success result
        
                
class Game:
    def GET(self, username):
        global s
        return render.game(username, s)

s = None

if __name__ == '__main__':
    app = web.application(urls, globals())
    app.run()