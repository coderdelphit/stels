#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# A library to display spinorama charts
#
# Copyright (C) 2020-2023 Pierre Aubert pierre(at)spinorama(dot)org
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

"""
usage: check_eqs.py [--help] [--version] [--dev] [--force]\
 [--log-level=<level>]

Options:
  --help            display usage()
  --version         script version number
  --force           regenerate pictures even if they already exist.
  --log-level=<level> default is WARNING, options are DEBUG INFO ERROR.
"""
import json
import os
import sys
import glob
import math

from docopt import docopt
import numpy as np

from generate_common import get_custom_logger, args2level
from spinorama.constant_paths import CPATH_METADATA_JSON, CPATH_DATAS_EQ
from spinorama.load_rew_eq import parse_eq_iir_rews
from spinorama.filter_peq import peq_spl


VERSION = 0.1
SCRIPT_NAME = "recompute_eqs.sh"


def check_eq(freq, peq, name):
    status = True
    spl = peq_spl(freq, peq)
    max_spl = np.max(spl)
    min_spl = np.min(spl)
    if max_spl > 15:
        print(f"{name} max spl {max_spl} above treshold")
        status = False
    if min_spl < -15:
        print(f"{name} min spl {min_spl} below treshold")
        status = False
    return status


def check_eqs(data, force):
    brand = data["brand"]
    model = data["model"]
    #
    freq = np.logspace(math.log10(2) + 1, math.log10(2) + 4, 200)
    eqs = glob.glob("{}/{} {}/*.txt".format(CPATH_DATAS_EQ, brand, model))
    peqs = [parse_eq_iir_rews(eq, 48000) for eq in eqs if os.path.basename(eq) != "iir.txt"]
    names = [os.path.basename(eq) for eq in eqs if os.path.basename(eq) != "iir.txt"]

    tobechecked = []
    for peq, name in zip(peqs, names, strict=True):
        if name in ("iir-autoeq.txt", "iir-autoeq-lw.txt", "iir-autoeq_score.txt"):
            eq_name = f"{brand} {model} {name}"
            status = check_eq(freq, peq, eq_name)
            if not status:
                tobechecked.append(f"{brand} {model}")
    return tobechecked


def createscript(speakers):
    lines = ["#!/bin/bash\n\n"]
    lines.append("# generated by check_eqs.py\n\n")
    lines.append("for SPEAKER in '{}'; do".format("' '".join(list(speakers))))
    lines.append('  rm -f "docs/speakers/$SPEAKER"/*/filters_*')
    lines.append('  rm -rf "docs/speakers/$SPEAKER"/*/*_eq')
    lines.append('  rm -f "datas/eq/$SPEAKER/iir-autoeq.txt"')
    lines.append(
        '  ./generate_peqs.py --verbose --force --optimisation=global --max-iter=5000 --speaker="$SPEAKER" --max-peq=7 --max-Q=3 --max-dB=3 --fitness=Flat'
    )
    lines.append(
        '  mv "./datas/eq/$SPEAKER/iir-autoeq.txt" "./datas/eq/$SPEAKER/iir-autoeq-lw.txt"'
    )
    lines.append('  rm -f "datas/eq/$SPEAKER/iir-autoeq.txt"')
    lines.append('  rm -f "docs/speakers/$SPEAKER"/*/filters_*')
    lines.append(
        '  ./generate_peqs.py --verbose --force --optimisation=global --max-iter=5000 --speaker="$SPEAKER" --max-peq=7 --max-Q=3 --max-dB=3 --fitness=Score'
    )
    lines.append(
        '  mv "./datas/eq/$SPEAKER/iir-autoeq.txt" "./datas/eq/$SPEAKER/iir-autoeq-score.txt"'
    )
    lines.append('  ./generate_graphs.py --speaker="$SPEAKER" --update-cache')
    lines.append("done")

    lines = ["{}\n".format(l) for l in lines]

    with open(SCRIPT_NAME, "w") as fd:
        for l in lines:
            fd.write(l)

    os.chmod(SCRIPT_NAME, 0o700)


def main(force):
    # load all metadata from generated json file
    json_filename = CPATH_METADATA_JSON
    if not os.path.exists(json_filename):
        logger.error("Cannot find %s", json_filename)
        sys.exit(1)

    jsmeta = None
    with open(json_filename, "r") as f:
        jsmeta = json.load(f)

    logger.info("Data %s loaded (%d speakers!", json_filename, len(jsmeta))

    tobechecked = set()
    for speaker_data in jsmeta.values():
        checked = check_eqs(speaker_data, force)
        tobechecked.update(checked)

    createscript(tobechecked)

    return 0


if __name__ == "__main__":
    args = docopt(
        __doc__,
        version=f"generate_radar.py version {VERSION:1.1f}",
        options_first=True,
    )

    logger = get_custom_logger(level=args2level(args), duplicate=True)

    FORCE = args["--force"]

    sys.exit(main(FORCE))
