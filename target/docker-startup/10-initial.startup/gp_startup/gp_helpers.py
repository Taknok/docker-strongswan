"""
This module contains some helper functions used within the startup script.
Author: Sascha Falk <sascha@falk-online.eu>
License: MIT License
"""

import chardet
import dns.resolver
import dns.rdtypes
import os
import platform
import re
import shutil
import subprocess
import sys

from .gp_log import Log


###################################################################################################################################################################################
# console helpers
###################################################################################################################################################################################


def print_error(message, *args):
    """
    Prints a formatted message to stderr.

    Args:
        message (str) : Message to print (may contain placeholders)
        args (tuple)  : Arguments to use when formatting the message
    """
    print("ERROR: " + message.format(*args), file=sys.stderr)


def readline_if_no_tty():
    """
    Reads a line from stdin, if the container is running without an attached pseudo TTY.

    Returns:
        The line read from stdin (excl. the newline character);
        None, if a preudo TTY is attached to the container or stdin is at EOF.
    """
    if not sys.stdin.isatty():
        line = sys.stdin.readline()
        if len(line) > 0:
            return line.rstrip()
    return None


###################################################################################################################################################################################
# file system operations
###################################################################################################################################################################################


def read_text_file(filename, encoding = None):
    """
    Reads a text file (detects the encoding automatically).

    Args:
        filename (str)           : Name of the text file to read.
        encoding (str, optional) : Encoding to enforce (None to try to detect the encoding automatically).

    Returns:
        The content of the specified file as a string.

    """
    with open(filename, 'rb') as file:
        if not encoding:
            raw = file.read(32)
            encoding = chardet.detect(raw)['encoding']
        with open(filename, encoding=encoding) as file:
            text = file.read()
        return text, encoding


# ---------------------------------------------------------------------------------------------------------------------


def write_text_file(filename, encoding, text):
    """
    Writes a text file.

    Args:
        filename (str) : Name of the text file to write.
        encoding (str) : Encoding to use.
        text (str)     : Text to write into the file.

    """
    with open(filename, 'w', encoding=encoding) as file:
        file.write(text)


# ---------------------------------------------------------------------------------------------------------------------


def touch_file(path):
    """
    Touches the specified file.

    Args:
        path (str) : Path of the file to touch.

    """
    with open(path, 'a'):
        os.utime(path, None)


# ---------------------------------------------------------------------------------------------------------------------


def copy_directory(src_path, dest_path):
    """
    Copies an entire directory retaining permissions and ownership information.

    Args:
        src_path (str)  : Path of the directory to copy from.
        dest_path (str) : Path of the directory to copy to.

    """

    os.mkdir(dest_path)

    for subdir, dirs, files in os.walk(src_path):

        relative_subdir = os.path.relpath(subdir, src_path)

        # adjust owner/group and stats of the current subdir
        if platform.system() == 'Linux':
            built_src_path = os.path.normpath(os.path.join(src_path, relative_subdir))
            built_dest_path = os.path.normpath(os.path.join(dest_path, relative_subdir))
            shutil.copystat(src_path, dest_path)
            src_stat = os.stat(built_src_path)
            os.chown(built_dest_path, src_stat.st_uid, src_stat.st_gid)

        for filename in files:
            built_src_path = os.path.normpath(os.path.join(src_path, relative_subdir, filename))
            built_dest_path = os.path.normpath(os.path.join(dest_path, relative_subdir, filename))
            shutil.copy(built_src_path, built_dest_path)
            if platform.system() == 'Linux':
                shutil.copystat(built_src_path, built_dest_path)
                src_stat = os.stat(built_src_path)
                os.chown(built_dest_path, src_stat.st_uid, src_stat.st_gid)

        for dirname in dirs:
            built_src_path = os.path.normpath(os.path.join(src_path, relative_subdir, dirname))
            built_dest_path = os.path.normpath(os.path.join(dest_path, relative_subdir, dirname))
            os.mkdir(built_dest_path)
            if platform.system() == 'Linux':
                shutil.copystat(built_src_path, built_dest_path)
                src_stat = os.stat(built_src_path)
                os.chown(built_dest_path, src_stat.st_uid, src_stat.st_gid)


# ---------------------------------------------------------------------------------------------------------------------


def remove_tree(path):
    """
    Removes the specified directory recursively.

    Args:
        path (str) : Path of the directory to remove recursively.

    """

    if os.path.isdir(path):
        files_to_remove = []
        files_to_remove.append((path, os.rmdir))
        for subdir, dirs, files in os.walk(path):
            for filename in files:
                file_path = os.path.join(subdir, filename)
                files_to_remove.append((file_path, os.remove))
            for dirname in dirs:
                dir_path = os.path.join(subdir, dirname)
                if os.path.islink(dir_path):
                    files_to_remove.append((dir_path, os.remove))
                else:
                    files_to_remove.append((dir_path, os.rmdir))
        files_to_remove.sort(key=lambda x: x[0], reverse=True)
        for file_path, remove_func in files_to_remove:
            remove_func(file_path)


