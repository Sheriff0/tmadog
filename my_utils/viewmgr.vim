function! GetViewFromFile (fname)
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


if !exists ("SetBufName") && !exists ("GetBufName")
	function! SetBufName (buftable, bufn)
		let a:buftable[a:bufn] = bufname (eval (a:bufn))
		return a:buftable[a:bufn]
	endfunction


	function! SetWin2Bufn(win2bufn, winid, bufn, line, col)
		if (bufname(eval(a:bufn))->empty())
			return -1 
		endif
		let a:win2bufn[a:winid] = [a:line, a:col, 0, a:bufn]
	endfunction

	function! GetBufName (buftable, bufn)
		if a:buftable->has_key(a:bufn)
			return a:buftable[a:bufn]
		else
			return SetBufName (a:buftable, a:bufn)
		endif
	endfunction
endif

function! SaveView (homedir, buftable, wlinetab, win2bufn)
	let homedir = fnamemodify(a:homedir, ":p:h")
	let vdir = {}
	let view = []
	for tb in deepcopy (gettabinfo ())
		let tview = []
		for ww in tb["windows"]
			let windir = trim(system("realpath -Pe --relative-to=" . homedir . " " . getcwd (ww, tb["tabnr"]) . " 2>/dev/null"))

			if windir == "."
				let windir = ""
			endif

			let wd = getcwd () . "/\\|" . windir . "/"
			let stack = deepcopy (gettagstack (ww))
			let winfo = getwininfo (ww)[0]
			let lfile = trim(system("realpath -Pe --relative-to=" . homedir . " " . GetBufName (a:buftable, winfo["bufnr"]) . " 2>/dev/null"))
			
			let lineinfo = (a:wlinetab->has_key(ww))? a:wlinetab[ww] : []

			if lfile->empty() && a:win2bufn->has_key(ww)
				let lineinfo = a:win2bufn[ww]
				let bn = lineinfo->remove(-1)
				let lfile = trim(system("realpath -Pe --relative-to=" . homedir . " " . GetBufName (a:buftable, bn) . " 2>/dev/null"))

			elseif lfile->empty()
				continue
			endif

			for item in stack['items']
				let key = trim(system("realpath -P --relative-to=" . homedir . " " . GetBufName (a:buftable, item['bufnr']) . " 2>/dev/null"))
				let item['bufnr'] = key
				let item['from'][0] = item['bufnr']
			endfor
			let wview = [[lfile], windir, stack]

			if !(lineinfo->empty())
				let wview[0] += lineinfo
			else
				call add (wview[0], line (".", ww))
			endif

			call add(tview, wview)
		endfor
		call add(view, tview)
	endfor
	let vdir["view"] = view
	let vdir["cur_tw"] = [tabpagenr (), winnr ()]
	call writefile ([json_encode (vdir)], homedir . '/.view.json')
endfunction

