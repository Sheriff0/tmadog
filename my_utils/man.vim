" Vim filetype plugin file
" Language:	man
" Maintainer:	SungHyun Nam <goweol@gmail.com>
" Last Change: 	2019 Sep 26
"		(fix by Jason Franklin)

" To make the ":Man" command available before editing a manual page, source
" this script from your startup vimrc file.

" If 'filetype' isn't "man", we must have been called to only define ":Man".
if &filetype == "man"

  " Only do this when not done yet for this buffer
  if exists("b:did_ftplugin")
    finish
  endif
  let b:did_ftplugin = 1
endif

let s:dev='ascii'
for var in [$LC_ALL, $LANG]
  if var =~? 'utf\W\?8'
    let s:dev='utf8'
    break
  endif
endfor

let s:cpo_save = &cpo
set cpo-=C

if &filetype == "man"
  " allow dot and dash in manual page name.
  setlocal iskeyword+=\.,-
  let b:undo_ftplugin = "setlocal iskeyword<"

  " Add mappings, unless the user didn't want this.
  if !exists("no_plugin_maps") && !exists("no_man_maps")
    if !hasmapto('<Plug>ManBS')
      nmap <buffer> <LocalLeader>h <Plug>ManBS
      let b:undo_ftplugin = b:undo_ftplugin
	    \ . '|silent! nunmap <buffer> <LocalLeader>h'
    endif
    nnoremap <buffer> <Plug>ManBS :%s/.\b//g<CR>:setl nomod<CR>''

    nnoremap <buffer> <c-]> :silent call <SID>PreGetPage(v:count)<CR>
    nnoremap <buffer> <c-t> :silent call <SID>PopPage()<CR>
    nnoremap <buffer> <silent> q :q<CR>

    " Add undo commands for the maps
    let b:undo_ftplugin = b:undo_ftplugin
	  \ . '|silent! nunmap <buffer> <Plug>ManBS'
	  \ . '|silent! nunmap <buffer> <c-]>'
	  \ . '|silent! nunmap <buffer> <c-t>'
	  \ . '|silent! nunmap <buffer> q'
  endif

  if exists('g:ft_man_folding_enable') && (g:ft_man_folding_enable == 1)
    setlocal foldmethod=indent foldnestmax=1 foldenable
    let b:undo_ftplugin = b:undo_ftplugin
	  \ . '|silent! setl fdm< fdn< fen<'
  endif

endif

if exists(":Man") != 2
  com -bang -count=0 -nargs=1 -complete=shellcmd Man call s:GetPageM(<q-count>, <q-args>, <q-mods>, <q-bang>)
  nmap <Leader>K :silent call <SID>PreGetPage(0)<CR>
  nmap <Plug>ManPreGetPage :silent call <SID>PreGetPage(0)<CR>
endif

" Define functions only once.
if !exists("s:man_tag_depth")

let s:man_tag_depth = 0

let s:man_sect_arg = ""
let s:man_find_arg = "-w"
try
  if !has("win32") && $OSTYPE !~ 'cygwin\|linux' && system('uname -s') =~ "SunOS" && system('uname -r') =~ "^5"
    let s:man_sect_arg = "-s"
    let s:man_find_arg = "-l"
  endif
catch /E145:/
  " Ignore the error in restricted mode
endtry

func <SID>PreGetPage(cnt)
	let old_isk = &iskeyword
	let pre = substitute(expand("%:t"), '\(^[^:]\+:\+\).*$', '\1', '')
	let pre = (pre[len(pre)-1] != ":")? "" : pre

  if a:cnt == 0
		exec "setl iskeyword+=(,)" . (!(pre->empty())? "," . pre[len(pre)-1] : "") 
    let str = expand("<cword>")
    let page = substitute(str, '(*\([^()]\+\).*', '\1', '')
    let sect = substitute(str, '\(\k\+\)(\([^()]*\)).*', '\2', '')
    if match(sect, '^[0-9 ]\+$') == -1
      let sect = ""
    endif
    if sect == page
      let sect = ""
    endif
  else
		exec "setl iskeyword+=" . (!(pre->empty())? "," . pre[len(pre)-1] : "")
    let sect = a:cnt
    let page = expand("<cword>")
  endif
	let &l:iskeyword = old_isk
  call s:GetPageM(sect, [page, pre . page])
endfunc

func <SID>GetCmdArg(sect, page)
  if a:sect == ''
    return a:page
  endif
  return s:man_sect_arg.' '.a:sect.' '.a:page
endfunc

