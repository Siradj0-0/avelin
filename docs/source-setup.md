# Running Avelin from source

Avelin is an experimental Linux desktop application, not a web service. These instructions run the checkout without installing it. Use an ordinary user account on a graphical desktop; do not run the app with `sudo`.

## Debian 12 / Ubuntu 24.04 example

The following package names are for Debian 12 and Ubuntu 24.04. Other distributions use different names; use their package manager to install Python 3.10 or newer, GTK 4 introspection data, PyGObject, its Cairo bridge, pycairo and the GLib command-line tools. The example dependencies follow the repository's GTK smoke job and Debian runtime dependency list; a successful install is not a claim of full desktop compatibility.

```sh
sudo apt update
sudo apt install git python3 python3-gi python3-gi-cairo python3-cairo gir1.2-gtk-4.0 libglib2.0-bin
```

Then, in a graphical session:

```sh
git clone https://github.com/Siradj0-0/avelin.git
cd avelin
/usr/bin/python3 --version
/usr/bin/python3 -m avelin
```

The version must be at least 3.10. If you already have a checkout, use it instead of cloning again. The command must run from the repository root so Python can find the `avelin` module. `/usr/bin/python3` selects the distribution interpreter that receives the system GI packages on these systems; a virtual environment or another `python3` on your PATH may not see them. The application checks GitHub releases at startup; it does not install updates.

`lspci` (usually from `pciutils`) is optional for PCI graphics details. Power-profile discovery requires `powerprofilesctl` and an available service. Profile changes are temporarily disabled because switching can cancel another application’s hold; switching back cannot restore it. GNOME settings are available only when the corresponding GNOME desktop settings can be read. Missing optional capabilities do not require running Avelin as root.

## Troubleshooting

- **`No module named avelin`:** change to the checkout root (the directory containing `avelin/`), then retry `/usr/bin/python3 -m avelin`.
- **`No module named gi` or GTK/Cairo import errors:** verify the system interpreter and the packages above. To check the same imports the app needs, run:

  ```sh
  /usr/bin/python3 -c "import gi; gi.require_version('Gtk', '4.0'); gi.require_foreign('cairo'); from gi.repository import Gtk; import cairo; print('GTK', Gtk.get_major_version(), Gtk.get_minor_version())"
  ```

  If this fails, read the final error and install the missing distribution package for that interpreter. Installing a package into a different virtual environment does not fix `/usr/bin/python3`.
- **Cannot open a display or no window appears:** launch from a terminal inside a logged-in graphical desktop session. A plain SSH or headless shell normally has no display. The smoke test below uses a virtual display, but it is not an interactive desktop test.
- **A feature is unavailable:** check its optional command/service and desktop prerequisites above. Availability also depends on the system and permissions; don't enable or change a system service merely to test Avelin without understanding its effects.

## Tests

From the checkout root, run the unit tests and compile check (these do not require a graphical display):

```sh
/usr/bin/python3 -m unittest discover -s tests -v
/usr/bin/python3 -m compileall -q avelin
```

For a GTK window smoke test on Debian/Ubuntu, additionally install `xvfb` and `xauth`, then run:

```sh
xvfb-run -a /usr/bin/python3 -m tests.gui_smoke
```

This opens and closes the app under a virtual display and checks that its main pages exist. It does not replace testing on a real desktop. When reporting a problem, include the distribution/version, desktop, Python version, the command and sanitized error output; remove usernames, paths, tokens and other private information first. See [contributing](../CONTRIBUTING.md).
