# -*- coding: Utf-8 -*

import os
import sys
import subprocess
import glob
import requests
import packaging.version
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.messagebox import showinfo, showerror
from zipfile import ZipFile
from my_pygame import threaded_function
from functools import wraps

def showerror_exception(function):

    @wraps(function)
    def wrapper(window: tk.Tk, *args, **kwargs):
        try:
            function(window, *args, **kwargs)
        except Exception as e:
            showerror(e.__class__.__name__, str(e))
            window.quit()

    return wrapper

class Updater(tk.Tk):

    OLD_FILE_PREFIX = "OLD_"
    REPOSITORY = "Py-Game-Case"
    OWNER = "francis-clairicia"
    NAME = "Py-Game-Case"

    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Updater")
        self.geometry("{}x{}".format(500, 300))

        self.label = tk.Label(self, font=("Times New Roman", 15))
        self.label.grid(row=0, sticky=tk.NSEW)
        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, mode="determinate")
        self.progress.grid(row=1, sticky=tk.EW)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.executable = sys.executable
        self.filepath = os.path.dirname(self.executable)
        for file in glob.glob(os.path.join(self.filepath, "**", "{prefix}*".format(prefix=Updater.OLD_FILE_PREFIX)), recursive=True):
            try:
                os.remove(file)
            except PermissionError:
                continue
        
        self.session = requests.Session()
        self.session.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "python-request/py-updater"
        }

    def __del__(self) -> None:
        self.session.close()

    def __get_release(self, url: str) -> dict:
        try:
            response = self.session.get(url)
            response.raise_for_status()
        except requests.HTTPError:
            return None
        return response.json()

    def install_latest_version(self, actual_version: str) -> None:
        if self.__check_github_api_rate_limit() is False:
            return
        url = "https://api.github.com/repos/{}/{}/releases/latest".format(Updater.OWNER, Updater.REPOSITORY)
        release = self.__get_release(url)
        if release is not None and packaging.version.parse(release["tag_name"]) > packaging.version.parse(actual_version):
            self.__install(release)

    def install_version(self, version: str) -> None:
        if self.__check_github_api_rate_limit() is False:
            return
        try:
            version = str(packaging.version.Version(version))
            url = "https://api.github.com/repos/{}/{}/releases/tags/{}".format(Updater.OWNER, Updater.REPOSITORY, version)
            release = self.__get_release(url)
            if release is None:
                raise packaging.version.InvalidVersion(f"There is no version {version}")
        except packaging.version.InvalidVersion as e:
            sys.exit(f"{e.__class__.__name__}: {e}")
        self.__install(release)

    def __install(self, release: dict) -> None:
        self.label["text"] = str()
        self.progress["value"] = self.progress["maximum"] = 0
        self.after(100, lambda: self.__start_install(release))
        self.mainloop()
        os.execv(self.executable, [self.executable])

    @threaded_function
    @showerror_exception
    def __start_install(self, release: dict) -> None:
        archive_to_download = self.__search_archive_assets(release)
        if archive_to_download is None:
            showerror("No assets", "There is no assets for this version or not for your platform")
        else:
            archive_filepath = self.__download(archive_to_download)
            if archive_filepath is None:
                showerror("Error download", "Can't download update")
            else:
                self.__extract(archive_filepath)
        self.quit()

    def __search_archive_assets(self, release: dict) -> dict:
        for asset in filter(lambda asset: asset["state"] == "uploaded", release["assets"]):
            if asset["name"] == "{}-{}.zip".format(Updater.NAME, sys.platform):
                return asset
        return None

    def __download(self, asset: dict) -> str:
        self.label["text"] = "Downloading {name}...".format(**asset)
        self.progress["value"] = 0
        self.progress["maximum"] = asset["size"]
        try:
            response = self.session.get(asset["browser_download_url"], stream=True)
            response.raise_for_status()
        except requests.HTTPError:
            return None
        archive = os.path.join(self.filepath, asset["name"])
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        with open(archive, "wb") as file_stream:
            for chunk in response.iter_content(chunk_size=1024*512):
                self.progress["value"] += file_stream.write(chunk)
        self.protocol("WM_DELETE_WINDOW", self.quit)
        return archive

    def __extract(self, archive: str) -> None:
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        with ZipFile(archive, "r") as zip_file:
            self.label["text"] = "Installing {}...".format(os.path.basename(archive))
            file_list = zip_file.namelist()
            self.progress["value"] = 0
            self.progress["maximum"] = len(file_list)
            for i, file in enumerate(file_list, start=1):
                try:
                    zip_file.extract(file, path=self.filepath)
                except PermissionError:
                    directory, filename = os.path.split(file)
                    os.rename(os.path.join(self.filepath, file), os.path.join(self.filepath, directory, Updater.OLD_FILE_PREFIX + filename))
                    zip_file.extract(file, path=self.filepath)
                finally:
                    self.progress["value"] = i
        self.protocol("WM_DELETE_WINDOW", self.quit)
        os.remove(archive)

    def __check_github_api_rate_limit(self) -> bool:
        url = "https://api.github.com/rate_limit"
        try:
            response = self.session.get(url)
            response.raise_for_status()
        except requests.HTTPError:
            return False
        return bool(response.json()["resources"]["core"]["remaining"] > 0)
