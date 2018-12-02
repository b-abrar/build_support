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
-print_status
"""
doc = \
"""
##########################################################################

Hello JANA Developer!

You are about to:
    - Configure this repository to use custom JANA git hooks.
    - Enforce JANA's forking workflow on to your development.
    - Initialize all dependencies required for J-TIMP development.
    - Enforce PEP8 styling to any new code written for this repo.


Hope you're okay with that. Why am I kidding, you have to be okay with it.
In any case, if you dont like the hooks, just use the '--no-verify' flag
on your commits to bypass them. But try not to be too smart,


I am watching.


Git hooks are awesome. They can do all sorts of things on your behalf:
   - Scan for any accidental hard tabs you placed in the src files
   - Warn you about any binary file being commiting to the repo.
   - Notify you about any unintentional file mode changes. (POSIX)
   - Stop you from commiting files that are unusually large for the repo.

Basically they block the most common types of undesired commits.


In addtion to custom hooks, I'll take the honor of:
    - setting your upstream to the proper JANA repository
    - setting up your styling to be consitent with JANA style guide


Also, this is a completely SSH friendly script.
Hoping to see you at work. Just press 'y' below and we're good to go.

PS: I'll install some dependencies first, that may take a minute.

##########################################################################
"""
# start script on user command
print(doc)
yn = input("Proceed ([y]/n)? ")
if yn.lower() != 'y':
    raise SystemExit("Fatal: Operation cancelled by user")

import os
import sys

# Will not run if Python version requirement is not met
try:
    assert sys.version_info >= (3, 5)
except AssertionError:
    version_num = str(sys.version_info[:2][0]) + '.' + \
        str(sys.version_info[:2][1])
    print("Fatal: Your current Python version is {}".format(version_num),
          file=sys.stderr)
    print("You must be running Python 3.6 or newer.", file=sys.stderr)
    raise SystemExit(1)

try:
    import subprocess as sp
except (ModuleNotFoundError, ImportError):
    print('Installing core shell dependencies ...')
    os.system('pip install subprocess')
    import subprocess as sp

dependencies = [
    'requests',
    'urllib3',
    'progress',
    'colorama',
    'termcolor'
]

print("Initializing dependencies ...")
print("This may take a while.")
print('------------------------')

# get a list of currently installed packages
reqs = sp.check_output([sys.executable, '-m', 'pip', 'freeze'])
installed_packages = [r.decode().split('==')[0] for r in reqs.split()]

# upgrade pip to use the dependency list propely
print("Upgrading pip ...")
sp.run("python -m pip install --upgrade pip")

# install all packages that aren't installed
for pkg in dependencies:
    if pkg not in installed_packages:
        print('Installing {}'.format(pkg))
        pkg_cmd = "pip install " + pkg
        sp.run(pkg_cmd)

# msgpack may not be available after a fresh python installation
# no need to import it however
print("Updrading msgpack ...")
sp.run("pip install --upgrade msgpack")

from requests import (
    get,
    ConnectionError,
)
from urllib3.exceptions import (
    NewConnectionError,
    MaxRetryError,
)
from progress.bar import (
    Bar,
    ShadyBar,
)
from time import sleep
from colorama import init
from termcolor import colored

# add color support
init()
# successful import
print('------------------------')
print(colored('Done', 'green'))
sleep(0.2)

# visual confirmating of passing version requirement
# actual test is done at top of file
sys.stdout.write('\nChecking Python Verison ... ')
sys.stdout.flush()
sleep(0.5)
sys.stdout.write(colored('Done\n', 'green'))
sys.stdout.flush()
sleep(0.5)

# state flags
flags = {
    'python_version': True,
    'atom_installed': False,
    'editorconfig_plugin': False,
    'correct_repo': True,
    'remote_added': False,
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
    sys.stdout.write("Creating git template directory ...\n")
    sys.stdout.flush()
    command = sp.run(mkd, stdout=sp.PIPE, shell=True)
    if command.returncode != 1:
        sys.stdout.write(colored('Done\n', 'green' ),msg)
    else:
        msg = "Git template directory exists." + \
            " Using exsisting directory. \n"
        print(colored('Warning:', 'yellow'), msg)


def dl_file(url, **kwargs):
    """
    Download the file from the given url
    Open file object in binary mode since get.content
    returns a byte object. Written file will have CRLF line endings.
    """
    # using carriage return to escape incompatible ANSI chars
    bar = ShadyBar('\rDownloading', max=10, suffix='%(percent)d%%')
    try:
        response = get(url)  # byte-like object
        # Added progress intervals for visual consistency.
        for i in range(10):
            sleep(0.05)
            bar.next()
            sys.stdout.flush()
        bar.finish()
        sys.stdout.flush()
        # errors related to internet connectivity
    except(NewConnectionError, MaxRetryError, ConnectionError):
        error_msg = "Failed to send request to URL." + \
        " Check your internet connection and try again."
        print(colored('\rFatal:', 'red'), error_msg, file=sys.stderr)
        raise SystemExit(1)
        # error related to HTTP responses
    if response.status_code != 200:
        print(colored("Fatal:", 'red'), "HTTP Error {})."
        .format(response.status_code), file=sys.stderr)
        print("Try setting up your repo manually or contact repo admin.",
        file=sys.stderr)
        raise SystemExit(1)

    # Write response to file
    if kwargs['file'] == 'pre-commit':
        file_name = os.path.join(get_hook_dir(), "pre-commit")
        # in odrer to write 'Done' inline
        sys.stdout.write('\nWriting response to file ... ')
        sys.stdout.flush()
        with open(file_name, "wb") as file:
            file.write(response.content)

    elif kwargs['file'] == '.editorconfig':
        file_name = os.path.join(os.getcwd(), ".editorconfig")
        # in odrer to write 'Done' inline
        sys.stdout.write('\nWriting response to file ... ')
        sys.stdout.flush()
        with open(file_name, "wb") as file:
            file.write(response.content)
    # delays for visual consistency
    sleep(0.5)
    sys.stdout.write(colored("Done", 'green'))
    sys.stdout.flush()
    print('\n')

def init_editorconfig(ec_url):
    """Initialize editorconfig if it doesn't exist"""
    print("Searching for an exisiting .editorconfig in repo root ...")
    if not os.path.isfile(".editorconfig"):
        # Then download the editorconfig
        print("No existing .editorconfig file found.")
        print('Fetching .editorconfig file from build_support.')
        dl_file(ec_url, file='.editorconfig')
        print('Success: initialized .editorconfig into {}\n'
              .format(os.getcwd()))
    # if editorconfig file already exists
    print("Repository is already initialized with .editorconfig. Skipping.\n")
    sleep(0.5)
    # Check if Atom is installed
    print("Searching for an instance of Atom Text Editor installation ...")
    sleep(0.5)
    check = sp.run("atom -v", stdout=sp.PIPE, shell=True)
    if check.returncode == 0:
        print(colored("Atom Text Editor installation found.", "green"))
        sleep(0.2)
        # install editorconfig plugin for atom
        print("\nInstalling EditorConfig plugin for Atom Text Editor ...")
        print("Note: If progress bar is idle for more than 30 seconds,",
              "hit Ctrl-C once to continue.")
        bar = ShadyBar('\rInstalling', max=10, suffix='%(percent)d%%')
        # show some progress before install begins
        for i in range(2):
            bar.next()
            sleep(2)
        sys.stdout.flush()
        install = sp.run("apm install editorconfig",
                         stdout=sp.PIPE, shell=True)
        # create the illusion of install
        for i in range(8):
            sleep(0.05)
            bar.next()
            sys.stdout.flush()
        bar.finish()
        sys.stdout.flush()

        if install.returncode != 0:
            print("Warning: Failed to install EditorConfig plugin for Atom",
                  file=sys.stderr)
            relax = "That's okay. You can manually install it afterwards from"
            print(relax, colored("https://editorconfig.org", 'cyan'))
        else:
            editorconfig_plugin = True
            print(colored('\nSuccess:', 'green'), 'EditorConfig configured!')
            print('NOTE: To use EditorConfig with other IDEs, visit',
                  colored("https://editorconfig.org\n", 'cyan'))
    else:
        msg = "Atom is not installed on this computer.\n" + \
        "Automatic editorconfig setup will not take place."
        print(colored(msg, 'yellow'))
        msg = "Note: To install EditorConfig plugin for your preferred " + \
            "text editor, visit "
        print(msg, colored("https://editorconfig.org", 'cyan'))


