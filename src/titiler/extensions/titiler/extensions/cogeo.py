"""rio-cogeo Extension."""

import sys
from dataclasses import dataclass

from fastapi import Depends, Query

from titiler.core.factory import BaseTilerFactory, FactoryExtension
from titiler.core.resources.responses import JSONResponse

if sys.version_info >= (3, 9):
    from typing import Annotated  # pylint: disable=no-name-in-module
else:
    from typing_extensions import Annotated

try:
    from rio_cogeo.cogeo import cog_info
    from rio_cogeo.models import Info
except ImportError:  # pragma: nocover
    cog_info = None  # type: ignore
    Info = None


@dataclass
class cogValidateExtension(FactoryExtension):
    """Add /validate endpoint to a COG TilerFactory."""

    def register(self, factory: BaseTilerFactory):
        """Register endpoint to the tiler factory."""

        assert (
            cog_info is not None
        ), "'rio_cogeo' must be installed to use CogValidateExtension"

        @factory.router.get(
            "/validate",
            response_model=Info,
            response_class=JSONResponse,
        )
        def validate(
            src_path=Depends(factory.path_dependency),
            strict: Annotated[
                bool,
                Query(description="Treat warnings as errors"),
            ] = False,
        ):
            """Validate a COG"""
            return cog_info(src_path, strict=strict)
