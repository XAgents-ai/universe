"""Persistent shared world with ordinary material entry actuators.

Local research server only. Journal replay verifies every committed world hash.
No live boundary ops, hidden 'create' commands, or global state in actor views.
An observer can separately obtain global read-only state for auditing; that
observer information must be disclosed if subsequently used for experiments.
"""
from __future__ import annotations
import copy, hashlib, json, os, secrets, threading
from pathlib import Path
from v0_kernel import World, Params

MAX_AGENTS=4
WORLD_SEED=20261017
SITE_X=(3,8,13,18)
SITE_Y=4


def build_shared_world():
    w=World(22,15,WORLD_SEED,Params())
    for x in SITE_X:
        w.add_source((x-2,SITE_Y),'E',2)
        w.place((x-1,SITE_Y),'B')
        w.place((x,SITE_Y),'K','S')
        w.place((x,SITE_Y+1),'C','S')
        w.place((x,SITE_Y+2),'A','S')
        w.bond_path([(x-1,SITE_Y),(x,SITE_Y),(x,SITE_Y+1),(x,SITE_Y+2)])
        w.place((x,SITE_Y+3),'S')
    # Shared unowned matter, with no role-dependent privileged properties.
    for x,y,sp,o in [(5,10,'C','W'),(10,11,'P','E'),(15,11,'G','N'),(19,11,'R','N'),(7,12,'W','E')]:
        w.place((x,y),sp,o)
    w.run({},20)
    return w


def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))


def global_snapshot(w):
    return dict(tick=w.tick,width=w.W,height=w.H,
      particles=[dict(x=x,y=y,species=p.sp,direction=p.o,excitation=p.x,charge=p.q,control=p.c,sensor_state=p.seen,pid=p.pid)
                 for (x,y),p in sorted(w.grid.items())],
      bonds=[[list(a),list(b)] for a,b in sorted(tuple(sorted(b)) for b in w.bonds)],
      sources=[dict(x=pos[0],y=pos[1],direction=d,period=period) for pos,(d,period) in sorted(w.sources.items())],
      heat=[dict(x=x,y=y,quanta=q) for (x,y),q in sorted(w.heat.items()) if q],
      energy=w.energy(),matter=w.matter(),hash=w.state_hash())


