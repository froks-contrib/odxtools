# SPDX-License-Identifier: MIT
import argparse
from typing import Dict, List, Optional

from ..database import Database
from ..diagservice import DiagService
from ..exceptions import odxraise
from ..odxtypes import ParameterValue
from ..singleecujob import SingleEcuJob
from . import _parser_utils

# name of the tool
_odxtools_tool_name_ = "decode"


def get_display_value(v: ParameterValue) -> str:
    if isinstance(v, bytes):
        return v.hex(" ")
    elif isinstance(v, int):
        return f"{v} (0x{v:x})"
    else:
        return str(v)


def print_summary(
        odxdb: Database,
        ecu_variants: Optional[List[str]] = None,
        data: bytes = b'',
        decode: bool = False,
) -> None:
    ecu_names = ecu_variants if ecu_variants else [ecu.short_name for ecu in odxdb.ecus]
    services: Dict[DiagService, List[str]] = {}
    for ecu_name in ecu_names:
        ecu = odxdb.ecus[ecu_name]
        if not ecu:
            print(f"The ecu variant '{ecu_name}' could not be found!")
            continue
        if data:
            found_services = ecu._find_services_for_uds(data)
            for found_service in found_services:
                ecu_names = services.get(found_service, [])
                ecu_names.append(ecu_name)
                services[found_service] = ecu_names

    print(f"Binary data: {data.hex(' ')}")
    for service, ecu_names in services.items():
        if isinstance(service, DiagService):
            print(
                f"Decoded by service '{service.short_name}' (decoding ECUs: {', '.join(ecu_names)})"
            )
        elif isinstance(service, SingleEcuJob):
            print(
                f"Decoded by single ecu job '{service.short_name}' (decoding ECUs: {', '.join(ecu_names)})"
            )
        else:
            print(f"Decoded by unknown diagnostic communication: '{service.short_name}' "
                  f"(decoding ECUs: {', '.join(ecu_names)})")

        if decode:
            if data is None:
                odxraise("Data is required for decoding")

            decoded = service.decode_message(data)
            print(f"Decoded data:")
            for param_name, param_value in decoded.param_dict.items():
                print(f"  {param_name}={get_display_value(param_value)}")


def add_subparser(subparsers: "argparse._SubParsersAction") -> None:
    parser = subparsers.add_parser(
        "decode",
        description="\n".join([
            "Decode request by hex-data",
            "",
            "Examples:",
            "  For displaying the service associated with the request 10 01 & decoding it:",
            "    odxtools decode ./path/to/database.pdx -d 10 01",
            "  For more information use:",
            "    odxtools decode -h",
        ]),
        help="Find & print services by hex-data, or name. Can also decode the request.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    _parser_utils.add_pdx_argument(parser)

    parser.add_argument(
        "-v",
        "--variants",
        nargs=1,
        metavar="VARIANT",
        required=False,
        help="Specifies which ecu variants should be included.",
        default="all",
    )

    parser.add_argument(
        "-d",
        "--data",
        nargs=1,
        default=None,
        metavar="DATA",
        required=True,
        help="Specify data of hex request.",
    )

    parser.add_argument(
        "-D",
        "--decode",
        action="store_true",
        required=False,
        help="Decode the specified hex request",
    )


def hex_to_binary(data_str: str) -> bytes:
    return bytes.fromhex(data_str)


def run(args: argparse.Namespace) -> None:
    odxdb = _parser_utils.load_file(args)
    variants = args.variants

    print_summary(
        odxdb,
        ecu_variants=None if variants == "all" else variants,
        data=bytes.fromhex("".join(args.data)),
        decode=args.decode,
    )
