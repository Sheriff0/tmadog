rc = r"""
[retros]
rumbu = tqatri
xstore = trextri

[events]
suspendables = TMA\W+COMING\W+SOON!
crs_skip = GST
page_skip = not\W+yet\W+ready\W+for,Contact\W+\[email\Wprotected\],VISIT\W+NOUN\W+GST\W+PAGE,Please\W+try\W+again\W+NX
traps = not\W+ready\W+for\W+now 
on_qst_submit = mark\W+for\W+question
on_complete = You\W+have\W+already\W+complete
on_cookie = Checking\W+your\W+browser
on_login_needed = login\W+first
on_incorrect_login = incor?rect\W+username\W+or\W+pas?sword,not\W+allowed

[describe]
crscode = (?P<cs>[A-Za-z]{3})\d{3}(?!\d+)
matno = (?P<cs>nou)\d{9}
tma = (?<=tma)[1-3]

[tmafile]
units: --,http,${describe:crscode},${describe:matno},^[1-3]$$

[kmap]
usr = [Matric Number]
pwd = [Password]


[home_page]
path = /:
requires =
volatile =
indices = 0

[login_page]
keys = ${kmap:usr}/${kmap:pwd}
indices = 0
path = Login
volatile =
requires = home_page

[logout_page]
path = Logout
indices = 0
requires = profile_page
volatile =

[qst_page]
path = Take TMA,TMA[1-3]
indices = 0,0
requires = profile_page
volatile = logout_page

[tma_page]
path = Take TMA
indices = 0
volatile = logout_page
requires = profile_page

[quiz_list]
path = 2020/2 Slips
indices = 0
requires = profile_page
volatile = logout_page

[profile_page]
path = ${login_page:keys}
indices = 0
requires = login_page
volatile = logout_page

[qmap]
qdescr = qdescr
ans = ans
score = totscore
qn = qj
crscode = crscode
qid = qid
opta = opta
optb = optb
optc = optc
optd = optd
pseudo_ans = A,B,C,D
""";