###################################################################################################################################################################################
# manipulating PHP files
###################################################################################################################################################################################


def replace_php_define(text, define, value):
    """
    Replaces a named constaint (define) in PHP code.
    
    Args:
        text (str)      : The PHP code to process.
        define (str)    : Name of the named constant to modify.
        value (int,str) : Value to set the 'define' to.

    Returns:
        The modified PHP code.

    """
    if isinstance(value, str): replacement = '\g<1>\'{0}\'\g<2>'.format(value)
    elif isinstance(value,int): replacement = '\g<1>{0}\g<2>'.format(value)
    else: raise RuntimeError('Datatype is not supported.')
    regex = '^(\s*define\s*\(\s*\'{0}\'\s*,\s*).*(\s*\)\s*;.*)'.format(re.escape(define))
    text,substitutions = re.subn(regex, replacement, text, 1, re.MULTILINE | re.UNICODE)
    if substitutions == 0: raise RuntimeError('Named constant \'{0}\' is not part of the specified php code.'.format(define))
    return text


# ---------------------------------------------------------------------------------------------------------------------


def replace_php_variable(text, variable, value):
    """
    Replaces a variable assignment in PHP code.

    Args:
        text (str)      : The PHP code to process.
        variable (str)  : Name of the PHP variable to modify.
        value (int,str) : Value to set the variable to.

    Returns:
        The modified PHP code.

    """
    if isinstance(value, str): replacement = '\g<1>\'{0}\'\g<2>'.format(value)
    elif isinstance(value,int): replacement = '\g<1>{0}\g<2>'.format(value)
    else: raise RuntimeError('Datatype is not supported.')
    regex = '^(\s*\${0}\s*=\s*).*(;.*)'.format(re.escape(variable))
    text,substitutions = re.subn(regex, replacement, text, 1, re.MULTILINE | re.UNICODE)
    if substitutions == 0: raise RuntimeError('Variable \'${0}\' is not part of the specified php code.'.format(variable))
    return text


###################################################################################################################################################################################
# password helpers
###################################################################################################################################################################################


