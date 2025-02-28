# Universal installation script

Since version 3.11 of the OpenQuake-engine, there is a universal installation script that works on any platform, provided you have Python 3.7, Python 3.8, or Python 3.9 installed.

- **Note 1**: Python 3.6 may work but it is untested and deprecated; Python 3.10 is not supported yet.
- **Note 2**: on some Linux distributions (i.e. Ubuntu) you may need to install the package `python3-venv` before running the installer
- **Note 3**: This script will install the OpenQuake engine in its own virtual environment. Users who need to use any additional Python packages (eg. Jupyter, Spyder) along with the OpenQuake-engine should install those packages within this virtual environment.
- **Note 4**: For `user` and `devel` installation methods, the virtual environment `openquake` will be created in the home directory. Make sure you have no folder called `openquake`in your home directory that can cause conflicts.
- **Note 5**: Users with no knowledge of virtual environments are referred to this page of the Python tutorial: https://docs.python.org/3/tutorial/venv.html
- **Note 6**: Conda is not supported; some users have been able to run the OpenQuake-engine with Conda, but GEM is not using and not testing conda; you are on your own.

The script allows the user to select between different kinds of installations:

1. `devel` installation (Windows, macOS, and Linux)
2. `user` installation (Windows, macOS, and Linux)
3. `server` installation (only available for Linux)
4. `devel_server` installation (only available for Linux)

A few notes about macOS:

- macOS 11.x (Big Sur) and macOS 12.x (Monterey) are not officially supported 
but users have managed to install the engine on both operating systems
(see for instance https://groups.google.com/g/openquake-users/c/hl8uI_j6zwM/m/A0LzduANAgAJ).
- new Macs with the M1 CPU are unsupported but users have managed to install
the engine via Rosetta or natively by using the system Python (version 3.9)
- make sure to run the script located under /Applications/Python 3.X/Install Certificates.command, after Python has been installed, to update the SSL certificates bundle see [see FAQ](../faq.md#certificate-verification-on-macOS).

## `devel` installation

Users who intend to modify the engine codebase or add new features for the engine should use the `devel` installation:

on macOS and Linux:
```
$ git clone https://github.com/gem/oq-engine.git
$ cd oq-engine && /usr/bin/python3 install.py devel
```

on Windows:
```
C:\>git clone https://github.com/gem/oq-engine.git
C:\>cd oq-engine 
C:\>python install.py devel
```

This installation method will create a Python virtual environment in `$HOME/openquake` and will install the engine
in development mode in this environment. Then, after activating the virtual environment with

on macOS and Linux:
```
$ source $HOME/openquake/bin/activate
```

on Windows:
```
C:\>%USERPROFILE%\openquake\Scripts\activate.bat
```

It should now be possible to develop with the engine. Calculation data will be stored in `$HOME/oqdata`.

## `user` installation

If you do not need to modify the engine codebase or develop new features with the engine, but intend to use it as an application, you should perform a `user` installation (on Windows / macOS) or a `server` installation (on Linux). The `user` installation is also the recommended option for Linux, in the case where you do not have root permissions on the machine. There is no need to clone the engine repository, you just need to download the installation script:

on macOS and Linux:
```
$ curl -O https://raw.githubusercontent.com/gem/oq-engine/master/install.py
$ /usr/bin/python3 install.py user
```

on Windows:
```
C:\>curl.exe -LO https://raw.githubusercontent.com/gem/oq-engine/master/install.py
C:\>python install.py user
```

This installation method will create a Python virtual environment in `$HOME/openquake` and will install the engine on it.
After that, you can activate the virtual environment with

on macOS and Linux:
```
$ source $HOME/openquake/bin/activate
```

on Windows:
```
C:\>%USERPROFILE%\openquake\Scripts\activate.bat
```

You can also invoke the `oq` command without activating the virtual environment by directly calling

on macOS and Linux:
```
$HOME/openquake/bin/oq
```

on Windows:
```
C:\>%USERPROFILE%\openquake\Scripts\oq
```

Calculation data will be stored in `$HOME/oqdata`.


## `server` installation

If you are on a Linux machine _and_ you have root permissions, the
recommended installation method is `server`. In this case, the engine
will work with multiple users and two system V services will be
automatically installed and started: `openquake-dbserver` and
`openquake-webui`.

```
$ curl -O https://raw.githubusercontent.com/gem/oq-engine/master/install.py
$ sudo -H /usr/bin/python3 install.py server
```

The installation script will automatically create a user called
`openquake` and will install the engine in the directory
`/opt/openquake`.  Calculation data will be stored in
`/var/lib/openquake/oqdata`.

*NB*: if you already have an engine installation made with debian or rpm
packages, before installing the new version you must uninstall the old
version, make sure that the dbserver and webui services are actually
stopped and then also remove the directory `/opt/openquake` and the
configuration file `/etc/openquake/openquake.cfg`. If you want to
preserve some configuration (like the [zworkers] section which is needed
on a cluster) you should keep a copy of `/etc/openquake/openquake.cfg`
and move it inside `/opt/openquake` once the new installation is finished.

## `devel_server` installation

This method adds to `server` installation the possibility to run the engine from a git repository.
If you are on a Linux machine _and_ you have root permissions

```
$ git clone https://github.com/gem/oq-engine.git
$ cd oq-engine && sudo -H /usr/bin/python3 install.py devel_server
```

## Cluster installation

It is possible to install the engine on a Linux cluster, but it requires additional steps. You should see the page about [clusters](cluster.md).

## Cloud installation

A set of [Docker containers](docker.md) is available for installing the engine in the cloud.

## Downgrading an installation

By default, in `user` and `server` mode the script will install the latest stable release of the engine.
If for some reason you want to use an older version you can specify the version number with the ``--version`` option:
```
$ python3 install.py user --version=3.10
```

## Uninstalling the engine

To uninstall the engine, use the --remove flag:

on macOS and Linux:
```
$ python3 install.py devel --remove
$ python3 install.py user --remove
$ sudo -H /usr/bin/python3 install.py server --remove
```

on Windows:
```
C:\>cd %USERPROFILE%
C:\>python install.py devel --remove
C:\>python install.py user --remove
```

The calculation data (in the `oqdata` directory) WILL NOT be removed.
You will have to remove the data manually, if desired.

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/u/0/g/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
