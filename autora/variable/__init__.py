from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Generator, Iterator, Optional, Sequence

import numpy as np


class ValueType(str, Enum):
    """Specifies supported value types supported by Variables."""

    REAL = "real"
    SIGMOID = "sigmoid"
    PROBABILITY = "probability"  # single probability
    PROBABILITY_SAMPLE = "probability_sample"  # sample from single probability
    PROBABILITY_DISTRIBUTION = (
        "probability_distribution"  # probability distribution over classes
    )
    CLASS = "class"  # sample from probability distribution over classes


class Variable:
    """Describes an experimental variable: name, type, range, units, and value of a variable."""

    def __init__(
        self,
        name: str = "",
        value_range: Sequence = (0, 1),
        units: str = "",
        type: ValueType = ValueType.REAL,
        variable_label: str = "",
        rescale: float = 1,
        is_covariate: bool = False,
    ):
        """
        Initialize a variable.

        Args:
            name: name of the variable
            value_range: range of the variable
            units: units of the variable
            type: type of the variable
            variable_label: label of the variable
            rescale: rescale factor for the variable
            is_covariate: whether this variable is a covariate
        """

        self._name = name
        self._units = units
        self._value_range = value_range
        self._value = 0
        self._type = type
        if variable_label == "":
            self._variable_label = self._name
        else:
            self._variable_label = variable_label
        self._rescale = rescale
        self._is_covariate = is_covariate

    @property
    def name(self) -> str:
        """Get variable name."""
        return self._name

    @property
    def units(self) -> str:
        """Get variable units.

        Returns:
            variable units
        """
        return self._units

    @property
    def variable_label(self) -> str:
        """Get variable label.

        Returns:
            variable label
        """
        return self._variable_label

    @property
    def type(self) -> ValueType:
        """
        Get variable value type.

        Returns:
            the relevant ValueType
        """
        return self._type


@dataclass(frozen=True)
class VariableCollection:
    """Immutable metadata about dependent / independent variables and covariates."""

    independent_variables: Sequence[Variable]
    dependent_variables: Sequence[Variable]
    covariates: Sequence[Variable] = field(default_factory=list)

    @property
    def all_variables(self) -> Iterator[Variable]:
        """Get all variables.

        Returns:
            iterator over all variables
        """
        for vars in (
            self.independent_variables,
            self.dependent_variables,
            self.covariates,
        ):
            for v in vars:
                yield v

    @property
    def variable_names(self) -> Generator[str, None, None]:
        """Get variable names.

        Returns:
            variable names
        """
        return (v.name for v in self.all_variables)

    @property
    def output_type(self) -> str:
        """Get output type.

        Returns:
            output type
        """
        first_type = self.dependent_variables[0].type
        assert all(dv.type == first_type for dv in self.dependent_variables), (
            "Dependent variable output types don't match. "
            "Different output types are not supported yet."
        )
        return first_type

    @property
    def input_dimensions(self) -> int:
        """The number of independent variables and covariates.

        Returns:
            number of independent variables and covariates
        """
        return len(self.independent_variables) + len(self.covariates)

    @property
    def output_dimensions(self) -> int:
        """The number of dependent variables.

        Returns:
            number of dependent variables
        """
        return len(self.dependent_variables)


class IV(Variable):
    """Independent variable."""

    def __init__(self, *args, **kwargs):
        """
        Initialize independent variable.

        For arguments, see [autora.variable.Variable][autora.variable.Variable.__init__]
        """
        self._name = "IV"
        self._variable_label = "Independent Variable"

        super().__init__(*args, **kwargs)

    # Method for measuring dependent variable.
    @abstractmethod
    def manipulate(self):
        """Manipulate independent variable."""
        pass


class DV(Variable):
    """Dependent variable."""

    def __init__(self, *args, **kwargs):
        """
        Initialize dependent variable.

        For arguments, see [autora.variable.Variable][autora.variable.Variable.__init__]
        """
        self._name = "DV"
        self._variable_label = "Dependent Variable"

        self._is_covariate = False

        super().__init__(*args, **kwargs)

    # Method for measuring dependent variable.
    @abstractmethod
    def measure(self):
        """Measure dependent variable."""
        pass

    # Get whether this dependent variable is treated as covariate.
    def __is_covariate__(self) -> bool:
        """Get whether this dependent variable is treated as covariate.

        Returns:
            whether this dependent variable is treated as covariate
        """
        return self._is_covariate

    # Set whether this dependent variable is treated as covariate.
    def __set_covariate__(self, is_covariate: bool):
        """Set whether this dependent variable is treated as covariate.

        Arguments:
            is_covariate: whether this dependent variable is treated as covariate
        """
        self._is_covariate = is_covariate


class IVTrial(IV):
    """
    Experiment trial as independent variable.
    """

    _name = "trial"
    _UID = ""
    _variable_label = "Trial"
    _units = "trials"
    _priority = 0
    _value_range = (0, 10000000)
    _value = 0

    def __init__(self, *args, **kwargs):
        """
        Initialize independent variable representing experiment trials.

        For arguments, see [autora.variable.Variable][autora.variable.Variable.__init__]
        """
        super(IVTrial, self).__init__(*args, **kwargs)

    # Waits until specified time has passed relative to reference time
    def manipulate(self):
        """
        Manipulate independent variable representing experiment trials.
        """
        pass

    def disconnect(self):
        """
        Disconnect independent variable representing experiment trials.
        """
        pass


dv_labels = {}
iv_labels = {}


def register_iv_label(**kwargs):
    iv_labels.update(kwargs)
    return


def register_dv_label(**kwargs):
    dv_labels.update(kwargs)
    return
