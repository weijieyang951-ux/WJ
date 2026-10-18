from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
PALETTES={'black_gold':('#090D15','#D9B66F','#F4F3ED'),'navy':('#071F38','#68D5EC','#FFFFFF'),'ivory':('#F3F0E8','#704F21','#182B43')}
def font(size):
    import os
    candidates=[os.getenv('POSTER_FONT',''),'/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']
    for p in candidates:
        if p and Path(p).exists(): return ImageFont.truetype(p,size)
    raise RuntimeError('Font required: install fonts-dejavu-core or set POSTER_FONT')
def draw_text(draw,xy,text,width,size,color):
    f=font(size)
    while draw.textbbox((0,0),text,font=f)[2]>width and size>16:
        size-=1; f=font(size)
    box=draw.textbbox(xy,text,font=f)
    if box[2]>xy[0]+width or box[3]>1920: raise ValueError('text overflow: '+text)
    draw.text(xy,text,font=f,fill=color)
    return {'text':text,'box':list(box)}
def poster(path,title,rows,day,next_day,simulated,template):
    bg,gold,white=PALETTES[template]; im=Image.new('RGB',(1080,1920),bg); d=ImageDraw.Draw(im); layout=[]
    def t(x,y,s,w=968,size=30,col=white): layout.append(draw_text(d,(x,y),s,w,size,col))
    t(56,48,'US EQUITY / DAILY RESEARCH',size=28,col=gold)
    t(56,105,title,size=59,col=gold); t(56,200,f'Close {day}  |  Outlook {next_day}',size=29)
    t(56,255,'SIMULATED DATA - NOT LIVE PRICES' if simulated else 'QUANTITATIVE RESEARCH - CONDITIONAL SCENARIOS',size=29,col=gold)
    d.line((56,325,1024,325),fill=gold,width=2)
    t(56,350,'TICKER / CLOSE / CHANGE',size=27); t(770,350,'OUTLOOK',w=254,size=27)
    for i,r in enumerate(rows[:15]):
        y=415+i*78
        t(56,y,r.symbol,w=210,size=32)
        t(300,y,f'${r.close:,.2f}',w=240,size=32)
        t(570,y,f'{r.change_pct:+.2f}%',w=185,size=32)
        t(800,y,{'看涨':'Bullish','震荡':'Neutral','看跌':'Bearish'}[r.outlook],w=224,size=31,col=gold)
        d.line((56,y+62,1024,y+62),fill='#38404A')
    if not rows: t(56,490,"No qualifying stocks in today's Top 300",size=36)
    bullish=sum(r.outlook=='看涨' for r in rows); bearish=sum(r.outlook=='看跌' for r in rows)
    view='Bullish bias; watch resistance' if bullish>bearish else 'Bearish bias; watch support' if bearish>bullish else 'Mixed signals; wait for confirmation'
    t(56,1645,'Sector: '+view,size=35,col=gold)
    t(56,1710,f'{len(rows)} stocks | Moving average and MACD signals',size=29)
    t(56,1765,'Missing news, social or earnings data are not inferred.',size=29)
    t(56,1828,'Research only | See full reports | No probability forecasts',size=25)
    im.save(path)
    with Image.open(path) as check:
        if check.size!=(1080,1920): raise ValueError('bad image size')
        check.verify()
    return layout
