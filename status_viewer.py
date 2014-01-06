'''
Created on Jan 1, 2014

@author: zhong
'''
import pickle
import inspect

def main():
    s = pickle.load(open('status/222714KillStatus.pickle')).pre()
    print s.__class__
    if getattr(s, 'actors', None) is not None:
        print "Actors:" + ','.join([p.username for p in s.actors])
    if getattr(s, 'targets', None) is not None:
        print "Targets:" + ','.join([p.username for p in s.targets])
        
    print inspect.getargspec(s.act)
    


if __name__ == '__main__':
    main()