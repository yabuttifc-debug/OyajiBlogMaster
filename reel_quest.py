# -*- coding: utf-8 -*-
"""クエストウォーク2026 in 日吉 テレビ放送告知リール（縦9:16・グラフィック）"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio.v2 as imageio

W, H = 1080, 1920
FPS = 30
D = 12
OUT = Path(r"Image/クエストウォーク/クエストウォーク2026_TV放送_reel.mp4")
FONT = r"C:\Windows\Fonts\BIZ-UDGothicB.ttc"
def font(sz): return ImageFont.truetype(FONT, sz, index=0)

NAVY1=(26,18,60); NAVY2=(12,10,38); PURPLE=(94,53,177)
GOLD=(255,206,64); RED=(214,40,57); WHITE=(255,255,255); CYAN=(120,220,255)

def vgrad(top, bottom):
    a=np.linspace(0,1,H)[:,None]
    row=(np.array(top)[None,:]*(1-a)+np.array(bottom)[None,:]*a)
    return np.tile(row[:,None,:],(1,W,1)).astype(np.uint8)

def shadow_text(d, xy, text, fnt, fill=WHITE, anchor="mm", sh=(0,0,0)):
    x,y=xy
    for dx,dy in [(-2,2),(2,2),(2,-2),(-2,-2),(0,3)]:
        d.text((x+dx,y+dy),text,font=fnt,fill=sh,anchor=anchor)
    d.text((x,y),text,font=fnt,fill=fill,anchor=anchor)

def draw_qmarks(d, p, seed=0):
    rng=np.random.RandomState(seed)
    for i in range(14):
        bx=rng.uniform(0,W); by=rng.uniform(0,H); sz=int(rng.uniform(40,140))
        drift=(np.sin(p*2*np.pi+i)*18)
        col=(60,48,120) if i%2 else (48,40,100)
        d.text((bx, by+drift), "?", font=font(sz), fill=col, anchor="mm")

def tv_icon(d, cx, cy, s, col=GOLD):
    d.rounded_rectangle([cx-s, cy-s*0.66, cx+s, cy+s*0.66], int(s*0.12), outline=col, width=10)
    d.line([cx-s*0.4, cy+s*0.66, cx-s*0.15, cy+s*0.95], fill=col, width=10)
    d.line([cx+s*0.4, cy+s*0.66, cx+s*0.15, cy+s*0.95], fill=col, width=10)

def glass_icon(d, cx, cy, r, col=CYAN):
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=col, width=12)
    d.line([cx+r*0.7, cy+r*0.7, cx+r*1.5, cy+r*1.5], fill=col, width=16)

def zoom(img, p):
    z=1.0+0.05*p
    bw,bh=img.size; cw,ch=bw/z, bh/z
    l=(bw-cw)/2; t=(bh-ch)/2
    return img.crop((int(l),int(t),int(l+cw),int(t+ch))).resize((W,H),Image.LANCZOS)

def base_card(): return Image.fromarray(vgrad(NAVY1,NAVY2))

def title_frame(p):
    img=base_card(); d=ImageDraw.Draw(img); draw_qmarks(d,p,seed=1)
    bw=300
    d.rounded_rectangle([W//2-bw//2,int(H*0.135),W//2+bw//2,int(H*0.135)+88],44,fill=RED)
    shadow_text(d,(W//2,int(H*0.135)+44),"ON AIR",font(54),fill=WHITE,sh=RED)
    shadow_text(d,(W//2,int(H*0.255)),"テレビ放送",font(118))
    shadow_text(d,(W//2,int(H*0.325)),"されました！",font(118),fill=GOLD)
    tv_icon(d,W//2,int(H*0.435),96)
    shadow_text(d,(W//2,int(H*0.535)),"クエストウォーク2026",font(74),fill=GOLD)
    shadow_text(d,(W//2,int(H*0.595)),"in 日吉",font(74),fill=GOLD)
    shadow_text(d,(W//2,int(H*0.68)),"イッツコム（iTSCOM）で紹介されました",font(42),fill=CYAN)
    return np.array(zoom(img,p))

def scene2(p):
    img=base_card(); d=ImageDraw.Draw(img); draw_qmarks(d,p,seed=4)
    glass_icon(d,W//2,int(H*0.25),110)
    shadow_text(d,(W//2,int(H*0.40)),"「500年後のSOSに応答せよ」",font(56),fill=CYAN)
    shadow_text(d,(W//2,int(H*0.485)),"5校合同の謎解きウォーク！",font(66))
    shadow_text(d,(W//2,int(H*0.575)),"日吉・綱島エリアを",font(60))
    shadow_text(d,(W//2,int(H*0.63)),"親子で歩いて謎を解く",font(60))
    shadow_text(d,(W//2,int(H*0.72)),"2026.5.16（土）開催",font(64),fill=GOLD)
    return np.array(zoom(img,p))

def scene3(p):
    img=base_card(); d=ImageDraw.Draw(img); draw_qmarks(d,p,seed=7)
    shadow_text(d,(W//2,int(H*0.20)),"↑ @ プロフィール",font(50),fill=CYAN)
    tv_icon(d,W//2,int(H*0.30),110,col=CYAN)
    shadow_text(d,(W//2,int(H*0.47)),"見逃した方も大丈夫！",font(76),fill=GOLD)
    shadow_text(d,(W//2,int(H*0.575)),"プロフィールのリンクから",font(62))
    shadow_text(d,(W//2,int(H*0.635)),"放送動画をチェック",font(62))
    return np.array(zoom(img,p))

def end_frame(p):
    img=Image.fromarray(vgrad(PURPLE,NAVY2)); d=ImageDraw.Draw(img); draw_qmarks(d,p,seed=9)
    shadow_text(d,(W//2,int(H*0.37)),"GREEN×EXPO 2027 連動企画",font(48),fill=CYAN)
    shadow_text(d,(W//2,int(H*0.47)),"クエストウォーク2026",font(78),fill=GOLD)
    shadow_text(d,(W//2,int(H*0.53)),"in 日吉",font(70),fill=GOLD)
    shadow_text(d,(W//2,int(H*0.64)),"また遊びに来てね！",font(58))
    shadow_text(d,(W//2,int(H*0.73)),"主催：日吉台小・箕輪小おやじの会",font(42))
    return np.array(zoom(img,p))

scenes=[(title_frame,96),(scene2,96),(scene3,84),(end_frame,90)]

print("rendering...")
writer=imageio.get_writer(str(OUT),fps=FPS,codec="libx264",quality=8,
                          macro_block_size=8,ffmpeg_params=["-pix_fmt","yuv420p"])
prev_last=None
for render,N in scenes:
    last=render(1.0)
    for j in range(N):
        fr=render(j/max(N-1,1))
        if prev_last is not None and j<D:
            a=j/D; fr=(prev_last*(1-a)+fr*a).astype(np.uint8)
        writer.append_data(fr)
    prev_last=last
writer.close()
print("done:", OUT, "/ 約", round(sum(n for _,n in scenes)/FPS,1),"秒")
