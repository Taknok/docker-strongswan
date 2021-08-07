"""
This module contains logging functions.
Author: Sascha Falk <sascha@falk-online.eu>
License: MIT License
"""

import abc
import datetime
import os
import socket
import sys

from syslog import syslog, openlog, closelog, \
                   LOG_EMERG, LOG_ALERT, LOG_CRIT, LOG_ERR, LOG_WARNING, LOG_NOTICE, LOG_INFO, LOG_DEBUG, \
                   LOG_KERN, LOG_USER, LOG_MAIL, LOG_DAEMON, LOG_AUTH, LOG_LPR, LOG_NEWS, LOG_UUCP, LOG_CRON, LOG_SYSLOG, \
                   LOG_LOCAL0, LOG_LOCAL1, LOG_LOCAL2, LOG_LOCAL3, LOG_LOCAL4, LOG_LOCAL5, LOG_LOCAL6, LOG_LOCAL7

from .gp_extensions import classproperty


# ---------------------------------------------------------------------------------------------------------------------


class LoggerBase(object):
    """
    Base class for custom loggers.

    """

    __metaclass__ = abc.ABCMeta

    _debug_level_enabled = False
    _info_level_enabled = False
    _note_level_enabled = False
    _warning_level_enabled = False
    _error_level_enabled = False


    def __init__(self):
        """
        Initializes the object.

        """
        self.set_verbosity(4) # all levels except 'debug'


    @abc.abstractmethod
    def write_debug(self, text, *args):
        """
        Writes a debug message to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        raise NotImplementedError("The method is abstract.")


    @abc.abstractmethod
    def write_info(self, text, *args):
        """
        Writes an informational message to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        raise NotImplementedError("The method is abstract.")


    @abc.abstractmethod
    def write_note(self, text, *args):
        """
        Writes a note to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        raise NotImplementedError("The method is abstract.")


    @abc.abstractmethod
    def write_warning(self, text, *args):
        """
        Writes a warning to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        raise NotImplementedError("The method is abstract.")


    @abc.abstractmethod
    def write_error(self, text, *args):
        """
        Writes an error to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        raise NotImplementedError("The method is abstract.")


    @property
    def uses_stdio(self):
        """
        Gets a value indicating whether the log writes to stdout/stderr.

        Returns:
            Always False.

        """
        return False


    def set_verbosity(self, level):
        """
        Sets the verbosity of startup system.

        Args:
            level (int): The minimum severity level of log messages to show:
                0 = logging disabled 
                1 = error only
                2 = error and warning
                3 = error, warning and note
                4 = error, warning, note and info
                5 = all messages (error, warning, note, info, debug)

        """
        self._error_level_enabled = level > 0
        self._warning_level_enabled = level > 1
        self._note_level_enabled = level > 2
        self._info_level_enabled = level > 3
        self._debug_level_enabled = level > 4


# ---------------------------------------------------------------------------------------------------------------------


class StdioLogger(LoggerBase):
    """
    A logger that writes messages to stdio/stderr.

    """

    def __init__(self):
        """
        Initializes the object.

        """
        super().__init__()


    def write_debug(self, text, *args):
        """
        Writes a debug message to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        if not self._debug_level_enabled: return
        message = str(datetime.datetime.now()) + ' [debug] ' + text.format(*args) + '\n'
        sys.stdout.write(message)


    def write_info(self, text, *args):
        """
        Writes an informational message to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        if not self._info_level_enabled: return
        message = str(datetime.datetime.now()) + ' [info] ' + text.format(*args) + '\n'
        sys.stdout.write(message)


    def write_note(self, text, *args):
        """
        Writes a note to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        if not self._note_level_enabled: return
        message = str(datetime.datetime.now()) + ' [note] ' + text.format(*args) + '\n'
        sys.stdout.write(message)


    def write_warning(self, text, *args):
        """
        Writes a warning to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        if not self._warning_level_enabled: return
        message = str(datetime.datetime.now()) + ' [warning] ' + text.format(*args) + '\n'
        sys.stdout.write(message)


    def write_error(self, text, *args):
        """
        Writes an error to the log.

        Args:
            text (str): Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        if not self._error_level_enabled: return
        message = str(datetime.datetime.now()) + ' [error] ' + text.format(*args) + '\n'
        sys.stderr.write(message)


    @property
    def uses_stdio(self):
        """
        Gets a value indicating whether the log writes to stdout/stderr.

        Returns:
            Always True.

        """
        return True