def generate_password(length, chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ0123456789+-*/!ยง$%&#;:,.~^<>{}[]()"):
    """
    Generated a random password of the specified length.

    Args:
        length (int)          : Length of the password to generate.
        chars (str, optional) : String containing chars allowed in the generated password.

    Returns:
        The generated password.

    """
    if not isinstance(length, int) or length < 1:
        raise ValueError("length must have positive length")
    return "".join(chars[int(c) % len(chars)] for c in os.urandom(length))


###################################################################################################################################################################################
# settings in environment variables
###################################################################################################################################################################################


def get_env_setting_bool(var_name, default_value = None):
    """
    Gets the value of the specified environment variable as a boolean value.

    This method gets the value of the specified environment variable as a boolean value and returns the specified
    default value, if the environment variable is not set. The following values are supported:
    - '0' or 'false' (case-invariant) => False
    - '1' or 'true' (case-invariant)  => True

    Args:
        var_name (str)       : Name of the environment variable to get.
        default_value (bool) : Default value to return, if the environment variable is not set.

    Returns:
        The value of the environment variable (if set), otherwise the default value is returned.

    """
    value = os.environ.get(var_name)
    if value:
        if value == '0' or value.lower() == 'false':
            Log.write_info('Environment variable \'{0}\' is set to \'false\'.'.format(var_name))
            return False
        elif value == '1' or value.lower() == 'true':
            Log.write_info('Environment variable \'{0}\' is set to \'true\'.'.format(var_name))
            return True
        else:
            error = 'Environment variable {0} does not specify a boolean value ({1}).'.format(var_name, value)
            raise ConfigurationError(error)
    else:
        if default_value != None:
            Log.write_info('Environment variable \'{0}\' is not set... Using \'{1}\' instead.'.format(var_name, default_value))
        else:
            Log.write_info('Environment variable \'{0}\' is not set...'.format(var_name))
        return default_value


# ---------------------------------------------------------------------------------------------------------------------


def get_env_setting_integer(var_name, default_value = None, min = None, max = None):
    """
    Gets the value of the specified environment variable as an integer value.

    This method gets the value of the specified environment variable as an integer value and returns the specified
    default value, if the environment variable is not set. Positive and negative decimal integer values are supported.

    Args:
        var_name (str)                : Name of the environment variable to get.
        default_value (int, optional) : Default value to return, if the environment variable is not set.
        min (int, optional)           : Lower bound of valid interval.
        max (int, optional)           : Upper bound of valid interval.

    Returns:
        The value of the environment variable (if set), otherwise the default value is returned.

    """
    value = os.environ.get(var_name)
    if value:

        try:
            value = int(value, 10)
        except exception:
            error = 'Environment variable\'{0}\' does not specify a valid integer ({1}).'.format(var_name, value)
            raise ConfigurationError(error)

        Log.write_info('Environment variable \'{0}\' is set to \'{1}\'.'.format(var_name, value))

        if min and value < min: 
            error = 'Environment variable\'{0}\' is less than the lower bound ({1}). Ignoring setting...'.format(var_name, min)
            raise ConfigurationError(error)

        if max and value > max: 
            error = 'Environment variable\'{0}\' is greater than the upper bound ({1}). Ignoring setting...'.format(var_name, max)
            raise ConfigurationError(error)

        return value

    else:

        if default_value != None:
            Log.write_info('Environment variable \'{0}\' is not set... Using \'{1}\' instead.'.format(var_name, default_value))
        else:
            Log.write_info('Environment variable \'{0}\' is not set...'.format(var_name))

        return default_value


# ---------------------------------------------------------------------------------------------------------------------


def get_env_setting_string(var_name, default_value = None):
    """
    Gets the value of the specified environment variable as a string.

    This method gets the value of the specified environment variable as a string and returns the specified default
    value, if the environment variable is not set.

    Args:
        var_name (str)      : Name of the environment variable to get.
        default_value (str) : Default value to return, if the environment variable is not set.

    Returns:
        The value of the environment variable (if set), otherwise the default value is returned.

    """
    value = os.environ.get(var_name)
    if value:
        Log.write_info('Environment variable \'{0}\' is set to \'{1}\'.'.format(var_name, value))
        return value
    else:
        if default_value != None:
            Log.write_info('Environment variable \'{0}\' is not set... Using \'{1}\' instead.'.format(var_name, default_value))
        else:
            Log.write_info('Environment variable \'{0}\' is not set...'.format(var_name))
        return default_value


###################################################################################################################################################################################
# kernel modules
###################################################################################################################################################################################


def is_kernel_module_loaded(module_name):
    """
    Checks whether the kernel module with the specified name is loaded.

    Args:
        module_name (str) : Name of the module to check.

    Returns:
        True, if the module is loaded; otherwise False.

    """
    with open("/proc/modules") as file:
        lines = file.readlines()
    lines = [x.strip() for x in lines]
    for line in lines:
        other_module_name = line.split(" ")[0]
        if (other_module_name == module_name):
            return True
    return False


# ---------------------------------------------------------------------------------------------------------------------


def load_kernel_module(module_name):
    """
    Loads the kernel module with the specified name.

    Args:
        module_name (str) : Name of the module to load.

    """
    if is_kernel_module_loaded(module_name):
        Log.write_info("Loading kernel module '{0}' not necessary, it is already loaded.".format(module_name))
        return

    # try to load the module
    try:
        process = subprocess.run(["modprobe", module_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        Log.write_error("Loading module '{0}' failed ('modprobe' is not installed).".format(module_name))
        raise

    # evaluate modprobe's exit code
    if process.returncode == 0:
        Log.write_info("Loading module '{0}' succeeded.".format(module_name))
    else:
        Log.write_error("Loading module '{0}' failed, modprobe returned with code {1}.".format(module_name, process.returncode))
        Log.write_error("The host's module directory must be linked into the container and the container must run in privileged mode to load modules.")
        raise RuntimeError()


###################################################################################################################################################################################
# Networking operations
###################################################################################################################################################################################

def is_email_address(s):
    """
    Performs a simple format check to find out whether the specified string is an e-mail address.

    Args:
        s (str) : String to check.

    Returns:
        True, if the specified string is an e-mail address;
        otherwise False.

    """
    return re.match(r"^.+@[^@]+\.[^@]+$", s)


def resolve_hostname(hostname):
    """
    Querys the DNS and returns IPv4 and IPv6 addresses of the specified hostname (querys A and AAAA records only).

    Args:
        hostname (str) : hostname to resolve.

    Returns:
        A tuple containing the IPv4 and IPv6 addresses
        Example: ( [ 192.168.0.1, 10.0.0.1 ], [ fd00:dead:beef::1, fd00:dead:beef::2 ] )

    """

    ipv4_addresses = []
    try:
        for record in dns.resolver.query(hostname, dns.rdatatype.A, dns.rdataclass.IN):
            ipv4_addresses.append(record.address)
    except dns.resolver.NoAnswer:
        pass

    ipv6_addresses = []
    try:
        for record in dns.resolver.query(hostname, dns.rdatatype.AAAA, dns.rdataclass.IN):
            ipv6_addresses.append(record.address)
    except dns.resolver.NoAnswer:
        pass

    return (ipv4_addresses, ipv6_addresses)


# ---------------------------------------------------------------------------------------------------------------------


def resolve_hostnames(hostnames):
    """Querys the DNS and returns IPv4 and IPv6 addresses of the specified hostnames (querys A and AAAA records only).

    Args:
        hostnames (list of str) : hostnames to resolve.

    Returns:
        A dictionary containing the IPv4/IPv6 addresses by the corresponding hostname.
        IPv4 and IPv6 addresses are separated in the tuple that forms the value of the dictionary entry.
        Example: { "myhost.mydomain.com" : ( [ 192.168.0.1, 10.0.0.1 ], [ fd00:dead:beef::1, fd00:dead:beef::2 ] ) }

    """
    
    return { hostname : resolve_hostname(hostname) for hostname in hostnames }


###################################################################################################################################################################################
# mounting
###################################################################################################################################################################################


def does_mount_point_exist(mnt):
    """
    Checks whether the specified point moint exists.

    Args:
        mnt (str) : Mount point to check.

    Returns:
        True, if the specified mount point exists;
        otherwise False

    """
    with open("/proc/mounts") as f:
        for line in f:
            device, mount_point, filesystem, flags, __, __ = line.split()
            flags = flags.split(",")
            if mount_point == mnt:
                return True
        return False


# ---------------------------------------------------------------------------------------------------------------------


def is_mount_point_readonly(mnt):
    """
    Checks whether the specified point moint is read-only.

    Args:
        mnt (str) : Mount point to check.

    Returns:
        True, if the specified mount point is read-only;
        otherwise False

    Exceptions:
        ValueError : The specified mount point doesn't exist.

    """
    with open("/proc/mounts") as f:
        for line in f:
            device, mount_point, filesystem, flags, __, __ = line.split()
            flags = flags.split(",")
            if mount_point == mnt:
                return 'ro' in flags
        raise ValueError("Mount point {0} doesn't exist".format(mnt))


###################################################################################################################################################################################
# firewalling / iptables
###################################################################################################################################################################################


def iptables_run(args, comment=None):
    """Calls 'iptables' with the specified arguments.

    Args:
        args (list of str)      : Arguments to pass to 'iptables'.
        comment (str, optional) : Comment to attach to the rule.

    """
    run_args = ["iptables", *args]
    if comment: run_args.extend(["-m", "comment", "--comment", comment])
    Log.write_debug("Running: {0}".format(" ".join(run_args)))
    subprocess.run(run_args, check=True, stdout=subprocess.DEVNULL)


# ---------------------------------------------------------------------------------------------------------------------


def ip6tables_run(args, comment=None):
    """Calls 'ip6tables' with the specified arguments.

    Args:
        args (list of str)      : Arguments to pass to 'ip6tables'.
        comment (str, optional) : Comment to attach to the rule.

    """
    run_args = ["ip6tables", *args]
    if comment: run_args.extend(["-m", "comment", "--comment", comment])
    Log.write_debug("Running: {0}".format(" ".join(run_args)))
    subprocess.run(run_args, check=True, stdout=subprocess.DEVNULL)


# ---------------------------------------------------------------------------------------------------------------------


def iptables_add(table, target, args=[], comment=None):
    """Adds a new netfilter rule to the specified table using the specified target and arguments.

    Args:
        table (str)             : Table to add the rule to.
        target (str)            : Table to add the rule to.
        args (list of str)      : Arguments to pass to 'iptables' (except '-A' and '-j').
        comment (str, optional) : Comment to attach to the rule.

    """
    run_args = ["iptables", "-A", table, *args, "-j", target]
    if comment: run_args.extend(["-m", "comment", "--comment", comment])
    Log.write_debug("Running: {0}".format(" ".join(run_args)))
    subprocess.run(run_args, check=True, stdout=subprocess.DEVNULL)


# ---------------------------------------------------------------------------------------------------------------------


def ip6tables_add(table, target, args=[], comment=None):
    """Adds a new netfilter rule to the specified table using the specified target and arguments.

    Args:
        table (str)             : Table to add the rule to.
        target (str)            : Table to add the rule to.
        args (list of str)      : Arguments to pass to 'ip6tables' (except '-A' and '-j').
        comment (str, optional) : Comment to attach to the rule.

    """
    run_args = ["ip6tables", "-A", table, *args, "-j", target]
    if comment: run_args.extend(["-m", "comment", "--comment", comment])
    Log.write_debug("Running: {0}".format(" ".join(run_args)))
    subprocess.run(run_args, check=True, stdout=subprocess.DEVNULL)

