if __name__ == '__main__':
    import shutil
    import tempfile
    import compileall
    import pathlib
    import os
    import sys
    import argparse
    import pip

    if sys.platform.startswith("win"):
        whldir = "win32_wheels";

    else:
        print("unsupported OS %s" % (sys.platform,));
        sys.exit(1);

    pkg_name = pathlib.Path(sys.argv[0]);
    whldir = pkg_name.parent.joinpath(whldir);
    whl = [str(whldir.joinpath(wl)) for wl in os.listdir(str(whldir))];
    
    pip_argv = [sys.executable, "-m pip", "install"];
    
    pip_argv.extend(whl);

    if os.system(" ".join(pip_argv)) != 0:
        pip_argv = [sys.executable, "-m pip", "install", "-r", str(pkg_name.parent.joinpath("deps_dog.txt").resolve())];

        if os.system(" ".join(pip_argv)) != 0:
            sys.exit(1);

    import requests
    import urllib.parse

    parser = argparse.ArgumentParser ();

    parser.add_argument ('--dest', help = "where to install the package",
            default = "dog_main", type = str);

    parser.add_argument ('--url', help = "where to get the package", type = str,
            default = "https://sheriff0.github.io/dogger/dogger.tar.xz");

    args = parser.parse_args();

    print("fetch files...")

    tdir = pathlib.Path(tempfile.mkdtemp());
    
    if args.url.startswith(("http", "HTTP")):
        url = urllib.parse.urlparse(args.url);

        pkg = requests.get(url.geturl()); # get pkg from url

        pkg.raise_for_status();


        p = pathlib.Path(url.path);

        ar = tdir.joinpath(p.stem + p.suffix);

        fp = open(str(ar), "wb");

        fp.write(pkg.content);

        fp.close();
    
    else:
        ar = pathlib.Path(args.url);
        p = pathlib.Path(args.url);
        if not ar.exists():
            print("no such file %s" % (str(ar),));
            sys.exit(1);


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
