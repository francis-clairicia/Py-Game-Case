# -*- coding: Utf-8 -*

import os
import sys
import platform
import glob
import shutil
import requests
import packaging.version
from typing import Union, Any
from zipfile import ZipFile
from my_pygame import ProgressBar

class GitReleaseAsset:

    def __init__(self, asset_dict: dict[str, Any]):
        self.__name = str(asset_dict["name"])
        self.__size = int(asset_dict["size"])
        self.__type = str(asset_dict["content_type"])
        self.__url = str(asset_dict["browser_download_url"])
        self.__state = str(asset_dict["state"])
        self.__uploaded = bool(self.__state == "uploaded")

    def __repr__(self) -> str:
        return "<{} name={} size={} state={}>".format(self.__class__.__name__, repr(self.__name), self.__size, self.__state)

    def __str__(self) -> str:
        return repr(self)

    name = property(lambda self: self.__name)
    size = property(lambda self: self.__size)
    type = property(lambda self: self.__type)
    url = property(lambda self: self.__url)
    state = property(lambda self: self.__state)
    uploaded = property(lambda self: self.__uploaded)

class GitRelease:

    def __init__(self, url: str, session: requests.Session):
        self.__exists = True
        self.__name = str()
        self.__version = packaging.version.Version("0.0.0")
        self.__assets = tuple()
        try:
            if not self.__check_github_api_rate_limit(session):
                raise requests.HTTPError
            response = session.get(url)
            response.raise_for_status()
        except requests.HTTPError:
            self.__exists = False
        else:
            release = response.json()
            self.__name = release["name"]
            self.__version = packaging.version.Version(release["tag_name"])
            self.__assets = tuple[GitReleaseAsset, ...](GitReleaseAsset(asset) for asset in release["assets"])

    def __repr__(self) -> str:
        if not self.__exists:
            return "<{} non-available>".format(self.__class__.__name__)
        return "<{} name={} version={}>".format(self.__class__.__name__, repr(self.__name), self.__version)

    def __str__(self) -> str:
        return repr(self)

    def __check_github_api_rate_limit(self, session: requests.Session) -> bool:
        url = "https://api.github.com/rate_limit"
        try:
            response = session.get(url)
            response.raise_for_status()
        except requests.HTTPError:
            return False
        return bool(response.json()["resources"]["core"]["remaining"] > 0)

    name = property(lambda self: self.__name)
    exists = property(lambda self: self.__exists)
    version = property(lambda self: self.__version)
    assets = property(lambda self: self.__assets)

class GitRepository:

    def __init__(self, owner: str, name: str):
        self.__api_link = f"https://api.github.com/repos/{owner}/{name}"
        self.__session = requests.Session()
        self.__session.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "python-request/git-repository-api"
        }
        if os.path.isfile("token"):
            with open("token", "r") as file:
                self.__session.headers["Authorization"] = "token {}".format(file.read())

    def close(self) -> None:
        self.__session.close()

    def __repr__(self) -> str:
        return "<{} link={}>".format(self.__class__.__name__, self.__api_link)

    def __str__(self) -> str:
        return repr(self)

    def __get_link(self, api_info: str) -> str:
        return self.__api_link + "/" + str(api_info)

    def get_latest_release(self) -> GitRelease:
        return GitRelease(self.__get_link("releases/latest"), self.__session)

    def get_release(self, version: Union[str, packaging.version.Version]) -> GitRelease:
        return GitRelease(self.__get_link(f"releases/tags/{version}"), self.__session)

    def download(self, asset: GitReleaseAsset, file_dest: str, progress: ProgressBar) -> str:
        progress.from_value = 0
        progress.to_value = asset.size
        progress.percent = 0
        progress.show_label("Downloading {}".format(asset.name), ProgressBar.S_TOP)
        progress.show_percent(ProgressBar.S_INSIDE, round_n=1)
        try:
            response = self.__session.get(asset.url, stream=True)
            response.raise_for_status()
            if not os.path.isdir(os.path.dirname(file_dest)):
                os.makedirs(os.path.dirname(file_dest))
            with open(file_dest, "wb") as file_stream:
                for chunk in response.iter_content(chunk_size=1024*512):
                    progress.value += file_stream.write(chunk)
        except Exception as e:
            progress.config_label_text("Error download\n{}: {}".format(e.__class__.__name__, str(e)), justify="center")
            progress.hide_percent()
            return None
        return file_dest