function! LoadView (sdir = {}, dir = '')

	let vdir = (len (a:sdir) && type (a:sdir) == v:t_dict)? a:sdir : GetViewFromFile ((len(a:sdir) && type (a:sdir) == v:t_string)? a:sdir : wd . '/.view.json')

	let wlinetab = {}

	let dir = (a:dir->empty())? getcwd() : a:dir
	let dir = fnamemodify(dir, ":p:h")

	if !(vdir->empty())
		let FILE_UNREADABLE = 0
		let tbcount = 0
		let view = vdir["view"]
		if !len (bufname ())
			let opened = -1
			let tbcount += 1
		else
			let opened = 0
		endif

		for tb in deepcopy (view)
			for [f_cur, cwd, stack] in tb
				"NOTE: Do same readability checks for other view loaders
				if filereadable (dir . '/' . f_cur[0]) || isdirectory(dir . '/' . f_cur[0])
					let f_cur[0] = dir . "/" . f_cur[0]

				elseif filereadable(cwd . "/" . f_cur[0]) || isdirectory(cwd . "/" . f_cur[0])
					let f_cur[0] = cwd . "/" . f_cur[0]
				else
					continue
				endif

				for item in stack['items']
					if filereadable(dir . "/" . item['bufnr']) || isdirectory(dir . "/" . item["bufnr"])
						let item['bufnr'] = dir . "/" . item['bufnr']
					elseif filereadable(cwd . "/" . item['bufnr']) || isdirectory(cwd . "/" . item["bufnr"])
						let item['bufnr'] = cwd . "/" . item['bufnr']
					"else
					"	let FILE_UNREADABLE = 1
					"	break
					endif

					let item['bufnr'] = bufadd (item['bufnr'])
					let item['from'][0] = item['bufnr']
				endfor
				if FILE_UNREADABLE
					let FILE_UNREADABLE = 0
					continue
				endif
				if opened == 0
					execute "$tabnew " . f_cur[0]
					let opened = 1
					let tbcount += 1
				elseif opened == 1
					execute "below split " . f_cur[0]
				elseif opened == -1
					execute "edit " . f_cur[0]
					let opened = 1
				endif
				let wlinetab[win_getid ()] = f_cur[1:]

				try
					call execute("lcd " . dir . "/" . cwd)
				catch /.*/
					"pass
				endtry

				let f_cur[0] = 0
				call setpos (".", f_cur)
				"How about cwd?
				call settagstack (winnr (), stack, 'r')
			endfor
			let opened = 0
		endfor

		execute (len (gettabinfo ()) - tbcount) + min([vdir["cur_tw"][0],tbcount]) . "tabnext"
		execute "normal " . vdir["cur_tw"][1] . "\<c-w>w"
	endif
	return [vdir, wlinetab] 
endfunction

function! ReloadWinView (tabnr = v:none, winnr = v:none, dir = '')
	let dir = (a:dir->empty())? getcwd() : a:dir
	let tabnr = (a:tabnr->empty())? tabpagenr () : eval (a:tabnr)
	let winnr = (a:winnr->empty())? winnr () : eval (a:winnr)
	if !s:viewdir->empty() && type (s:viewdir) == v:t_dict
		let view = deepcopy (s:viewdir["view"])
		let lt = len (view)
		let tb = (tabnr > 0 && tabnr < lt)? view[tabnr-1] : (tabnr <= 0)? view[0] : view[-1]
		let [f_cur, cwd, stack] = (winnr > 0 && winnr < lt)? tb[winnr-1] : (winnr <= 0)? tb[0] : tb[-1]
		if filereadable(f_cur[0])
			"pass
		elseif filereadable(dir . "/" . f_cur[0])
			let f_cur[0] = dir . "/" . f_cur[0]
			let cwd = dir
		elseif filereadable(cwd . "/" . f_cur[0])
			let f_cur[0] = cwd . "/" . f_cur[0]
		else
			return -1
		endif

		for item in stack['items']
			if filereadable(item["bufnr"])
				"pass
			elseif filereadable(dir . "/" . item['bufnr'])
				let item['bufnr'] = dir . "/" . item['bufnr']
			elseif filereadable(cwd . "/" . item['bufnr'])
				let item['bufnr'] = cwd . "/" . item['bufnr']
			else
				return
			endif
			let item['bufnr'] = bufadd (item['bufnr'])
			let item['from'][0] = item['bufnr']
		endfor
		execute "below split " . f_cur[0]
		let f_cur[0] = 0
		call setpos (".", f_cur)
		try
			call execute("lcd " . cwd)
		catch /.*/
			"pass
		endtry

		call settagstack (winnr (), stack, 'r')

	endif
endfunction

