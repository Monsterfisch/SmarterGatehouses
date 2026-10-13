"""Ranged damage to troops on top of a large gatehouse, on both exes."""
import os, sys, struct
BENCH = os.path.dirname(os.path.abspath(__file__))
os.environ['TUNNELERS_MODULE'] = os.path.join(os.path.dirname(BENCH), 'module')
sys.path.insert(0, BENCH)
os.chdir(BENCH)
import harness
from harness import Host

FAILS = []
def check(name, got, want):
    ok = got == want
    print('   %-58s %s   (got %s, want %s)' % (name, 'ok' if ok else 'FAIL', got, want))
    if not ok:
        FAILS.append(name)

SITE = "29 8C 3E DC 09 00 00 33 ED 39 AC 3E DC 09 00 00 7F 07 89 AC 3E DC 09 00 00"
LAYERS = ("F7 04 8D ? ? ? ? 00 01 00 00 75 1F 0F BF 14 4D ? ? ? ? 69 D2 2C 03 00 00 0F BF 8A ? ? ? ? "
          "83 3C 8D ? ? ? ? 00")
DETECT = "0F BF 88 ? ? ? ? 8B 54 24 30 3B D1 7E 04 2B D1 EB 04 2B CA 8B D1 0F BF 80 ? ? ? ? 8B 4C 24 34"
LINK = "8B 4C 24 04 69 C9 2C 03 00 00 53 55 56 0F BF B1 ? ? ? ? 57 8B B9 ? ? ? ? 8B C7 99 2B C2 D1 F8 66 83 B9 ? ? ? ? 50"


def run(extreme):
    print('=== %s' % ('Extreme' if extreme else 'vanilla'))
    for pct in (70, 100):
        H = Host(extreme=extreme, config={'damage': {'large_gatehouse': pct}}, texts=False)
        E = H.E
        print('   log:', H.logs[-1])
        site = E.find(SITE)[0]
        bmap = E.u32(E.find(LAYERS)[0] + 17)
        units = E.u32(E.find(DETECT)[0] + 3) - 0xB6
        bld = E.u32(E.find(LINK)[0] + 16) - 0xEE
        state = units - 0x614
        tile = 5000

        def hit(kind, building, passage=0, damage=90):
            uid = 3
            u = units + uid * 0x490
            H.put32(u + 0xD4, tile)
            H.put16(bmap + tile * 2, 9 if building else 0)
            H.put16(bld + 9 * 0x32C + 0xD2, building or 0)
            H.put8(u + 0x402, passage)
            H.put32(u + 0x3C8, 1000)                    # health (+0x9DC - 0x614)
            cpu = H.run(site, until=site + 7, regs={'esi': uid * 0x490, 'edi': state, 'ebx': kind,
                                                    'ecx': damage, 'ebp': 0x55})
            assert cpu.r['ebp'] == 0x55 and cpu.r['esi'] == uid * 0x490 and cpu.r['edi'] == state
            return 1000 - struct.unpack('<i', H.m.read(u + 0x3C8, 4))[0]

        want = 63 if pct == 70 else 90
        check('%d%%: arrow on top of a large gatehouse' % pct, hit(1, 0x2D), want)
        check('%d%%: crossbow bolt there' % pct, hit(7, 0x2D), want)
        check('%d%%: sling stone there' % pct, hit(0x21, 0x2D), want)
        check('%d%%: arrow on a small gatehouse: unchanged' % pct, hit(1, 0x2E), 90)
        check('%d%%: arrow in the large gatehouse\'s passage: unchanged' % pct, hit(1, 0x2D, passage=10), 90)
        check('%d%%: arrow on open ground: unchanged' % pct, hit(1, None), 90)
        check('%d%%: catapult rock on the large gatehouse: unchanged' % pct, hit(2, 0x2D), 90)


for extreme in (False, True):
    run(extreme)
print()
print('FAILURES: %s' % ', '.join(FAILS) if FAILS else 'ALL OK')
