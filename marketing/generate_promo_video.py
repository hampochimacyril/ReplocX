#!/usr/bin/env python3
"""Render a polished animated MP4 promo for the Representative Location Explorer.

Pure Python motion graphics (Pillow + numpy) streamed to ffmpeg (H.264 + AAC),
with a soft generated ambient music bed. No external assets, no network.

Run:  python3 generate_promo_video.py
Out:  promo.mp4   (1600x900, ~53s)
"""
from __future__ import annotations
import math, struct, subprocess, sys, wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

W, H, FPS = 1600, 900, 30
HERE = Path(__file__).resolve().parent
OUT = HERE / "promo.mp4"
WAV = HERE / "_bed.wav"

# palette
NAVY0=(3,12,20); NAVY1=(11,40,58); TEAL=(95,202,191); TEAL_D=(10,150,144)
GOLD=(243,220,166); INK=(234,243,243); SUB=(168,196,201)
CLIMATE={"cold":(57,119,168),"dry":(201,154,56),"humid":(10,150,144),"marine":(120,107,168),"mixed":(183,89,77)}

def font(paths, size):
    for p in paths:
        try: return ImageFont.truetype(p, size)
        except OSError: continue
    return ImageFont.load_default()
SERIF=lambda s: font(["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"], s)
SANS =lambda s: font(["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"], s)
SANSB=lambda s: font(["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"], s)

def ease(t): return 1-(1-t)**3
def clamp(x,a=0.0,b=1.0): return max(a,min(b,x))

# ---- background (precomputed radial gradient) ----
def make_bg():
    ys=np.linspace(0,1,H)[:,None]; xs=np.linspace(0,1,W)[None,:]
    d=np.sqrt((xs-0.74)**2+((ys-0.30)*1.1)**2)
    k=np.clip(1-d*1.05,0,1)[...,None]
    base=np.array(NAVY0); top=np.array((14,50,66))
    img=(base*(1-k)+top*k).astype(np.uint8)
    img=np.repeat(img,3,axis=2) if img.shape[2]==1 else img
    bg=Image.fromarray(img,"RGB")
    dr=ImageDraw.Draw(bg,"RGBA")
    for gx in range(0,W,54): dr.line([(gx,0),(gx,H)],fill=(255,255,255,8))
    for gy in range(0,H,54): dr.line([(0,gy),(W,gy)],fill=(255,255,255,8))
    # vignette
    v=Image.new("L",(W,H),0); vd=ImageDraw.Draw(v)
    vd.ellipse([-W*0.3,-H*0.3,W*1.3,H*1.3],fill=80)
    bg.paste((0,0,0),(0,0),Image.eval(v,lambda p:80-p))
    return bg
BG=make_bg()

# ---- US map raster ----
US_PATHS=[
 "M44 83 L103 61 L174 63 L211 81 L262 80 L305 93 L355 102 L403 88 L463 101 L512 82 L579 85 L632 104 L697 91 L758 122 L797 183 L771 223 L744 245 L730 301 L690 318 L665 345 L629 336 L602 287 L568 276 L541 251 L507 267 L474 255 L446 277 L415 252 L380 271 L347 260 L310 282 L274 262 L247 273 L222 238 L188 238 L163 214 L133 206 L116 173 L72 163 Z"]
METROS=[(-122.33,47.61,"marine"),(-122.68,45.52,"marine"),(-124.16,40.80,"marine"),
 (-118.24,34.05,"dry"),(-112.07,33.45,"dry"),(-111.89,40.76,"cold"),(-104.99,39.74,"cold"),
 (-93.27,44.98,"cold"),(-87.65,41.85,"cold"),(-94.58,39.10,"cold"),(-74.0,40.71,"cold"),
 (-71.06,42.36,"cold"),(-95.37,29.76,"humid"),(-90.07,29.95,"humid"),(-80.19,25.76,"humid"),
 (-96.80,32.78,"humid"),(-84.39,33.75,"mixed"),(-77.04,38.90,"mixed"),(-86.78,36.16,"mixed")]
PHILLY=(-75.16,39.95)
def parse(d):
    pts=[];
    for tok in d.replace("Z","").split("L"):
        tok=tok.replace("M","").strip()
        if not tok: continue
        x,y=tok.split(); pts.append((float(x),float(y)))
    return pts