def add_upstream_remote():
    """Find out the JANA url of the current repository
    and add it to the upstream. Works for both HTTPS and SSH"""
    cmd = 'git config --get remote.origin.url'
    # [:-1] is used to remove carriage return
    sys.stdout.write("Configuring upstream to be JANA remote ...\n")
    sys.stdout.flush()
    fork = sp.run(cmd, stdout=sp.PIPE).stdout.decode('utf-8')[:-1]
    sleep(1.5)
    # check if url is SSH or HTTPS
    isSSH = False
    if fork.startswith("git@"):
        isSSH = True
    elif fork.startswith("http"):
        pass
    else:
        print("Fatal: Invalid remote URL. Must be either SSH or HTTPS",
              file=sys.stderr)
        raise SystemExit(1)
    # obtain JANA url from SSH or HTTPS
    if not isSSH:
        print("HTTPS remote detected. Using HTTPS.")
        sleep(0.2)
        fork = fork.split('/')
        # if using main repo instead of fork, throw error
        if fork[-2] == 'JANA-Technology':
            msg = "You are using a clone of the JANA repository." + \
            " You must clone a fork of the JANA repository instead."
            print(colored('Fatal:', 'red'), msg, file=sys.stderr)
            raise SystemExit(1)
        fork[-2] = 'JANA-Technology'
        jana_remote = '/'.join(fork)

    else:  # if isSSH
        print("SSH remote detected. Using SSH.")
        sleep(0.2)
        fork = fork.split('/')
        fork_inner = fork[0].split(':')
        if fork_inner[1] == "JANA-Technology":
            msg = "You are using a clone of the JANA repository." + \
            " You must clone a fork of the JANA repository instead."
            print(colored('Fatal:', 'red'), msg, file=sys.stderr)
            raise SystemExit(1)
        fork_inner[1] = "JANA-Technology"
        fork[0] = ':'.join(fork_inner)
        jana_remote = '/'.join(fork)

    # add the jana remote as upstream
    cmd = 'git remote add upstream ' + jana_remote
    add_remote = sp.run(cmd, stdout=sp.PIPE)
    if add_remote.returncode == 0:
        print(colored('Success:', 'green'),
                "Set upstream as JANA repository:\n")
        print('        {}' .format(jana_remote))
    # if upstream remote already exists, overwrite it
    elif add_remote.returncode == 128:
        msg = "Upstream remote already exists.\n" + \
            "            -> Updating it to JANA repository.\n"
        print(colored('Warning:', 'yellow'), msg)
        sleep(0.2)
        cmd = 'git remote set-url upstream ' + jana_remote
        sp.run(cmd, stdout=sp.PIPE)
        msg = "Updated upstream remote to JANA repository.\n"
        print(colored('Success:', 'green'),msg)
        print('        {}\n\n' .format(jana_remote))
    # Unknwon error. Stop script
    else:
        error_msg = "    Warning: Could not set upstream remote." + \
            " You should set it manually to be the JANA repository"
        print(error_msg, stdout=sys.stderr)


