# encoding=utf8
import sublime
import sublime_plugin
import os
import base64

mime_extensions = {
    "image/gif":        ["gif"],
    "image/jpeg":       ["jpg", "jpeg", "jpe"],
    "image/png":        ["png"],
    "image/x-icon":     ["ico"],
    "image/x-ms-bmp":   ["bmp"],
}


def convert_image(file, mime):
    with open(file, "rb") as image_file:
        encoded_bytes = base64.b64encode(image_file.read())
        return 'data:%s;base64,%s' % (mime, encoded_bytes.decode())
    return None


def copy_image_to_clipboard(file_name, image):
    sublime.status_message('%s copied to clipboard as Base64' % file_name)
    sublime.set_clipboard(image)


def get_image_info(file_name):
    name, extension = os.path.splitext(file_name)
    extension = extension.lower().replace('.', '')
    mime = None
    for m, extensions in mime_extensions.items():
        if extension in extensions:
            mime = m
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
