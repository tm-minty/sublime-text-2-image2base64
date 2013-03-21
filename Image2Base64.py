#encoding=utf8
import sublime, sublime_plugin
import os, base64


class Image2Base64(sublime_plugin.EventListener):
    def on_load(self, view):
        if view.file_name():
            fileName, fileExtension = os.path.splitext(view.file_name())
            extension = fileExtension.lower().replace('.','')
            for mime, extensions in mime_extensions.items():
                if extension in extensions:
                    image = convert_image(view, mime)
                    if image:
                        view.run_command("i2b64_change", {"image": image})
                        #view.run_command("i2b64_panel", {"image": image})
                    break


class I2b64Change(sublime_plugin.TextCommand):
    def run(self, edit, image):
        view = self.view
        view.set_scratch(True)
        view.replace(edit, sublime.Region(0, view.size()), image)
        view.set_read_only(True)
        view.run_command("select_all")


class I2b64Panel(sublime_plugin.TextCommand):
    def run(self, edit, image):
        window = self.view.window()
        self.image = image
        print("window")
        items = []
        items.append("Copy base64 image to clipboard")
        items.append("Don't copy base64 image to clipboard")
        print(items)
        window.show_quick_panel(items, self.on_done)

    def on_done(self, selected):
        if selected == 0:
            print(self.image)


mime_extensions = {
        "image/gif":        ["gif"],
        "image/jpeg":       ["jpg","jpeg","jpe"],
        "image/png":        ["png"],
        "image/x-icon":     ["ico"],
        "image/x-ms-bmp":   ["bmp"],
    }


def convert_image(view, mime):
    with open(view.file_name(), "rb") as image_file:
        encoded_bytes = base64.b64encode(image_file.read())
        return 'data:%s;base64,%s' % (mime, encoded_bytes.decode())
    return None
