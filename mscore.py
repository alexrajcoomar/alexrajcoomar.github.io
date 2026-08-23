"""
Beneish M-Score computation.
Specification as reproduced from three independent sources that agree exactly on
coefficients and threshold (Wikipedia entry citing Beneish 1999/2013/2020; AAII Journal;
GMT Research). Original FAJ 1999 text is closed-access and was NOT obtained.
M = -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI + 0.115*DEPI
        - 0.172*SGAI + 4.679*TATA - 0.327*LVGI
TATA = (income from continuing operations - cash flow from operations) / total assets   [cash-flow form]
Thresholds: -1.78 (commonly cited) and -2.22 (more permissive/older cut-off).
"""
from dataclasses import dataclass, field

@dataclass
class Y:
    sales: float; cogs: float; ar: float; ca: float; ppe: float; sec: float
    ta: float; dep: float; sga: float; cl: float; ltd: float; ico: float; cfo: float

def mscore(t: Y, p: Y, include_sec=True, label=""):
    DSRI = (t.ar/t.sales)/(p.ar/p.sales)
    GMI  = ((p.sales-p.cogs)/p.sales)/((t.sales-t.cogs)/t.sales)
    sec_t = t.sec if include_sec else 0.0
    sec_p = p.sec if include_sec else 0.0
    aq_t = 1-((t.ca+t.ppe+sec_t)/t.ta)
    aq_p = 1-((p.ca+p.ppe+sec_p)/p.ta)
    AQI  = aq_t/aq_p
    SGI  = t.sales/p.sales
    DEPI = (p.dep/(p.dep+p.ppe))/(t.dep/(t.dep+t.ppe))
    SGAI = (t.sga/t.sales)/(p.sga/p.sales)
    LVGI = ((t.cl+t.ltd)/t.ta)/((p.cl+p.ltd)/p.ta)
    TATA = (t.ico-t.cfo)/t.ta
    M = (-4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI
         + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI)
    v = dict(DSRI=DSRI, GMI=GMI, AQI=AQI, SGI=SGI, DEPI=DEPI, SGAI=SGAI, LVGI=LVGI, TATA=TATA, M=M)
    print(f"--- {label} (securities in AQI: {include_sec}) ---")
    for k in ["DSRI","GMI","AQI","SGI","DEPI","SGAI","LVGI","TATA"]:
        print(f"  {k:5s} {v[k]:+.4f}   contribution {dict(DSRI=0.920,GMI=0.528,AQI=0.404,SGI=0.892,DEPI=0.115,SGAI=-0.172,LVGI=-0.327,TATA=4.679)[k]*v[k]:+.4f}")
    print(f"  M-SCORE {M:+.4f}   flag@-1.78: {'YES' if M>-1.78 else 'no'}   flag@-2.22: {'YES' if M>-2.22 else 'no'}")
    return v

# ---------------- Sino-Forest, Canadian GAAP, US$000 ----------------
sf10 = Y(sales=1_923_536, cogs=1_252_023, ar=636_626, ca=2_079_295, ppe=113_150, sec=32_101,
         ta=5_729_033, dep=5_145, sga=89_712, cl=755_784, ltd=1_659_682, ico=395_426, cfo=840_085)
sf09c= Y(sales=1_238_185, cogs=797_800,  ar=282_306, ca=1_586_761, ppe=77_377,  sec=70_387,
         ta=3_963_899, dep=4_693, sga=63_980, cl=373_780, ltd=925_466, ico=286_370, cfo=784_517)
sf09 = Y(sales=1_238_185, cogs=797_292,  ar=282_306, ca=1_586_761, ppe=77_377,  sec=70_387,
         ta=3_963_899, dep=4_693, sga=64_488, cl=373_780, ltd=925_466, ico=286_370, cfo=784_517)
sf08 = Y(sales=896_045,  cogs=530_083,  ar=225_753, ca=811_457,  ppe=63_704,  sec=45_784,
         ta=2_603_924, dep=3_206, sga=53_372, cl=290_692, ltd=714_468, ico=228_593, cfo=487_183)

mscore(sf10, sf09c, True,  "Sino-Forest FY2010 vs FY2009")
mscore(sf09, sf08,  True,  "Sino-Forest FY2009 vs FY2008")

# depletion sensitivity for Sino-Forest FY2010 (timber depletion treated as depreciation)
sf10d = Y(**{**sf10.__dict__, 'dep':754_393})
sf09d = Y(**{**sf09c.__dict__, 'dep':527_090})
mscore(sf10d, sf09d, True, "Sino-Forest FY2010 [DEPI incl. timber depletion]")

# ---------------- Nortel, US GAAP, US$M ----------------
nt02 = Y(sales=10_560, cogs=6_953, ar=1_910, ca=8_476, ppe=1_444, sec=0,
         ta=15_971, dep=705, sga=2_675, cl=6_982, ltd=3_719, ico=-3_585, cfo=-589)
nt01 = Y(sales=17_511, cogs=14_167, ar=2_923, ca=11_762, ppe=2_571, sec=0,
         ta=21_137, dep=722, sga=5_911, cl=9_457, ltd=4_094, ico=-24_307, cfo=0)
mscore(nt02, nt01, False, "Nortel FY2002 vs FY2001")

# ---------------- Poseidon: quarterly receivables diagnostic (NOT an M-Score) -------
print("--- Poseidon Concepts 2012 interim receivables diagnostic (CAD $000,000) ---")
q = [("Q1 2012", 52.129, 83.018), ("Q2 2012", 54.875, 118.641), ("Q3 2012", 41.116, 125.516)]
base = None
for name, rev, ar in q:
    ratio = ar/rev
    dso = ratio*91.25
    if base is None: base = ratio
    print(f"  {name}: revenue {rev:6.3f}  AR {ar:7.3f}  AR/quarterly revenue {ratio:5.3f}  ~DSO {dso:6.1f} days  index vs Q1 {ratio/base:5.3f}")