def proj(lon,lat): return (((lon+126)/60)*840, ((50.5-lat)/27)*430+12)
def draw_map(layer, cx, cy, scale, reveal=1.0, glow=1.0):
    dr=ImageDraw.Draw(layer,"RGBA")
    def T(x,y): return (cx+(x-420)*scale, cy+(y-235)*scale)
    poly=[T(*p) for p in parse(US_PATHS[0])]
    dr.polygon(poly, fill=(15,47,63,235), outline=(29,85,102,255))
    ga=int(140*glow); dr.line(poly+[poly[0]], fill=(95,202,191,ga), width=2)
    n=int(len(METROS)*clamp(reveal))
    for i,(lon,lat,c) in enumerate(METROS[:n]):
        x,y=proj(lon,lat); X,Y=T(x,y); r=5*scale*22/22
        col=CLIMATE[c]; dr.ellipse([X-r,Y-r,X+r,Y+r], fill=col+(255,))
    if reveal>0.85:
        x,y=proj(*PHILLY); X,Y=T(x,y); r=7*scale
        pulse=0.5+0.5*math.sin(reveal*20)
        dr.ellipse([X-r*2,Y-r*2,X+r*2,Y+r*2], outline=(243,220,166,int(120*pulse)), width=2)
        dr.ellipse([X-r,Y-r,X+r,Y+r], fill=GOLD+(255,))

# ---- helpers ----
def text(dr,xy,s,fnt,fill,anchor="mm",alpha=255,spacing=0):
    if len(fill)==3: fill=fill+(alpha,)
    if spacing:
        # manual letter spacing for kickers
        total=sum(dr.textlength(ch,font=fnt)+spacing for ch in s)-spacing
        x=xy[0]-total/2; y=xy[1]
        for ch in s:
            w=dr.textlength(ch,font=fnt); dr.text((x,y),ch,font=fnt,fill=fill,anchor="lm"); x+=w+spacing
    else:
        dr.text(xy,s,font=fnt,fill=fill,anchor=anchor)

def envelope(t,fin=0.16,fout=0.12):
    a=clamp(t/fin) if t<fin else (clamp((1-t)/fout) if t>1-fout else 1.0)
    return ease(a)

def rise(t, dist=26, d=0.0):
    p=ease(clamp((t-d)/0.5)); return (1-p)*dist, p

# ---- scenes (draw onto transparent layer; return) ----
def s_title(t):
    L=Image.new("RGBA",(W,H),(0,0,0,0)); dr=ImageDraw.Draw(L)
    floaty=math.sin(t*2)*6
    draw_map(L, W*0.5, H*0.46+floaty, 0.92, reveal=clamp(t*1.4), glow=1)
    a=int(255*envelope(t))
    dy,_=rise(t,d=0.05); text(dr,(W/2,H*0.66+dy),"RESEARCH DECISION-SUPPORT",SANSB(24),TEAL,alpha=int(a*0.95),spacing=8)
    dy,_=rise(t,d=0.2); text(dr,(W/2,H*0.74+dy),"Representative Location Explorer",SERIF(78),INK,alpha=a)
    dy,_=rise(t,d=0.45); text(dr,(W/2,H*0.84+dy),"Choose the right places to simulate America's buildings.",SANS(30),SUB,alpha=a)
    return L
def s_problem(t):
    L=Image.new("RGBA",(W,H),(0,0,0,0)); dr=ImageDraw.Draw(L); a=int(255*envelope(t))
    text(dr,(W/2,H*0.34),"THE PROBLEM",SANSB(24),TEAL,alpha=a,spacing=8)
    dy,_=rise(t,d=0.15); text(dr,(W/2,H*0.46+dy),"You can't simulate everywhere.",SERIF(66),INK,alpha=a)
    dy,_=rise(t,d=0.4); text(dr,(W/2,H*0.58+dy),"So which handful of places represent the whole country?",SANS(30),SUB,alpha=a)
    return L
