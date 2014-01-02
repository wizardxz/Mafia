'''
Created on Jan 1, 2014

@author: zhong
'''
import pickle

def main():
    s = pickle.load(open('status/190140TalkStatus')).pre()
    print s.__class__
    if getattr(s, 'actors', None) is not None:
        print "Actors:" + ','.join([p.username for p in s.actors])
    if getattr(s, 'targets', None) is not None:
        print "Targets:" + ','.join([p.username for p in s.targets])
        
    print s.act.func_code.co_argcount


if __name__ == '__main__':
    main()