class Updater:

    OLD_FILE_PREFIX = "UPDATER_OLD_"
    PROJECT_OWNER = "francis-clairicia"
    PROJECT_NAME = "Py-Game-Case"

    STATE_NO_NEW_RELEASE = "no_new_release"
    STATE_ERROR_DOWNLOAD = "error_download"
    STATE_ERROR_INSTALLATION = "error_installation"
    STATE_INSTALLED = "installed"

    def __init__(self, actual_version: str):
        self.__actual_version = packaging.version.Version(actual_version)
        self.__git = GitRepository(Updater.PROJECT_OWNER, Updater.PROJECT_NAME)
        self.__filepath = os.path.dirname(sys.executable)
        self.__cache_directory = os.path.join(self.__filepath, "cache")
        self.__cache_file = os.path.join(self.__cache_directory, "archive.zip")
        for file in glob.glob(os.path.join(self.__filepath, "**", "{}*".format(Updater.OLD_FILE_PREFIX)), recursive=True):
            try:
                os.remove(file)
            except PermissionError:
                sys.exit("An another launcher is running. Close it before reopen the launcher.")
        self.__latest_release = None
        self.__release_asset = None

    def close(self) -> None:
        self.__git.close()

    def check_for_new_release(self) -> None:
        if not isinstance(self.__latest_release, GitRelease):
            self.__latest_release = self.__git.get_latest_release()
            for asset in filter(lambda asset: asset.uploaded, self.__latest_release.assets):
                if asset.name.endswith("-{}.zip".format(platform.system())):
                    self.__release_asset = asset
                    break

    def has_a_new_release(self) -> bool:
        if os.path.isfile(self.__cache_file):
            return True
        return bool(self.__has_a_release() and self.__latest_release.version > self.__actual_version)

    def __has_a_release(self) -> bool:
        self.check_for_new_release()
        return bool(self.__latest_release.exists and isinstance(self.__release_asset, GitReleaseAsset))

    def install_latest_version(self, progress: ProgressBar, *, compare_versions=True) -> str:
        if os.path.isfile(self.__cache_file):
            archive = self.__cache_file
        else:
            if (not compare_versions and not self.__has_a_release()) or (compare_versions and not self.has_a_new_release()):
                return Updater.STATE_NO_NEW_RELEASE
            archive = self.__git.download(self.__release_asset, self.__cache_file, progress)
            if archive is None or not os.path.isfile(archive):
                if os.path.isdir(self.__cache_directory):
                    shutil.rmtree(self.__cache_directory, ignore_errors=True)
                return Updater.STATE_ERROR_DOWNLOAD
        try:
            progress.show_label("Installing {}...".format(os.path.basename(archive)), ProgressBar.S_TOP)
            progress.show_percent(ProgressBar.S_INSIDE, round_n=0)
            with ZipFile(archive, "r") as zip_file:
                file_list = zip_file.namelist()
                progress.from_value = 0
                progress.to_value = len(file_list)
                progress.percent = 0
                for i, file in enumerate(file_list, start=1):
                    try:
                        zip_file.extract(file, path=self.__filepath)
                    except (PermissionError, FileExistsError):
                        directory, filename = os.path.split(file)
                        src = os.path.join(self.__filepath, file)
                        dest = os.path.join(self.__filepath, directory, Updater.OLD_FILE_PREFIX + filename)
                        try:
                            os.rename(src, dest)
                            zip_file.extract(file, path=self.__filepath)
                        except (PermissionError, FileExistsError):
                            pass
                    finally:
                        progress.value = i
        except Exception as e:
            progress.config_label_text("Error installation\n{}: {}".format(e.__class__.__name__, str(e)), justify="center")
            progress.hide_percent()
            return Updater.STATE_ERROR_INSTALLATION
        shutil.rmtree(self.__cache_directory, ignore_errors=True)
        return Updater.STATE_INSTALLED
