#!/usr/bin/env python
# -*- coding: utf-8 -*- 
'''
Created on Dec 30, 2013

@author: zhong
'''
import datetime
import pickle

KILLER = 1
POLICE = 2
CIVILIAN = 3

class Message:
    def __init__(self, category, text, actor = None, target = None):
        self.category = category
        self.text = text
        self.actor = actor
        self.target = target
        self.time = datetime.datetime.now()
    
class MessageManager:
    def __init__(self):
        self.data = []
        
    def add(self, category, text, actor = None, target = None):
        msg = Message(category, text, actor, target)
        if len(self.data) > 0 and self.data[-1].category == 'temp':
            del self.data[-1]
        self.data.append(msg)
        
class Player:
    def __init__(self, username, identity):
        self.username = username
        self.identity = identity
        self.nickname = username
        self.live = True
        
        self.message = MessageManager()
        
class Context:
    def __init__(self, players):
        self.players = players
        self.dying_man_can_talk_before = (sum([1 for p in players if p.identity == KILLER]) - 1) / 2
        self.hanging_man_can_talk_before = (sum([1 for p in players if p.identity == KILLER]) - 2) / 2
        self.civilian_all_die_winner = KILLER
        self.clear()

    def clear(self, gameround = None):
        self.gameround = gameround
        self.dying = None
        self.suspect = None
        self.vulnerable = []
        
    def get_player(self, username):
        for p in self.players:
            if p.username == username:
                return p

class Status:
    def save(self):
        filename = "status/%s%s.pickle" % (datetime.datetime.now().strftime("%H%M%S"), str(self.__class__).split('.')[-1])
        print filename
        out = open(filename, 'w')
        pickle.dump(self, out)
        out.close()
        

class ActStatus(Status):
    def __init__(self, actors, targets):
        self.actors = actors
        self.targets = targets
        self.completed = dict([(p, False) for p in actors])
        
    @staticmethod
    def controlled_execution(func):
        def inner(*args, **kwargs):
            assert 'actor' in kwargs
            actor = kwargs['actor']
            target = kwargs.get('target', None)
            self = args[0]
            if actor in self.actors:
                if target is None or target in self.targets:
                    self.completed[actor] = (func.__name__ == 'act')
                    func(self, **kwargs)
                    
            if all(self.completed.values()):
                return self.post()
            else:
                return self
        return inner
    
class GameStart(Status):
    def __init__(self, context):
        self.context = context
        self.save()
        
    def pre(self):
        for p in self.context.players:
            p.message.add("sys", u"你拿到的身份牌是%s" % (u"杀手" if p.identity == KILLER else u"警察" if p.identity == POLICE else u"平民"))
        return RoundStart(self.context).pre()
            
class RoundStart(Status):
    def __init__(self, context):
        self.context = context
        self.save()
    
    def pre(self):
        self.context.clear(0 if self.context.gameround is None else \
                           self.context.gameround + 1)
        for p in self.context.players:
            p.message.add("temp", u"天黑请闭眼")

        return KillStatus(self.context).pre()

class KillStatus(ActStatus):
    def __init__(self, context):
        self.context = context
        ActStatus.__init__(self, 
            actors = [p for p in context.players if p.live and p.identity == KILLER],
            targets = [p for p in context.players if p.live], 
        )
        self.mapping = dict([(p, None) for p in self.actors])
        self.save()

    def pre(self):
        for p in self.context.players:
            if p.live and p.identity == KILLER:
                ally = [p1.nickname for p1 in self.context.players if p1.identity == KILLER and p != p1]
                if len(ally) == 0:
                    ally_text = u"你没有同伴"
                else:
                    ally_text = u'你的同伴是' + (', '.join(ally))
                p.message.add("temp", u"轮到你了，%s" % ally_text)
            else:
                p.message.add("temp", u"等待杀手杀人")
        return self
        
    
    def post(self):
        if len(set(self.mapping.values())) == 1:
            self.context.dying = self.mapping.values()[0]
            #possible game over
            winner = get_winner(self.context)
            if winner is not None:
                for p in self.context.players:
                    p.message.add("kill_result", u"%s在昨晚被杀手杀死了" % self.context.dying.nickname,
                                  target = self.context.dying)
                return GameOver(self.context, winner).pre()
            
            return InvestigateStatus(self.context).pre()
        else:
            return self

    @ActStatus.controlled_execution    
    def act(self, actor, target):
        self.mapping[actor] = target
        for p in self.actors:
            p.message.add("kill", u"%s的目标是%s" % (actor.nickname, target.nickname), actor, target)
        
    @ActStatus.controlled_execution    
    def cancel(self, actor):
        self.mapping[actor] = None
        for p in self.actors:
            p.message.add("kill", u"%s取消了行动" % (actor.nickname), actor)
        
