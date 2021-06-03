function! GetTagStackFromFile (fname)
    let l:tstackdir = {}
    if filereadable (a:fname)

	let l:flist = readfile (a:fname)
	let l:fstr = join (l:flist, '')
	if len (l:fstr)
	    try
		let l:tstackdir = json_decode (l:fstr)
		let l:tstackdir = (type (l:tstackdir) != v:none)? l:tstackdir : {}
	    catch /^Vim(call):/
		let l:tstackdir = {}
	    endtry
	endif
    endif

    return l:tstackdir
endfunc

function! SetBufName (buftable, bufn)
    let a:buftable[a:bufn] = bufname (eval (a:bufn))
    return a:buftable[a:bufn]
endfunction

function! GetBufName (buftable, bufn)
    if a:buftable->has_key(a:bufn)
	return a:buftable[a:bufn]
    else
	return SetBufName (a:buftable, a:bufn)
    endif
endfunction

function! SaveStack (homedir, buf, buftable, blinetab)
    let l:tstackdir = GetTagStackFromFile (a:homedir . '/.tagstack.json')
    let wd = getcwd ()
    let wd = (wd[-1] != '/')? wd . '/' : wd
    for [owner,tstack] in a:buf->items()
	if len (tstack['items'])
	    for item in tstack['items']
		let key = substitute (fnamemodify (GetBufName (a:buftable, item['bufnr']), ':p'), wd, "", "")
		let item['bufnr'] = key
		let item['from'][0] = item['bufnr']
	    endfor
	    let oname = substitute (fnamemodify (GetBufName (a:buftable, owner), ':p'), wd, "", "")
	    let l:tstackdir[oname] = {}
	    let l:tstackdir[oname]['stack'] = tstack
	    let l:tstackdir[oname]['lfile'] = [0] + a:blinetab[tstack["lbuf"]]
	    let l:tstackdir[oname]['lfile'][0] = substitute (fnamemodify (GetBufName (a:buftable, tstack["lbuf"]), ':p'), wd, "", "")
	    call remove (tstack, "lbuf")

	else
	    let k = substitute (fnamemodify (owner, ':p'), wd, "", "")
	    if l:tstackdir->has_key(k)
		call remove (l:tstackdir, k)
	    endif
	endif
    endfor

    call writefile ([json_encode (l:tstackdir)], a:homedir . '/.tagstack.json')
endfunction

function! LoadStack (sdir = {}, key = '')
    
    let wd = getcwd ()
    let wd = (wd[-1] != '/')? wd . '/' : wd
    let l:tstackdir = (len (a:sdir) && type (a:sdir) == v:t_dict)? a:sdir : GetTagStackFromFile ((len(a:sdir) && type (a:sdir) == v:t_string)? a:sdir : wd . '/.tagstack.json')

    let l:bufname = (len (a:key))? a:key : substitute (expand ('%:p'), wd, "", "")

    if len (l:tstackdir)
	if has_key (l:tstackdir,l:bufname) && len (l:tstackdir[l:bufname]['stack']['items'])
	    let l:tstack = copy (l:tstackdir[l:bufname]['stack'])
	    for item in l:tstack['items']
		let item['bufnr'] = bufadd (item['bufnr'])
		let item['from'][0] = item['bufnr']
	    endfor
	    execute "edit " . l:tstackdir[l:bufname]['lfile'][0]
	    let l:tstackdir[l:bufname]['lfile'][0] = 0
	    call setpos (".", l:tstackdir[l:bufname]['lfile'])
	    call settagstack (winnr (), l:tstack, 'r')

	endif
    endif "non-empty

endfunction

function! CacheStack (buf)

    for info in getwininfo ()
	let stack = gettagstack (info["winid"])->copy()
	let stack["lbuf"] = info["bufnr"]
	if len (stack['items'])
	    let a:buf[stack['items'][0]['bufnr']] = stack
	else
	    let a:buf[info["bufnr"]] = stack
	endif
    endfor

endfunction

if !exists ("s:buftable")
    let s:buftable = {}
    let s:tstackdir = {}
    let s:blinetab = {}
		let s:dir = getcwd()
    "set cscopeverbose

    "execute 'cscope add ' . expand('<sfile>:h') . '/cscope.out ' . expand('<sfile>:h') . '/..'

    "set cscopetagorder=0

    "call LoadStack ('./.tagstack.json')

endif

augroup keepstack
    autocmd!
    autocmd BufLeave * let s:blinetab[bufnr ()] = [line ("."), col ("."), 0]
    autocmd BufWipeout * call SetBufName (s:buftable, expand ('<abuf>'))
    autocmd ExitPre * call SaveStack (s:dir, s:tstackdir, s:buftable, s:blinetab)
    autocmd QuitPre * let s:blinetab[bufnr ()] = [line ("."), col ("."), 0] | call CacheStack (s:tstackdir)
    autocmd TabNew * let s:blinetab[bufnr ()] = [line ("."), col ("."), 0]
    autocmd WinNew * let s:blinetab[bufnr ()] = [line ("."), col ("."), 0]
augroup END
