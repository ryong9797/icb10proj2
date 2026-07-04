1) HTTP 요청정보
Request URL
https://www.klook.com/v1/cardinfocenterservicesrv/search/platform/complete_search_v3?location=158%2C157%2C156%2C25723%2C5031%2C8928&sort=most_relevant&tab_key=0&start=1&query=%EB%8C%80%ED%95%9C%EB%AF%BC%EA%B5%AD&size=15&search_scope=main_search&k_lang=ko_KR&k_currency=KRW
Request Method
GET
Status Code
200 OK
Remote Address
104.18.31.170:443
Referrer Policy
strict-origin-when-cross-origin
2) HTTP 헤더정보
priority
u=1, i
referer
https://www.klook.com/ko/search/result/?query=%EB%8C%80%ED%95%9C%EB%AF%BC%EA%B5%AD&search_scope=main_search&location=158,157,156,25723,5031,8928&sort=most_relevant&tab_key=0&start=1
sec-ch-device-memory
16
sec-ch-ua
"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"
sec-ch-ua-arch
"x86"
sec-ch-ua-full-version-list
"Google Chrome";v="149.0.7827.115", "Chromium";v="149.0.7827.115", "Not)A;Brand";v="24.0.0.0"
sec-ch-ua-mobile
?0
sec-ch-ua-model
""
sec-ch-ua-platform
"Windows"
sec-fetch-dest
empty
sec-fetch-mode
cors
sec-fetch-site
same-origin
sentry-trace
5fcb3472498346cbadd12bedec34af02-b3ac22fd28a0c45c-0
token
user-agent
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36
version
5.6
x-klook-affiliate-aid
x-klook-affiliate-pid
x-klook-channel-level-one
SEM
x-klook-host
www.klook.com
x-klook-kepler-id
dd56adb9-3476-41d6-ae6e-03af1e3e41f6
x-klook-market
global
x-klook-page-open-id
x-klook-tint
{"kepler":["253:861","669:3215","684:3546","694:3667","695:3674","706:3783","732:4304","741:4469","761:4623","768:4732","778:4888","779:4897","780:4904","787:4996","788:5005","818:5278","822:5363","851:5735","853:5740","854:5751","855:5752","871:5974","877:6067","885:6186","901:6288","910:6455","931:6736","933:6751","936:9309","948:7023","969:7423","970:7425","978:7536","980:7551","994:7879","1006:8210","1016:8314","1017:8338","1020:8414","1038:8663","1058:9017","1084:9630","1091:9724","1128:10287","1147:10834","1171:11684","1172:11691","1180:11872","1191:12047","1193:12099","1205:12359","1206:12363","1209:12385","1219:12858","1226:13132","1229:13466","1233:13337","1243:13401","1245:13481","1264:13863","1295:15296","1298:15429","1304:15491","1309:15661","1315:15687","1334:16011","1339:16217","1340:16222","1350:16662","1351:16664","1358:16742","1364:16920","1369:17000","1371:17009","1372:17053","1375:17136","1378:17205","1379:17209","1382:17315","1386:17616","1397:18048","1487:20706","1522:22730","1533:21689","1537:21796","1572:22732","1573:22735","1574:22738","1599:23643","1600:23648","1602:24273","1604:24849","1605:23681","1606:23683","1663:31775","1664:24744","1665:30692","1666:25831","1691:26210","1692:26200","1693:26203","1694:26859","1695:26856","1696:26853","1697:25430","1702:25542","1741:29845","1748:30655","1749:30652","1887:30172","1901:30291","1903:30330","1909:30461","1914:32288","1915:30646","1916:32296","1918:30619","1919:30623","1921:30870","1922:30755","1926:30897","1930:30926","1956:31532","1963:31519","1992:32257","2003:32588","2014:32761","2016:32825","2018:32880","2019:32887","2022:32948","2031:33250","2058:33422","2074:33686","2078:33785","2079:33788","2080:33790","2081:33793","2082:33834"]}
x-klook-traffic-channel
google_sem
x-klook-user-residence
10_KR
x-platform
desktop
x-requested-with
XMLHttpRequest

3) Payload 정보
location=158%2C157%2C156%2C25723%2C5031%2C8928&sort=most_relevant&tab_key=0&start=1&query=%EB%8C%80%ED%95%9C%EB%AF%BC%EA%B5%AD&size=15&search_scope=main_search&k_lang=ko_KR&k_currency=KRW

4) 응답의 일부를 Response 에서 일부를 복사해서 넣어주기 (전체는 토큰 수 제한으로 어렵습니다.)

{
    "success": true,
    "error": {
        "code": "",
        "message": ""
    },
    "result": {
        "search_result": {
            "total": 1000,
            "cards": [
                {
                    "data": {


5) 한페이지가 성공적으로 수집되는지 확인하고 csv 파일로 저장할 것