class LiveUniverse:
    def __init__(self,root):
        self.lock=threading.RLock()
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.journal=self.root/'events.jsonl';self.w=build_shared_world()
        self.by_token={};self.next_slot=0;self.last_chain='0'*64;self.actions=[];self._poisoned=False
        if self.journal.exists():self._load()

    @staticmethod
    def _token_hash(token):
        # Tokens are 256-bit random bearer credentials; SHA-256 serves only as a stable
        # lookup identifier. Do not log the raw token, even in observer evidence.
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def _commit(self,record,staged_world):
        # Journal-first commit. The live world is swapped only after durable append.
        # Never run model-supplied world transitions directly on self.w.
        if self._poisoned:
            raise RuntimeError('Journal error: restart and verify before another mutation')
        record=dict(record)
        record['prev']=self.last_chain
        record['world_hash']=staged_world.state_hash()
        record['chain']=hashlib.sha256((self.last_chain+canonical({k:v for k,v in record.items() if k!='chain'})).encode()).hexdigest()
        try:
            fd=os.open(self.journal,os.O_WRONLY|os.O_APPEND|os.O_CREAT,0o600)
            with os.fdopen(fd,'a') as f:
                f.write(canonical(record)+'\n');f.flush();os.fsync(f.fileno())
        except OSError:
            # A write/fsync error can leave a valid or torn record on disk. Stop all
            # writes until a restart resolves the disk journal as the authority.
            self._poisoned=True
            raise
        self.last_chain=record['chain']
        return record

    def _complete_lines(self):
        # A trailing unterminated fragment is not a committed event, even if JSON
        # happens to parse. Every earlier newline-terminated event MUST validate.
        raw=self.journal.read_bytes()
        if raw and not raw.endswith(b'\n'):
            end=raw.rfind(b'\n')+1
            with open(self.journal,'r+b') as f:
                f.truncate(end);f.flush();os.fsync(f.fileno())
            raw=raw[:end]
        return raw.decode('utf-8').splitlines()

    def _load(self):
        for lineno,line in enumerate(self._complete_lines(),1):
            r=json.loads(line)
            if r['prev']!=self.last_chain:raise RuntimeError(f'Broken journal chain at line {lineno}')
            expected=hashlib.sha256((self.last_chain+canonical({k:v for k,v in r.items() if k!='chain'})).encode()).hexdigest()
            if r['chain']!=expected:raise RuntimeError(f'Altered journal event at line {lineno}')
            if r['kind']=='join':
                assert r['slot']==self.next_slot
                self.w.grant(r['agent'],tuple(r['site']))
                self.by_token[r['token_hash']]={'agent':r['agent'],'site':r['site'], 'controller':r['controller'],
                    'global_exposure_declared':r['global_exposure_declared'], 'observations':[], 'actions':[], 'calls':0}
                self.next_slot+=1
            elif r['kind']=='step':
                token_hash=r['token_hash'];s=self.by_token[token_hash]
                a=[] if r['op']=='wait' else [(s['agent'],r['op'],tuple(r['pos']))]
                ev=self.w.step(agent_ops=a)
                self._record_actor(s,r['op'],r['pos'],ev)
            else:raise RuntimeError(f'Unknown journal event type at {lineno}')
            if self.w.state_hash()!=r['world_hash']:raise RuntimeError(f'Replay world hash mismatch at line {lineno}')
            self.last_chain=r['chain']

    def join(self,controller='human',global_exposure_declared=False):
        if controller not in ('human','model','program'):raise ValueError('invalid controller')
        with self.lock:
            if self.next_slot>=MAX_AGENTS:raise ValueError('all seeded entry sites occupied')
            slot=self.next_slot
            site=(SITE_X[slot],SITE_Y)
            agent=f'entrant-{slot}'
            token=secrets.token_urlsafe(32)
            token_hash=self._token_hash(token)
            staged=self.w.clone()
            staged.grant(agent,site)
            actor={'agent':agent,'site':list(site),'controller':controller,
                'global_exposure_declared':global_exposure_declared,'observations':[],'actions':[],'calls':0}
            self._commit(dict(kind='join',slot=slot,agent=agent,site=list(site),
                token_hash=token_hash,controller=controller,
                global_exposure_declared=global_exposure_declared),staged)
            self.w=staged
            self.by_token[token_hash]=actor
            self.next_slot+=1
            return dict(token=token,**self.actor_view(token))

    def _get(self,token):
        key=self._token_hash(token)
        if key not in self.by_token:raise KeyError('Unknown participant token')
        return self.by_token[key]

    def actor_view(self,token):
        with self.lock:
            s=self._get(token)
            return dict(role='agent',agent=s['agent'],controller=s['controller'],
                global_exposure_declared=s['global_exposure_declared'],
                width=self.w.W,height=self.w.H,
                authorized=[list(p) for p in self.w.authorized_sites(s['agent'])],
                observed=s['observations'][-4:],actions=s['actions'][-14:],calls=s['calls'],
                notice='No global physical state. Observations are paid snapshots and may be stale.')

    def _record_actor(self,s,kind,pos,event):
        s['calls']+=1
        if kind!='wait':
            result=event['agent'][0]
            s['actions'].append(dict(action=kind,pos=list(pos),result=result[3]))
            if kind=='observe' and result[3]=='ok':
                view=result[4]
                s['observations'].append(dict(at_call=s['calls'],site=list(pos),radius=self.w.P.obs_radius,
                    particles=[dict(x=p[0],y=p[1],species=v[0],direction=v[1],excitation=v[2],charge=v[3]) for p,v in sorted(view.items())]))
                s['observations']=s['observations'][-4:]
        s['actions']=s['actions'][-14:]

    def act(self,token,kind,x=0,y=0):
        if kind not in ('set','observe','claim','wait'):raise ValueError('No boundary ops in the live universe')
        with self.lock:
            s=self._get(token)
            pos=(x,y)
            if kind!='wait' and not self.w.inb(pos):raise ValueError('outside lattice')
            staged=self.w.clone()
            staged_actor=copy.deepcopy(s)
            ev=staged.step(agent_ops=[] if kind=='wait' else [(s['agent'],kind,pos)])
            self._record_actor(staged_actor,kind,pos,ev)
            self._commit(dict(kind='step',token_hash=self._token_hash(token),op=kind,pos=list(pos)),staged)
            self.w=staged
            self.by_token[self._token_hash(token)]=staged_actor
            return self.actor_view(token)

    def observer_view(self):
        with self.lock:return dict(role='observer',frame=global_snapshot(self.w),
            participant_count=self.next_slot,
            note='Read-only global state; declaring it as prior exposure is required for controlled trials.')

    def observer_log(self):
        with self.lock:
            # Inspecting a journal is an observer privilege, never an actor response.
            return dict(role='observer',events=[json.loads(s) for s in self.journal.read_text().splitlines()] if self.journal.exists() else [])
