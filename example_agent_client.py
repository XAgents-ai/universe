"""Minimal agent-side HTTP client. No server-side privileges, no LLM implied.

Example: python example_agent_client.py --steps 8
To integrate a model, replace choose_action(view) with your own model call. Only
pass the returned paid observations, actor history and owned-site coordinates.
Do not provide the global observer API result to an uninformed research actor.
"""
import argparse,json,urllib.request,urllib.error


def http(root,path,payload=None,token=None):
    body=json.dumps(payload).encode() if payload is not None else None
    headers={'Content-Type':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    req=urllib.request.Request(root.rstrip('/')+path,data=body,headers=headers)
    with urllib.request.urlopen(req,timeout=15) as r:return json.load(r)


def choose_action(view):
    """Deterministic example policy, NOT AI: observe once, then actuate or wait."""
    owned=view['authorized']
    if not owned:return dict(kind='wait')
    site=owned[0]
    if not view['observed']:return dict(kind='observe',x=site[0],y=site[1])
    # The stored energy information comes only from the previous charged observation.
    observed=view['observed'][-1]['particles']
    stores=[p for p in observed if p['species']=='B' and abs(p['x']-site[0])+abs(p['y']-site[1])==1]
    can_act=any(p['charge']>=2 for p in stores)
    return dict(kind='set' if can_act else 'observe',x=site[0],y=site[1])


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--url',default='http://127.0.0.1:8765')
    ap.add_argument('--steps',type=int,default=6)
    ap.add_argument('--token',default=None,help='Resume a participant without allocating a new entry slot')
    args=ap.parse_args()
    if args.token:
        token=args.token;view=http(args.url,'/api/live/actor',token=token)
    else:
        joined=http(args.url,'/api/live/join',dict(controller='program',global_exposure_declared=False))
        token=joined.pop('token');view=joined
        print('Private resume token (do not paste publicly):',token)
    for _ in range(args.steps):
        action=choose_action(view)
        view=http(args.url,'/api/live/act',action,token)
        print('call',view['calls'],'action',action['kind'],'last outcome',view['actions'][-1] if view['actions'] else 'wait')
    print('Only locally paid observations were used; all effects occurred in the shared kernel.')

if __name__=='__main__':main()
