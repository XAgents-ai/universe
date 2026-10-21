"""Universe V0 audit-first viewer and two-door local interaction prototype.

Three separate worlds:
 * audit: immutable registered O2 witness replay, read-only full instrumentation.
 * agent: human is agent-0, only charged set/observe/claim + wait.
 * experiment: isolated research clone, only logged boundary ops + wait.

This is a LOCAL RESEARCH PROTOTYPE, not a hardened public server.
"""
from __future__ import annotations

import json
import os
import secrets
import threading
from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from v0_oracle import build_seed_world, AG, TARGET_BOND
from open_world import LiveUniverse, ClockPolicy
from v0_responder import seed_world as build_responder_seed_world

HERE = Path(__file__).resolve().parent
APP = FastAPI(title='Universe V0 physical-state viewer', version='0.1')
SESSIONS = {}
LOCK = threading.RLock()
# W1: the world owns its clock. UNIVERSE_TICK_SECONDS > 0 runs the scheduler; 0 is manual mode for tests/harnesses.
LIVE = LiveUniverse(Path(os.environ.get('UNIVERSE_STATE_DIR', str(HERE/'.universe_state'))),
                    clock=ClockPolicy(tick_seconds=float(os.environ.get('UNIVERSE_TICK_SECONDS', '1.0'))),
                    single_writer=True)   # one authoritative writer per state directory; a second process refuses to start


class Create(BaseModel):
    role: Literal['audit', 'agent', 'experiment']


class Join(BaseModel):
    controller: Literal['human', 'model', 'program'] = 'human'
    global_exposure_declared: bool = False


class Action(BaseModel):
    kind: Literal['wait', 'set', 'observe', 'claim', 'drop', 'remove', 'replace']
    x: int = Field(default=0, ge=0, lt=1000)
    y: int = Field(default=0, ge=0, lt=1000)
    species: Literal['S', 'C', 'G', 'A', 'W', 'B', 'P', 'K', 'R'] = 'S'
    direction: Literal['N', 'E', 'S', 'W'] = 'N'


@dataclass
class Session:
    role: str
    world: object | None = None
    frames: list = field(default_factory=list)
    cursor: int = 0
    observations: list = field(default_factory=list)
    agent_events: list = field(default_factory=list)
    recent: list = field(default_factory=list)
    calls: int = 0


def as_particles(world):
    return [dict(x=x, y=y, species=p.sp, direction=p.o, excitation=p.x,
                 charge=p.q, control=p.c, sensor_state=p.seen, pid=p.pid)
            for (x,y), p in sorted(world.grid.items())]


def as_bonds(world):
    return [[list(a), list(b)] for a,b in sorted((tuple(sorted(b)) for b in world.bonds))]


def as_sources(world):
    return [dict(x=p[0], y=p[1], direction=v[0], period=v[1]) for p,v in sorted(world.sources.items())]


def audit_frame(world, ev=None):
    return dict(tick=world.tick, width=world.W, height=world.H,
                particles=as_particles(world), bonds=as_bonds(world),
                sources=as_sources(world), heat=[dict(x=k[0], y=k[1], quanta=q) for k,q in sorted(world.heat.items())],
                energy=world.energy(), matter=world.matter(), hash=world.state_hash(),
                event=normalize_event(ev) if ev else None)


def normalize_event(ev):
    if not ev: return None
    # Event tuples have only serializable items except observe payload, whose position keys are tuples.
    out = dict(tick=ev['tick'], blocked=ev['blocked'], environment=ev['env'],
               boundary=ev['boundary'], effects=ev['acts'], hash=ev['hash'],
               agent=[])
    for a in ev['agent']:
        out['agent'].append(dict(agent=a[0], op=a[1], pos=list(a[2]), result=a[3]))
    return out


def build_audit_frames():
    """Freeze a verified, deterministic event history. No writes in audit mode."""
    w = build_responder_seed_world(seed=7)
    w.run({}, 20)
    frames = [audit_frame(w)]
    trace = json.loads((HERE/'o2_witness_autonomous_responder.json').read_text())['trace']
    schedule = {int(t): ([(AG, op, tuple(pos))], ()) for t, op, pos in trace if op}
    schedule[30] = ((), [('drop', (7,5), 'S', 'N')])  # post-disconnect sensor test, registered boundary input
    for t in range(20, 36):
        a,e = schedule.get(t, ((), ()))
        ev = w.step(a,e)
        frames.append(audit_frame(w, ev))
    return frames


AUDIT_FRAMES = build_audit_frames()


def agent_frame(s):
    w = s.world
    return dict(role='agent', width=w.W, height=w.H, observed=s.observations,
                authorized=[list(p) for p in w.authorized_sites(AG)],
                calls=s.calls, actions=s.agent_events[-14:],
                notice='All cells outside paid observation windows are unknown. Snapshots may be stale.')


def session_payload(s):
    if s.role == 'audit':
        return dict(role='audit', cursor=s.cursor, length=len(s.frames), frame=s.frames[s.cursor])
    if s.role == 'agent':
        return agent_frame(s)
    return dict(role='experiment', frame=audit_frame(s.world), events=s.recent[-20:])


@APP.get('/')
def index():
    return FileResponse(HERE/'static'/'index.html')


@APP.get('/static/{filename}')
def static_file(filename: str):
    if filename not in ('app.js', 'style.css'):
        raise HTTPException(404)
    return FileResponse(HERE/'static'/filename)


