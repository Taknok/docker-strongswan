"""
This module contains the base class for command processor plugins.
Author: Sascha Falk <sascha@falk-online.eu>
License: MIT License
"""

import abc
import sys
from .gp_log import Log
from .gp_helpers import print_error, readline_if_no_tty
from .gp_errors import *


# -------------------------------------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------------------------------------


class PositionalArgument(object):
    """
    A positional argument definition (needed when registering a command handler).

    """

    def __init__(self):
        raise NotImplementedError("Please use the parameterized constructor.")

    def __init__(self, name):
        """
        Initializes a new instance of the NamedArgument class.

        Args:
            name (str) : Name of the parameter

        """
        self.name = name


# -------------------------------------------------------------------------------------------------------------------------------------------------------------
# NamedArgument Class
# -------------------------------------------------------------------------------------------------------------------------------------------------------------


class NamedArgument(object):
    """
    A named argument definition (needed when registering a command handler).

    """

    def __init__(self):
        raise NotImplementedError("Please use the parameterized constructor.")

    def __init__(self, name, from_stdin = False, min_occurrence = 0, max_occurrence = 1):
        """
        Initializes a new instance of the NamedArgument class.

        Args:
            name (str)           : Name of the parameter following the leading '--'
            from_stdin (bool)    : True to read the variable from the command line and from stdin as well (command line has precedence);
                                   False to read the variable from the command line only
            min_occurrence (int) : Minimum number of occurrences
            max_occurrence (int) : Maximum number of occurrences

        """
        if not type(name) is str:           raise TypeError("Argument 'name' must be str.")
        if not type(from_stdin) is bool:    raise TypeError("Argument 'from_stdin' must be bool.")
        if not type(min_occurrence) is int: raise TypeError("Argument 'min_occurrence' must be int.")
        if not type(max_occurrence) is int: raise TypeError("Argument 'max_occurrence' must be int.")

        if min_occurrence > max_occurrence:
            raise ValueError("Maximum number of arguments must not exceed the minimum number.")

        if from_stdin and max_occurrence > 1:
            raise ValueError("The argument must occur only once, if it should be read from stdin as well.")

        self.name = name
        self.from_stdin = from_stdin
        self.min_occurrence = min_occurrence
        self.max_occurrence = max_occurrence


# -------------------------------------------------------------------------------------------------------------------------------------------------------------
# CommandProcessor
# -------------------------------------------------------------------------------------------------------------------------------------------------------------


