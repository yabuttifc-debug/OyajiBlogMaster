# -*- coding: utf-8 -*-
"""eスポーツ大会ブログ紹介リール（縦9:16）を生成"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio.v2 as imageio

W, H = 1080, 1920
FPS = 30
D = 12  # クロスフェード長(フレーム)

IMGDIR = Path(r"Image/20260619_eスポーツ/blurred")
OUT = Path(r"Image/20260619_eスポーツ/eスポーツ大会_reel.mp4")
FONT = r"C:\Windows\Fonts\BIZ-UDGothicB.ttc"

def font(sz): return ImageFont.truetype(FONT, sz, index=0)

PURPLE=(94,53,177); INDIGO=(40,53,147); BLUE1=(21,101,192); BLUE2=(13,71,161)
RED=(198,40,40); WHITE=(255,255,255)

def vgrad(top, bottom):
    a=np.linspace(0,1,H)[:,None]
    row=(np.array(top)[None,:]*(1-a)+np.array(bottom)[None,:]*a)
    return np.tile(row[:,None,:],(1,W,1)).astype(np.uint8)

def cover(im, tw, th):
    iw,ih=im.size; s=max(tw/iw, th/ih)
    im=im.resize((int(iw*s)+1,int(ih*s)+1), Image.LANCZOS)
    iw,ih=im.size; l=(iw-tw)//2; t=(ih-th)//2
    return im.crop((l,t,l+tw,t+th))

def kenburns(base_big, p):
    # base_big は (W*1.12, H*1.12)。p:0->1 でゆっくりズームイン
    z=1.0+0.12*p
    bw,bh=base_big.size
    cw,ch=bw/z, bh/z
    l=(bw-cw)/2; t=(bh-ch)/2
    return base_big.crop((int(l),int(t),int(l+cw),int(t+ch))).resize((W,H),Image.LANCZOS)

def shadow_text(d, xy, text, fnt, fill=WHITE, anchor="mm", sh=(0,0,0)):
    x,y=xy
    for dx,dy in [(-2,2),(2,2),(2,-2),(-2,-2),(0,3)]:
        d.text((x+dx,y+dy),text,font=fnt,fill=sh,anchor=anchor)
    d.text((x,y),text,font=fnt,fill=fill,anchor=anchor)

def bottom_scrim(img):
    # 下部に黒のグラデーションを重ねて文字を読みやすく
    ov=Image.new("L",(W,H),0); od=ImageDraw.Draw(ov)
    for i in range(640):
        y=H-640+i; a=int(200*(i/640))
        od.line([(0,y),(W,y)],fill=a)
    black=Image.new("RGB",(W,H),(0,0,0))
    return Image.composite(black,img,ov)

# ---- 各シーン定義 ----
def title_frame(p):
    bg=Image.fromarray(vgrad(PURPLE,INDIGO))
    # 上に開会写真をうっすら
    photo=cover(Image.open(IMGDIR/"01_始まり.jpg").convert("RGB"),W,int(H*0.55))
    bg.paste(photo,(0,int(H*0.16)))
    bg=Image.composite(Image.new("RGB",(W,H),(30,20,70)),bg,Image.new("L",(W,H),120))
    d=ImageDraw.Draw(bg)
    shadow_text(d,(W//2,int(H*0.30)),"BLOG UPDATE",font(54),fill=(255,224,80))
    shadow_text(d,(W//2,int(H*0.40)),"eスポーツ大会",font(132))
    shadow_text(d,(W//2,int(H*0.49)),"2026",font(150),fill=(255,224,80))
    # 紅白バー
    d.rounded_rectangle([W//2-360,int(H*0.57),W//2+360,int(H*0.57)+96],28,fill=(255,255,255))
    shadow_text(d,(W//2,int(H*0.57)+48),"紅白対抗・大逆転の大熱戦！",font(46),fill=PURPLE,sh=(255,255,255))
    shadow_text(d,(W//2,int(H*0.66)),"箕輪小学校おやじの会",font(44))
    return np.array(bg)

def photo_scene(fname, tag, caption, base_cache={}):
    if fname not in base_cache:
        base_cache[fname]=cover(Image.open(IMGDIR/fname).convert("RGB"),int(W*1.12),int(H*1.12))
    big=base_cache[fname]
    def render(p):
        img=kenburns(big,p)
        img=bottom_scrim(img)
        d=ImageDraw.Draw(img)
        if tag:
            tw=d.textlength(tag,font=font(40))
            d.rounded_rectangle([60,150,60+tw+56,150+74],20,fill=RED)
            d.text((60+28,150+37),tag,font=font(40),fill=WHITE,anchor="lm")
        # キャプション(自動改行)
        cap_f=font(66); words=caption.split("\n")
        y=H-300
        for line in words:
            shadow_text(d,(60,y),line,cap_f,anchor="lm")
            y+=88
        shadow_text(d,(60,H-90),"箕輪小おやじの会ブログ",font(36),fill=(230,230,230))
        return np.array(img)
    return render

def end_frame(p):
    bg=Image.fromarray(vgrad(BLUE1,BLUE2))
    d=ImageDraw.Draw(bg)
    shadow_text(d,(W//2,int(H*0.26)),"当日の写真を",font(90))
    shadow_text(d,(W//2,int(H*0.335)),"ブログで公開中！",font(90),fill=(255,224,80))
    shadow_text(d,(W//2,int(H*0.45)),"プロフィールのリンク",font(56))
    shadow_text(d,(W//2,int(H*0.50)),"からチェック",font(56))
    # 次回告知カード
    d.rounded_rectangle([90,int(H*0.60),W-90,int(H*0.74)],32,fill=(255,255,255))
    shadow_text(d,(W//2,int(H*0.635)),"NEXT EVENT",font(40),fill=RED,sh=(255,255,255))
    shadow_text(d,(W//2,int(H*0.685)),"7/25(土) みずでっぽう大会",font(52),fill=BLUE2,sh=(255,255,255))
    shadow_text(d,(W//2,int(H*0.815)),"#箕輪小おやじの会 #eスポーツ大会",font(38),fill=(220,235,255))
    return np.array(bg)

# ---- タイムライン ----
scenes=[
    ("fn", title_frame, 96),
    ("fn", photo_scene("01_始まり.jpg","OPENING","全学年で\n紅白対抗戦！"), 78),
    ("fn", photo_scene("03_マリオ.jpg","種目①","マリオカートで\nバトル！"), 66),
    ("fn", photo_scene("05_テニス.jpg","種目②","白熱のテニス\nラリー対決"), 66),
    ("fn", photo_scene("05_バンバン.jpg","種目③","シューティング\nバンバンバンディッツ"), 66),
    ("fn", photo_scene("06_同点.jpg","CLIMAX","決勝で\nまさかの同点…！"), 78),
    ("fn", photo_scene("07_サドンデス.jpg","SUDDEN DEATH","サドンデスへ\n突入！"), 72),
    ("fn", photo_scene("08_表彰式.jpg","WINNER","白組が大逆転で\n優勝！！"), 90),
    ("fn", end_frame, 108),
]

print("rendering...")
writer=imageio.get_writer(str(OUT),fps=FPS,codec="libx264",quality=8,
                          macro_block_size=8,ffmpeg_params=["-pix_fmt","yuv420p"])
prev_last=None
for _,render,N in scenes:
    last=render(1.0)
    for j in range(N):
        fr=render(j/max(N-1,1))
        if prev_last is not None and j<D:
            a=j/D
            fr=(prev_last*(1-a)+fr*a).astype(np.uint8)
        writer.append_data(fr)
    prev_last=last
writer.close()
print("done:", OUT, "/ 約", round(sum(n for _,_,n in scenes)/FPS,1), "秒")