def init_all(url, ec_url):
    """Main function to initialize hooks, set remote
    and configure EditorConfig sytling for current repo"""
    # check if current dir is a git repository
    if not os.path.isdir(".git"):
        error_msg = "Not a git repository." + \
        " Run script from the root of a git repository."
        print(colored('Fatal:', 'red'), error_msg)
        raise SystemExit(1)

    # create the git template directory
    print('### TEMPLATE DIRECTORY SET UP ###')
    create_template_dir()
    sleep(1)

    # download git hooks from url
    print('### HOOK INITIALIZATION ###')
    print("Fetching pre-commit hooks from build_support ...")
    dl_file(url, file='pre-commit')
    sleep(1)

    # Set the newly created the git_template as the template dir
    cmd = "git config --global init.templatedir " + get_template_dir()
    sp.run(cmd)

    # Update the current repo by removing old hooks
    # and running 'git init' in .git dir
    print("### OVERWRITING OLD HOOKS ###")
    if os.path.isfile(r".git\hooks\pre-commit"):
        sys.stdout.write("Removing old hooks from repository ... ")
        sys.stdout.flush()
        cmd = r"del .git\hooks\pre-commit"
        sp.run(cmd, shell=True)
        sys.stdout.write(colored('Done', 'green'))
        sleep(0.5)
    # Replace existing hooks with newer ones
    # and reinitialize repository
    cmd = "git init"
    git_init = sp.run(cmd, stdout=sp.PIPE)
    if git_init.returncode == 0:
        print("\nReinitialized existing git repository in\n\n", "    {} \n\n"
              .format(os.getcwd()))
        sleep(0.5)

    # add upstream for the repository
    print("### SETTING UPSTREAM REMOTE ###")
    add_upstream_remote()
    sleep(0.5)

    # init editorconfig
    print("### INITIALIZING EDITORCONFIG ###")
    init_editorconfig(ec_url)
    sleep(0.5)


def print_status(flags):
    """Final status message"""
    pass


if __name__ == '__main__':

    print("\nReading System Variables and initializing script ...\n" )
    # provide time buffer to cancel script

    hook_url = 'https://raw.githubusercontent.com/b-abrar/build_support/master/pre-commit.pl'
    ec_url = 'https://raw.githubusercontent.com/b-abrar/build_support/master/.editorconfig'
    init_all(hook_url, ec_url)

    print('### TIMP REQUIREMENTS INSTALLATION ###')
    print("Repo initialized.\nNow running install_requirements.py ...\n")

    print("...You are all set!... (This is a lazy message, I'll update it with a status table later)")
