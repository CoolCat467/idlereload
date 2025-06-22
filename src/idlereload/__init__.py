"""IdleReload - Reload File Contents IDLE Extension."""

# Programmed by CoolCat467

from __future__ import annotations

# IdleReload - Reload File Contents IDLE Extension.
# Copyright (C) 2023-2025  CoolCat467
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__title__ = "idlereload"
__author__ = "CoolCat467"
__license__ = "GPLv3"
__version__ = "0.1.0"

import difflib
import importlib
import os
import sys
import time
import traceback
from contextlib import contextmanager
from functools import wraps
from idlelib.config import idleConf
from pathlib import Path
from tkinter import Event, Misc, Text, messagebox
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from idlelib.iomenu import IOBinding
    from idlelib.pyshell import PyShellEditorWindow
    from idlelib.undo import UndoDelegator
    from types import ModuleType

    from typing_extensions import ParamSpec

    PS = ParamSpec("PS")


T = TypeVar("T")
LOG_PATH = Path(idleConf.userdir) / "logs" / f"{__title__}.log"


def debug(message: str) -> None:
    """Print debug message."""
    # TODO: Censor username/user files
    line = f"[{__title__}] DEBUG: {message}"
    print(f"\n{line}")
    extension_log(line)


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
    values: dict[str, str | None],
) -> bool:
    """For each key in values, make sure key exists. Return if edited.

    If not, create and set to value.
    """
    need_save = False
    for key, default in values.items():
        if default is None:
            continue
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


@contextmanager
def undo_block(undo: UndoDelegator) -> Generator[None, None, None]:
    """Undo block context manager."""
    undo.undo_block_start()
    try:
        yield None
    finally:
        undo.undo_block_stop()


@contextmanager
def temporary_overwrite(
    object_: object,
    attribute: str,
    value: object,
) -> Generator[None, None, None]:
    """Temporarily overwrite object_.attribute with value, restore on exit."""
    if not hasattr(object_, attribute):
        yield None
    else:
        original = getattr(object_, attribute)
        setattr(object_, attribute, value)
        try:
            yield None
        finally:
            setattr(object_, attribute, original)


