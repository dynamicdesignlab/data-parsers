""" Common dialogs used for plotting

This module contains a collection of common dialogs used for plotting.

"""

from pathlib import Path

import gi
from matplotlib.backends import backend_gtk3

from .data_selection import SelectionPlotter

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402 - import must be under previous line


class NavigationToolbarNoCoordinates(backend_gtk3.NavigationToolbar2GTK3):
    """NavigationToolbar2TkNoCoordinates

    This custom toolbar class removes the normal coordinate
    readout of the default toolbar

    """

    def set_message(self, s):
        pass


class DataBoundSelectorDialog(Gtk.Dialog):
    def __init__(self, plotter: SelectionPlotter, step: float, digits: int):
        super().__init__(title="My Dialog", flags=0)

        self._plotter = plotter
        self._step = step
        self._digits = digits

        plot_box = self.get_content_area()

        toolbar_box = Gtk.Box()
        toolbar = NavigationToolbarNoCoordinates(self._plotter.canvas, plot_box)
        toolbar.update()
        toolbar_box.pack_start(toolbar, False, False, 0)

        plot_box.pack_start(self._plotter.canvas, True, True, 0)
        plot_box.pack_start(toolbar_box, True, True, 0)

        self._create_action_entries()
        self.show_all()

    def _create_action_entries(self):
        action_box = self.get_action_area()

        selection_label = Gtk.Label()
        selection_label.set_markup(r"<b>BOUNDS</b>")
        min_label = Gtk.Label(label="Lower")
        min_label.set_justify(Gtk.Justification.RIGHT)
        max_label = Gtk.Label(label="Upper")
        max_label.set_justify(Gtk.Justification.RIGHT)

        init_lower, init_upper = self._plotter.get_bounds()
        self._min_entry = Gtk.SpinButton.new_with_range(
            min=init_lower, max=init_upper, step=self._step
        )
        self._min_entry.set_value(init_lower)
        self._min_entry.set_digits(self._digits)
        self._min_entry.connect("value-changed", self._entry_changed_callback)

        self._max_entry = Gtk.SpinButton.new_with_range(
            min=init_lower, max=init_upper, step=self._step
        )
        self._max_entry.set_value(init_upper)
        self._max_entry.set_digits(self._digits)
        self._max_entry.connect("value-changed", self._entry_changed_callback)

        action_box.pack_start(selection_label, False, False, 0)
        action_box.pack_start(min_label, False, False, 0)
        action_box.pack_start(self._min_entry, False, False, 0)
        action_box.pack_start(max_label, False, False, 0)
        action_box.pack_start(self._max_entry, False, False, 0)

        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Accept", Gtk.ResponseType.ACCEPT)

    def _entry_changed_callback(self, *_) -> None:
        lower_bound = self._min_entry.get_value()
        upper_bound = self._max_entry.get_value()
        self._plotter.update_bounds(lower=lower_bound, upper=upper_bound)

    def get_bounds(self) -> tuple[float, float]:
        return self._plotter.get_bounds()


def create_data_bound_dialog(
    plotter: SelectionPlotter, step: float = 1.0, digits: float = 2
) -> tuple[float, float]:
    dialog = DataBoundSelectorDialog(plotter=plotter, step=step, digits=digits)
    response = dialog.run()

    if response == Gtk.ResponseType.CANCEL:
        dialog.destroy()
        dialog.show()
        exit()

    lower, upper = dialog.get_bounds()
    dialog.destroy()
    while Gtk.events_pending():
        Gtk.main_iteration()

    return lower, upper


def open_file_dialog(default_dir: Path, label="All Files", filt_pattern="*"):
    dialog = Gtk.FileChooserDialog(
        title="Please choose a file", action=Gtk.FileChooserAction.OPEN
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL,
        Gtk.ResponseType.CANCEL,
        Gtk.STOCK_OPEN,
        Gtk.ResponseType.OK,
    )
    dialog.set_current_folder(str(default_dir))
    filter_obj = Gtk.FileFilter()
    filter_obj.set_name(label)
    filter_obj.add_pattern(filt_pattern)
    dialog.add_filter(filter_obj)

    response = dialog.run()
    if response == Gtk.ResponseType.CANCEL:
        dialog.destroy()
        dialog.show()
        exit()

    file_path = Path(dialog.get_filename())
    dialog.destroy()
    while Gtk.events_pending():
        Gtk.main_iteration()

    return file_path


def save_file_dialog(
    default_dir: Path,
    label="All Files",
    file_suffix: str = None,
    default_name: str = None,
):
    dialog = Gtk.FileChooserDialog(
        title="Please choose file save location", action=Gtk.FileChooserAction.SAVE
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL,
        Gtk.ResponseType.CANCEL,
        Gtk.STOCK_SAVE,
        Gtk.ResponseType.ACCEPT,
    )
    dialog.set_current_folder(str(default_dir))
    dialog.set_do_overwrite_confirmation(True)

    if default_name is None:
        default_name = ""
    dialog.set_current_name(default_name)

    if file_suffix is None:
        filt_pattern = "*"
    else:
        filt_pattern = f"*{file_suffix}"

    filter_obj = Gtk.FileFilter()
    filter_obj.set_name(f"{label} ({filt_pattern})")
    filter_obj.add_pattern(filt_pattern)
    dialog.add_filter(filter_obj)

    response = dialog.run()
    if response == Gtk.ResponseType.CANCEL:
        dialog.destroy()
        dialog.show()
        exit()

    file_path = Path(dialog.get_filename()).with_suffix(file_suffix)

    dialog.destroy()
    while Gtk.events_pending():
        Gtk.main_iteration()

    return file_path
