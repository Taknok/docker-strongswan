"""
This module contains common application exit codes and exceptions that map to them.
Author: Sascha Falk <sascha@falk-online.eu>
License: MIT License
"""


EXIT_CODE_SUCCESS                      = 0
EXIT_CODE_GENERAL_ERROR                = 1
EXIT_CODE_COMMAND_LINE_ARGUMENT_ERROR  = 2
EXIT_CODE_FILE_NOT_FOUND               = 3
EXIT_CODE_IO_ERROR                     = 4
EXIT_CODE_CONFIGURATION_EROR           = 5


# -----------------------------------------------------------------------------------------------------------------------------------------


class ExitCodeError(Exception):
    """
    Base class for exceptions that should let the application exit with a certain exit code.

    Attributes:
        exitcode (int) : Code the application should exit with.
        message (str)  : Explanation of the error.

    """

    def __init__(self):
        raise NotImplementedError("Please use the constructor taking an exit code and an error message describing what is wrong!")

    def __init__(self, exitcode, message, *args):
        self.exitcode = exitcode
        self.message = message.format(*args)


# -----------------------------------------------------------------------------------------------------------------------------------------


class GeneralError(ExitCodeError):
    """
    Exception that is raised, if an error occurs that cannot be specified any further.

    Attributes:
        message (str) : Explanation of the error.

    """

    def __init__(self):
        raise NotImplementedError("Please use the constructor taking an error message describing what is wrong!")

    def __init__(self, message, *args):
        super(CommandLineArgumentError, self).__init__(EXIT_CODE_GENERAL_ERROR, message, *args)


# -----------------------------------------------------------------------------------------------------------------------------------------


class CommandLineArgumentError(ExitCodeError):
    """
    Exception that is raised, if there is something wrong with specified command line arguments.

    Attributes:
        message (str) : Explanation of the error.

    """

    def __init__(self):
        raise NotImplementedError("Please use the constructor taking an error message describing what is wrong!")

    def __init__(self, message, *args):
        super(CommandLineArgumentError, self).__init__(EXIT_CODE_COMMAND_LINE_ARGUMENT_ERROR, message, *args)


# -----------------------------------------------------------------------------------------------------------------------------------------


class FileNotFoundError(ExitCodeError):
    """
    Exception that is raised, if a required file does not exist.

    Attributes:
        message (str) : Explanation of the error.

    """

    def __init__(self):
        raise NotImplementedError("Please use the constructor taking an error message describing what is wrong!")

    def __init__(self, message, *args):
        super(FileNotFoundError, self).__init__(EXIT_CODE_FILE_NOT_FOUND, message, *args)


# -----------------------------------------------------------------------------------------------------------------------------------------


class IoError(ExitCodeError):
    """
    Exception that is raised in case of i/o related errors.

    Attributes:
        message (str) : Explanation of the error.

    """

    def __init__(self):
        raise NotImplementedError("Please use the constructor taking an error message describing what is wrong!")

    def __init__(self, message, *args):
        super(IoError, self).__init__(EXIT_CODE_IO_ERROR, message, *args)


# -----------------------------------------------------------------------------------------------------------------------------------------


class ConfigurationError(ExitCodeError):
    """
    Exception that is raised when something with the container configuration is wrong.

    Attributes:
        message (str) : Explanation of the error.

    """

    def __init__(self):
        raise NotImplementedError("Please use the constructor taking an error message describing what is wrong!")

    def __init__(self, message, *args):
        super(ConfigurationError, self).__init__(EXIT_CODE_CONFIGURATION_ERROR, message, *args)


# -----------------------------------------------------------------------------------------------------------------------------------------
