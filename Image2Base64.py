# encoding=utf8
import sublime
import sublime_plugin
import os
import base64
import tempfile
import mimetypes

try:
    import urllib.request
    urlretrieve = urllib.request.urlretrieve
except ImportError:
    import urllib
    urlretrieve = urllib.urlretrieve

supported_mime_types = (
    "image/gif",
    "image/jpeg",
    "image/pjpeg",
    "image/png",
    "image/svg+xml",
    "image/tiff",
    "image/x-icon",
    "image/x-ms-bmp",
    "image/vnd.microsoft.icon",
    "image/vnd.wap.wbmp",
    "image/webp",
)

line_endings = {
    "Unix": "\n",
    "CR": "\r",
    "Windows": "\r\n",
}

settings = sublime.load_settings('Image2Base64.sublime-settings')

def split_line(data):
    cols = settings.get('split_line_cols')
    if cols is None or cols <= 0:
        return data
    lines = [data[i:i+cols] for i in range(0, len(data), cols)]
    le = line_endings[sublime.active_window().active_view().line_endings()]
    return le.join(lines)

def convert_image(file, mime):
    with open(file, "rb") as image_file:
        encoded_bytes = base64.b64encode(image_file.read())
        return split_line('data:%s;base64,%s' % (mime, encoded_bytes.decode()))
    return None


def copy_image_to_clipboard(file_name, image):
    sublime.status_message('%s copied to clipboard as Base64' % file_name)
    sublime.set_clipboard(image)


def get_image_info(file_name):
    name, extension = os.path.splitext(file_name)
    extension = extension.lower().replace('.', '')
    mime, encoding = mimetypes.guess_type(file_name)
    if mime not in supported_mime_types:
        mime = None
    return name, extension, mime


class Image2Base64(sublime_plugin.EventListener):

    def on_load(self, view):
        if not view.file_name():
            return
        file_name, file_extension, mime = get_image_info(view.file_name())
        if not mime:
            return
        converted_image = convert_image(view.file_name(), mime)
        if converted_image:
            _i = {"image": converted_image}
            view.run_command("i2b64_change", _i)
            sublime.active_window().run_command("i2b64_copy_panel", _i)


class I2b64ChangeCommand(sublime_plugin.TextCommand):

    def run(self, edit, image):
        self.view.set_scratch(True)
        self.view.replace(edit, sublime.Region(0, self.view.size()), image)
        self.view.set_read_only(True)
        self.view.run_command("select_all")


class I2b64CopyPanelCommand(sublime_plugin.WindowCommand):

    def run(self, image):
        self.image = image
        self.window.show_quick_panel(
            ['Copy base64 image to clipboard'], self.copy_image)

    def copy_image(self, item):
        if item == 0 and self.image:
            copy_image_to_clipboard('Image', self.image)


class ImageBase64ToClipboardCommand(sublime_plugin.WindowCommand):

    def run(self):
        sublime.status_message('Scanning project folders...')
        self.files_panel = []
        self.project_files = []
        open_folders = self.window.folders()
        if not len(open_folders):
            sublime.status_message(
                'Add some folders to project for searching images')
            return

        for folder in open_folders:
            for fold in os.walk(folder):
                subdir, dir_name, files = fold
                for f in files:
                    file_name, extension, mime = get_image_info(f)
                    if not mime:
                        continue
                    if os.path.relpath(subdir, folder) == '.':
                        relpath = ''
                    else:
                        relpath = os.sep + \
                            os.path.relpath(subdir, folder)
                    self.files_panel.append(
                        [f, os.path.split(folder)[-1] + relpath + os.sep])
                    self.project_files.append(
                        [f, subdir + os.sep + f, mime])
        self.window.show_quick_panel(self.files_panel, self.copy_image)
        sublime.status_message(
            'Select the image to be copied to clipboard')

    def copy_image(self, item):
        if item != -1:
            file_name, file_path, mime = self.project_files[item]
            copy_image_to_clipboard(file_name, convert_image(file_path, mime))

class UrlBase64ToClipboardCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.show_input_panel('Image url to convert to base64', '', self.on_done, self.on_change, self.on_cancel)

    def on_done(self, url):
        sublime.status_message('Downloading image: %s...' % (url))
        mime, encoding = mimetypes.guess_type(url)
        s, file_path = tempfile.mkstemp(prefix='i2b_')
        urlretrieve(url, file_path)
        copy_image_to_clipboard(url, convert_image(file_path, mime))

    def on_change(self, url):
        pass

    def on_cancel(self):
        pass

class PasteBase64ImageToCss(sublime_plugin.TextCommand):
    def run(self, edit):
        clipboard = sublime.get_clipboard()
        self.view.insert(edit, self.view.sel()[0].begin(), self.escapeNewline(clipboard))


    def escapeNewline(self, str):
        le = line_endings[self.view.line_endings()]
        return ("\\" + le).join(str.split(le))