def s_matrix(t):
    L=Image.new("RGBA",(W,H),(0,0,0,0)); dr=ImageDraw.Draw(L); a=int(255*envelope(t))
    text(dr,(W/2,H*0.20),"THE METHOD",SANSB(24),TEAL,alpha=a,spacing=8)
    text(dr,(W/2,H*0.30),"20 representative catchments",SERIF(60),INK,alpha=a)
    keys=["cold","dry","humid","marine","mixed"]; cols=4
    gw,gh,gap=120,52,14; gx0=W/2-(cols*gw+(cols-1)*gap)/2; gy0=H*0.40
    k=0
    for r,key in enumerate(keys):
        for c in range(cols):
            d=0.2+k*0.025; p=ease(clamp((t-d)/0.5))
            if p<=0: k+=1; continue
            x=gx0+c*(gw+gap); y=gy0+r*(gh+gap); col=CLIMATE[key]
            ca=int(a*p); sz=p
            cx,cy=x+gw/2,y+gh/2
            dr.rounded_rectangle([cx-gw/2*sz,cy-gh/2*sz,cx+gw/2*sz,cy+gh/2*sz],radius=8,
                                 fill=col+(int(210*p),), outline=(255,255,255,int(40*p)))
            k+=1
    # legend
    lx=W/2-520
    for key,name in zip(keys,["Cold & Very Cold","Hot-Dry & Mixed Dry","Hot-Humid","Marine","Mixed-Humid"]):
        text(dr,(lx,H*0.86),"",SANS(22),INK,alpha=a)
        dr.ellipse([lx,H*0.86-7,lx+14,H*0.86+7],fill=CLIMATE[key]+(a,))
        dr.text((lx+22,H*0.86),name,font=SANS(22),fill=SUB+(a,),anchor="lm"); lx+=ImageDraw.Draw(L).textlength(name,font=SANS(22))+60
    return L
def s_zip(t):
    L=Image.new("RGBA",(W,H),(0,0,0,0)); dr=ImageDraw.Draw(L); a=int(255*envelope(t))
    text(dr,(W/2,H*0.22),"ZIP CODES, DONE RIGHT",SANSB(24),TEAL,alpha=a,spacing=8)
    # card
    cw,ch=720,300; x0=W/2-cw/2; y0=H*0.30
    dr.rounded_rectangle([x0,y0,x0+cw,y0+ch],radius=22,fill=(255,255,255,16),outline=(255,255,255,40))
    text(dr,(W/2,y0+90),"19104",SERIF(92),INK,alpha=a,spacing=10)
    chips=[("ZCTA 19104",TEAL_D,False),("Philadelphia County",TEAL_D,False),("CBSA 37980",(201,154,56),True)]
    n=clamp((t-0.3)/0.5); shown=int(len(chips)*n+0.001)
    cxs=[W/2-230,W/2,W/2+250]
    for i,(label,col,gold) in enumerate(chips):
        if i>=shown: continue
        p=ease(clamp((t-0.3-i*0.12)/0.4)); cy=y0+200+(1-p)*12; ca=int(a*p)
        tw=dr.textlength(label,font=SANSB(22))+44
        bx=cxs[i]
        fill=(201,154,56,int(45*p)) if gold else (10,150,144,int(45*p))
        outl=(243,220,166,int(180*p)) if gold else (95,202,191,int(180*p))
        dr.rounded_rectangle([bx-tw/2,cy-22,bx+tw/2,cy+22],radius=20,fill=fill,outline=outl)
        dr.text((bx,cy),label,font=SANSB(22),fill=(INK if not gold else GOLD)+(ca,),anchor="mm")
    dy,_=rise(t,d=0.2); text(dr,(W/2,H*0.80+dy),"A ZIP is an entry point — never blurred into a boundary it isn't.",SANS(28),SUB,alpha=a)
    return L
