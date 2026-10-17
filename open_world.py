"""Persistent shared world with ordinary material entry actuators and a WORLD-OWNED CLOCK (W1).

Time belongs to the universe, not to whoever makes the most API requests:
 * An HTTP request never advances physics. A participant SUBMITS at most one action for the
   next tick (set / observe / claim / wait, where 'wait' is the explicit no-op).
 * The world advances on its own clock - a fixed scheduler interval - including when participants
   are silent. A missing action is a no-op. Nothing a participant does can make a tick come sooner:
   there is no all-submitted barrier and no tick endpoint (review finding B).
 * The accepted batch is ordered by a seeded permutation keyed by (world seed, tick): a function of
   the world, never of network arrival, replayable, and without the parity structure that a rotation
   rule gives sparse contests (review finding C). Each tick is executed as ONE kernel tick and
   journaled as ONE replayable transition with its outcomes, energy ledger and resulting state hash.
   Physical conflicts inside the tick are resolved by the kernel's seeded rule.
 * Journal-first commit: the published world is swapped only after the record is durable.

Local research server only. No live boundary ops, no privileged tick endpoint, no global state in
actor views. An observer can obtain global read-only state for auditing; that exposure must be
disclosed if subsequently used for experiments.
"""
from __future__ import annotations
import copy, fcntl, hashlib, json, os, random, secrets, threading, time
from pathlib import Path
from v0_kernel import World, Params

MAX_AGENTS=4
WORLD_SEED=20261017
SITE_X=(3,8,13,18)
SITE_Y=4
JOURNAL_FORMAT='w1-tick-batch'
ACTIONS=('set','observe','claim','wait')      # 'wait' is the explicit no-op; boundary ops never
DUPLICATE_POLICY='first-submission-binding'   # a second submission for the same tick is refused


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


class ClockPolicy:
    """The world's own clock: strictly periodic.

    tick_seconds <= 0 : manual mode - advance() is called by the owning process (tests, harnesses).
    tick_seconds  > 0 : a scheduler thread advances every tick_seconds, whether or not anyone acted.
    There is deliberately no early-tick barrier: participant behaviour cannot shorten a tick.
    """
    def __init__(self,tick_seconds=1.0):
        self.tick_seconds=float(tick_seconds)

    def describe(self):
        return dict(journal_format=JOURNAL_FORMAT,tick_seconds=self.tick_seconds,
                    early_tick=False,duplicate_policy=DUPLICATE_POLICY,
                    order='seeded permutation of the sorted batch keyed by (world seed, tick); physical conflicts by kernel seed',
                    privileged_tick_endpoint=False)


def canonical_batch(pending,tick,seed=WORLD_SEED):
    """Arrival-independent order: a seeded permutation of the sorted batch keyed by (seed, tick).
    Deterministic and replayable; no participant has standing priority, and sparse contests (e.g. only
    on even ticks) see no parity structure, because the permutation is pseudo-random per tick."""
    items=sorted(pending.items())
    if len(items)<2:return items
    key=int.from_bytes(hashlib.sha256(f'{seed}:{tick}'.encode()).digest()[:8],'big')
    random.Random(key).shuffle(items)
    return items


