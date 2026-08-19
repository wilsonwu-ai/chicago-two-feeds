#!/usr/bin/env python3
"""Compose the guide body from the research data and splice it into src/page.html.

Every string that reaches the page exists in both English and Chinese. Nothing here
invents a fact: fields absent from the research render as absent, not as filler.
"""
import html, json, pathlib, re, sys
from gridcoord import grid_caption

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "src" / "data"
PAGE = ROOT / "src" / "page.html"

CN_DIR = {"N": "麦迪逊街以北", "S": "麦迪逊街以南", "E": "州街以东", "W": "州街以西"}


def e(s):
    return html.escape(str(s or ""), quote=True)


def load(name, default=None):
    p = DATA / name
    if not p.exists():
        if default is None:
            sys.exit(f"FAIL: missing data file {name}")
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def bi(en, zh, cls=""):
    """A bilingual inline pair. Renders nothing at all if both sides are empty."""
    en, zh = (en or "").strip(), (zh or "").strip()
    if not en and not zh:
        return ""
    c = f' class="{cls}"' if cls else ""
    return (f"<span{c}>" if cls else "") + (
        f'<span class="en">{e(en or zh)}</span><span class="zh">{e(zh or en)}</span>'
    ) + ("</span>" if cls else "")


def block(tag, en, zh, cls=None):
    en, zh = (en or "").strip(), (zh or "").strip()
    if not en and not zh:
        return ""
    c = f' class="{cls}"' if cls else ""
    return (f'<{tag}{c}><span class="en">{e(en or zh)}</span>'
            f'<span class="zh">{e(zh or en)}</span></{tag}>')



# The research populated closed_days inconsistently: some rows hold a genuine closure
# ("Closed Tuesdays"), some hold opening hours, and some hold placeholders. Labelling
# them all "Closed" produced "Closed open daily", so classify before rendering.
_NO_INFO = re.compile(r"^(n/?a|none|check hours|open 7 days|open daily|unknown|-+)\.?$", re.I)
_DAY = r"(mon|tues?|wed(nes)?|thur?s?|fri|sat(ur)?|sun)(day)?s?"
_STARTS_CLOSED = re.compile(rf"^\s*(closed\b|{_DAY}\b\s*(,|and|\+|plus|$))", re.I)
_STARTS_HOURS = re.compile(r"^\s*(open\b|hours\b|daily\b)", re.I)


def hours_chip(raw):
    """Return (english, chinese) for the closed_days field, or None when it says nothing.

    The field arrived heterogeneous -- real closures, opening hours and placeholders --
    so a blanket "Closed" prefix produced "Closed open daily". Only prefix when the
    value actually begins with a closure; sentences that explain themselves pass through.
    """
    v = (raw or "").strip().rstrip(".")
    if not v or _NO_INFO.match(v):
        return None
    low = v.lower()
    if low.startswith("none") or low.startswith("never closed"):
        return None
    if _STARTS_CLOSED.match(v):
        body = re.sub(r"^closed\s+", "", v, flags=re.I)
        return f"Closed {body}", f"休 {body}"
    if _STARTS_HOURS.match(v):
        return f"Hours: {v}", f"营业: {v}"
    return v, v


STAR_PTS = ("50.00,0.00 62.00,29.22 93.30,25.00 74.00,50.00 93.30,75.00 62.00,70.78 "
            "50.00,100.00 38.00,70.78 6.70,75.00 26.00,50.00 6.70,25.00 38.00,29.22")

TIER_STARS = {"essential": 3, "strong": 2, "niche": 1}
TIER_LABEL = {"essential": ("Essential", "必去"), "strong": ("Worth it", "值得去"),
              "niche": ("Specific interest", "看兴趣")}


def star_svg(cls="star"):
    return f'<svg class="{cls}" viewBox="0 0 100 100" aria-hidden="true"><use href="#cstar"/></svg>'


def render_rail(p, tier):
    src = p.get("source", "tiktok")
    src_cls = {"tiktok": "src-tt", "xhs": "src-xhs", "both": "src-both"}[src]
    src_txt = {"tiktok": ("TikTok", "TikTok"), "xhs": ("小红书", "小红书"),
               "both": ("Both", "两边都有")}[src]
    n = TIER_STARS.get(tier, 1)
    tl = TIER_LABEL.get(tier, TIER_LABEL["niche"])
    stars = "".join(star_svg() for _ in range(n))

    gc = grid_caption(p.get("address", ""))
    if gc:
        coord, cap = gc
        d = coord.split()[-1]
        cap_zh = "≈" + cap.split(" mi ")[0] + " 英里 · " + CN_DIR[d]
        grid = (f'<div class="grid-coord">{e(coord)}'
                f'<span class="en">≈{e(cap)}</span><span class="zh">{e(cap_zh)}</span></div>')
    else:
        grid = ""

    return (f'<div class="rail">'
            f'<span class="src {src_cls}"><span class="en">{e(src_txt[0])}</span>'
            f'<span class="zh">{e(src_txt[1])}</span></span>'
            f'<span class="tier" title="{e(tl[0])}" role="img" '
            f'aria-label="{e(tl[0])}">{stars}</span>'
            f'{grid}</div>')


