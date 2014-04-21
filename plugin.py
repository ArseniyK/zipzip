import os
import locale
import zipimport

from zipfile import is_zipfile, ZipFile
from ConfigParser import ConfigParser


class Section:
    NAME = 'Name'
    DESCRIPTION = 'Description'
    VERSION = 'Version'
    AUTHOR = 'Author'


class ZipZip:
    def __init__(self, app):
        self.app = app
        self.user_path = self.app.user_plugin_path
        tab_number = self.app.preferences_window._tab_names['plugins']
        self._load_options_original = self.app.preferences_window._tabs.get_nth_page(tab_number)._load_options
        self.app.preferences_window._tabs.get_nth_page(tab_number)._load_options = self.load_options_hook

        self._load_plugins()
        #self._load_options()
        #self._get_plugin_list()

    def is_plugin(self, zip):
        with ZipFile(zip) as z:
            files = z.namelist()
            return 'plugin.py' in files

    def _get_plugin_list(self):
        if os.path.isdir(self.user_path):
            user_list = filter(lambda item: is_zipfile(os.path.join(self.user_path, item)), os.listdir(self.user_path))
            user_list = filter(lambda item: self.is_plugin(os.path.join(self.user_path, item)), user_list)

        return user_list

    def get_plugin_config(self, zip):
        with ZipFile(zip) as z:
            files = z.namelist()
            if 'plugin.conf' in files:
                return z.open('plugin.conf')

    def load_options_hook(self):
        self._load_options_original()
        self._load_options()

    def _load_options(self):
        """Load terminal tab options"""
        options = self.app.options

        # get list of plugins
        plugin_list = self._get_plugin_list()
        plugins_to_load = options.get('plugins')

        # extract current locale
        language = locale.getdefaultlocale()[0]

        # populate list
        for plugin in plugin_list:
            # default values
            plugin_name = plugin
            plugin_author = ''
            plugin_version = ''
            plugin_site = None
            plugin_contact = None
            plugin_description = _('This plugin has no description')

            # prefer user plugin over system version
            plugin_config = self.get_plugin_config(os.path.join(self.user_path, plugin))
            # read plugin data from configuration file
            if plugin_config:
                config = ConfigParser()
                config.readfp(plugin_config)

                if config.has_section(Section.NAME) and language is not None:
                    if config.has_option(Section.NAME, language):
                        # try to get plugin name for current language
                        plugin_name = config.get(Section.NAME, language)

                    elif config.has_option(Section.NAME, 'en'):
                        # try to get plugin name for default language
                        plugin_name = config.get(Section.NAME, 'en')

                if config.has_section(Section.AUTHOR):
                    # get author name
                    if config.has_option(Section.AUTHOR, 'name'):
                        plugin_author = config.get(Section.AUTHOR, 'name')

                    # get contact email
                    if config.has_option(Section.AUTHOR, 'contact'):
                        plugin_contact = config.get(Section.AUTHOR, 'contact')

                    if config.has_option(Section.AUTHOR, 'site'):
                        plugin_site = config.get(Section.AUTHOR, 'site')

                if config.has_section(Section.DESCRIPTION) and language is not None:
                    if config.has_option(Section.DESCRIPTION, language):
                        # try to get plugin description for current language
                        plugin_description = config.get(Section.DESCRIPTION, language)

                    elif config.has_option(Section.DESCRIPTION, 'en'):
                        # try to get plugin description for default language
                        plugin_description = config.get(Section.DESCRIPTION, 'en')

                if config.has_section(Section.VERSION):
                    if config.has_option(Section.VERSION, 'number'):
                        plugin_version = config.get(Section.VERSION, 'number')

            # add plugin data to list
            tab_number = self.app.preferences_window._tab_names['plugins']
            self.app.preferences_window._tabs.get_nth_page(tab_number)._plugins.append((
                plugin in plugins_to_load,
                plugin,
                plugin_name,
                plugin_author,
                plugin_version,
                plugin_contact,
                plugin_site,
                plugin_description
            ))

    def _load_plugins(self):
        options = self.app.options

        plugin_files = self._get_plugin_list()
        plugins_to_load = options.get('plugins')
        plugin_files = filter(lambda file_name: file_name in plugins_to_load, plugin_files)

        for plugin_zip in plugin_files:
            try:
                path = os.path.join(self.user_path, plugin_zip)
                zi = zipimport.zipimporter(path)
                plugin = zi.load_module('plugin')
                plugin.register_plugin(self.app)

            except Exception as error:
                print 'Error: Unable to load plugin "{0}": {1}'.format(plugin_zip, error)


def register_plugin(application):
    ZipZip(application)