@APP.post('/api/session')
def new_session(request: Create):
    with LOCK:
        sid = secrets.token_urlsafe(24)
        if request.role == 'audit':
            s = Session(role='audit', frames=AUDIT_FRAMES)
        else:
            w = build_seed_world(seed=11 if request.role=='experiment' else 57)
            w.run({}, 20)
            s = Session(role=request.role, world=w)
        SESSIONS[sid] = s
        return dict(session=sid, **session_payload(s))


def get_session(sid):
    if sid not in SESSIONS: raise HTTPException(404, 'No such session')
    return SESSIONS[sid]


@APP.get('/api/session/{sid}')
def read_session(sid: str):
    with LOCK: return session_payload(get_session(sid))


@APP.post('/api/session/{sid}/frame/{index}')
def select_audit_frame(sid: str, index: int):
    with LOCK:
        s = get_session(sid)
        if s.role != 'audit': raise HTTPException(403, 'Only read-only audit sessions have a timeline')
        if index < 0 or index >= len(s.frames): raise HTTPException(400, 'Invalid frame')
        s.cursor = index
        return session_payload(s)


@APP.post('/api/session/{sid}/act')
def act(sid: str, cmd: Action):
    with LOCK:
        s = get_session(sid)
        if s.role == 'audit': raise HTTPException(403, 'Audit is read-only')
        w = s.world
        pos = (cmd.x, cmd.y)
        if not w.inb(pos): raise HTTPException(400, 'Outside lattice')
        if s.role == 'agent':
            if cmd.kind not in ('wait', 'set', 'observe', 'claim'):
                raise HTTPException(403, 'Agent cannot issue boundary operations')
            a = () if cmd.kind == 'wait' else [(AG, cmd.kind, pos)]
            ev = w.step(agent_ops=a)
            s.calls += 1
            if a:
                result = ev['agent'][0]
                record = dict(action=cmd.kind, pos=list(pos), result=result[3])
                s.agent_events.append(record)
                if cmd.kind == 'observe' and result[3] == 'ok':
                    # The paid observe response is the ONLY source of local particle data.
                    view = result[4]
                    s.observations.append(dict(at_call=s.calls, site=list(pos),
                         radius=w.P.obs_radius,
                         particles=[dict(x=p[0], y=p[1], species=v[0], direction=v[1],
                                         excitation=v[2], charge=v[3]) for p,v in sorted(view.items())]))
                    s.observations = s.observations[-4:]
            return session_payload(s)
        # Separate experimental clone with registered and logged boundary ops only.
        if cmd.kind not in ('wait', 'drop', 'remove', 'replace'):
            raise HTTPException(403, 'Experimenter cannot write control bits')
        if cmd.kind == 'wait':
            ev = w.step()
        elif cmd.kind in ('drop', 'replace'):
            ev = w.step(env_ops=[(cmd.kind, pos, cmd.species, cmd.direction)])
        else:
            ev = w.step(env_ops=[('remove', pos)])
        s.recent.append(normalize_event(ev))
        return session_payload(s)


@APP.get('/api/session/{sid}/export')
def export(sid: str):
    with LOCK:
        s = get_session(sid)
        if s.role == 'agent':
            # Private actor log only; no complete world replay or state data.
            return dict(role='agent', actions=s.agent_events, observations=s.observations)
        if s.role == 'audit':
            return dict(role='audit', frames=s.frames)
        # Authored experimental interventions and their kernel outcomes; no privileged live role.
        return dict(role='experiment', initial='R0.2 build_seed_world seed=11, 20 charging ticks', events=s.recent)




# ---- Shared persistent universe: separate participant and observer views ----
def _bearer(authorization):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401,'Participant bearer token required')
    return authorization[7:]


@APP.post('/api/live/join')
def live_join(request: Join):
    try:return LIVE.join(request.controller,request.global_exposure_declared)
    except ValueError as e:raise HTTPException(409,str(e))


@APP.get('/api/live/actor')
def live_actor(authorization: str | None = Header(default=None)):
    try:return LIVE.actor_view(_bearer(authorization))
    except KeyError:raise HTTPException(401,'Unknown participant token')


@APP.post('/api/live/act')
def live_act(cmd:Action, authorization: str | None = Header(default=None)):
    # W1: SUBMIT one action for the next world tick. This request never advances physics.
    token=_bearer(authorization)
    try:return LIVE.submit(token,cmd.kind,cmd.x,cmd.y)
    except KeyError:raise HTTPException(401,'Unknown participant token')
    except ValueError as e:raise HTTPException(403,str(e))
    except RuntimeError as e:raise HTTPException(503,str(e))   # journal poisoned: fail closed, never acknowledge


@APP.get('/api/live/clock')
def live_clock():
    # Read-only description of the world's clock policy and the current tick. There is deliberately
    # no endpoint that advances the world: time is not a participant privilege.
    return LIVE.clock_view()


@APP.get('/api/live/observer')
def live_observer():
    frame=LIVE.observer_view()
    with LIVE.lock:
        frame['event']=normalize_event(LIVE.w.log[-1]) if LIVE.w.tick>20 else None
    return frame


@APP.get('/api/live/events')
def live_events():
    # Public audit evidence never contains participant bearer tokens.
    entries=LIVE.observer_log()['events']
    return dict(role='observer',events=[{k:v for k,v in e.items() if k!='token'} for e in entries])


app = APP