class LiveUniverse:
    def __init__(self,root,clock=None,world_factory=build_shared_world,single_writer=False):
        self.lock=threading.RLock()
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self._lockfile=None
        if single_writer:
            # Deployment guard: one authoritative writer per state directory. A second process (or a
            # second worker) sharing the journal would have its own clock, memory and lock.
            self._lockfile=open(self.root/'.writer.lock','a+')
            try:fcntl.flock(self._lockfile.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            except OSError:
                self._lockfile.close();self._lockfile=None
                raise RuntimeError(f'another writer holds {self.root}: refusing to start a second authority')
        self.journal=self.root/'events.jsonl';self.w=world_factory()
        self.by_token={};self.next_slot=0;self.last_chain='0'*64;self._poisoned=False
        self.pending={}                       # agent -> (kind,pos), at most one per tick
        self.clock=clock or ClockPolicy()
        self.last_tick_at=None
        if self.journal.exists():self._load()
        self._stop=threading.Event();self._thread=None
        if self.clock.tick_seconds>0:
            self._thread=threading.Thread(target=self._run_clock,daemon=True,name='universe-clock');self._thread.start()

    # ---------------- clock ----------------
    def _run_clock(self):
        # Fixed cadence anchored to the start time, so neither request volume nor tick duration drifts it.
        period=self.clock.tick_seconds;due=time.monotonic()+period
        while not self._stop.is_set():
            remaining=due-time.monotonic()
            if remaining>0:
                self._stop.wait(min(remaining,0.25));continue
            try:self.advance()
            except Exception:pass                   # poisoned journal: wait for restart, keep the thread alive
            due+=period
            if time.monotonic()-due>period:due=time.monotonic()+period   # fell far behind: re-anchor, never burst

    def close(self):
        self._stop.set()
        if self._thread:self._thread.join(timeout=2)
        if self._lockfile:
            try:fcntl.flock(self._lockfile.fileno(),fcntl.LOCK_UN)
            except OSError:pass
            self._lockfile.close();self._lockfile=None

    def clock_view(self):
        with self.lock:
            return dict(**self.clock.describe(),tick=self.w.tick,participants=self.next_slot,
                        pending_submissions=len(self.pending),last_tick_at=self.last_tick_at,
                        journal_poisoned=self._poisoned)

    # ---------------- identity / journal ----------------
    @staticmethod
    def _token_hash(token):
        # Tokens are 256-bit random bearer credentials; SHA-256 serves only as a stable
        # lookup identifier. Do not log the raw token, even in observer evidence.
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def _commit(self,record,staged_world):
        # Journal-first commit. The live world is swapped only after durable append.
        # Never run participant transitions directly on self.w.
        if self._poisoned:
            raise RuntimeError('Journal error: restart and verify before another mutation')
        record=dict(record)
        record['format']=JOURNAL_FORMAT
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
            if r.get('format')!=JOURNAL_FORMAT:
                raise RuntimeError(f'Journal line {lineno} has format {r.get("format")!r}; this build replays only {JOURNAL_FORMAT!r} '
                                   '(pre-W1 per-request journals are not replayable here)')
            if r['kind']=='join':
                assert r['slot']==self.next_slot
                self.w.grant(r['agent'],tuple(r['site']))
                self.by_token[r['token_hash']]=self._new_actor(r['agent'],r['site'],r['controller'],r['global_exposure_declared'])
                self.next_slot+=1
            elif r['kind']=='tick':
                if r['tick']!=self.w.tick:raise RuntimeError(f'Journal tick {r["tick"]} does not match replay tick {self.w.tick} at line {lineno}')
                batch=[(b['agent'],(b['op'],tuple(b['pos']))) for b in r['batch']]
                ev=self.w.step(agent_ops=[(a,k,p) for a,(k,p) in batch if k!='wait'])
                outcomes=self._apply_outcomes(self.by_token,batch,ev)
                if outcomes!=r['outcomes']:raise RuntimeError(f'Replay outcomes differ from journal at line {lineno}')
                if ev['energy']!=r['energy']:raise RuntimeError(f'Replay energy ledger differs from journal at line {lineno}')
            else:raise RuntimeError(f'Unknown journal event type at {lineno}')
            if self.w.state_hash()!=r['world_hash']:raise RuntimeError(f'Replay world hash mismatch at line {lineno}')
            self.last_chain=r['chain']

    # ---------------- participants ----------------
    @staticmethod
    def _new_actor(agent,site,controller,global_exposure_declared):
        return {'agent':agent,'site':list(site),'controller':controller,
                'global_exposure_declared':global_exposure_declared,
                'observations':[],'actions':[],'submissions':[],'calls':0}

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
            actor=self._new_actor(agent,site,controller,global_exposure_declared)
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
            pend=self.pending.get(s['agent'])
            return dict(role='agent',agent=s['agent'],controller=s['controller'],
                global_exposure_declared=s['global_exposure_declared'],
                width=self.w.W,height=self.w.H,
                authorized=[list(p) for p in self.w.authorized_sites(s['agent'])],
                observed=s['observations'][-4:],actions=s['actions'][-14:],
                submissions=s['submissions'][-6:],calls=s['calls'],
                pending=(dict(action=pend[0],pos=list(pend[1])) if pend else None),
                next_tick=self.w.tick,
                notice='No global physical state. Actions are submitted for the next world tick; the world advances on its own clock. Observations are paid snapshots and may be stale.')

    # ---------------- submit (never advances physics) ----------------
    def submit(self,token,kind,x=0,y=0):
        if kind not in ACTIONS:raise ValueError('No boundary ops in the live universe')
        with self.lock:
            if self._poisoned:
                # Never acknowledge an action the world cannot execute (review finding A).
                raise RuntimeError('Journal error: the world is not accepting actions until restart and verification')
            s=self._get(token)
            pos=(x,y)
            if kind!='wait' and not self.w.inb(pos):raise ValueError('outside lattice')
            agent=s['agent']
            if agent in self.pending:
                status='refused:already-submitted'
            else:
                self.pending[agent]=(kind,pos);status='accepted'
            s['calls']+=1
            s['submissions'].append(dict(for_tick=self.w.tick,action=kind,pos=list(pos),status=status))
            s['submissions']=s['submissions'][-6:]
            view=self.actor_view(token)
            view.update(submission=status,scheduled_for_tick=self.w.tick)
            return view

    # ---------------- advance: one world tick for one accepted batch ----------------
    def _apply_outcomes(self,actors,batch,ev):
        by_agent={a['agent']:a for a in actors.values()}
        results={e[0]:e for e in ev['agent']}          # at most one op per agent per tick
        outcomes=[]
        for agent,(kind,pos) in batch:
            s=by_agent[agent]
            if kind=='wait':
                result='noop'
            else:
                e=results[agent];result=e[3]
                s['actions'].append(dict(tick=ev['tick'],action=kind,pos=list(pos),result=result))
                s['actions']=s['actions'][-14:]
                if kind=='observe' and result=='ok':
                    view=e[4]
                    s['observations'].append(dict(tick=ev['tick'],site=list(pos),radius=self.w.P.obs_radius,
                        particles=[dict(x=p[0],y=p[1],species=v[0],direction=v[1],excitation=v[2],charge=v[3]) for p,v in sorted(view.items())]))
                    s['observations']=s['observations'][-4:]
            outcomes.append(dict(agent=agent,op=kind,pos=list(pos),result=result))
        return outcomes

    def advance(self):
        """Execute exactly one world tick with the canonically ordered accepted batch."""
        with self.lock:
            if self._poisoned:raise RuntimeError('Journal error: restart and verify before another mutation')
            batch=canonical_batch(self.pending,self.w.tick,self.w.seed)
            staged=self.w.clone()
            staged_actors={h:copy.deepcopy(a) for h,a in self.by_token.items()}
            ev=staged.step(agent_ops=[(a,k,p) for a,(k,p) in batch if k!='wait'])
            outcomes=self._apply_outcomes(staged_actors,batch,ev)
            record=dict(kind='tick',tick=ev['tick'],
                        batch=[dict(agent=a,op=k,pos=list(p)) for a,(k,p) in batch],
                        outcomes=outcomes,blocked=ev['blocked'],effects=ev['acts'],energy=ev['energy'])
            rec=self._commit(record,staged)
            self.w=staged;self.by_token=staged_actors;self.pending={};self.last_tick_at=time.time()
            return rec

    # ---------------- observer ----------------
    def observer_view(self):
        with self.lock:return dict(role='observer',frame=global_snapshot(self.w),
            participant_count=self.next_slot,clock=self.clock_view(),
            note='Read-only global state; declaring it as prior exposure is required for controlled trials.')

    def observer_log(self):
        with self.lock:
            # Inspecting a journal is an observer privilege, never an actor response.
            return dict(role='observer',events=[json.loads(s) for s in self.journal.read_text().splitlines()] if self.journal.exists() else [])