class InvestigateStatus(ActStatus):
    def __init__(self, context):
        self.context = context
        ActStatus.__init__(self, 
            actors = [p for p in context.players if p.live and p.identity == POLICE],
            targets = [p for p in context.players if p.live and p.identity != POLICE], 
        )
        self.mapping = dict([(p, None) for p in self.actors])
        self.save()

    def pre(self):
        for p in self.context.players:
            if p.live and p.identity == POLICE:
                ally = [p1.nickname for p1 in self.context.players if p1.identity == POLICE and p != p1]
                if len(ally) == 0:
                    ally_text = u"你没有同伴"
                else:
                    ally_text = u'你的同伴是' + (', '.join(ally))
                p.message.add("temp", u"轮到你了，%s" % ally_text)
            else:
                p.message.add("temp", u"等待警察验人")
        return self
    
    def post(self):
        if len(set(self.mapping.values())) == 1:
            self.context.suspect = self.mapping.values()[0]
            message_text = u"法官告诉你们，你们的目标%s%s是杀手" % \
            (self.context.suspect.nickname, '' if self.context.suspect.identity == KILLER else u'不')
            for p in self.actors:
                p.message.add("investigate_result", message_text, 
                              target = self.context.suspect)
            self.context.dying.live = False # kill
            for p in self.context.players:
                p.message.add("kill_result", u"%s在昨晚被杀手杀死了" % self.context.dying.nickname,
                              target = self.context.dying)
            
            return TalkStatus(self.context, self.context.dying,
                              targets = [p for p in self.context.players if p.live],
                              terminate = self.context.dying,
                              incremental = 1).pre()

        else:
            return self
        
    @ActStatus.controlled_execution    
    def act(self, actor, target):
        self.mapping[actor] = target
        for p in self.actors:
            p.message.add("investigate", u"%s的目标是%s" % (actor.nickname, target.nickname), actor, target)
        
    @ActStatus.controlled_execution    
    def cancel(self, actor):
        self.mapping[actor] = None
        for p in self.actors:
            p.message.add("investigate", u"%s取消了行动" % (actor.nickname), actor)

class TalkStatus(ActStatus):
    def __init__(self, context, talker, targets, terminate, incremental, pk = False):
        self.context = context
        self.talker = talker
        self.terminate = terminate
        self.incremental = incremental
        self.pk = pk
        ActStatus.__init__(self, 
            actors = [talker], 
            targets = targets,
        )
        self.save()
        
    def get_next_talker(self):
        i = (self.context.players.index(self.talker) + self.incremental) % len(self.context.players)
        next_talker = self.context.players[i]
        return next_talker
    
    def pre(self):
        if (self.talker.live or (self.talker == self.context.dying \
                                 and self.context.gameround <= self.context.dying_man_can_talk_before)) \
                                 and (not self.pk or self.talker in self.context.vulnerable):
            for p in self.context.players:
                if p != self.talker:
                    p.message.add('temp', u"等待%s的发言" % self.talker.nickname)
                else:
                    p.message.add('temp', u"目前被点的有%s，请发言" % ','.join([p.nickname for p in self.context.vulnerable]))
            return self
        else:
            return self.post()

    @ActStatus.controlled_execution    
    def act(self, actor, words, target = None):
        if target is not None and not target in self.context.vulnerable:
            self.context.vulnerable.append(target)
        for p in self.context.players:
            p.message.add('talk', u"%s说：%s" % (actor.nickname, words), actor, target)
            
    def post(self):
        next_talker = self.get_next_talker()
        if next_talker == self.terminate:
            return VoteStatus(self.context).pre()        
        else:
            return TalkStatus(self.context, next_talker, self.targets,
                              self.terminate, self.incremental, 
                              self.pk).pre()
            
