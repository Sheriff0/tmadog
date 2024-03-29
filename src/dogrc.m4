[retros]
rumbu = tqatri
xstore = trextri

[fb]
on_qst_submit = mark for question

[kmap]
matno = [Matric Number]
pwd = [Password]


[home_page]
path = /
requires =
volatile =
indices = 0

[login_page]
keys = ${kmap:matno}/${kmap:pwd}
indices = 0
path = Login
volatile =
requires = home_page

[logout_page]
path = Logout
indices = 0
requires = tma_page
volatile =

[qst_page]
path = TMA2
indices = 0
requires = tma_page
volatile = logout_page

[tma_page]
path = TMA2,${login_page:keys}
indices = 0,0
volatile = logout_page
requires = home_page

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
