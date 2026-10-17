"""F6: sound cold-oracle state equivalence without changing live seeded behavior."""
from dataclasses import replace
from v0_kernel import World,Params

def competing(seed,policy):
    p=Params().cold()
    p.conflict_policy=policy
    w=World(7,7,seed,p)
    w.place((2,3),'C','E');w.grid[(2,3)].x=1
    w.place((4,3),'C','W');w.grid[(4,3)].x=1
    w.place((3,3),'C','N')
    return w

def material(w):
    return tuple(sorted((p,q.sp,q.o,q.x,q.q,q.c,q.seen) for p,q in w.grid.items()))

def test_f6():
    a,b=competing(1,'canonical'),competing(5,'canonical')
    assert a.physical_key()==b.physical_key()
    a.step();b.step()
    assert material(a)==material(b),'Cold oracle must be RNG-independent for physical outcomes'
    c,d=competing(1,'seeded'),competing(5,'seeded')
    assert c.physical_key()!=d.physical_key(),'Seeded mode must distinguish RNG states'
    c.step();d.step()
    assert material(c)!=material(d),'Counterexample must still exist in actual live physics'
    print('PASS F6: cold canonical mode yields same future from merged material states; live seeded RNG remains future-relevant and in key')

if __name__=='__main__':test_f6()
