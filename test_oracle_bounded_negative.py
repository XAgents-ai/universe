"""A quick, actual exhaustive bounded-negative result under canonical cold rules."""
from v0_kernel import World,Params
from v0_oracle import oracle_o2

def test_negative():
    w=World(5,5,9,Params())
    w.place((2,2),'K','E');w.place((2,3),'B',q=8);w.grant('agent-0',(2,2))
    w.run({},1)
    def goal(x):return any(p.sp=='P' for p in x.grid.values())
    res=oracle_o2(w,[(2,2)],goal,max_depth=4,max_nodes=10000)
    assert res['status']=='NOT_ESTABLISHED' and res['reason']=='exhausted',res
    print('PASS bounded negative: no sensor species can arise from a K+B inventory; horizon 4; mode canonical cold;',res['nodes'],'generated successors')

if __name__=='__main__':test_negative()
