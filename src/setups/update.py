if __name__ == '__main__':
    import shutil
    import requests
    import tempfile
    import compileall
    import pathlib
    import os
    import urllib.parse
    import sys
    
    print("fetch files...")

    url = urllib.parse.urlparse("https://sheriff0.github.io/dogger/dogger.tar.xz");

    pkg = requests.get(url.geturl()); # get pkg from url

    pkg.raise_for_status();
    
    tdir = pathlib.Path(tempfile.mkdtemp());
   
    p = pathlib.Path(url.path);

    ar = tdir.joinpath(p.stem + p.suffix);

    fp = open(str(ar), "wb");

    fp.write(pkg.content);
    
    fp.close();

    pkg_name = pathlib.Path(sys.argv[0]);

    shutil.unpack_archive(str(ar), str(tdir));

    if compileall.compile_dir(str(tdir), force = True, legacy = True):
        shutil.copytree(str(tdir), str(pkg_name.parent), ignore = shutil.ignore_patterns("*py", "*" + p.suffix), dirs_exist_ok = True);
        print("everything good");
    
    shutil.rmtree(str(tdir));