def extension_log(content: str) -> None:
    """Log content to extension log."""
    if not LOG_PATH.exists():
        LOG_PATH.parent.mkdir(exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fp:
        format_time = time.strftime("[%Y-%m-%d %H:%M:%S] ")
        for line in content.splitlines(keepends=True):
            fp.write(f"{format_time}{line}")
        if not line.endswith("\n"):
            fp.write("\n")


def extension_log_exception(exc: BaseException) -> None:
    """Log exception to extension log."""
    exception_text = "".join(traceback.format_exception(exc))
    extension_log(exception_text)


def log_exceptions(function: Callable[PS, T]) -> Callable[PS, T]:
    """Log any exceptions raised."""

    @wraps(function)
    def wrapper(*args: PS.args, **kwargs: PS.kwargs) -> T:
        """Catch Exceptions, log them to log file, and re-raise."""
        try:
            return function(*args, **kwargs)
        except Exception as exc:
            extension_log_exception(exc)
            raise

    return wrapper


# Important weird: If event handler function returns 'break',
# then it prevents other bindings of same event type from running.
# If returns None, normal and others are also run.


class idlereload:  # noqa: N801
    """Reload file contents without restarting IDLE."""

    __slots__ = (
        "editwin",
        "files",
        "text",
        "undo",
    )
    # Extend the file and format menus.
    menudefs: ClassVar = [
        (
            "file",
            [
                None,
                ("_Reload File", "<<reload-file>>"),
                ("Reload _Extensions", "<<idlereload-reload-extensions>>"),
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
        "idlereload-reload-extensions": None,
    }

    def __init__(self, editwin: PyShellEditorWindow) -> None:
        """Initialize the settings for this extension."""
        self.editwin: PyShellEditorWindow = editwin
        self.text: Text = editwin.text
        self.undo: UndoDelegator = editwin.undo
        self.files: IOBinding = editwin.io

        # self.triorun = tktrio.TkTrioRunner(
        #     self.editwin.top,
        #     self.editwin.close,
        # )
        #
        # for attr_name in dir(self):
        #     if attr_name.startswith("_"):
        #         continue
        #     if attr_name.endswith("_event_async"):
        #         bind_name = "-".join(attr_name.split("_")[:-2]).lower()
        #         self.text.bind(f"<<{bind_name}>>", self.get_async(attr_name))
        #         # print(f'{attr_name} -> {bind_name}')

        # Bind non-keyboard triggered events, as IDLE only binds
        # keyboard events automatically.
        for bind_name, key in self.bind_defaults.items():
            if key is not None:
                continue
            bind_func_name = bind_name.replace("-", "_") + "_event"
            if not hasattr(self, bind_func_name):
                debug(f"Missing function {bind_func_name}")
                continue
            bind_func = getattr(self, bind_func_name)
            if not callable(bind_func):
                debug(f"{bind_func_name} should be callable")
                continue
            self.text.bind(f"<<{bind_name}>>", bind_func)

    # def get_async(
    #     self,
    #     name: str,
    # ) -> Callable[[Event[Any]], str]:
    #     """Get sync callable to run async function."""
    #     async_function = getattr(self, name)
    #
    #     @wraps(async_function)
    #     def call_trio(event: Event[Any]) -> str:
    #         self.triorun(partial(async_function, event))
    #         return "break"
    #
    #     return call_trio

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
            debug("Raw filename is None")
            return "break", None
        file: str = os.path.abspath(raw_filename)

        # Everything worked
        return None, file

    @log_exceptions
    def reload_file_event(self, event: Event[Misc]) -> str:
        """Reload currently open file."""
        init_return, filename = self.initial()

        if init_return is not None:
            return init_return
        if filename is None:
            debug("Filename is None")
            self.text.bell()
            return "break"
        if not self.files.get_saved():
            if self.ask_save_dialog():
                # clear to save
                self.files.save(None)
            else:
                return "break"

        # Otherwise, read from disk
        # Ensure file exists
        if not os.path.exists(filename) or os.path.isdir(filename):
            debug(f"Filename {filename!r} does not exist or is a directory.")
            self.text.bell()
            return "break"

        # Remember where we started
        start_line_no: int = self.editwin.getlineno()

        self.files.set_saved(False)

        # # Reload file contents
        # if self.files.loadfile(filename):
        #     is_py_src = self.editwin.ispythonsource(filename)
        #     self.editwin.set_indentation_params(is_py_src)
        # self.editwin.gotoline(start_line_no)

        # Get original and new text
        source_text = self.text.get("1.0", "end-1c").splitlines()
        with open(filename, encoding=self.files.fileencoding) as disk:
            new_text = disk.read().splitlines()

        # debug('\nNew segment start:')
        matcher = difflib.SequenceMatcher(None, source_text, new_text)

        # Edit current text into new version
        with undo_block(self.undo):
            line_offset = 1
            start_offset = 0
            # For each delta operation
            for tag, a_low, a_high, b_low, b_high in matcher.get_opcodes():
                # debug(f"{tag:8} a[{a_low}:{a_high}] b[{b_low}:{b_high}]")
                source_data = "\n".join(source_text[a_low:a_high]) + "\n"
                final_data = "\n".join(new_text[b_low:b_high]) + "\n"
                # debug(f"> {source_data!r} {final_data!r}")

                if tag == "replace":
                    self.text.delete(
                        f"{a_low + line_offset}.0",
                        f"{a_high + line_offset}.0",
                    )
                    self.text.insert(
                        f"{a_low + line_offset}.0",
                        final_data,
                        (),
                    )
                    line_offset += (b_high - b_low) - (a_high - a_low)
                    if a_low < start_line_no:
                        start_offset += (b_high - b_low) - (a_high - a_low)
                elif tag == "delete":
                    get = self.text.get(
                        f"{a_low + line_offset}.0",
                        f"{a_high + line_offset}.0",
                    )
                    assert get == source_data, f"{get!r} != {source_data!r}"
                    self.text.delete(
                        f"{a_low + line_offset}.0",
                        f"{a_high + line_offset}.0",
                    )
                    line_offset -= a_high - a_low
                    if a_low < start_line_no:
                        start_offset -= a_high - a_low
                elif tag == "insert":
                    self.text.insert(
                        f"{a_low + line_offset}.0",
                        final_data,
                        (),
                    )
                    line_offset += b_high - b_low
                    if a_low < start_line_no:
                        start_offset += b_high - b_low
                elif tag == "equal":
                    get = self.text.get(
                        f"{a_low + line_offset}.0",
                        f"{a_high + line_offset}.0",
                    )
                    assert get == source_data, f"{get!r} != {source_data!r}"
                    continue
                else:
                    raise ValueError(f"Unknown tag {tag!r}")
            self.files.set_saved(True)
        self.editwin.gotoline(start_line_no + start_offset)

        self.text.bell()
        return "break"

    # def undo_fill_menu(self, menudefs, keydefs) -> None:
    #     for mname, entrylist in menudefs:
    #         if not entrylist:
    #             continue
    #         menu = self.editwin.menudict.get(mname)
    #         if not menu:
    #             continue
    #         label: str | None = None
    #         for entry_list_index, entry in enumerate(entrylist):
    #             if entry is None:
    #                 continue
    #             label, _eventname = entry
    #             underline, label = prepstr(label)
    #             break
    #         if label is None:
    #             debug("Valid label not found.")
    #             continue
    #         start_index = menu.index(label) - entry_list_index
    #         print(f'{menu.entryconfig(start_index) = }')
    # ##            print(f'{menu.entrycget(start_index, "label") = }')
    # ##            entry_count = len(entrylist)
    # ##            menu.delete(start_index, entry_count)
    #
    # def undo_fill_menu(self) -> None:
    #     for _menu_name, menu in self.editwin.menudict.items():
    #         menu.delete(None)
    #     self.editwin.fill_menus()

    def unload_extensions(self) -> None:
        """Unload extensions."""
        for extension_name, extension in self.editwin.extensions.items():
            ext_keydefs = idleConf.GetExtensionBindings(extension_name)
            # undo fill_menus(cls.menudefs, keydefs)
            # if hasattr(extension, "menudefs"):
            #     self.undo_fill_menu(extension.menudefs, ext_keydefs)
            for event, keylist in ext_keydefs.items():
                try:
                    self.editwin.text.event_delete(event, *keylist)
                except ValueError as exc:
                    traceback.print_exception(exc)
                try:
                    self.editwin.text.event_delete(event)
                except ValueError as exc:
                    traceback.print_exception(exc)

            try:
                if hasattr(extension, "close"):
                    extension.close()
            except Exception as exc:
                traceback.print_exception(exc)
                extension_log_exception(exc)

            try:
                if hasattr(extension, "on_reloading"):
                    extension.on_reloading()
            except Exception as exc:
                traceback.print_exception(exc)
                extension_log_exception(exc)

            if extension_name in sys.modules:
                to_remove: list[ModuleType] = [sys.modules[extension_name]]

                submodule = f"{extension_name}."
                for name, module in sys.modules.items():
                    if name.startswith(submodule):
                        to_remove.append(module)
                for module in to_remove:
                    importlib.reload(module)

        self.editwin.extensions.clear()

    @log_exceptions
    def idlereload_reload_extensions_event(self, event: Event[Misc]) -> str:
        """Reload extensions."""
        print(f"[{__title__}]: Reloading extensions")
        self.unload_extensions()

        def noop(*args: Any, **kwargs: Any) -> None:
            """Do nothing."""

        with temporary_overwrite(self.editwin, "fill_menus", noop):
            self.editwin.load_extensions()

        self.text.bell()
        return "break"


idlereload.reload()


if __name__ == "__main__":
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
    check_installed()
