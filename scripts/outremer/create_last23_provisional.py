#!/usr/bin/env python3
"""MMD31: 23 provisional club badges. Clearly NOT authentic club crests.
The authentic 303 PNGs are preserved verbatim. All generated artwork is original,
contains only a generic shield/monogram, and is labelled PROV.
"""
import csv,hashlib,io,json,re,unicodedata,collections
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path("flags/clubs/standard/outremer-2026-27")
AUD=Path("audit/outremer-2026-27")
ROSTER=list(csv.DictReader((AUD/"roster_326.csv").open(encoding="utf-8")))
assert len(ROSTER)==326 and len({r["team_id"] for r in ROSTER})==326
CURRENT={p.stem for p in ROOT.glob("*.png")}
assert len(CURRENT)==303,("expected 303 existing crests, found",len(CURRENT))
MISSING=[r for r in ROSTER if r["team_id"] not in CURRENT]
assert len(MISSING)==23,("expected 23 unresolved clubs",len(MISSING))
PALETTES=[
 ((23,79,138),(156,207,245)), ((90,57,130),(205,178,238)),
 ((26,110,93),(161,224,198)), ((136,57,68),(237,181,188)),
 ((113,82,30),(242,213,148)), ((31,94,112),(175,219,231)),
 ((119,63,115),(236,184,222)), ((36,81,66),(163,214,183)),
 ((101,57,45),(227,177,147)), ((49,70,125),(171,186,238))]
FONTS=[
 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
 "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]
def font(px):
 for p in FONTS:
  if Path(p).exists():return ImageFont.truetype(p,px)
 return ImageFont.load_default()
def norm(s):
 s=unicodedata.normalize("NFKD",s)
 return "".join(c for c in s if not unicodedata.combining(c))
def acronym(name):
 stripped=norm(name).upper().replace("’","'")
 tokens=re.findall(r"[A-Z0-9]+",stripped)
 remove={"A","AS","A.S","AJS","FC","F","C","U","S","US","J","JS","JSC","ASC","CLUB","DE","DES","DU","D","LA","LE","LES","ENT","SPORTIVE","ET","FOOTBALL"}
 core=[x for x in tokens if x not in remove]
 if len(core)>=2:return (core[0][0]+core[1][0])[:3]
 if core:return core[0][:3]
 return "".join(t[0] for t in tokens[:3]) or "FC"
def fit(draw,s,max_width,high,low=7):
 for size in range(high,low-1,-1):
  f=font(size)
  if draw.textbbox((0,0),s,font=f)[2]<=max_width:return f
 return font(low)
def create(row):
 tid=row["team_id"];name=row["name"]
 seed=int(hashlib.sha256(tid.encode()).hexdigest()[:8],16)
 primary,light=PALETTES[seed%len(PALETTES)]
 img=Image.new("RGB",(120,96),light)
 d=ImageDraw.Draw(img)
 # A solid club-color-inspired canvas, simple distinct original crest.
 d.rounded_rectangle((4,4,115,91),radius=8,fill=primary)
 d.rounded_rectangle((6,6,113,89),radius=7,outline=light,width=1)
 # Original unbranded generic shield, designed to avoid asserting ownership of a real crest.
 shield=[(42,12),(78,12),(90,23),(86,55),(76,70),(60,79),(44,70),(34,55),(30,23)]
 d.polygon(shield,fill=(248,249,246))
 d.line(shield+[shield[0]],fill=primary,width=2,joint="curve")
 d.line([(39,25),(81,25)],fill=light,width=2)
 d.text((60,42),acronym(name),font=fit(d,acronym(name),48,19,12),anchor="mm",fill=primary,stroke_width=0)
 # Identifiable as a provisional, not an authentic club logo.
 upper=norm(name).upper()
 if len(upper)>18:
  parts=upper.split()
  top="";bottom=""
  for w in parts:
   if len(top+" "+w)<=17:top=(top+" "+w).strip()
   else:bottom=(bottom+" "+w).strip()
  upper=(top or upper[:17])
  if bottom:
   upper=top[:17]+" / "+bottom[:17]
 if len(upper)>29: upper=upper[:27]+"…"
 small=fit(d,upper,105,8,6)
 d.rounded_rectangle((8,79,112,88),radius=2,fill=(246,248,249))
 d.text((60,83.5),upper,font=small,anchor="mm",fill=primary)
 d.text((110,8),"P",font=font(7),anchor="ra",fill=(255,255,255))
 buf=io.BytesIO();img.save(buf,format="PNG",optimize=True)
 return buf.getvalue(),acronym(name),primary,light
entries=[]
for r in MISSING:
 tid=r["team_id"];dest=ROOT/(tid+".png")
 assert not dest.exists(),tid
 blob,abbr,primary,light=create(r)
 dest.write_bytes(blob)
 verify=Image.open(dest)
 assert verify.size==(120,96) and verify.format=="PNG",tid
 entry={"team_id":tid,"club":r["name"],"territory":r["territory"],
        "status":"PROVISOIRE_NON_AUTHENTIQUE",
        "filename":dest.name,"monogram":abbr,"background_rgb":list(primary),
        "sha256":hashlib.sha256(blob).hexdigest(),"bytes":len(blob)}
 entries.append(entry)
assert len(entries)==23 and len({e["sha256"] for e in entries})==23
assert {p.stem for p in ROOT.glob("*.png")}==CURRENT|{r["team_id"] for r in MISSING}
audit={"total_overseas":326,"existing_authenticated_source_pngs":303,
       "new_provisional_pngs":23,"total_pngs":326,
       "width":120,"height":96,
       "description":"Original generic monogram graphics, NOT official/authentic crests. They must be replaced when real club emblems are found.",
       "retention":"The pre-existing 303 files are never opened for modification.",
       "generated":entries}
(AUD/"lot13_remaining23_provisional_manifest.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
# Full status manifest: match each team ID to a verified file on the branch.
base="https://raw.githubusercontent.com/MMMMMMD31/mmd31-wavy-flags/mmd31-outremer-ecussons-20261023/flags/clubs/standard/outremer-2026-27/"
provisional={e["team_id"] for e in entries}
with (AUD/"published_overseas_manifest_326.csv").open("w",encoding="utf-8",newline="") as f:
 fields=["team_id","club","territoire","division","type_ecusson","flagUrl","sha256"]
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for r in ROSTER:
  tid=r["team_id"];p=ROOT/(tid+".png")
  w.writerow({"team_id":tid,"club":r["name"],"territoire":r["territory"],
       "division":r["division"],"type_ecusson":"PROVISOIRE_NON_AUTHENTIQUE" if tid in provisional else "EXISTANT_SOURCE_CLUB",
       "flagUrl":base+tid+".png","sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
print("SUCCESS 326 PNG / 326 CLU BS; provisional 23; existing 303 preserved",flush=True)