def render_entry(p, tier):
    head = (f'<div class="entry-head"><h3>{e(p["name"])}</h3>'
            + (f'<span class="zh-name">{e(p.get("name_zh"))}</span>' if p.get("name_zh") else "")
            + "</div>")

    parts = [head]
    parts.append(block("p", p.get("signature"), p.get("signature_zh"), "sig"))
    parts.append(block("p", p.get("why"), p.get("why_zh"), "why"))
    parts.append(block("p", p.get("tip"), p.get("tip_zh"), "tip"))

    cav_en, cav_zh = (p.get("caveat") or "").strip(), (p.get("caveat_zh") or "").strip()
    if cav_en or cav_zh:
        parts.append(
            f'<p class="caveat"><b><span class="en">The catch —</span>'
            f'<span class="zh">注意 —</span></b> '
            f'<span class="en">{e(cav_en or cav_zh)}</span>'
            f'<span class="zh">{e(cav_zh or cav_en)}</span></p>')

    meta = []
    if p.get("neighborhood"):
        meta.append(f'<span class="en">{e(p["neighborhood"])}</span>'
                    f'<span class="zh">{e(p.get("neighborhood_zh") or p["neighborhood"])}</span>')
    if p.get("per_person"):
        meta.append(f'<span class="zh">{e(p["per_person"])}</span>'
                    f'<span class="en">{e(p.get("price_band") or p["per_person"])}</span>')
    elif p.get("price_band"):
        meta.append(f"<span>{e(p['price_band'])}</span>")
    if p.get("rating_note"):
        meta.append(f'<span class="rating">{e(p["rating_note"])}</span>')
    chip = hours_chip(p.get("closed_days"))
    if chip:
        meta.append(f'<span class="en">{e(chip[0])}</span><span class="zh">{e(chip[1])}</span>')
    if p.get("address"):
        meta.append(f"<span>{e(p['address'])}</span>")
    metahtml = ('<div class="meta label">' + "".join(f"<span>{m}</span>" for m in meta) + "</div>"
                ) if meta else ""
    parts.append(metahtml)

    return ('<article class="entry">' + render_rail(p, tier)
            + '<div class="body-col">' + "".join(x for x in parts if x) + "</div></article>")


def section(num, id_, title_en, title_zh, lede_en, lede_zh, body):
    return f"""<section id="{id_}">
<div class="wrap">
<div class="sec-head">
<p class="label"><span class="num">{num}</span> &nbsp;<span class="en">{e(title_en.upper())}</span><span class="zh">{e(title_zh)}</span></p>
{block("h2", title_en, title_zh)}
{block("p", lede_en, lede_zh, "lede")}
</div>
{body}
</div>
</section>"""


def entries_block(items, tiers):
    if not items:
        return ""
    return ('<div class="entries">'
            + "".join(render_entry(p, tiers.get(p["name"], "strong")) for p in items)
            + "</div>")


# ---------------------------------------------------------------- static copy
def kv(en, zh):
    return {"en": en, "zh": zh}


