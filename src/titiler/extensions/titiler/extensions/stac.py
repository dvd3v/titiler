"""rio-stac Extension."""

import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

from fastapi import Depends, Query

from titiler.core.factory import BaseTilerFactory, FactoryExtension

# Avoids a Pydantic error:
# TypeError: You should use `typing_extensions.TypedDict` instead of `typing.TypedDict` with Python < 3.9.2.
# Without it, there is no way to differentiate required and optional fields when subclassed.
# Ref: https://github.com/pydantic/pydantic/pull/3374
if sys.version_info < (3, 9, 2):
    from typing_extensions import TypedDict
else:
    from typing import TypedDict

if sys.version_info >= (3, 9):
    from typing import Annotated  # pylint: disable=no-name-in-module
else:
    from typing_extensions import Annotated

try:
    import pystac
    from pystac.utils import datetime_to_str, str_to_datetime
    from rio_stac.stac import create_stac_item
except ImportError:  # pragma: nocover
    create_stac_item = None  # type: ignore
    pystac = None  # type: ignore
    str_to_datetime = datetime_to_str = None  # type: ignore


class Item(TypedDict, total=False):
    """STAC Item."""

    type: str
    stac_version: str
    stac_extensions: Optional[List[str]]
    id: str
    geometry: Dict[str, Any]
    bbox: List[float]
    properties: Dict[str, Any]
    links: List[Dict[str, Any]]
    assets: Dict[str, Any]
    collection: str


@dataclass
class stacExtension(FactoryExtension):
    """Add /stac endpoint to a COG TilerFactory."""

    def register(self, factory: BaseTilerFactory):
        """Register endpoint to the tiler factory."""

        assert (
            create_stac_item is not None
        ), "'rio-stac' must be installed to use stacExtension"
        assert pystac is not None, "'pystac' must be installed to use stacExtension"

        media = [m.value for m in pystac.MediaType] + ["auto"]

        @factory.router.get("/stac", response_model=Item, name="Create STAC Item")
        def create_stac(
            src_path=Depends(factory.path_dependency),
            datetime: Annotated[
                Optional[str],
                Query(
                    description="The date and time of the assets, in UTC (e.g 2020-01-01, 2020-01-01T01:01:01).",
                ),
            ] = None,
            extensions: Annotated[
                Optional[List[str]],
                Query(description="STAC extension URL the Item implements."),
            ] = None,
            collection: Annotated[
                Optional[str],
                Query(description="The Collection ID that this item belongs to."),
            ] = None,
            collection_url: Annotated[
                Optional[str],
                Query(description="Link to the STAC Collection."),
            ] = None,
            # properties: Optional[Dict] = Query(None, description="Additional properties to add in the item."),
            id: Annotated[
                Optional[str],
                Query(
                    description="Id to assign to the item (default to the source basename)."
                ),
            ] = None,
            asset_name: Annotated[
                Optional[str],
                Query(description="asset name for the source (default to 'data')."),
            ] = "data",
            asset_roles: Annotated[
                Optional[List[str]],
                Query(description="list of asset's roles."),
            ] = None,
            asset_media_type: Annotated[  # type: ignore
                Optional[Literal[tuple(media)]],
                Query(description="Asset's media type"),
            ] = "auto",
            asset_href: Annotated[
                Optional[str],
                Query(description="Asset's URI (default to source's path)"),
            ] = None,
            with_proj: Annotated[
                Optional[bool],
                Query(description="Add the `projection` extension and properties."),
            ] = True,
            with_raster: Annotated[
                Optional[bool],
                Query(description="Add the `raster` extension and properties."),
            ] = True,
            with_eo: Annotated[
                Optional[bool],
                Query(description="Add the `eo` extension and properties."),
            ] = True,
            max_size: Annotated[
                Optional[int],
                Query(
                    gt=0,
                    description="Limit array size from which to get the raster statistics.",
                ),
            ] = 1024,
        ):
            """Create STAC item."""
            properties = (
                {}
            )  # or properties = properties or {} if we add properties in Query

            dt = None
            if datetime:
                if "/" in datetime:
                    start_datetime, end_datetime = datetime.split("/")
                    properties["start_datetime"] = datetime_to_str(
                        str_to_datetime(start_datetime)
                    )
                    properties["end_datetime"] = datetime_to_str(
                        str_to_datetime(end_datetime)
                    )
                else:
                    dt = str_to_datetime(datetime)

            return create_stac_item(
                src_path,
                input_datetime=dt,
                extensions=extensions,
                collection=collection,
                collection_url=collection_url,
                properties=properties,
                id=id,
                asset_name=asset_name,
                asset_roles=asset_roles,
                asset_media_type=asset_media_type,
                asset_href=asset_href or src_path,
                with_proj=with_proj,
                with_raster=with_raster,
                with_eo=with_eo,
                raster_max_size=max_size,
            ).to_dict()