class VoteStatus(ActStatus):  
    def __init__(self, context):
        self.context = context
        if len(context.vulnerable) == 0:
            context.vulnerable = [p for p in context.players if p.live]
        ActStatus.__init__(self, 
            actors = [p for p in context.players if p.live], 
            targets = context.vulnerable,
        )
        self.mapping = dict([(p, None) for p in self.actors])
        self.save()
        
    def pre(self):
        if len(self.targets) == 1:
            for p in self.actors:
                p.message.add('sys', u"目前只有%s被点" % self.targets[0].nickname)
            return self.post()
        
        for p in self.actors:
            p.message.add('temp', u"请投票")
        return self
        
    
    def post(self):
        if len(self.targets) == 1:
            pk = self.targets[:]
        else:
            tickets = dict([(p, 0) for p in self.actors])
            for target in self.mapping.values():
                if target is not None:
                    tickets[target] += 1
             
            most_ticket = max(tickets.values())
            tickets_list = [(target, ticket) for target, ticket in tickets.iteritems()]
            tickets_list.sort(key = lambda x:x[1], reverse = True)
            result_message = ','.join([u"%s有%d票(%s)"%(target.nickname, ticket, ','.join([k.nickname for k, v in self.mapping.iteritems() if v == target])) 
                                       for target, ticket in tickets_list if ticket > 0])
            
            pk = [p for p in self.context.vulnerable if tickets[p] == most_ticket]
            for p in self.context.players:
                p.message.add('vote_result', result_message)
        if len(pk) == 1:
            pk[0].live = False
                
            for p in self.context.players:
                p.message.add('execute', u"处决%s" % pk[0].nickname, target = pk[0])

            #possible game over
            winner = get_winner(self.context)
            if winner is not None:
                return GameOver(self.context, winner).pre()

            if self.context.gameround <= self.context.hanging_man_can_talk_before:
                return LastWordsStatus(self.context, pk[0]).pre()
            else:
                return RoundStart(self.context).pre()
        else:
            for p in self.context.players:
                p.message.add('pk', ', '.join([p.nickname for p in pk]) + u'一起走上pk台')
            self.context.vulnerable = pk
            
            return TalkStatus(self.context, self.context.dying,
                              targets = None,
                              terminate = self.context.dying,
                              incremental = 1,
                              pk = True
                              ).pre()

    @ActStatus.controlled_execution    
    def act(self, actor, target):
        self.mapping[actor] = target
        if target is not None:
            actor.message.add('vote', u"你投给了%s" % target.nickname, actor, target)
        else:
            actor.message.add('vote', u"你弃权", actor)
        
class LastWordsStatus(ActStatus):
    def __init__(self, context, talker):
        self.context = context
        self.talker = talker
        ActStatus.__init__(self, 
            actors = [talker],
            targets = None,
        )
        self.save()
        
    def pre(self):
        for p in self.context.players:
            if p != self.talker:
                p.message.add('temp', u"等待%s说遗言" % self.talker.nickname)
        self.talker.message.add('temp', u"请说遗言")
        return self

    @ActStatus.controlled_execution    
    def act(self, actor, words):
        for p in self.context.players:
            p.message.add('lastwords', u"%s的遗言是：%s." % (actor.nickname, words), actor)
            
    def post(self):
        return RoundStart(self.context).pre()
    
def get_winner(context):
    if not any([p.live and context.dying != p for p in context.players if p.identity == KILLER]):
        return POLICE
    elif not any([p.live and context.dying != p for p in context.players if p.identity == POLICE]):
        return KILLER
    elif not any([p.live and context.dying != p for p in context.players if p.identity == CIVILIAN]):
        return context.civilian_all_die_winner
    return None

class GameOver(Status):
    def __init__(self, context, winner):
        self.context = context
        self.winner = winner
        self.save()
        
    def pre(self):
        for p in self.context.players:
            p.message.add('final', u"真相大白：%s是杀手；%s是警察。%s取得了胜利！" % (
                ','.join([p.nickname for p in self.context.players if p.identity == KILLER]),
                ','.join([p.nickname for p in self.context.players if p.identity == POLICE]),
                u'杀手' if self.winner == KILLER else u'警察'))
        return self
    
        