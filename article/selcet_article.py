import requests
import json
from lxml import etree
import js2py
from login import login
from config import USERNAME, PASSWORD
COOKIES = login(USERNAME, PASSWORD )
HEADERS = {
    'Cookies': COOKIES
}
text = requests.get("https://www.tadu.com/book/catalogue/1004090").text

html = etree.HTML(text)

hrefs = html.xpath('//div[@class="chapter clearfix"]/a/@href')

article_id=[herf.split('/')[-2] for herf in hrefs]

js_code = """
function encipher(e) {
    var a = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
      , t = "="
      , o = function(e) {
        var o, s = "", i = e.length;
        for (o = 0; i - 2 > o; o += 3)
            s += a[e.charCodeAt(o) >> 2],
            s += a[((3 & e.charCodeAt(o)) << 4) + (e.charCodeAt(o + 1) >> 4)],
            s += a[((15 & e.charCodeAt(o + 1)) << 2) + (e.charCodeAt(o + 2) >> 6)],
            s += a[63 & e.charCodeAt(o + 2)];
        return i % 3 && (o = i - i % 3,
        s += a[e.charCodeAt(o) >> 2],
        i % 3 == 2 ? (s += a[((3 & e.charCodeAt(o)) << 4) + (e.charCodeAt(o + 1) >> 4)],
        s += a[(15 & e.charCodeAt(o + 1)) << 2],
        s += t) : (s += a[(3 & e.charCodeAt(o)) << 4],
        s += t + t)),
        s
    };
    return o(e)
}
"""
encipher = js2py.eval_js(js_code)


for i in range(len(article_id)):
    print(i)
    datalimit = encipher(article_id[i])
    response = requests.get(f"https://www.tadu.com/getPartContentByCodeTable/1004090/{i+1}", headers=HEADERS)

    data = json.loads(response.text)

    content = data['data']['content']

    # print(content)
    html = etree.HTML(content)
    text = html.xpath(f'//p[not(contains(@data-limit, "{datalimit}"))]/text()')
    for t in text:
        print(t)