# ---------------------------------------------------------------------------------------------------------------------


class FileLogger(LoggerBase):
    """
    A logger that writes messages to a file.

    """

    __path = None

    def __init__(self, path):
        """
        Initializes the object.

        Args:
            path (str) : Path of the log file to write to.

        """
        super().__init__()
        self.__path = path


    def write_debug(self, text, *args):
        """
        Writes a debug message to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        if not self._debug_level_enabled: return
        message = str(datetime.datetime.now()) + ' [debug] ' + text.format(*args) + '\n'
        with open(self.__path, "a+", encoding="utf-8") as text_file:
           text_file.write(message)


    def write_info(self, text, *args):
        """
        Writes an informational message to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        if not self._info_level_enabled: return
        message = str(datetime.datetime.now()) + ' [info] ' + text.format(*args) + '\n'
        with open(self.__path, "a+", encoding="utf-8") as text_file:
           text_file.write(message)


    def write_note(self, text, *args):
        """
        Writes a note to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        if not self._note_level_enabled: return
        message = str(datetime.datetime.now()) + ' [note] ' + text.format(*args) + '\n'
        with open(self.__path, "a+", encoding="utf-8") as text_file:
           text_file.write(message)


    def write_warning(self, text, *args):
        """
        Writes a warning to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        if not self._warning_level_enabled: return
        message = str(datetime.datetime.now()) + ' [warning] ' + text.format(*args) + '\n'
        with open(self.__path, "a+", encoding="utf-8") as text_file:
           text_file.write(message)


    def write_error(self, text, *args):
        """
        Writes an error to the log.

        Args:
            text (str): Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        if not self._error_level_enabled: return
        message = str(datetime.datetime.now()) + ' [error] ' + text.format(*args) + '\n'
        with open(self.__path, "a+", encoding="utf-8") as text_file:
           text_file.write(message)


# ---------------------------------------------------------------------------------------------------------------------


class SyslogLogger(LoggerBase):
    """
    A logger that writes messages to syslog.

    """

    __ident = None
    __facility = LOG_LOCAL5

    def __init__(self):
        """
        Initializes the logger.

        """
        super().__init__()

        # use the container name as ident
        self.__ident = "Docker ({0})".format(socket.gethostname())


    def write_debug(self, text, *args):
        """
        Writes a debug message to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        if not self._debug_level_enabled: return
        message = text.format(*args)
        openlog(ident = self.__ident, facility = self.__facility)
        syslog(LOG_DEBUG, message)
        closelog()


    def write_info(self, text, *args):
        """
        Writes an informational message to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        if not self._debug_level_enabled: return
        message = text.format(*args)
        openlog(ident = self.__ident, facility = self.__facility)
        syslog(LOG_INFO, message)
        closelog()


    def write_note(self, text, *args):
        """
        Writes a note to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        if not self._note_level_enabled: return
        message = text.format(*args)
        openlog(ident = self.__ident, facility = self.__facility)
        syslog(LOG_NOTICE, message)
        closelog()


    def write_warning(self, text, *args):
        """
        Writes a warning to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        if not self._warning_level_enabled: return
        message = text.format(*args)
        openlog(ident = self.__ident, facility = self.__facility)
        syslog(LOG_WARN, message)
        closelog()


    def write_error(self, text, *args):
        """
        Writes an error to the log.

        Args:
            text (str): Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        if not self._error_level_enabled: return
        message = text.format(*args)
        openlog(ident = self.__ident, facility = self.__facility)
        syslog(LOG_ERR, message)
        closelog()


# ---------------------------------------------------------------------------------------------------------------------


