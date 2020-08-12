#!/usr/bin/env python3

import glob
import hashlib
import os
import shutil
import sys

import _jsonnet


def main():
    # for simplicity, just strip all the '-'s for easy arg checking
    args = {arg.replace("-", "") for arg in sys.argv[1:]}

    # print usage on help or if unrecognized args show up
    nonsense = args - {"release", "clean", "verbose", "help"}
    if nonsense or "help" in args:
        print(f"Usage: {sys.argv[0]} [--release] [--clean] [--verbose] [--help]\n")
        print("  --release drops the '-dev' from the version number")
        print("  --clean removes the out dir before building")
        print("  --verbose is noisy")
        print("  --help shows this page")
        print("\nAlso, you can drop the '--'s on all of these, they're optional")
        if nonsense:
            print(f"\nUnrecognized option: {nonsense}")
            sys.exit(1)
        return

    # cd to the script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # remove the out directory for a clean build
    if "clean" in args and os.path.exists("out"):
        if "verbose" in args:
            print("removing out directory")
        shutil.rmtree("out")


    hashes = {}

    # get all the json files and convert them
    for file in glob.iglob("src/**/*.json*", recursive=True):
        # jsonnet files get compiled, json gets copied
        compiling = file.endswith(".jsonnet")

        # out structure should match src structure, .jsonnet => .json
        out_file = file.replace("src", "out", 1)
        if compiling:
            out_file = out_file[0:-3]  # strip 'net' from jsonnet

        # logging
        if "verbose" in args:
            print(f"{'compiling' if compiling else 'copying'} {file} to {out_file}")

        # read in the input
        with open(file, "r") as i:
            input_content = i.read()

        # hash the input
        hashes[file] = hashlib.sha256(input_content.encode('utf-8')).hexdigest()

        # generate the output
        if compiling:
            json_str = _jsonnet.evaluate_snippet(file, input_content)
        else:
            json_str = input_content

        # write out
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        with open(out_file, "w") as o:
            o.write(json_str)
    
    # hash the hashes for version number
    version_hash = hashlib.sha256()
    for file, digest in hashes.items():
        summary = file + " " + digest + "\n"
        if "verbose" in args:
            print(summary)
        version_hash.update(summary.encode('utf-8'))
    version_hash_digest = version_hash.hexdigest()

    # write out version number
    with open("src/version.txt", "r") as i:
        with open("out/version.txt", "w") as o:
            # read in
            version = i.read().strip()

            # add the version hash
            version += "-" + version_hash_digest

            # non-release builds get 'dev' so that KT Manager always picks them up as new
            if "release" not in args:
                version += "-dev"

            # logging
            if "verbose" in args:
                print(f"adding version file: {version}")

            # write out
            o.write(version)


if __name__ == "__main__":
    main()
