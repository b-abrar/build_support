"""Requirement : python version > Python 3.5
@author:co-op6 b-abrar
TO-DO:
-search for .git dir in current dir
-setup hooks
-setup editorconfig
-set upstream remote
    - git config --get remote.origin.url
-stop clones of actual jana repo
-add ssh support
-progress bar
"""
import os
import sys
import subprocess as sp
try:
    from requests import (
        get,
        ConnectionError,
    )
except ModuleNotFoundError:
    print('requests library not found. Installing it first.')
    sp.run("pip install requests")
    from requests import (
        get,
        ConnectionError,
    )
try:
    from urllib3.exceptions import (
        NewConnectionError,
        MaxRetryError,
    )
except ModuleNotFoundError:
    print('urllib3 library not found. Installing it first.')
    sp.run("pip install urllib3")
    from urllib3.exceptions import (
        NewConnectionError,
        MaxRetryError,
    )

# state flags
flags = {
    'atom_installed': False,
    'editorconfig_plugin': False
}


def get_home_dir():
    """
     Obtain HOME directory of the windows system.
     On Windows, shell=True must be used for shell-intergrated
     processes However, it is vulnerable to shell injection
     from untrusted commands.

     The output from subprocess
     is a byte object. Must convert to str before use.
     """
    cmd = r"echo %UserProfile%"
    home_dir = sp.run(cmd, stdout=sp.PIPE, shell=True).stdout.decode('utf-8')
    home_dir = home_dir[:-2] + "\\"  # remove carriage return

    return home_dir


def get_template_dir():
    """Directory that will be copied over on git init"""
    return os.path.join(get_home_dir(), ".git_template")


def get_hook_dir():
    """ Subdirectory of template_dir, where hooks are stored"""
    return os.path.join(get_template_dir(), "hooks")


def create_template_dir():
    """Create git template dir and hook dir if those don't exist"""
    hook_dir = get_hook_dir()
    mkd = "mkdir " + hook_dir
    command = sp.run(mkd, stdout=sp.PIPE, shell=True)
    if command.returncode != 1:
        print("Success: Created git template directory. Setting up hooks...")
    else:
        msg = "Warning: Git template directory exists." + \
            "Using exsisting directory. \n"
        print(msg)


def dl_file(url, **kwargs):
    """
    Download the file from the given url
    Open file object in binary mode since get.content
    returns a byte object. Written file will have CRLF line endings.
    """
    try:
        response = get(url)  # byte-like object
        # errors related to internet connectivity
    except(NewConnectionError, MaxRetryError, ConnectionError):
        error_msg = "Fatal: Failed to send request to URL." + \
        " Check your internet connection and try again."
        print(error_msg, file=sys.stderr)
        raise SystemExit(1)
        # error related to HTTP responses
    if response.status_code != 200:
        print("Fatal: HTTP Error {})."
        .format(response.status_code), file=sys.stderr)
        print("Try setting up your repo manually or contact repo admin.",
        file=sys.stderr)
        raise SystemExit(1)

    # Write response to file
    if kwargs['file'] == 'pre-commit':
        file_name = os.path.join(get_hook_dir(), "pre-commit")
        with open(file_name, "wb") as file:
            file.write(response.content)
    elif kwargs['file'] == '.editorconfig':
        file_name = os.path.join(os.getcwd(), ".editorconfig")
        with open(file_name, "wb") as file:
            file.write(response.content)


def init_hooks_remote(url):
    """Main function to initialize hooks and set remote"""
    # check if current dir is a git repository
    if not os.path.isdir(".git"):
        error_msg = "Fatal: Not a git repository." + \
            " Run script from the root of a git repository"
        print(error_msg)
        raise SystemExit(1)
    # create the git template directory
    create_template_dir()
    # download git hooks from url
    print("Fetching pre-commit hooks from build_support.")
    dl_file(url, file='pre-commit')
    print("Success: Downloaded pre-commit hooks. \n")
    # Set the newly created the git_template as the template dir
    cmd = "git config --global init.templatedir " + get_template_dir()
    sp.run(cmd)

    # Update the current repo by removing old hooks
    # and running 'git init' in .git dir
    if os.path.isfile(r".git\hooks\pre-commit"):
        cmd = r"del .git\hooks\pre-commit"
        sp.run(cmd, shell=True)
        print("Success: Removed old hooks.")
    # Replace existing hooks with newer ones
    # and reinitialize repository
    cmd = "git init"
    git_init = sp.run(cmd, stdout=sp.PIPE)
    if git_init.returncode == 0:
        print("Success: Reinitialized existing git repository in {} \n"
              .format(os.getcwd()))

    # add upstream for the repository
    add_upstream_remote()