function! ReloadTabView (tabnr = v:none, dir = '')

	let dir = (a:dir->empty())? getcwd() : a:dir

	let tabnr = (a:tabnr->empty())? tabpagenr () : eval (a:tabnr)
	if !(s:viewdir->empty()) && type (s:viewdir) == v:t_dict
		let view = deepcopy (s:viewdir["view"])
		let lt = len (view)
		let tb = (tabnr > 0 && tabnr < lt)? view[tabnr-1] : (tabnr <= 0)? view[0] : view[-1]

		let FILE_UNREADABLE = 0

		for [f_cur, cwd, stack] in tb
			if filereadable(f_cur[0])
				"pass
			elseif filereadable(dir . "/" . f_cur[0])
				let f_cur[0] = dir . "/" . f_cur[0]
				let cwd = dir
			elseif filereadable(cwd . "/" . f_cur[0])
				let f_cur[0] = cwd . "/" . f_cur[0]
			else
				continue
			endif
			for item in stack['items']
				if filereadable(item["bufnr"])
					"pass
				elseif filereadable(dir . "/" . item['bufnr'])
					let item['bufnr'] = dir . "/" . item['bufnr']
				elseif filereadable(cwd . "/" . item['bufnr'])
					let item['bufnr'] = cwd . "/" . item['bufnr']
				else
					let FILE_UNREADABLE = 1
					break
				endif
				let item['bufnr'] = bufadd (item['bufnr'])
				let item['from'][0] = item['bufnr']
			endfor

			if FILE_UNREADABLE
				let FILE_UNREADABLE = 0
				continue
			endif

			execute "below split " . f_cur[0]
			let f_cur[0] = 0
			call setpos (".", f_cur)
			try
				call execute("lcd " . cwd)
			catch /.*/
				"pass
			endtry

			call settagstack (winnr (), stack, 'r')
		endfor
	endif
endfunction

if !exists ("s:wlinetab")
	let s:lastab = 0
	let s:buftable = {}
	let s:win2bufn = {}
	let s:viewdir = './.view.json'
	let s:dir = getcwd()
	let [s:viewdir, s:wlinetab] =  LoadView (s:viewdir, s:dir)

	function Goto_lastab()
		if s:lastab > 0
			execute "tabnext " . s:lastab
		endif
	endfunction



	function Poptab()
		if s:lastab > 0
			execute "tabnext " . s:lastab
		endif
	endfunction


	function Pushtab()
		if s:lastab > 0
			execute "tabnext " . s:lastab
		endif
	endfunction


	nmap Tt :call Goto_lastab()<CR><Esc>

endif

augroup keepview
	autocmd!
	autocmd TabLeave * let s:lastab = tabpagenr()
	autocmd BufWipeout * let s:wlinetab[win_getid ()] = [line ("."), col ("."), 0] | call SetBufName (s:buftable, expand ('<abuf>')) | call SetWin2Bufn(s:win2bufn, win_getid(), expand('<abuf>'), line("."), col("."))
	autocmd BufLeave * let s:wlinetab[win_getid ()] = [line ("."), col ("."), 0] | call SetWin2Bufn(s:win2bufn, win_getid(), expand('<abuf>'), line("."), col("."))
	autocmd BufEnter * let s:wlinetab[win_getid ()] = [line ("."), col ("."), 0] | call SetWin2Bufn(s:win2bufn, win_getid(), expand('<abuf>'), line("."), col("."))
	autocmd ExitPre * let s:wlinetab[win_getid ()] = [line ("."), col ("."), 0] | call SetWin2Bufn(s:win2bufn, win_getid(), expand('<abuf>'), line("."), col(".")) | call SaveView (s:dir, s:buftable, s:wlinetab, s:win2bufn)
	autocmd TabNew * let s:wlinetab[win_getid ()] = [line ("."), col ("."), 0] | call SetWin2Bufn(s:win2bufn, win_getid(), expand('<abuf>'), line("."), col("."))
	autocmd WinNew * let s:wlinetab[win_getid ()] = [line ("."), col ("."), 0] | call SetWin2Bufn(s:win2bufn, win_getid(), expand('<abuf>'), line("."), col("."))
	autocmd QuitPre * let s:wlinetab[win_getid ()] = [line ("."), col ("."), 0] | call SetWin2Bufn(s:win2bufn, win_getid(), expand('<abuf>'), line("."), col("."))
	autocmd WinLeave * let s:wlinetab[win_getid ()] = [line ("."), col ("."), 0] | call SetWin2Bufn(s:win2bufn, win_getid(), expand('<abuf>'), line("."), col("."))
augroup END