LOGISTICS_CARDS = [
    ("Getting in from the airport", "从机场进城", [
        kv("Blue Line runs 24/7 from inside O'Hare to the Loop. 40-50 minutes, <b>$5.00</b> flat. Rideshare is roughly $35-65+ and no faster in traffic.",
           "蓝线 24 小时从奥黑尔机场直达市中心，40-50 分钟，统一 <b>$5.00</b>。打车大约 $35-65 以上，堵起来并不更快。"),
        kv("From Midway, the Orange Line reaches the Loop in 25-30 minutes at the standard rail fare. It does <b>not</b> run 24 hours.",
           "中途机场坐橙线到市中心 25-30 分钟，普通票价。橙线<b>不是</b> 24 小时运营。"),
    ]),
    ("Paying for transit", "交通怎么付钱", [
        kv("You do not need a Ventra card. Tap a contactless credit card or Apple/Google Pay straight onto the reader at any turnstile or bus farebox.",
           "不需要办 Ventra 卡。直接用带感应功能的信用卡或 Apple/Google Pay 在闸机、公交刷卡机上一拍就行。"),
        kv("Bus <b>$2.25</b>. Rail <b>$2.50</b>. Blue Line originating at O'Hare <b>$5.00</b>.",
           "公交 <b>$2.25</b>，地铁 <b>$2.50</b>，从奥黑尔上车的蓝线 <b>$5.00</b>。"),
        kv("1-, 3-, 7- and 30-day unlimited passes exist. We could not verify current 2026 prices, so check transitchicago.com/fares rather than trusting a number here.",
           "有 1 天、3 天、7 天、30 天的不限次通票。我们没能核实 2026 年的现价，请自己查 transitchicago.com/fares，不要信这里给的数字。"),
    ]),
    ("Attraction passes", "景点通票", [
        kv("<b>CityPASS</b> is $144 adult / $114 child, valid 9 days. Shedd and Skydeck are compulsory, then you pick three more. It works only if you genuinely want five paid attractions.",
           "<b>CityPASS</b> 成人 $144、儿童 $114，9 天有效。谢德水族馆和西尔斯塔是固定的，再从名单里选三个。只有你真的想去五个收费景点时才划算。"),
        kv("<b>Go City Explorer</b> from $109 lets you choose how many attractions, 30 days to use them. The more flexible of the two.",
           "<b>Go City Explorer</b> $109 起，自己选去几个景点，30 天内用完，是两者中更灵活的。"),
        kv("<b>Go City All-Inclusive</b> from $149 is the one to be sceptical of. It is priced assuming four to six attractions a day, which almost nobody actually does while also eating, walking and resting.",
           "<b>Go City All-Inclusive</b> $149 起，这个要多留个心眼。它的定价假设你一天刷四到六个景点，而实际上你还要吃饭、走路、休息，几乎没人做得到。"),
    ]),
    ("When to come", "什么时候来", [
        kv("Late May to early October is the reliable window. June, July and September are the sweet spot: warm, long daylight, and every river cruise and outdoor attraction running.",
           "5 月底到 10 月初是稳妥的窗口。6 月、7 月、9 月最舒服：暖和、白天长，游船和户外项目全部正常运营。"),
        kv("Winter is a real constraint, not a minor inconvenience. December to February sits in the low-to-mid 30s°F with lows in the teens, and the wind off the lake makes it worse.",
           "冬天是实打实的限制，不是小小的不方便。12 月到 2 月最高温只有 0°C 上下，最低到零下十度左右，湖上的风还会让体感更冷。"),
        kv("Book the architecture river cruise one to two weeks ahead for a peak-season weekend. A few days is usually enough midweek.",
           "旺季周末的建筑游船要提前一到两周订。平日提前几天一般就够。"),
        kv("Museum free days are frequently restricted to Illinois residents with ID. Read the fine print before you build a day around one.",
           "博物馆的免费日经常只限伊利诺伊州居民并要查证件。别为了免费日安排一整天，先看清楚条款。"),
    ]),
    ("Money", "花钱", [
        kv("Tip 18-20% at sit-down restaurants. 15% now reads as a below-average tip.",
           "正式餐厅小费 18-20%。给 15% 现在会被理解成\"不太满意\"。"),
        kv("Chicago's combined sales tax is 10.5%, among the highest of any major US city, and downtown restaurant bills run higher still.",
           "芝加哥的综合销售税是 10.5%，在美国大城市里数一数二，市中心餐厅的账单还要更高。"),
        kv("Many restaurants now add an automatic 3-5% service or kitchen fee <b>on top of tax and separate from your tip</b>. Check the bill before you tip again.",
           "很多餐厅现在会自动加 3-5% 的服务费或后厨费，<b>是在税之外、也和小费分开的</b>。再给小费之前先看一眼账单。"),
    ]),
]