func <SID>FindPage(sect, page)
  let where = system("man ".s:man_find_arg.' '.s:GetCmdArg(a:sect, a:page))
  if where !~ "^/"
    if matchstr(where, " [^ ]*$") !~ "^ /"
      return 0
    endif
  endif
  return 1
endfunc

func <SID>GetPage(cmdmods, ...)
  if a:0 >= 2
    let sect = a:1
    let page = a:2
  elseif a:0 >= 1
    let sect = ""
    let page = a:1
  else
    return
  endif

  " To support:	    nmap K :Man <cword>
  if page == '<cword>'
    let page = expand('<cword>')
  endif

  if !exists('g:ft_man_no_sect_fallback') || (g:ft_man_no_sect_fallback == 0)
    if sect != "" && s:FindPage(sect, page) == 0
      let sect = ""
    endif
  endif
  if s:FindPage(sect, page) == 0
    let msg = "\nNo manual entry for ".page
    if sect != ""
      let msg .= " in section ".sect
    endif
    echo msg
    return
  endif
  exec "let s:man_tag_buf_".s:man_tag_depth." = ".bufnr("%")
  exec "let s:man_tag_lin_".s:man_tag_depth." = ".line(".")
  exec "let s:man_tag_col_".s:man_tag_depth." = ".col(".")
  let s:man_tag_depth = s:man_tag_depth + 1

  let open_cmd = 'edit'

  " Use an existing "man" window if it exists, otherwise open a new one.
  if &filetype != "man"
    let thiswin = winnr()
    exe "norm! \<C-W>b"
    if winnr() > 1
      exe "norm! " . thiswin . "\<C-W>w"
      while 1
	if &filetype == "man"
	  break
	endif
	exe "norm! \<C-W>w"
	if thiswin == winnr()
	  break
	endif
      endwhile
    endif
    if &filetype != "man"
      if exists("g:ft_man_open_mode")
        if g:ft_man_open_mode == 'vert'
	  let open_cmd = 'vsplit'
        elseif g:ft_man_open_mode == 'tab'
	  let open_cmd = 'tabedit'
        else
	  let open_cmd = 'split'
        endif
      else
	let open_cmd = a:cmdmods . ' split'
      endif
    endif
  endif

  silent execute open_cmd . " $HOME/" . page . '.' . sect . '~'

  " Avoid warning for editing the dummy file twice
  setl buftype=nofile noswapfile

  setl fdc=0 ma nofen nonu nornu
  silent exec "norm! 1GdG"
  let unsetwidth = 0
  if empty($MANWIDTH)
    let $MANWIDTH = winwidth(0)
    let unsetwidth = 1
  endif

  " Ensure Vim is not recursively invoked (man-db does this) when doing ctrl-[
  " on a man page reference by unsetting MANPAGER.
  " Some versions of env(1) do not support the '-u' option, and in such case
  " we set MANPAGER=cat.
  if !exists('s:env_has_u')
    call system('env -u x true')
    let s:env_has_u = (v:shell_error == 0)
  endif
  let env_cmd = s:env_has_u ? 'env -u MANPAGER' : 'env MANPAGER=cat'
  let man_cmd = env_cmd . ' man ' . s:GetCmdArg(sect, page) . ' | col -b'
  silent exec "r !" . man_cmd

  if unsetwidth
    let $MANWIDTH = ''
  endif
  " Remove blank lines from top and bottom.
  while line('$') > 1 && getline(1) =~ '^\s*$'
    silent keepj norm! ggdd
  endwhile
  while line('$') > 1 && getline('$') =~ '^\s*$'
    silent keepj norm! Gdd
  endwhile
  1
  setl ft=man nomod
  setl bufhidden=hide
  setl nobuflisted
  setl noma
endfunc

func <SID>PopPage()
  if s:man_tag_depth > 0
    let s:man_tag_depth = s:man_tag_depth - 1
    exec "let s:man_tag_buf=s:man_tag_buf_".s:man_tag_depth
    exec "let s:man_tag_lin=s:man_tag_lin_".s:man_tag_depth
    exec "let s:man_tag_col=s:man_tag_col_".s:man_tag_depth
    exec s:man_tag_buf."b"
    exec s:man_tag_lin
    exec "norm! ".s:man_tag_col."|"
    exec "unlet s:man_tag_buf_".s:man_tag_depth
    exec "unlet s:man_tag_lin_".s:man_tag_depth
    exec "unlet s:man_tag_col_".s:man_tag_depth
    unlet s:man_tag_buf s:man_tag_lin s:man_tag_col
  endif
endfunc