class CombinedLogger(LoggerBase):
    """
    A logger that combines multiple other loggers.

    """

    __loggers = []

    def __init__(self, *loggers):
        """
        Initializes the combined logger.

        Args:
            loggers (LoggerBase) : Loggers to combine.

        """
        super().__init__()
        self.__loggers.extend(loggers)


    def write_debug(self, text, *args):
        """
        Writes a debug message to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        for logger in self.__loggers:
            logger.write_debug(text, *args)


    def write_info(self, text, *args):
        """
        Writes an informational message to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        for logger in self.__loggers:
            logger.write_info(text, *args)


    def write_note(self, text, *args):
        """
        Writes a note to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        for logger in self.__loggers:
            logger.write_note(text, *args)


    def write_warning(self, text, *args):
        """
        Writes a warning to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        for logger in self.__loggers:
            logger.write_warning(text, *args)


    def write_error(self, text, *args):
        """
        Writes an error to the log.

        Args:
            text (str): Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        for logger in self.__loggers:
            logger.write_error(text, *args)


    def set_verbosity(self, level):
        """
        Sets the verbosity of startup system.

        Args:
            level (int): The minimum severity level of log messages to show:
                0 = error only
                1 = error and warning
                2 = error, warning and note
                3 = all messages (error, warning, note, debug)

        """
        for logger in self.__loggers:
            logger.set_verbosity(level)


    @property
    def uses_stdio(self):
        """
        Gets a value indicating whether the log writes to stdout/stderr.

        Returns:
            True, if the log writes to stdout/stderr; otherwise False.

        """
        for logger in self.__loggers:
            use = logger.uses_stdio
            if use: return True
        return False


    def add(self, logger):
        """
        Adds a logger to the combined logger.

        Args:
            logger (LoggerBase) : Logger to add.

        """
        if not isinstance(logger, LoggerBase):
            raise ValueError("The specified logger does not derive from 'LoggerBase'.")

        self.__loggers.append(logger)


# ---------------------------------------------------------------------------------------------------------------------


class Log(object):
    """
    The application's log.

    """

    __instance = None


    @classproperty
    def instance(cls):
        """
        Gets the singleton instance of the Log.

        """
        if not Log.__instance:
            Log.__instance = StdioLogger()
        return Log.__instance


    @instance.setter
    def instance(cls, value):
        """
        Sets the singleton instance of the Log.

        """
        Log.__instance = value


    @staticmethod
    def write_debug(text, *args):
        """
        Writes a debug message to the log.

        Args:
            text (str)  : Text to write to the log.
            args (list) : Arguments to use when formatting the text.

        """
        Log.instance.write_debug(text, *args)


    @staticmethod
    def write_info(text, *args):
        """
        Writes an informational message to the log.

        Args:
            text (str)   : Text to write to the log.
            args (tuple) : Arguments to use when formatting the text.

        """
        Log.instance.write_info(text, *args)


    @staticmethod
    def write_note(text, *args):
        """
        Writes a note to the log.

        Args:
            text (str)  : Text to write to the log.
            args (list) : Arguments to use when formatting the text.

        """
        Log.instance.write_note(text, *args)


    @staticmethod
    def write_warning(text, *args):
        """
        Writes a warning to the log.

        Args:
            text (str)  : Text to write to the log.
            args (list) : Arguments to use when formatting the text.

        """
        Log.instance.write_warning(text, *args)


    @staticmethod
    def write_error(text, *args):
        """
        Writes an error to the log.

        Args:
            text (str)  : Text to write to the log.
            args (list) : Arguments to use when formatting the text.

        """
        Log.instance.write_error(text, *args)


    @classproperty
    def uses_stdio(cls):
        """
        Gets a value indicating whether the log writes to stdout/stderr.

        Returns:
            True, if the log writes to stdout/stderr; otherwise False.

        """
        return Log.instance.uses_stdio


    @staticmethod
    def set_verbosity(level):
        """
        Sets the verbosity of startup system.

        Args:
            level (int): The minimum severity level of log messages to show:
                0 = logging disabled 
                1 = error only
                2 = error and warning
                3 = error, warning and note
                4 = error, warning, note and info
                5 = all messages (error, warning, note, info, debug)

        """
        Log.instance.set_verbosity(level)