SAFETY = [
    kv("Chicago is a normal major US city for visitors. The Loop, River North, Streeterville, Lincoln Park, Lakeview, Wicker Park, West Loop and Hyde Park are all standard tourist ground.",
       "对游客来说芝加哥就是一座普通的美国大城市。卢普区、河北区、Streeterville、林肯公园、Lakeview、Wicker Park、西环、海德公园都是常规游客区。"),
    kv("<b>\"Avoid the South Side\" is bad geography, and this guide's own Xiaohongshu source repeated it.</b> Hyde Park is on the South Side, and it holds the University of Chicago and the Griffin Museum of Science and Industry. It is a normal place to spend a day.",
       "<b>\"别往南边走\"这个说法在地理上就是错的，而这份攻略的小红书来源恰好也这么讲。</b>海德公园就在南边，芝加哥大学和科学与工业博物馆都在那儿，去待一天完全正常。"),
    kv("The precaution that is actually well documented is car break-ins. Lock a rental car and leave nothing visible inside.",
       "真正有据可查的风险是车辆被砸。租来的车一定锁好，车里不要留任何看得见的东西。"),
    kv("Use ordinary late-night judgement on the CTA, particularly the Red Line in the small hours. That is a reason to pay attention, not a reason to avoid the trains.",
       "深夜坐 CTA 保持基本警觉，尤其是凌晨的红线。这是让你留意，不是让你不坐地铁。"),
]


def logistics_section():
    cards = []
    for en, zh, items in LOGISTICS_CARDS:
        lis = "".join(f'<li><span class="en">{en_}</span><span class="zh">{zh_}</span></li>'
                      for en_, zh_ in ((i["en"], i["zh"]) for i in items))
        cards.append(f'<div class="card">{block("h3", en, zh)}'
                     f'<ul class="tight">{lis}</ul></div>')
    safety = "".join(f'<li><span class="en">{i["en"]}</span><span class="zh">{i["zh"]}</span></li>'
                     for i in SAFETY)
    return ('<div class="cards">' + "".join(cards) + "</div>"
            + f'<div class="note" style="margin-top:var(--s5)">'
            + block("h3", "On safety", "关于安全")
            + f'<ul class="tight">{safety}</ul></div>')


FEEDS = [
    ("The unit of recommendation differs", "推荐的单位不一样",
     "TikTok recommends a <b>dish</b>. Xiaohongshu recommends a <b>visit</b>. A Chicago TikTok hit is forty-five seconds on one item, and viewers arrive ordering that and nothing else. An XHS note is structured as a whole outing: 人均, the room, the photo angle, parking.",
     "TikTok 推荐的是<b>一道菜</b>，小红书推荐的是<b>一次出行</b>。芝加哥的 TikTok 爆款就是 45 秒讲一样东西，看完的人到店只点那一样。小红书笔记则是一整趟安排：人均、环境、出片点、停车。"),
    ("They optimise for different frames", "两边优化的是不同的画面",
     "TikTok needs motion and sound — the cheese pull, the crunch, the pour. Xiaohongshu needs a still frame — 出片 lighting, a wood-toned room, a window seat with skyline. That pushes the two feeds toward genuinely different venues.",
     "TikTok 要的是动态和声音：拉丝、脆响、浇汁。小红书要的是一张静态照片：出片的光线、木色调的空间、能拍到天际线的窗边位。这让两边推的店从根上就不一样。"),
    ("The cuisine skew is real", "菜系上的偏差是真实存在的",
     "Xiaohongshu's Chicago is heavily Chinese and East Asian — Chinatown, hotpot, Korean Lakeview, boba, omakase as the splurge. TikTok's Chicago is American-viral — Italian beef, deep dish, tavern thin crust, birria, smash burgers. Use one feed only and you get a genuinely incomplete city.",
     "小红书的芝加哥重心在中餐和东亚菜：中国城、火锅、Lakeview 的韩餐、奶茶，贵一点就是日料 omakase。TikTok 的芝加哥是美式爆款：意式牛肉、深盘、酒吧薄脆、birria、smash burger。只看一边，你拿到的是一座不完整的城市。"),
    ("They go stale in opposite directions", "两边过期的方式正好相反",
     "TikTok churns fast, so the risk is arriving after the viral moment collapsed — or at a second location that is nothing like the original. Xiaohongshu ranks on accumulated saves, so a three-year-old note still sits at the top for a restaurant that has changed chef, price or owner. Ask TikTok <i>is this still hot</i>, and Xiaohongshu <i>is this still true</i>.",
     "TikTok 更新极快，风险是你到的时候热度已经过去了，或者去的是和本店完全不一样的二店。小红书按收藏量排序，所以三年前的笔记还挂在最上面，而那家店可能早就换了厨师、涨了价、易了主。对 TikTok 要问<i>还火吗</i>，对小红书要问<i>还准吗</i>。"),
    ("Only one of them tells you the price and the queue", "只有一边会告诉你价格和排队",
     "Xiaohongshu states 人均 as a matter of convention, and routinely gives 排队 tactics by time of day. TikTok almost never states a price — a $28 sandwich and a $9 sandwich look identical on camera — and shows the line as social proof rather than telling you how to avoid it.",
     "小红书写人均几乎是惯例，还会告诉你几点去排队最短。TikTok 基本不提价格——$28 的三明治和 $9 的在镜头里长得一样——而且拍队伍是为了证明它火，不是为了教你怎么避开。"),
]


