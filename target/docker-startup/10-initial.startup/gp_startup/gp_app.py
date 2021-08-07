"""
This module contains the application class of the startup- and configuration script of the Griffin+ container startup system.
Author: Sascha Falk <sascha@falk-online.eu>
License: MIT License
"""

import os
import os.path
import importlib
from sys import argv

from .gp_extensions import classproperty
from .gp_helpers import print_error
from .gp_log import Log, CombinedLogger, StdioLogger, FileLogger, SyslogLogger

# -----------------------------------------------------------------------------------------------------------------------------------------


LOG_FILE_PATH = "/var/log/gp-startup.log"


# -----------------------------------------------------------------------------------------------------------------------------------------


class AppImpl(object):
    "The startup application."

    # -------------------------------------------------------------------------------------------------------------------------------------


    def __init__(self):
        pass


    # -------------------------------------------------------------------------------------------------------------------------------------


    def run(self):

        # assume everything will work
        exitcode = None

        # configure the logging subsystem
        self.configure_logging()

        Log.write_info('--- Griffin+ Container Startup System')
        Log.write_info('--------------------------------------------------------------------------------')

        # load command processor plugins
        command_processors = self.load_command_processors()

        # let command processors process the command
        exitcode = None
        for processor in command_processors:
            code = processor.process(tuple(argv[1:]))
            if code != None:
                exitcode = code
                if exitcode != 0: break

        # 'run' or 'run-and-enter' may be missing, but that's ok for the base image
        if exitcode == None and (len(argv) > 1 and argv[1].lower() == "run" or argv[1].lower() == "run-and-enter"):
            Log.write_error("Could not find a command processor plugin that handles '{0}'.", argv[1])
            Log.write_error("Please implement a command processor plugin that handles 'run' and 'run-and-enter' appropriately.")
            exitcode = 0

        # print error, if the command was not handled
        if exitcode == None:
            print_error('Unknown command ({0}).', argv[1:])
            exitcode = 127

        Log.write_info('--------------------------------------------------------------------------------')
        Log.write_info('--- Griffin+ Container Startup System exited with code ({0})'.format(exitcode))

        return exitcode


    # -------------------------------------------------------------------------------------------------------------------------------------


    def configure_logging(self):
        """
        Configures the verbosity of the startup script depending on the environment variable STARTUP_VERBOSITY.
        The value must be an integer value. Valid values are:
        - 0 = logging disabled
        - 1 = error only
        - 2 = error and warning
        - 3 = error, warning and note
        - 4 = error, warning, note and info
        - 5 = all messages (error, warning, note, info, debug)

        """

        # select the appropriate loggers (depends on the specified commands)
        # ---------------------------------------------------------------------
        # - run / run-and-enter : stdio + syslog (if /dev/log is present)
        #                       : stdio + file (if /dev/log is not present)
        # - other commands      : syslog (if /dev/log is present)
        #                       : file (if /dev/log is not present)
        # ---------------------------------------------------------------------
        use_syslog = os.path.exists("/dev/log")
        if argv[1] == "run" or argv[1] == "run-and-enter":
            logger = CombinedLogger(StdioLogger())
            if use_syslog: logger.add(SyslogLogger())
            else:          logger.add(FileLogger(LOG_FILE_PATH))
        else:
            if use_syslog: logger = SyslogLogger()
            else:          logger = FileLogger(LOG_FILE_PATH)
        Log.instance = logger

        # set log verbosity
        # ---------------------------------------------------------------------
        value = os.environ.get('STARTUP_VERBOSITY')
        if value:
            value = int(value, 10)
            Log.set_verbosity(value)


    # -------------------------------------------------------------------------------------------------------------------------------------


    def load_command_processors(self):
        """
        Loads command processor plugins brought along via images deriving from the base docker image.
        The plugins are expected to be located within the gp_startup package in subfolder 'plugins'.
        The file name of plugin module must start with 'gp_cmdproc_' to be found by this function.
        The plugin module must declare the following things:
        - a global boolean variable named 'enabled' that specified whether the plugin should be run or not.
        - a global string variable named 'processor_name' that specifies the name of the command processor the plugin will set up.
        - a global function named 'get_processor' (no parameters) that returns an instance of a class that derives from
          the command processor plugin base class (CommandProcessor).
        """
    
        Log.write_debug('Loading command processor plugins...')
        processors = []
        script_dir = os.path.dirname(os.path.abspath(__file__))
        plugins_directory_path = os.path.realpath(os.path.join(script_dir, 'plugins'))
        for file in sorted(os.listdir(plugins_directory_path)):
            if (file.startswith('gp_cmdproc_') and file.endswith(".py")):
                Log.write_debug('Trying to load command processor plugin module \'{0}\'.'.format(file))
                module_name = '.plugins.' + '.'.join(file.split('.')[0:-1])
                module = importlib.import_module(module_name, __package__)
                Log.write_debug('Loading command processor plugin module \'{0}\' succeeded.'.format(file))
                if (module.enabled == True):
                    Log.write_debug('Trying to instantiate the command processor class...')
                    processors.append(module.get_processor())
                    Log.write_debug('Command processor was instantiated successfully.')
                else:
                    Log.write_debug('Skipping command processor module, since it is disabled.')
        Log.write_debug('Finished loading command processor plugins.')
        return processors


# -----------------------------------------------------------------------------------------------------------------------------------------


class App(object):
    """The application class."""

    __instance = None;

    @classproperty
    def instance(cls):
        if not App.__instance:
            App.__instance = AppImpl()
        return App.__instance

    @classmethod
    def run(cls):
        return App.instance.run()


# -----------------------------------------------------------------------------------------------------------------------------------------


