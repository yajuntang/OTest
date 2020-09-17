import os
import shutil
import subprocess

import requests


class VersionManger:
    """
    版本控制器
    """
    app_path = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "apps")

    def __init__(self, platform, url, app_name, version_name, version_code):
        """
        初始化
        :param platform: 平台
        :param url: 需要下载的app链接
        :param app_name:
        :param version_name:
        :param version_code:
        """
        self.platform = platform
        self.app_name = app_name
        self.url = url
        self.version_name = version_name
        self.version_code = version_code

    def check_version(self, device, is_cover_install):
        if self.platform == "Android":
            result = AndroidVersion.get_version(device, self.app_name) == (self.version_name, self.version_code)
            if not result:
                print("UUID为{0}的手机 没有安装{1}[{2}]版本的app".format(device, self.version_name, self.version_code))
                if not is_cover_install:
                    AndroidVersion.uninstall(device, self.app_name)
                    print("UUID为{0}的手机 卸载完成App:{1}".format(device, self.app_name))
                AndroidVersion.install(device, self.check_download(AndroidVersion.suffix()))
                result = AndroidVersion.get_version(device, self.app_name) == (self.version_name, self.version_code)
                if not result:
                    raise FileNotFoundError("没有找到{0}[{1}]的安装包".format(self.version_name, self.version_code))

    def check_download(self, suffix):
        if not os.path.exists(self.app_path):
            os.makedirs(self.app_path)
        app_file_name = self.get_app_name()
        app_file_path = os.path.join(self.app_path, app_file_name + suffix)
        if os.path.exists(app_file_path):
            return app_file_path
        if not self.url:
            raise FileNotFoundError("没有找到{0}[{1}]的安装包".format(self.version_name, self.version_code))
        self.download(self.url, app_file_path)
        return app_file_path

    @classmethod
    def download(cls, url, file_path):
        if url.startswith("http"):
            download_file(url, file_path)
        else:
            copyfile(url, file_path)

    def get_app_name(self):
        return self.app_name.replace(".", "_") + "_" + self.version_name.replace(".", "-") + "_" + self.version_code


class AndroidVersion:

    @classmethod
    def get_version(cls, device, app_name):
        version_string = subprocess.getoutput("adb -s {} shell dumpsys package {}".format(device, app_name))
        lines = [line.strip() for line in version_string.splitlines() if
                 line.__contains__("versionName=") or line.__contains__("versionCode=")]
        version_name = None
        version_code = None
        for item in lines:
            if item.startswith("versionName="):
                version_name = item.split(" ")[0].replace("versionName=", "")
            if item.startswith("versionCode="):
                version_code = item.split(" ")[0].replace("versionCode=", "")
        return version_name, version_code

    @classmethod
    def uninstall(cls, device, app_name):
        subprocess.call("adb -s {} uninstall {}".format(device, app_name))

    @classmethod
    def install(cls, device, path):
        subprocess.call("adb -s {} install -r {}".format(device, path))

    @classmethod
    def suffix(cls):
        return ".apk"


def copyfile(path, dst_path):
    shutil.copyfile(path, dst_path)


def download_file(url, file_path):
    r = requests.get(url)
    if r.status_code != requests.codes.ok:
        raise FileNotFoundError(url)
    else:
        with open(file_path, "wb") as f:
            f.write(r.content)
