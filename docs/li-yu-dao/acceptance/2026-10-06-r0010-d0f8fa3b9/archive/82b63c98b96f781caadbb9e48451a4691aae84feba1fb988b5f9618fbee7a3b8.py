"""Independent policy oracle; never interprets CK3 or mutates native objects."""
from dataclasses import dataclass,field

class Refused(ValueError): pass

@dataclass(frozen=True)
class Member:
    id:str
    rite:str
    human:bool=False
    eligible:bool=True
    alive:bool=True

@dataclass(frozen=True)
class School:
    id:str
    counties:int=0
    owned:bool=True
    doctrine:str='none'

@dataclass
class World:
    schools:dict[str,School]
    members:dict[str,Member]
    faith:str='lyd_common_faith'
    main:str='kongmen'
    head:object=None
    political_titles:dict[str,str]=field(default_factory=dict)

def snapshot(world):
    return (world.faith,world.main,world.head,tuple(sorted(world.schools.items())),tuple(sorted(world.members.items())))

@dataclass
class Institution:
    world:World
    actor:str
    serial:int
    nonce:int
    deadline:int=365
    phase:str='draft'
    nominees:dict[str,str]=field(default_factory=dict)
    votes:dict[str,bool]=field(default_factory=dict)
    consents:set[str]=field(default_factory=set)
    signatures:set[str]=field(default_factory=set)

    def __post_init__(self):
        if self.world.faith!='lyd_common_faith' or self.world.head is not None: raise Refused('Foreign or headed faith')
        actor=self.world.members[self.actor]
        if not actor.human or actor.rite!=self.world.main: raise Refused('Only a player main-rite initiator')
        if any(not s.owned or s.doctrine!='none' for s in self.world.schools.values()): raise Refused('Foreign/incompatible rite')
        self.frozen=snapshot(self.world)
        self.electors={r:{m.id for m in self.world.members.values() if m.rite==r and m.eligible} for r in self.world.schools}
        self.dormant={r for r,s in self.world.schools.items() if s.counties==0 and not any(m.rite==r for m in self.world.members.values())}
        self.active=set(self.world.schools)-self.dormant
        self.players={m.id for m in self.world.members.values() if m.human}

    def token(self): return (self.actor,self.serial,self.nonce,self.phase)

    def verify(self,token,day=0):
        if self.phase=='closed' or day>=self.deadline or token!=self.token(): raise Refused('Expired/stale callback')
        if snapshot(self.world)!=self.frozen: raise Refused('Changed membership or terms')

    def nominate(self,rite,person,token):
        self.verify(token)
        if self.phase!='draft' or rite not in self.active or person not in self.electors[rite] or rite in self.nominees:
            raise Refused('Invalid/duplicate nominee')
        self.nominees[rite]=person

    def seal(self,token):
        self.verify(token)
        if self.phase!='draft' or set(self.nominees)!=self.active or any(not self.electors[r] for r in self.active): raise Refused('Unorganized active school')
        self.phase='ballot';self.nonce+=1

    def vote(self,person,yes,token):
        self.verify(token)
        if self.phase!='ballot' or person in self.votes or not self.world.members[person].eligible: raise Refused('Invalid/duplicate vote')
        self.votes[person]=yes

    def consent(self,person,yes,token):
        self.verify(token)
        if self.phase!='ballot' or person not in self.players or person in self.consents: raise Refused('Invalid/duplicate human consent')
        if not yes: self.phase='closed';return
        self.consents.add(person)

    def quorum(self,rite):
        electorate=self.electors[rite]
        yes=sum(self.votes.get(m) is True for m in electorate)
        return bool(electorate) and 3*yes>=2*len(electorate)

    def sign(self,rite,person,token):
        self.verify(token)
        if self.phase!='ballot' or self.nominees.get(rite)!=person or not self.quorum(rite) or rite in self.signatures:
            raise Refused('Invalid/early/duplicate signature')
        self.signatures.add(rite)

    def cancel(self,actor,token,day=0):
        # Withdrawal only needs a live human owner and this exact active token;
        # membership/qualification drift stops enactment but not cleanup.
        if self.phase=='closed' or day>=self.deadline or token!=self.token(): raise Refused('Expired/stale cancellation')
        current=self.world.members.get(actor)
        if actor!=self.actor or current is None or not current.human or not current.alive: raise Refused('Foreign/nonliving/nonhuman cancellation')
        self.phase='closed'

    def plan(self,token,native_proof=False):
        self.verify(token)
        if self.phase!='ballot' or self.signatures!=self.active or self.consents!=self.players or not all(self.quorum(r) for r in self.active):
            raise Refused('Incomplete independent mandates/consent/signatures')
        if not native_proof: raise Refused('Native primitive conjunction not admitted')
        # Return a policy-approved plan, NOT a native head or changed World.
        return {'faith':self.world.faith,'rites':tuple(sorted(self.world.schools)),
                'old':'doctrine_no_head','new':'doctrine_temporal_head','holder_candidate':self.actor,
                'political_transfers':(),'government_changes':(),'layer':'ORACLE_ONLY'}
