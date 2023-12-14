"""Reload File IDLE Extension."""

# Programmed by CoolCat467

from __future__ import annotations

__title__ = "idlereload"
__author__ = "CoolCat467"
__license__ = "GPLv3"
__version__ = "0.0.0"
__ver_major__ = 0
__ver_minor__ = 0
__ver_patch__ = 0

import os
import sys
from collections.abc import Callable
from functools import partial, wraps
from idlelib.config import idleConf
from idlelib.format import FormatRegion
from idlelib.iomenu import IOBinding
from idlelib.pyshell import PyShellEditorWindow, PyShellFileList
from idlelib.undo import UndoDelegator
from tkinter import Event, Text, Tk, messagebox
from typing import Any, ClassVar

from idlereload import tktrio


def debug(message: str) -> None:
    """Print debug message."""
    # TODO: Censor username/user files
    print(f"\n[{__title__}] DEBUG: {message}")


def get_required_config(
    values: dict[str, str],
    bind_defaults: dict[str, str],
) -> str:
    """Get required configuration file data."""
    config = ""
    # Get configuration defaults
    settings = "\n".join(
        f"{key} = {default}" for key, default in values.items()
    )
    if settings:
        config += f"\n[{__title__}]\n{settings}"
        if bind_defaults:
            config += "\n"
    # Get key bindings data
    settings = "\n".join(
        f"{event} = {key}" for event, key in bind_defaults.items()
    )
    if settings:
        config += f"\n[{__title__}_cfgBindings]\n{settings}"
    return config


def check_installed() -> bool:
    """Make sure extension installed."""
    # Get list of system extensions
    extensions = set(idleConf.defaultCfg["extensions"])

    # Do we have the user extend extension?
    has_user = "idleuserextend" in idleConf.GetExtensions(active_only=True)

    # If we don't, things get messy and we need to change the root config file
    ex_defaults = idleConf.defaultCfg["extensions"].file
    if has_user:
        # Otherwise, idleuserextend patches IDLE and we only need to modify
        # the user config file
        ex_defaults = idleConf.userCfg["extensions"].file
        extensions |= set(idleConf.userCfg["extensions"])

    # Import this extension (this file),
    module = __import__(__title__)

    # Get extension class
    if not hasattr(module, __title__):
        print(
            f"ERROR: Somehow, {__title__} was installed improperly, "
            f"no {__title__} class found in module. Please report "
            "this on github.",
            file=sys.stderr,
        )
        sys.exit(1)

    cls = getattr(module, __title__)

    # Get extension class keybinding defaults
    required_config = get_required_config(
        getattr(cls, "values", {}),
        getattr(cls, "bind_defaults", {}),
    )

    # If this extension not in there,
    if __title__ not in extensions:
        # Tell user how to add it to system list.
        print(f"{__title__} not in system registered extensions!")
        print(
            f"Please run the following command to add {__title__} "
            + "to system extensions list.\n",
        )
        # Make sure line-breaks will go properly in terminal
        add_data = required_config.replace("\n", "\\n")
        # Tell them the command
        append = "| sudo tee -a"
        if has_user:
            append = ">>"
        print(f"echo -e '{add_data}' {append} {ex_defaults}\n")
    else:
        print(f"Configuration should be good! (v{__version__})")
        return True
    return False


def ensure_section_exists(section: str) -> bool:
    """Ensure section exists in user extensions configuration.

    Returns True if edited.
    """
    if section not in idleConf.GetSectionList("user", "extensions"):
        idleConf.userCfg["extensions"].AddSection(section)
        return True
    return False


def ensure_values_exist_in_section(
    section: str,
    values: dict[str, str],
) -> bool:
    """For each key in values, make sure key exists. Return if edited.

    If not, create and set to value.
    """
    need_save = False
    for key, default in values.items():
        value = idleConf.GetOption(
            "extensions",
            section,
            key,
            warn_on_default=False,
        )
        if value is None:
            idleConf.SetOption("extensions", section, key, default)
            need_save = True
    return need_save


# Important weird: If event handler function returns 'break',
# then it prevents other bindings of same event type from running.
# If returns None, normal and others are also run.


