changequote`'changequote({, })dnl
define(
{MODULE_INIT},
{changequote`'define(__file__`_MODNAME', ifelse(len($1), 0, __file__, $1))define(__file__`_divnum', divnum)`'divert(ifelse(len($2), 0, -1, $2))}
)dnl
define(
{MODULE_START},
{changequote`'ifdef(__file__`_divnum', `ifdef(indir(__file__`_MODNAME'), `divert(-1)', `divert(indir(__file__`_divnum'))')', `errprint(`Warn: ' __file__`: MODULE_START not called')MODULE_INIT($1, divnum)')}dnl
)dnl
define({MODULE_END}, {changequote`'ifdef(__file__`_MODNAME', `define(indir(__file__`_MODNAME'))divert(indir(__file__`_divnum'))', `errprint(`err: '__file__`: Module not initialized')m4exit(1)')})dnl
changequote`'MODULE_START()MODULE_END()dnl