class CommandProcessor(object):
    "Base class for a command processor."

    __metaclass__ = abc.ABCMeta

    # -------------------------------------------------------------------------------------------------------------------------------------


    __cmdline_handlers = None
    __exception_handlers = None


    # -------------------------------------------------------------------------------------------------------------------------------------


    def __init__(self):
        """
        Constructor.

        """
        self.__cmdline_handlers = []
        self.__exception_handlers = []


    # -------------------------------------------------------------------------------------------------------------------------------------


    def add_handler(self, handler, *args):
        """
        Adds a command line handler that handles commands with the specified positional arguments.

        Args:
            handler (callable)  : Handler to invoke
            args (tuple) : Positional command line argument definitions (PositionalArgument) that must match in the specified order to
                           invoke the handler and named command line argument definitions (NamedArgument) that are allowed in conjunction
                           with the command

        """

        pos_args = []
        named_args = []
        for arg in args:
            if type(arg) is PositionalArgument: pos_args.append(arg)
            elif type(arg) is NamedArgument: named_args.append(arg)
            else: raise TypeError("Only 'PositionalArgument' and 'NamedArgument' objects are expected, you specified a {0}.".format(type(arg)))

        self.__cmdline_handlers.append((handler, pos_args, named_args))


    # -------------------------------------------------------------------------------------------------------------------------------------


    def add_exception_handler(self, handler, exception_type):
        """
        Adds an exception handler that is called, when an exception of the specified type is thrown by a command line handler.

        Args:
            handler (callable)    : Handler to invoke
            exception_type (type) : Type of the exception to handle
        """

        self.__exception_handlers.append((handler, exception_type))


    # -------------------------------------------------------------------------------------------------------------------------------------


    def process(self, args):
        """
        Processes a custom command.

        Derived classes can register handlers by adding a member method with the signature
        handler(self,pos_args,named_args) to the '__cmdline_handlers' variable. Each registration consists of a tuple.
        The first element of the tuple is the handler method to call. The second element of the tuple is another tuple
        containing the positional arguments that must match the command line arguments to call the handler. The handler
        with the most fitting arguments is called.

        You may implement your own command processing logic by overriding this method.

        Args:
            args (tuple): Command line arguments of the application.

        Returns:
            The exit code of the command;
            None, if the command was not handled

        """

        # split up positional arguments and named arguments
        # -------------------------------------------------------------------------------------------------------------
        specified_positional_arguments = []
        specified_named_arguments = {}
        for arg in args:
            arg = arg.strip()
            if arg.startswith("--"):
                arg = arg[2:]
                arg_tokens = arg.split("=")
                key = arg_tokens[0].lower().strip()
                if len(key) > 0:
                    if not key in specified_named_arguments: specified_named_arguments[key] = []
                    specified_named_arguments[key].append("=".join(arg_tokens[1:]))
                else:
                    error = "Invalid named argument format."
                    Log.write_error(error)
                    if not Log.uses_stdio: print_error(error)
                    return EXIT_CODE_COMMAND_LINE_ARGUMENT_ERROR
            else:
                specified_positional_arguments.append(arg)

        # find handler with a signature that matches best
        # -------------------------------------------------------------------------------------------------------------

        best_fit_index = -1
        best_fit_count = -1
        for (index, registration) in enumerate(self.__cmdline_handlers):

            method                        = registration[0]  # function
            expected_positional_arguments = registration[1]  # list of PositionalArgument

            # skip, if the handler needs more arguments than specified
            if len(expected_positional_arguments) > len(specified_positional_arguments): continue

            # determine the number of matching arguments
            match_count = 0
            for i in range(len(expected_positional_arguments)):
                if (args[i].lower() != expected_positional_arguments[i].name.lower()): break
                match_count = match_count + 1

            # keep the handler with the most matching arguments
            if (match_count == len(expected_positional_arguments) and match_count > best_fit_count):
                best_fit_count = match_count
                best_fit_index = index

        # call the determined command handler
        # -------------------------------------------------------------------------------------------------------------

        if best_fit_index != -1:

            try:

                handler                  = self.__cmdline_handlers[best_fit_index][0]  # function
                expected_named_arguments = self.__cmdline_handlers[best_fit_index][2]  # list

                # check whether all specified named arguments are expected and within bounds
                # -------------------------------------------------------------------------------------------------------------------------
                not_specified_named_arguments = expected_named_arguments[:]
                for arg_name, arg_values in specified_named_arguments.items():

                    # find definition of the named argument
                    arg_def = None
                    for x in expected_named_arguments:
                        if arg_name.lower() == x.name:
                            arg_def = x
                            if arg_def in not_specified_named_arguments:
                                not_specified_named_arguments.remove(arg_def)
                            break

                    # abort, if the argument does not have a definition (=> argument is not allowed)
                    if arg_def == None:
                        error = "The named argument '--{0}' is not allowed in conjunction with the specified positional arguments.".format(arg_name)
                        Log.write_error(error)
                        if not Log.uses_stdio: print_error(error)
                        return EXIT_CODE_COMMAND_LINE_ARGUMENT_ERROR

                    if len(arg_values) < arg_def.min_occurrence:
                        error = "The named argument '--{0}' is required at least {1} times.".format(arg_name, arg_def.min_occurrence)
                        Log.write_error(error)
                        if not Log.uses_stdio: print_error(error)
                        return EXIT_CODE_COMMAND_LINE_ARGUMENT_ERROR

                    if len(arg_values) > arg_def.max_occurrence:
                        error = "The named argument '--{0}' is allowed at maximum {1} times.".format(arg_name, arg_def.max_occurrence)
                        Log.write_error(error)
                        if not Log.uses_stdio: print_error(error)
                        return EXIT_CODE_COMMAND_LINE_ARGUMENT_ERROR

                # craft the effective named arguments
                # -------------------------------------------------------------------------------------------------------------------------
                effective_named_arguments = {}
                for arg_def in expected_named_arguments:

                    Log.write_debug("Evaluating named argument '{0}'...", arg_def.name)

                    effective_argument_values = []

                    # read from stdin, if configured
                    arg_value_from_stdin = None
                    if arg_def.from_stdin and arg_def.max_occurrence == 1:
                         arg_value_from_stdin = readline_if_no_tty()
                         if arg_value_from_stdin != None:
                             Log.write_debug("=> Reading from stdin returned '{0}'.", arg_value_from_stdin)
                             if arg_def in not_specified_named_arguments:
                                 not_specified_named_arguments.remove(arg_def)
                         elif sys.stdin.isatty():
                             Log.write_debug("=> Reading from stdin does not work, running in terminal mode.")
                             if arg_def in not_specified_named_arguments:
                                 not_specified_named_arguments.remove(arg_def)
                         else:
                             Log.write_debug("=> Reading from stdin failed. Not enough data piped in?")

                    # read values of named arguments
                    if arg_def.name in specified_named_arguments:
                        arg_values = specified_named_arguments[arg_def.name]
                        for arg_value in arg_values:
                            Log.write_debug("=> Reading from command line returned '{0}'.", arg_value)
                            effective_argument_values.append(arg_value)

                    # apply the value read from stdin, if the corresponding named argument was not specified
                    if len(effective_argument_values) == 0 and arg_value_from_stdin != None:
                        effective_argument_values.append(arg_value_from_stdin)

                    # keep argument
                    effective_named_arguments[arg_def.name] = effective_argument_values

                # check whether required named arguments have been specified
                # -------------------------------------------------------------------------------------------------------------------------
                for arg_def in not_specified_named_arguments:
                    if arg_def.min_occurrence > 0:
                        error = "The named argument '--{0}' must be specified. ".format(arg_def.name)
                        Log.write_error(error)
                        if not Log.uses_stdio: print_error(error)
                        return EXIT_CODE_COMMAND_LINE_ARGUMENT_ERROR

                # invoke handler
                # -------------------------------------------------------------------------------------------------------------------------
                exitcode = handler(specified_positional_arguments, effective_named_arguments)
                if not type(exitcode) is int: raise RuntimeError('The command line handler did not return an exit code.')
                return exitcode

            except Exception as e:

                # try to call registered exception handler
                for exception_handler in self.__exception_handlers:
                    if exception_handler[1] == type(e):
                        return exception_handler[0](e)

                # handle exceptions that are associated with exit codes
                if isinstance(e, ExitCodeError):
                    print_error(e.message)
                    return e.exitcode

                raise

        else:

            # Command was not processed...
            return None


    # -------------------------------------------------------------------------------------------------------------------------------------
