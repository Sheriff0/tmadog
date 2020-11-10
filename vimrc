let s:bdir = getcwd()

if !(&viminfofile->empty())
	set history=10000
	let &viminfofile = trim(system("realpath -L " . &viminfofile))

endif

call mkdir(s:bdir . "/fundos", "p")
let &undodir = s:bdir . "/fundos//"
set undofile

augroup undos

    autocmd ExitPre * call delete(s:bdir . "/fundos", "rf")
augroup END

autocmd VimLeavePre * if !(&viminfofile->empty()) | call delete(&viminfofile) | endif

if exists("$TOOLS_HOME")
	"Because viewmgr changes dir:
    source $VIMRUNTIME/ftplugin/man.vim
    source $TOOLS_HOME/viewmgr.vim

endif

function KeepUndos ()
    au! undos
endfunc

function! ViewUnload ()
    au! keepview
endfunction