def feeds_section():
    rows = "".join(
        f'<div class="card">{block("h3", t_en, t_zh)}'
        f'<p><span class="en">{b_en}</span><span class="zh">{b_zh}</span></p></div>'
        for t_en, t_zh, b_en, b_zh in FEEDS)
    return f'<div class="cards">{rows}</div>'


def plans_section(plans):
    if not plans:
        return ""
    out = []
    for pl in sorted(plans, key=lambda x: x.get("days", 0)):
        d = pl.get("days")
        stops = "".join(
            f'<div class="stop"><div class="t">{e(s.get("time",""))}</div>'
            f'<div><div class="n">{e(s.get("name",""))}</div>'
            f'<div class="r"><span class="en">{e(s.get("reason",""))}</span>'
            f'<span class="zh">{e(s.get("reason_zh") or s.get("reason",""))}</span></div></div></div>'
            for s in pl.get("stops", []))
        assumes = ""
        if pl.get("assumes"):
            assumes = (f'<p class="label"><span class="en">{e(pl["assumes"])}</span>'
                       f'<span class="zh">{e(pl.get("assumes_zh") or pl["assumes"])}</span></p>')
        out.append(f'<div class="card">'
                   f'{block("h3", f"{d} day" + ("s" if d != 1 else ""), f"{d} 天")}'
                   f'{assumes}<div class="plan">{stops}</div></div>')
    return f'<div class="cards plans">{"".join(out)}</div>'


def skip_section(items):
    if not items:
        return ""
    rows = "".join(
        f'<div class="skip-row"><b>{e(s.get("name",""))}</b>'
        f'<div class="r"><span class="en">{e(s.get("reason",""))}</span>'
        f'<span class="zh">{e(s.get("reason_zh") or s.get("reason",""))}</span></div></div>'
        for s in items)
    return f'<div class="skip">{rows}</div>'


HOWTO = [
    ("Where it came from", "这条是哪来的",
     "Every entry carries the feed that surfaced it. Nothing is blended into one anonymous list, because the two sources are wrong in different ways and you should be able to weight them yourself.",
     "每一条都标了是哪个平台推出来的。这里不把两边混成一个匿名清单，因为它们出错的方式不一样，你应该能自己判断该信几分。"),
    ("How much it matters", "有多值得去",
     "Three stars is essential on a two-day trip. Two is worth it with more time. One is for a specific interest. The stars are the Chicago flag's, and on the flag each one stands for a particular event rather than a rating.",
     "三颗星是两天行程里必去的，两颗星是时间宽裕再去，一颗星是有特定兴趣才去。星星取自芝加哥市旗——在旗上每颗星代表一个具体事件，而不是评分。"),
    ("Where it is", "它在哪儿",
     "Chicago numbers addresses outward from State &amp; Madison, 800 units to the mile, so the number in an address states exactly how far that door sits from the centre line. We show the block and the distance along that one axis — not straight-line distance, and diagonal streets like Archer and Clybourn cut across the grid.",
     "芝加哥的门牌号以州街和麦迪逊街交叉口为原点向外编号，800 号等于一英里，所以地址里的数字本身就说明了这扇门离中轴线有多远。我们标的是街区号和沿<b>这一个方向</b>的距离，不是直线距离；而且像 Archer、Clybourn 这样的斜街是斜穿网格的。"),
]



# Hand-verified cross-feed matches. Fuzzy name matching produced a false positive here
# (Phoenix Restaurant in Chinatown vs Garden of the Phoenix in Jackson Park are different
# places), so the pairs below are checked by address rather than by string similarity.
MERGE_GROUPS = [
    ["Cloud Gate (The Bean)", 'Cloud Gate ("The Bean")'],
    ["Chicago Riverwalk", "Chicago Riverwalk / Urban Kayaks",
     "Chicago Riverwalk viewpoints / Promontory Point"],
    ["LH Rooftop", "LH Rooftop, LondonHouse Chicago"],
    ["Skydeck Chicago (Willis Tower)", "Skydeck Chicago - The Ledge", "Willis Tower Skydeck"],
    ["Chicago Architecture River Cruise",
     "Chicago Architecture River Cruise (Wendella / CAC First Lady)"],
    ["360 CHICAGO", "360 CHICAGO - TILT",
     "360 CHICAGO (John Hancock Center observation deck) + TILT",
     "360 Chicago (John Hancock Observatory) \u2014 TILT"],
    ["Starbucks Reserve Roastery", "World's Largest Starbucks Reserve Roastery"],
    ["Portillo's", "Chicago-style Hot Dog (Portillo's River North)", "Portillo's River North"],
    ["Lao Sze Chuan", "Lao Sze Chuan (Chinatown)"],
    ["Garfield Park Conservatory"], ["Navy Pier"], ["Art Institute of Chicago"],
    ["Pequod's Pizza"],
]