def s_scenario(t):
    L=Image.new("RGBA",(W,H),(0,0,0,0)); dr=ImageDraw.Draw(L); a=int(255*envelope(t))
    text(dr,(W/2,H*0.22),"BUILD A SCENARIO",SANSB(24),TEAL,alpha=a,spacing=8)
    rows=[("Housing coverage",0.45),("Population density",0.35),("Population coverage",0.20),("Density screen",0.60)]
    bw=720; x0=W/2-bw/2+150; y=H*0.34
    for i,(lab,w) in enumerate(rows):
        yy=y+i*70
        dr.text((x0-170,yy),lab,font=SANS(24),fill=SUB+(a,),anchor="lm")
        dr.rounded_rectangle([x0,yy-9,x0+bw,yy+9],radius=10,fill=(255,255,255,26))
        p=ease(clamp((t-0.15-i*0.08)/0.7))
        fillw=bw*w*p
        if fillw>2:
            dr.rounded_rectangle([x0,yy-9,x0+fillw,yy+9],radius=10,fill=(10,150,144,a))
            dr.ellipse([x0+fillw-12,yy-13,x0+fillw+12,yy+13],fill=TEAL+(a,))
    dy,_=rise(t,d=0.3); text(dr,(W/2,H*0.82+dy),"Tune the weights and rules — a deterministic allocation updates instantly.",SANS(28),SUB,alpha=a)
    return L
def s_kpi(t):
    L=Image.new("RGBA",(W,H),(0,0,0,0)); dr=ImageDraw.Draw(L); a=int(255*envelope(t))
    # mini scatter, right
    rng=np.random.default_rng(7)
    keys=list(CLIMATE.values())
    for i in range(46):
        x=W*0.66+rng.random()*W*0.28; y=H*0.30+rng.random()*H*0.4
        col=keys[i%5]; r=3+rng.random()*3
        dr.ellipse([x-r,y-r,x+r,y+r],fill=col+(int(a*0.5),))
    text(dr,(W*0.40,H*0.30),"MEASURED TRADE-OFFS",SANSB(24),TEAL,alpha=a,spacing=8)
    val=99.7*ease(clamp((t-0.1)/0.5))
    text(dr,(W*0.40,H*0.48),f"{val:0.1f}%",SERIF(150),INK,alpha=a)
    text(dr,(W*0.40,H*0.62),"COVERAGE EFFICIENCY",SANSB(24),TEAL,alpha=a,spacing=6)
    dy,_=rise(t,d=0.35); text(dr,(W/2,H*0.84+dy),"Protect national coverage — keep 99.7% of the score. Every substitution shows why.",SANS(28),SUB,alpha=a)
    return L
def s_trust(t):
    L=Image.new("RGBA",(W,H),(0,0,0,0)); dr=ImageDraw.Draw(L); a=int(255*envelope(t))
    text(dr,(W/2,H*0.26),"TRANSPARENT BY DESIGN",SANSB(24),TEAL,alpha=a,spacing=8)
    items=[("Deterministic","Same inputs, same result"),("Reproducible","Versioned, exportable scenarios"),("Auditable","Exact simulation filters")]
    bw=380; gap=40; x0=W/2-(3*bw+2*gap)/2; y0=H*0.38; bh=230
    for i,(title,desc) in enumerate(items):
        p=ease(clamp((t-0.2-i*0.12)/0.5));
        if p<=0: continue
        x=x0+i*(bw+gap); ca=int(a*p); yo=(1-p)*18
        dr.rounded_rectangle([x,y0+yo,x+bw,y0+bh+yo],radius=18,fill=(255,255,255,int(16*p)),outline=(255,255,255,int(40*p)))
        cx=x+bw/2; cy=y0+70+yo
        dr.ellipse([cx-34,cy-34,cx+34,cy+34],outline=TEAL+(ca,),width=3,fill=(10,150,144,int(40*p)))
        dr.text((cx,cy),"✓",font=SANSB(40),fill=TEAL+(ca,),anchor="mm")
        dr.text((cx,cy+80),title,font=SANSB(30),fill=INK+(ca,),anchor="mm")
        dr.text((cx,cy+118),desc,font=SANS(20),fill=SUB+(ca,),anchor="mm")
    return L
