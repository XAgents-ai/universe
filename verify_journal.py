"""Reconstruct the shared universe and verify chained events and state hashes."""
import argparse
from open_world import LiveUniverse

def main():
    ap=argparse.ArgumentParser();ap.add_argument('state_directory');args=ap.parse_args()
    u=LiveUniverse(args.state_directory)
    print('VALID JOURNAL: tick',u.w.tick,'participants',u.next_slot,'world hash',u.w.state_hash(),
          'energy ledger',u.w.energy(),'chain tip',u.last_chain)

if __name__=='__main__':main()