RICHER = ("why", "why_zh", "signature", "signature_zh", "tip", "tip_zh",
          "caveat", "caveat_zh", "rating_note", "address", "closed_days",
          "per_person", "price_band", "name_zh", "neighborhood_zh")


def merge_feeds(xhs, tik, editorial_dupes):
    """Collapse the same place appearing in both feeds into one entry stamped 'both'."""
    groups = [list(g) for g in MERGE_GROUPS]
    for d in editorial_dupes or []:
        groups.append([d["canonical"]] + list(d.get("fold_in", [])))

    by_name = {}
    order = []
    for p in xhs + tik:
        if p["name"] not in by_name:
            order.append(p["name"])
        by_name.setdefault(p["name"], []).append(p)

    alias = {}
    for g in groups:
        present = [n for n in g if n in by_name]
        if len(present) < 2:
            continue
        head = present[0]
        for other in present[1:]:
            alias[other] = head

    out, done = [], set()
    for name in order:
        head = alias.get(name, name)
        if head in done:
            continue
        done.add(head)
        members = list(by_name.get(head, []))
        for other, h in alias.items():
            if h == head:
                members.extend(by_name.get(other, []))
        if not members:
            continue

        base = dict(members[0])
        base["name"] = head
        for m in members[1:]:
            for f in RICHER:
                if len((m.get(f) or "")) > len((base.get(f) or "")):
                    base[f] = m[f]
        # Ratings differ by platform (Google vs Yelp) and both are true. Keeping only the
        # longer string dropped real numbers, so union them instead.
        seen_r, rated = set(), []
        for m in members:
            rn = (m.get("rating_note") or "").strip()
            if rn and rn.lower() not in seen_r:
                seen_r.add(rn.lower())
                rated.append(rn)
        if rated:
            base["rating_note"] = "  ·  ".join(rated)
        srcs = {m.get("source", "tiktok") for m in members}
        base["source"] = "both" if len(srcs) > 1 else members[0].get("source", "tiktok")
        out.append(base)
    return out


