import logging
import pathlib
from typing import Optional

import typer
import yaml

from autora.controller import Controller
from autora.theorist.__main__ import _configure_logger

_logger = logging.getLogger(__name__)


def main(
    manager: pathlib.Path,
    directory: pathlib.Path,
    step_name: Optional[str] = None,
    verbose: bool = False,
    debug: bool = False,
):
    _logger.debug("initializing")
    _configure_logger(debug, verbose)
    controller_ = _load_manager(manager)

    _logger.debug(f"loading manager state from {directory=}")
    controller_.load(directory)

    if step_name is not None:
        step_name_: str = step_name
        _logger.info(f"setting next {step_name=}")
        assert isinstance(step_name_, str)
        controller_.planner = lambda _: step_name_

    _logger.info("running next step")
    next(controller_)

    _logger.debug(f"last result: {controller_.state.history[-1]}")

    _logger.info("writing out results")
    controller_.dump(directory)

    return


def _load_manager(path: pathlib.Path) -> Controller:
    _logger.debug(f"_load_manager: loading from {path=}")
    with open(path, "r") as f:
        controller_ = yaml.load(f, yaml.Loader)
    assert isinstance(
        controller_, Controller
    ), f"controller type {type(controller_)=} unsupported"
    return controller_


if __name__ == "__main__":
    typer.run(main)