def s_cta(t):
    L=Image.new("RGBA",(W,H),(0,0,0,0)); dr=ImageDraw.Draw(L); a=int(255*envelope(t))
    cx,cy=W/2,H*0.36
    p=ease(clamp(t/0.5)); r=46; ca=int(a*p)
    dr.rounded_rectangle([cx-r,cy-r,cx+r,cy+r],radius=18,outline=TEAL+(ca,),width=3,fill=(10,150,144,int(40*p)))
    # drawn location-pin glyph (teardrop + dot)
    dr.ellipse([cx-16,cy-20,cx+16,cy+12],outline=TEAL+(ca,),width=3)
    dr.polygon([(cx-9,cy+6),(cx+9,cy+6),(cx,cy+24)],fill=TEAL+(ca,))
    dr.ellipse([cx-6,cy-12,cx+6,cy],fill=TEAL+(ca,))
    dy,_=rise(t,d=0.2); text(dr,(cx,H*0.55+dy),"Representative Location Explorer",SERIF(60),INK,alpha=a)
    dy,_=rise(t,d=0.4); text(dr,(cx,H*0.65+dy),"Rigorous method, made inspectable.",SANS(30),SUB,alpha=a)
    # CTA pill
    p2=ease(clamp((t-0.5)/0.4));
    if p2>0:
        label="Explore it live  →"; tw=dr.textlength(label,font=SANSB(28))+64; by=H*0.78
        dr.rounded_rectangle([cx-tw/2,by-30,cx+tw/2,by+30],radius=30,fill=TEAL+(int(a*p2),))
        dr.text((cx,by),label,font=SANSB(28),fill=(6,35,31,int(a*p2)),anchor="mm")
    return L

SCENES=[(s_title,7.0),(s_problem,6.0),(s_matrix,7.0),(s_zip,7.0),(s_scenario,7.0),(s_kpi,7.0),(s_trust,6.0),(s_cta,6.0)]
TOTAL=sum(d for _,d in SCENES)

# ---- music bed ----
def make_music(seconds):
    sr=44100; n=int(sr*seconds); t=np.linspace(0,seconds,n,endpoint=False)
    chord=[146.83,220.0,277.18,329.63]; sig=np.zeros(n)
    for i,f in enumerate(chord):
        lfo=0.5+0.5*np.sin(2*np.pi*(0.05+i*0.013)*t)
        wave_=np.sin(2*np.pi*f*t)*(0.6 if i==0 else 0.3)
        sig+=wave_*(0.6+0.4*lfo)
    # gentle bell accents at scene starts
    acc=np.zeros(n); tt=0.0
    for _,d in SCENES:
        idx=int(tt*sr)
        if idx<n:
            env=np.exp(-np.linspace(0,4,min(sr*2,n-idx)))
            bell=np.sin(2*np.pi*880*np.linspace(0,2,len(env)))*env*0.08
            acc[idx:idx+len(env)]+=bell
        tt+=d
    sig=sig/np.max(np.abs(sig))*0.5+acc
    # fade in/out
    fi=int(sr*2); fo=int(sr*3)
    sig[:fi]*=np.linspace(0,1,fi); sig[-fo:]*=np.linspace(1,0,fo)
    sig=np.clip(sig,-1,1); pcm=(sig*32767*0.85).astype(np.int16)
    with wave.open(str(WAV),"w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())

def main():
    print(f"Rendering {TOTAL:.0f}s @ {FPS}fps ({int(TOTAL*FPS)} frames)…")
    make_music(TOTAL)
    cmd=["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
         "-i",str(WAV),"-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p",
         "-c:a","aac","-b:a","160k","-movflags","+faststart","-shortest",str(OUT)]
    proc=subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    bounds=[]; acc=0.0
    for fn,d in SCENES: bounds.append((acc,acc+d,fn)); acc+=d
    total_frames=int(TOTAL*FPS)
    for f in range(total_frames):
        T=f/FPS
        for a,b,fn in bounds:
            if a<=T<b:
                local=(T-a)/(b-a); layer=fn(local); break
        else:
            layer=bounds[-1][2](1.0)
        frame=BG.copy(); frame.alpha_composite(layer.convert("RGBA")) if frame.mode=="RGBA" else frame.paste(layer,(0,0),layer)
        proc.stdin.write(frame.convert("RGB").tobytes())
        if f%90==0: print(f"  {f}/{total_frames}")
    proc.stdin.close(); proc.wait()
    try:
        WAV.unlink(missing_ok=True)
    except OSError:
        pass  # some synced filesystems (e.g. OneDrive) block unlink; harmless
    print("Wrote", OUT, f"({OUT.stat().st_size//1024} KB)")

if __name__=="__main__":
    main()