def main():
    xhs = load("xhs_source.json")
    tik = load("tiktok_entries.json", [])
    ed = load("editorial.json", {})
    meta = load("tiktok_meta.json", {"dropped": [], "sweeps": []})

    tiers = {t["name"]: t["tier"] for t in ed.get("tiers", [])}

    places = merge_feeds(xhs, tik, ed.get("duplicates", []))

    def pick(pred):
        return sorted([p for p in places if pred(p)],
                      key=lambda p: (TIER_STARS.get(tiers.get(p["name"], "strong"), 2) * -1, p["name"]))

    chinatown = pick(lambda p: p.get("neighborhood") == "Chinatown")
    ct_names = {p["name"] for p in chinatown}
    food = pick(lambda p: p["category"] == "food" and p["name"] not in ct_names)
    attractions = pick(lambda p: p["category"] == "attraction" and p["name"] not in ct_names)
    views = pick(lambda p: p["category"] in ("photo", "nightlife", "drink")
                 and p["name"] not in ct_names)
    sweets = pick(lambda p: p["category"] in ("dessert", "neighborhood", "shopping")
                  and p["name"] not in ct_names)

    n_ess = sum(1 for t in tiers.values() if t == "essential")
    stats = [
        (str(len(places)), "places, each checked against live sources", "个地点，逐一对照实时来源核过"),
        (str(len(meta.get("dropped", []))), "dropped in verification", "个在核实阶段被删掉"),
        ("2", "feeds, kept separate", "个平台，分开标注"),
        ("0", "external requests on this page", "个外部请求"),
    ]
    stat_html = "".join(
        f'<div class="stat"><b>{e(n)}</b>'
        f'<span class="label en">{e(en)}</span><span class="label zh">{e(zh)}</span></div>'
        for n, en, zh in stats)

    howto = "".join(f'<div class="card">{block("h3", a, b)}'
                    f'<p><span class="en">{c}</span><span class="zh">{d}</span></p></div>'
                    for a, b, c, d in HOWTO)

    ct = load("chinatown.json", {})
    ct_note = ""
    if ct.get("getting_there"):
        ct_note = (f'<div class="note" style="margin-bottom:var(--s5)">'
                   f'{block("h3", "Getting there", "怎么去")}'
                   f'<p><span class="en">{e(ct["getting_there"][:400])}</span>'
                   f'<span class="zh">红线坐到 Cermak-Chinatown 站。从卢普区出发向南约 8 分钟，'
                   f'班次约 10 分钟一趟，24 小时运营。出站后走半个街区就是牌坊。</span></p></div>')

    body = f"""<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><symbol id="cstar" viewBox="0 0 100 100"><polygon points="{STAR_PTS}" fill="currentColor"/></symbol></svg>

<header class="topbar">
<div class="topbar-in">
<span class="brand">{star_svg()}<b><span class="en">Two Feeds, One City</span><span class="zh">两个算法，一座芝加哥</span></b></span>
<span class="ctrl" role="group" aria-label="Language">
<button type="button" data-lang="en" aria-pressed="true">EN</button>
<button type="button" data-lang="zh" aria-pressed="false">中文</button>
</span>
<span class="ctrl" role="group" aria-label="Theme">
<button type="button" data-theme="auto" aria-pressed="true" title="Match system">Auto</button>
<button type="button" data-theme="light" aria-pressed="false" title="Light">Light</button>
<button type="button" data-theme="dark" aria-pressed="false" title="Dark">Dark</button>
</span>
</div>
</header>

<div class="wrap">
<div class="hero">
<hr class="flagrule">
<div class="eyebrow" style="margin-top:var(--s5)">
<span class="label">Chicago &nbsp;/&nbsp; 芝加哥</span>
<span class="label"><span class="en">Field guide</span><span class="zh">实地攻略</span> &nbsp;/&nbsp; 2026</span>
</div>
<h1><span class="en">Two Feeds,<br>One <span class="accent">City.</span></span><span class="zh">两个算法，<br>一座<span class="accent">芝加哥。</span></span></h1>
<p class="lede"><span class="en">Xiaohongshu and TikTok recommend measurably different Chicagos. This guide keeps both and tells you which feed sent you — because they are wrong in different ways, and knowing which one is talking is most of the skill of using either.</span><span class="zh">小红书和 TikTok 推荐的，其实是两个不一样的芝加哥。这份攻略两边都收，并且告诉你每一条是从哪边来的——因为它们出错的方式不同，而分得清是谁在说话，本身就是用好它们的关键。</span></p>
<div class="stats">{stat_html}</div>
</div>
</div>

{section("01", "how", "How to read this", "怎么看这份攻略",
         "Three things sit in the left margin of every entry.",
         "每条目左边一栏有三样东西。", f'<div class="cards">{howto}</div>')}

{section("02", "before", "Before you go", "出发之前",
         "Fares, passes, weather and the tipping arithmetic — including the parts our own sources got wrong.",
         "票价、通票、天气和小费算法——包括我们自己的来源讲错的部分。", logistics_section())}

{section("03", "food", "Food", "吃",
         "Restaurants outside Chinatown, which has its own section below.",
         "中国城以外的餐厅，中国城单独一节放在下面。", entries_block(food, tiers))}

{section("04", "chinatown", "Chinatown", "中国城",
         "One of the few Chinatowns in the United States still growing rather than shrinking.",
         "全美少数几个还在扩张而不是萎缩的中国城之一。", ct_note + entries_block(chinatown, tiers))}

{section("05", "see", "Attractions & museums", "景点与博物馆",
         "Check the closed days before you build a day around any of these.",
         "围着其中任何一个安排一天之前，先确认闭馆日。", entries_block(attractions, tiers))}

{section("06", "views", "Views, rooftops & photo spots", "机位、顶楼与天际线",
         "Where to actually stand, and at what hour.",
         "具体站在哪儿，几点站。", entries_block(views, tiers))}

{section("07", "sweets", "Dessert, cafés & neighbourhoods", "甜点、咖啡与街区",
         "The category both feeds push hardest, and the one where hype and quality diverge most.",
         "两个平台推得最凶的一类，也是热度和实际水平差最远的一类。", entries_block(sweets, tiers))}

{section("08", "plans", "If you only have a few days", "只有几天的话",
         "Routed so the walking works, and so you do not arrive on a closed day.",
         "按地理动线排的，顺便避开闭馆日。", plans_section(ed.get("day_plans", [])))}

{section("09", "skip", "What to skip", "可以跳过的",
         "Popular things that do not repay the time.",
         "很红但不值得花时间的。", skip_section(ed.get("skip_list", [])))}

{section("10", "feeds", "Where the two feeds disagree", "两个平台的分歧在哪",
         "The differences are structural, not random. They follow from what each platform rewards.",
         "这些差异是结构性的，不是随机的，源自两个平台各自奖励什么。", feeds_section())}

<footer>
<div class="wrap">
<hr class="flagrule thin" style="margin-bottom:var(--s6)">
<div class="prose">
{block("h3", "How this was made", "这份攻略是怎么做的")}
<p><span class="en">Seven parallel research sweeps covered TikTok from different angles; a separate pass covered Xiaohongshu. Every candidate was then handed to a verification step that checked it against live sources — open or closed, current rating, address, closed days — with instructions to drop rather than keep when the evidence did not hold. {len(meta.get('dropped', []))} places were dropped that way, including one permanently closed and one closing in September 2026.</span><span class="zh">七路并行的检索从不同角度覆盖 TikTok，另有一路覆盖小红书。所有候选地点都进了核实环节，对照实时来源逐条检查——是否还开着、当前评分、地址、休息日——并且明确要求证据不足时删掉而不是保留。这样删掉了 {len(meta.get('dropped', []))} 个地点，其中一个已永久关闭，一个将在 2026 年 9 月关闭。</span></p>
<p><span class="en">Both language versions are written, not machine-translated. Where a fact could not be verified, the page says so rather than filling the gap — CTA multi-day pass prices are the clearest example.</span><span class="zh">两种语言都是分别写的，不是机器翻译。凡是核不实的信息，页面会直接说明，而不是拿东西填上——CTA 多日通票的价格就是最明显的例子。</span></p>
<p><span class="en">Ratings and opening hours move. Treat every number here as of August 2026 and check anything you are building a day around. This page makes no external requests and sets no cookies.</span><span class="zh">评分和营业时间会变。这里所有数字都是 2026 年 8 月的状态，凡是要围着它安排一整天的，请自己再确认一次。本页面不发起任何外部请求，也不设置 cookie。</span></p>
</div>
</div>
</footer>

<script>
(function () {{
  var root = document.documentElement;
  function setLang(l) {{
    root.lang = l;
    try {{ localStorage.setItem('cg-lang', l); }} catch (err) {{}}
    document.querySelectorAll('[data-lang]').forEach(function (b) {{
      b.setAttribute('aria-pressed', String(b.dataset.lang === l));
    }});
  }}
  function setTheme(t) {{
    if (t === 'auto') root.removeAttribute('data-theme');
    else root.setAttribute('data-theme', t);
    try {{ localStorage.setItem('cg-theme', t); }} catch (err) {{}}
    document.querySelectorAll('[data-theme]').forEach(function (b) {{
      if (b.tagName === 'BUTTON') b.setAttribute('aria-pressed', String(b.dataset.theme === t));
    }});
  }}
  document.addEventListener('click', function (ev) {{
    var b = ev.target.closest('button[data-lang], button[data-theme]');
    if (!b) return;
    if (b.dataset.lang) setLang(b.dataset.lang);
    else setTheme(b.dataset.theme);
  }});
  var sl, st;
  try {{ sl = localStorage.getItem('cg-lang'); st = localStorage.getItem('cg-theme'); }} catch (err) {{}}
  setLang(sl === 'zh' ? 'zh' : 'en');
  setTheme(st === 'light' || st === 'dark' ? st : 'auto');
}})();
</script>"""

    page = PAGE.read_text(encoding="utf-8")
    if "<!-- @BODY -->" in page:
        page = re.sub(r"<!-- @BODY -->.*?<!-- @/BODY -->", "", page, flags=re.S)
    page = page.rstrip() + "\n\n<!-- @BODY -->\n" + body + "\n<!-- @/BODY -->\n"
    PAGE.write_text(page, encoding="utf-8")

    print(f"places rendered: {len(places)}  (xhs {len(xhs)} + tiktok {len(tik)}, deduped)")
    print(f"  food {len(food)} | chinatown {len(chinatown)} | attractions {len(attractions)} "
          f"| views {len(views)} | sweets/hoods {len(sweets)}")
    print(f"  essential {n_ess} | plans {len(ed.get('day_plans', []))} | skip {len(ed.get('skip_list', []))}")
    print(f"body spliced into {PAGE.name}")


if __name__ == "__main__":
    main()