class idlereload:  # noqa: N801
    """Add comments from mypy to an open program."""

    __slots__ = (
        "editwin",
        "text",
        "undo",
        "formatter",
        "files",
        "flist",
        "triorun",
    )
    # Extend the file and format menus.
    menudefs: ClassVar = [
        (
            "file",
            [
                None,
                ("_Reload File", "<<reload-file>>"),
            ],
        ),
    ]
    # Default values for configuration file
    values: ClassVar = {
        "enable": "True",
        "enable_editor": "True",
        "enable_shell": "False",
    }
    # Default key binds for configuration file
    bind_defaults: ClassVar = {
        "reload-file": "<Control-Shift-Key-R>",
    }

    # Class attributes
    idlerc_folder = os.path.expanduser(idleConf.userdir)

    def __init__(self, editwin: PyShellEditorWindow) -> None:
        """Initialize the settings for this extension."""
        self.editwin: PyShellEditorWindow = editwin
        self.text: Text = editwin.text
        self.undo: UndoDelegator = editwin.undo
        self.formatter: FormatRegion = editwin.fregion
        self.flist: PyShellFileList = editwin.flist
        self.files: IOBinding = editwin.io

        self.triorun = tktrio.TkTrioRunner(
            self.editwin.top,
            self.editwin.close,
        )

        for attr_name in dir(self):
            if attr_name.startswith("_"):
                continue
            if attr_name.endswith("_event_async"):
                bind_name = "-".join(attr_name.split("_")[:-2]).lower()
                self.text.bind(f"<<{bind_name}>>", self.get_async(attr_name))
                # print(f'{attr_name} -> {bind_name}')

    def get_async(
        self,
        name: str,
    ) -> Callable[[Event[Any]], str]:
        """Get sync callable to run async function."""
        async_function = getattr(self, name)

        @wraps(async_function)
        def call_trio(event: Event[Any]) -> str:
            self.triorun(partial(async_function, event))
            return "break"

        return call_trio

    def __repr__(self) -> str:
        """Return representation of self."""
        return f"{self.__class__.__name__}({self.editwin!r})"

    @classmethod
    def ensure_bindings_exist(cls) -> bool:
        """Ensure key bindings exist in user extensions configuration.

        Return True if need to save.
        """
        if not cls.bind_defaults:
            return False

        need_save = False
        section = f"{cls.__name__}_cfgBindings"
        if ensure_section_exists(section):
            need_save = True
        if ensure_values_exist_in_section(section, cls.bind_defaults):
            need_save = True
        return need_save

    @classmethod
    def ensure_config_exists(cls) -> bool:
        """Ensure required configuration exists for this extension.

        Return True if need to save.
        """
        need_save = False
        if ensure_section_exists(cls.__name__):
            need_save = True
        if ensure_values_exist_in_section(cls.__name__, cls.values):
            need_save = True
        return need_save

    @classmethod
    def reload(cls) -> None:
        """Load class variables from configuration."""
        # Ensure file default values exist so they appear in settings menu
        save = cls.ensure_config_exists()
        if cls.ensure_bindings_exist() or save:
            idleConf.SaveUserCfgFiles()

        # Reload configuration file
        idleConf.LoadCfgFiles()

        # For all possible configuration values
        for key, default in cls.values.items():
            # Set attribute of key name to key value from configuration file
            if key not in {"enable", "enable_editor", "enable_shell"}:
                value = idleConf.GetOption(
                    "extensions",
                    cls.__name__,
                    key,
                    default=default,
                )
                setattr(cls, key, value)

    def ask_save_dialog(self) -> bool:
        """Ask to save dialog stolen from idlelib.runscript.ScriptBinding."""
        msg = "File Has Modifications\n" + 5 * " " + "OK to Overwrite?"
        confirm: bool = messagebox.askokcancel(
            title="Overwrite File",
            message=msg,
            default=messagebox.OK,
            parent=self.text,
        )
        return confirm

    def initial(self) -> tuple[str | None, str | None]:
        """Do common initial setup. Return error or none, file.

        Reload configuration, make sure file is saved,
        and make sure mypy is installed
        """
        self.reload()

        # Get file we are checking
        raw_filename: str | None = self.files.filename
        if raw_filename is None:
            return "break", None
        file: str = os.path.abspath(raw_filename)

        # Everything worked
        return None, file

    def reload_file_event(self, event: Event[Any]) -> str:
        """Perform a mypy check and add comments."""
        init_return, filename = self.initial()

        if init_return is not None:
            return init_return
        if filename is None:
            return "break"
        if not self.files.get_saved() and self.ask_save_dialog():
            # clear to save
            self.files.save(None)
            return "break"
        # Otherwise, read from disk

        # Remember where we started
        start_line_no: int = self.editwin.getlineno()

        # Reload file contents
        if (
            os.path.exists(filename)
            and not os.path.isdir(filename)
            and self.files.loadfile(filename)
        ):
            is_py_src = self.editwin.ispythonsource(filename)
            self.editwin.set_indentation_params(is_py_src)
        self.editwin.gotoline(start_line_no)

        self.text.bell()
        return "break"

    # def close(self) -> None:
    #    """Called when any idle editor window closes"""


idlereload.reload()


def get_fake_editwin(root_tk: Tk) -> PyShellEditorWindow:
    """Get fake edit window for testing."""
    from idlelib.pyshell import PyShellEditorWindow

    class FakeEditWindow(PyShellEditorWindow):  # type: ignore[misc,unused-ignore]
        """FakeEditWindow for testing."""

        def __init__(self) -> None:
            return

        from tkinter import Text

        class _FakeText(Text):
            """Make bind do nothing."""

            def __init__(self) -> None:
                """Requires no arguments."""
                return

            bind = lambda x, y: None  # type: ignore[assignment]  # noqa
            root = root_tk
            close: Any = None

        text = _FakeText()
        fregion: Any = FormatRegion
        flist: Any = PyShellFileList
        io: Any = IOBinding

    return FakeEditWindow()


if __name__ == "__main__":
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
    check_installed()
    # self = idlereload(get_fake_editwin())