func <SID>FindPageM(sect, page)
	let pages = (type(a:page) == v:t_string)? [a:page] : a:page

	if type(pages) != v:t_list
		return []
	endif
	
	let where = []
	for page in pages
		let x = systemlist("man ".s:man_find_arg.' '.s:GetCmdArg(a:sect, page) . " 2>/dev/null")
		if !(x->empty()) && x[0] =~ "^/"
			return x
		endif
	endfor
  return where
endfunc

func <SID>GetPageM(sect, page, cmdmods = "", all_bang = "")
  let sect = (a:sect != '0')? a:sect : ''
  let page = a:page

  " To support:	    nmap K :Man <cword>
  if type(page) == v:t_string && page == '<cword>'
    let page = expand('<cword>')
  endif
  
  let manfiles = s:FindPageM(sect, page)

  if !exists('g:ft_man_no_sect_fallback') || (g:ft_man_no_sect_fallback == 0)
    if sect != "" && manfiles->empty()
      let sect = ""
    endif
  endif
  if manfiles->empty()
		let page = (type(page) == v:t_list)? page[0] : page
    let msg = "\nNo manual entry for ".page
    if sect != ""
      let msg .= " in section ".sect
    endif
    echo msg
    return
	else
		let page = fnamemodify(manfiles[0], ":t:r")
  endif
  exec "let s:man_tag_buf_".s:man_tag_depth." = ".bufnr("%")
  exec "let s:man_tag_lin_".s:man_tag_depth." = ".line(".")
  exec "let s:man_tag_col_".s:man_tag_depth." = ".col(".")
  let s:man_tag_depth = s:man_tag_depth + 1

  let open_cmd = 'edit'

  " Use an existing "man" window if it exists, otherwise open a new one.
  if &filetype != "man"
    let thiswin = winnr()
    exe "norm! \<C-W>b"
    if winnr() > 1
      exe "norm! " . thiswin . "\<C-W>w"
      while 1
	if &filetype == "man"
	  break
	endif
	exe "norm! \<C-W>w"
	if thiswin == winnr()
	  break
	endif
      endwhile
    endif
    if &filetype != "man"
      if exists("g:ft_man_open_mode")
        if g:ft_man_open_mode == 'vert'
	  let open_cmd = 'vsplit'
        elseif g:ft_man_open_mode == 'tab'
	  let open_cmd = 'tabedit'
        else
	  let open_cmd = 'split'
        endif
      else
	let open_cmd = a:cmdmods . ' split'
      endif
    endif
  endif

  silent execute open_cmd . " $HOME/" . page . '.' . sect . '~'

  " Avoid warning for editing the dummy file twice
  setl buftype=nofile noswapfile

  setl fdc=0 ma nofen nonu nornu
  silent exec "norm! 1GdG"
  let unsetwidth = 0
  if empty($MANWIDTH)
    let $MANWIDTH = winwidth(0)
    let unsetwidth = 1
  endif

  " Ensure Vim is not recursively invoked (man-db does this) when doing ctrl-[
  " on a man page reference by unsetting MANPAGER.
  " Some versions of env(1) do not support the '-u' option, and in such case
  " we set MANPAGER=cat.
  if !exists('s:env_has_u')
    call system('env -u x true')
    let s:env_has_u = (v:shell_error == 0)
  endif
  let env_cmd = s:env_has_u ? 'env -u MANPAGER' : 'env MANPAGER=cat'
  let man_cmd = env_cmd . ' man ' . s:GetCmdArg(sect, page) . ' | col -b'

  setlocal sidescrolloff=0 sidescroll=1 scrolloff=1

  let outv = []
  for manfile in manfiles
    if a:all_bang->empty() && !(outv->empty())
      break
    elseif !(outv->empty())
      call extend(outv, ['', '------>', ''])
    endif

    if manfile[-2:] =~? 'gz'
      call extend(outv, systemlist('gunzip -c  "' . manfile . '" | groff -t -c -m man -T' . s:dev . ' 2>/dev/null'))
    else
      call extend(outv, systemlist('groff -t -c -m man -T' . s:dev . ' "' . manfile . '" 2>/dev/null'))
    endif
  endfor

  silent call append(0, outv)
  silent %s/_\(.\s*\)/\1/eg
  silent %s/.//eg

  if unsetwidth
    let $MANWIDTH = ''
  endif
  1
  setl ft=man nomod
  setl bufhidden=hide
  setl nobuflisted
  setl noma
endfunc

endif

let &cpo = s:cpo_save
unlet s:cpo_save

" vim: set sw=2 ts=8 noet:
