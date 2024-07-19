""" Classes for data selection plotting

This module contains a collection of data selection plotters intended
to be used with the plot_dialogs module.

"""

import abc
from dataclasses import InitVar, dataclass, field
from typing import Any, Protocol

import numpy as np
from matplotlib import axis, figure, lines
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas


def trim_data_to_bounds(
    xdata: np.ndarray, ydata: np.ndarray, lower: float, upper: float, axis: int = 0
) -> tuple[np.ndarray, np.ndarray]:
    """
    Trims data to selected boundaries.

    The boundaries determine the maximum and minimum values allowable in the
    xdata array.  The xdata array is trimmed to these values and returned. The
    values of the ydata array that correspond to the returned xdata values are
    returned as well.

    Parameters
    ----------
    xdata: np.ndarray
        Reference data array
    ydata: np.ndarray
        Data array of interest
    lower: float
        Lower bound on allowable xdata values
    upper: float
        Upper bound on allowable xdata values
    axis: int
        Axis along which to trim values

    Returns
    -------
    trim_xdata: np.ndarray
        Trimmed xdata array
    trim_ydata: np.ndarray
        Trimmed ydata array

    """
    idx, *_ = np.where(np.logical_and(xdata >= lower, xdata <= upper))
    xtrim = xdata[idx]
    ytrim = np.take(ydata, idx, axis=axis)
    return xtrim, ytrim


@dataclass
class SelectionPlotter(abc.ABC):
    """
    Base class implementation of a selection plotter.

    This class's children are designed to be used with the data selection
    dialog class.

    """

    _figure: figure.Figure = field(init=False)
    _canvas: FigureCanvas = field(init=False)
    _lower_bound: float = field(init=False)
    _upper_bound: float = field(init=False)

    @property
    @abc.abstractmethod
    def data_lower_bound(self):
        """
        Lower bound contained in data.

        Returns
        -------
        lower_bound: float

        """

    @property
    @abc.abstractmethod
    def data_upper_bound(self):
        """
        Upper bound contained in data.

        Returns
        -------
        upper_bound: float

        """

    @abc.abstractmethod
    def _update_plot(self) -> None:
        """Update plot based on new user entered data bounds."""

    @property
    def canvas(self):
        """
        Get FigureCanvas object for use in GUI building.

        Returns
        -------
        canvas: FigureCanvas
            Canvas that figure exists on
        """
        return self._canvas

    @property
    def lower_bound(self):
        """
        Current user-defined lower bound.

        Returns
        -------
        lower_bound: float

        """
        return self._lower_bound

    @property
    def upper_bound(self):
        """
        Current user-defined upper bound.

        Returns
        -------
        upper_bound: float

        """
        return self._upper_bound

    def get_bounds(self) -> tuple[float, float]:
        """
        Get current data bounds.

        Returns
        -------
        lower_bound: float
            Lower data bound
        upper_bound: float
            Upper data bound
        """
        return (self.lower_bound, self.upper_bound)

    def redraw_plot(self) -> None:
        """
        Redraw plot when data bounds are updated.

        Calls the user-defined _update_plot() method and then redraws the canvas.

        """
        self._update_plot()
        self._canvas.draw()
        self._canvas.flush_events()

    def update_bounds(self, lower: float, upper: float) -> None:
        """
        Update current data bounds.

        If the supplied bounds lie outside the data's range, the values
        are clamped to valid values. The clamped values are returned.

        Parameters
        ----------
        lower: float
            Desired lower bound
        upper: float
            Desired upper bound
        """
        self._lower_bound = lower
        self._upper_bound = upper

        self.redraw_plot()

    def __post_init__(self) -> None:
        """Initialize plotter figure and Canvas."""
        self._figure = figure.Figure(tight_layout=True)
        self._canvas = FigureCanvas(self._figure)
        self._canvas.set_size_request(800, 600)

        self._lower_bound = self.data_lower_bound
        self._upper_bound = self.data_upper_bound


class WorldProtocol(Protocol):
    @property
    def s_m(self) -> np.ndarray:
        pass

    @property
    def east_m(self) -> np.ndarray:
        pass

    @property
    def north_m(self) -> np.ndarray:
        pass

    def plot(self, ax: axis, *args, **kwargs) -> None:
        pass


@dataclass
class PathDistanceSelectionPlotter(SelectionPlotter):
    """SelectionPlotter for selecting parts of a world.

    Implementation of the SelectionPlotter class for selecting a piece of a
    given world to visualize.  This plotter will highlight the selected portion
    of the world interactively.
    """

    world: WorldProtocol = field(repr=False)

    xlabel: InitVar[str]
    ylabel: InitVar[str]

    s_data: InitVar[np.ndarray] = None

    plot_kwargs: InitVar[dict[str, Any]] = None
    axis_kwargs: InitVar[dict[str, Any]] = None

    _highlight_plot: lines.Line2D = field(init=False)

    @property
    def data_lower_bound(self):
        return self.min_s

    @property
    def data_upper_bound(self):
        return self.max_s

    def _update_plot(self) -> None:
        _, east_select = trim_data_to_bounds(
            xdata=self.world.s_m,
            ydata=self.world.east_m,
            lower=self.lower_bound,
            upper=self.upper_bound,
        )
        _, north_select = trim_data_to_bounds(
            xdata=self.world.s_m,
            ydata=self.world.north_m,
            lower=self.lower_bound,
            upper=self.upper_bound,
        )
        self._highlight_plot.set_data(east_select, north_select)

    def __post_init__(
        self,
        xlabel: str,
        ylabel: str,
        s_data: np.ndarray,
        plot_kwargs: dict[str, Any],
        axis_kwargs: dict[str, Any],
    ) -> None:
        if s_data is None:
            self.min_s = np.min(self.world.s_m)
            self.max_s = np.max(self.world.s_m)
        else:
            self.min_s = np.min(s_data)
            self.max_s = np.max(s_data)

        super().__post_init__()
        ax = self._figure.add_subplot()

        if plot_kwargs is None:
            plot_kwargs = {}
        self.world.plot(ax=ax, **plot_kwargs)

        (self._highlight_plot,) = ax.plot(
            self.world.east_m, self.world.north_m, "r-", linewidth=2
        )

        if axis_kwargs is None:
            axis_kwargs = {}
        ax.set(**axis_kwargs)

        ax.grid(True)
        ax.set_title("Select Data Boundaries by Path Position")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.axis("equal")

        self._update_plot()


@dataclass
class TimeSeriesPlotter(SelectionPlotter):
    """SelectionPlotter for selecting a range of timeseries data.

    Implementation of the SelectionPlotter class for selecting a range of time
    to visualize.  This plotter will highlight the selected portion
    of the timeseries interactively.
    """

    xdata: np.ndarray
    ydata: np.ndarray

    xlabel: InitVar[str]
    ylabel: InitVar[str]
    ylim: InitVar[tuple[float, float]] = None

    _highlight_plot: lines.Line2D = field(init=False)

    @property
    def data_lower_bound(self):
        return np.min(self.xdata)

    @property
    def data_upper_bound(self):
        return np.max(self.xdata)

    def _update_plot(self) -> None:
        xdata_select, ydata_select = trim_data_to_bounds(
            xdata=self.xdata,
            ydata=self.ydata,
            lower=self.lower_bound,
            upper=self.upper_bound,
        )
        self._highlight_plot.set_data(xdata_select, ydata_select)

    def __post_init__(
        self, xlabel: str, ylabel: str, ylim: tuple[float, float]
    ) -> None:
        super().__post_init__()
        ax = self._figure.add_subplot()
        ax.plot(self.xdata, self.ydata, "k-")

        if ylim is not None:
            ax.set_ylim(*ylim)

        ax.set_title("Select Data Boundaries by Time")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True)

        (self._highlight_plot,) = ax.plot(
            self.xdata, self.ydata, "r-", linewidth=8, alpha=0.6
        )
