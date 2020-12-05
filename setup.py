# -*- coding:Utf-8 -*

import os
import sys
import platform
import argparse
import glob
from zipfile import ZipFile, ZIP_DEFLATED
from cx_Freeze import setup, Executable

def zip_compress():
    global executable_infos, options
    zip_filename = "{}-{}.zip".format(
        executable_infos["project_name"],
        platform.system(),
    ).replace(" ", "_")
    print(f"Compressing executable in {zip_filename}...")
    output_folder = options.get("build_exe", ".")
    output_zip = os.path.join(output_folder, zip_filename)
    all_files = list()
    all_executables = [exec_file["name"] for exec_file in executable_infos["executables"]]
    pattern_list = [*all_executables, "lib", "python*.dll", "vcruntime*.dll", *options["include_files"]]
    for pattern in pattern_list:
        pattern = os.path.join(output_folder, pattern)
        for path in glob.glob(pattern):
            if os.path.isfile(path):
                all_files.append({"filename": path, "arcname": path.replace(output_folder, ".")})
            elif os.path.isdir(path):
                for root, folders, files in os.walk(path):
                    for file in files:
                        file = os.path.join(root, file)
                        all_files.append({"filename": file, "arcname": file.replace(output_folder, ".")})
    with ZipFile(output_zip, "w", compression=ZIP_DEFLATED) as zip_file_fp:
        for file in all_files:
            zip_file_fp.write(**file)

def get_application_version(app: str) -> str:
    app_globals = dict()
    with open(os.path.join(app, "version.py")) as file:
        exec(file.read(), app_globals)
    return app_globals["__version__"]

#############################################################################
# Parsing des arguments

parser = argparse.ArgumentParser(prog="setup.py", description="Setup for executable freezing")
parser.add_argument("--zip", help="Create a zip file when it's finished", action="store_true")
parser.add_argument("--version", help="Use a custom version instead of applcation version")
args = parser.parse_args()

#############################################################################
# Recupération des valeurs

application = "py_game_case"

dependencies = ["pygame", "my_pygame", "psutil", "navy", "four_in_a_row"]

additional_files = ["resources"]

executable_infos = {
    "project_name": "Py-Game-Case",
    "description": "Py-Game-Case - A library of board games using pygame",
    "author": "Francis Clairicia-Rose-Claire-Josephine",
    "version": args.version or get_application_version(application),
    "executables": [
        {
            "script": "run.pyw",
            "name": "Py_game_case",
            "base": "Win32GUI",
            "icon": "resources/py_game_case/img/icon.ico"
        }
    ],
    "copyright": "Copyright (c) 2020 Francis Clairicia-Rose-Claire-Josephine"
}

options = {
    "path": sys.path,
    "build_exe": os.path.join(sys.path[0], "build"),
    "includes": [application, *dependencies],
    "excludes": [],
    "include_files": additional_files,
    "optimize": 0,
    "silent": True
}

print("-----------------------------------{ cx_Freeze }-----------------------------------")
print("Project Name: {project_name}".format(**executable_infos))
print("Author: {author}".format(**executable_infos))
print("Version: {version}".format(**executable_infos))
print("Description: {description}".format(**executable_infos))
print()
for i, infos in enumerate(executable_infos["executables"], start=1):
    print(f"Executable number {i}")
    print("Name: {name}".format(**infos))
    print("Icon: {icon}".format(**infos))
    print()
print("Dependencies: {includes}".format(**options))
print("Additional files/folders: {include_files}".format(**options))
print()

while True:
    OK = input("Is this ok ? (y/n) : ").lower()
    if OK in ("y", "n"):
        break

if OK == "n":
    sys.exit(0)

print("-----------------------------------------------------------------------------------")

if "tkinter" not in options["includes"]:
    options["excludes"].append("tkinter")

# pour inclure sous Windows les dll system de Windows necessaires
if sys.platform.startswith("win"):
    options["include_msvcr"] = True

#############################################################################
# preparation de la cible

executables = list()
for infos in executable_infos["executables"]:
    if sys.platform.startswith("win"):
        infos["name"] += ".exe"
    else:
        infos["base"] = None
    target = Executable(
        script=os.path.join(sys.path[0], infos["script"]),
        base=infos["base"],
        targetName=infos["name"],
        icon=infos["icon"],
        copyright=executable_infos["copyright"]
    )
    executables.append(target)

#############################################################################
# creation du setup

sys.argv = [sys.argv[0], "build_exe"]

try:
    result = str()
    setup(
        name=executable_infos["project_name"],
        version=executable_infos["version"],
        description=executable_infos["description"],
        author=executable_infos["author"],
        options={"build_exe": options},
        executables=executables
    )
except Exception as e:
    result = f"{e.__class__.__name__}: {e}"
else:
    result = "Build done"
    if args.zip:
        zip_compress()
finally:
    print("-----------------------------------------------------------------------------------")
    print(result)
    print("-----------------------------------------------------------------------------------")
    if sys.platform.startswith("win"):
        os.system("pause")