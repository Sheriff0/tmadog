if __name__ == '__main__':
    import shutil
    import requests
    import tempfile
    import compileall
    import pathlib
    import os
    import urllib.parse
    import sys
    import argparse
   
    pkg_name = pathlib.Path(sys.argv[0]);

    parser = argparse.ArgumentParser ();

    parser.add_argument ('--dest', help = "where to install the package",
            default = "dog_main", type = str);

    args = parser.parse_args();

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

    dest = pathlib.Path(args.dest);

    shutil.unpack_archive(str(ar), str(tdir));

    if compileall.compile_dir(str(tdir), force = True, legacy = True):
        if dest.exists():
            if dest.is_dir():
                shutil.rmtree(str(dest));
            else:
                dest.unlink();

        try:
            shutil.copytree(str(tdir), str(dest), copy_function = shutil.copy, ignore = shutil.ignore_patterns("*py", "*" + p.suffix));

        except shutil.Error as err:
            pass;

        shutil.move(str(dest.joinpath("dog_main.pyc")),
                str(dest.joinpath("__main__.pyc")));

        print("\neverywhere good!!!", "\nYou can now run \"%s\"" % (str(dest),));
    
    shutil.rmtree(str(tdir));