def init_editorconfig(ec_url):
    """Initialize editorconfig if it doesn't exist"""
    print("Searching for an exisiting .editorconfig in repo root.")
    if not os.path.isfile(".editorconfig"):
        # Then download the editorconfig
        print("No existing .editorconfig file found.")
        print('Fetching .editorconfig file from build_support.')
        dl_file(ec_url, file='.editorconfig')
        print('Success: initialized .editorconfig into {}\n'
              .format(os.getcwd()))
    print("Success: Repository is already initialized with .editorconfig.\n")
    # Check if Atom is installed
    print("Searching for an instance of Atom Text Editor installation..")
    check = sp.run("atom -v", stdout=None, shell=True)
    if check.returncode == 0:
        print("Success: Atom Text Editor installation found.\n")
        # install editorconfig plugin for atom
        print("Installing EditorConfig plugin for Atom Text Editor..")
        install = sp.run("apm install editorconfig", shell=True)
        if install.returncode != 0:
            print("Warning: Failed to install EditorConfig plugin for Atom",
                  file=sys.stderr)
            relax = "That's okay. You can manually install it afterwards" + \
                    " from https://editorconfig.org"
            print(relax)
        else:
            editorconfig_plugin = True
            print("Success: EditorConfig configured!")
    else:
        msg = "Note: Install EditorConfig plugin for your preferred text " + \
            "editor from" + " https://editorconfig.org"
        print(msg)


def add_upstream_remote():
    """Find out the JANA url of the current repository
    and add it to the upstream. Works for both HTTPS and SSH"""
    cmd = 'git config --get remote.origin.url'
    # [:-1] is used to remove carriage return
    fork = sp.run(cmd, stdout=sp.PIPE).stdout.decode('utf-8')[:-1]
    # check if url is SSH or HTTPS
    isSSH = False
    if fork.startswith("git@"):
        isSSH = True
    elif fork.startswith("http"):
        pass
    else:
        print("Invalid remote URL. Must be either SSH or HTTPS",
              file=sys.stderr)
        raise SystemExit(1)
    # obtain JANA url from SSH or HTTPS
    if not isSSH:
        fork = fork.split('/')
        # if using main repo instead of fork, throw error
        if fork[-2] == 'JANA-Technology':
            msg = "Fatal: You are using a clone of the JANA repository." + \
            " You must clone a fork of the JANA repository instead."
            print(msg, file=sys.stderr)
            raise SystemExit(1)
        fork[-2] = 'JANA-Technology'
        jana_remote = '/'.join(fork)

    else:  # if isSSH
        fork = fork.split('/')
        fork_inner = fork[0].split(':')
        if fork_inner[1] == "JANA-Technology":
            msg = "Fatal: You are using a clone of the JANA repository." + \
            " You must clone a fork of the JANA repository instead."
            print(msg, file=sys.stderr)
            raise SystemExit(1)
        fork_inner[1] = "JANA-Technology"
        fork[0] = ':'.join(fork_inner)
        jana_remote = '/'.join(fork)

    # add the jana remote as upstream
    cmd = 'git remote add upstream ' + jana_remote
    add_remote = sp.run(cmd, stdout=sp.PIPE)
    if add_remote.returncode == 0:
        print("Added JANA repository as upstream remote.")
    elif add_remote.returncode == 128:
        msg = "Warning: Upstream remote already exists. " + \
            "Updating it to JANA repository."
        print(msg)
        cmd = 'git remote set-url upstream ' + jana_remote
        sp.run(cmd, stdout=sp.PIPE)
        print("Success: Updated upstream remote to JANA repository.\n")
    else:
        error_msg = "Warning: Error setting upstream remote." + \
            " You should set it manually to be the JANA repository"
        print(error_msg, stdout=sys.stderr)


def print_status(flags):
    pass


if __name__ == '__main__':
    print("Initializing script. \nReading System Variables.\n" )
    # Will not run if Python version requirement is not met
    try:
        assert sys.version_info >= (3, 5)
    except AssertionError:
        version_num = str(sys.version[:2][0]) + '.' + str(sys.version[:2][1])
        print("Fatal: Your current Python version is {}" .format(version_num),
              file=sys.stderr)
        print("You must be running Python 3.5 or newer.", file=sys.stderr)
        raise SystemExit(1)

    hook_url = 'https://raw.githubusercontent.com/b-abrar/build_support/master/pre-commit.pl'
    ec_url = 'https://raw.githubusercontent.com/b-abrar/build_support/master/.editorconfig'
    init_hooks_remote(hook_url)
    init_editorconfig(ec_url)
    print("...You are all set!...")
