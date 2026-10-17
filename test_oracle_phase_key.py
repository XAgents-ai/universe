"""F5 (closed in R0.2): cold oracle key must include source clock phase.
This test should PASS against the installed R0.2 kernel.
A witness found via BFS is still a valid witness; completeness/exhaustion is unproven.
"""
from v0_kernel import World

a=World(5,5,7)
a.add_source((2,2),'E',2)
a.place((3,2),'B')
b=a.clone();b.tick=1
same=a.physical_key()==b.physical_key()
a.step();b.step()
differ=a.grid[(3,2)].q != b.grid[(3,2)].q
assert differ, 'Setup must have different physical futures'
assert not same, 'Physical-key collision: equal keys, but sources have different phases'
print('PASS: cold oracle state keys distinguish time-dependent source phase')
