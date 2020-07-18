#!/usr/bin/env python3
#                                                  -*- coding: utf-8 -*-
# A library to display spinorama charts
#
# Copyright (C) 2020 Pierre Aubert pierreaubert(at)yahoo(dot)fr
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
"""Usage:
generate_graphs.py [-h|--help] [-v] [--width=<width>] [--height=<height>]\
  [--force] [--type=<ext>] [--log-level=<level>]\
  [--origin=<origin>]  [--speaker=<speaker>] [--mversion=<mversion>]\
  [--only-compare=<compare>]

Options:
  -h|--help         display usage()
  --width=<width>   width size in pixel
  --height=<height> height size in pixel
  --force           force regeneration of all graphs, by default only generate new ones
  --type=<ext>      choose one of: json, html, png, svg
  --log-level=<level> default is WARNING, options are DEBUG INFO ERROR.
  --origin=<origin> restrict to a specific origin, usefull for debugging
  --speaker=<speaker> restrict to a specific speaker, usefull for debugging
  --mversion=<mversion> restrict to a specific mversion (for a given origin you can have multiple measurements)
  --only-compare=<compare> if true then skip graphs generation and only dump compare data
"""
import json
import logging
import sys
import pandas as pd
import flammkuchen as fl
# import ray
import datas.metadata as metadata
from docopt import docopt
from src.spinorama.load_parse import parse_all_speakers, parse_graphs_speaker, parse_eq_speaker
from src.spinorama.speaker_print import print_graphs, print_compare


# ray.init(num_cpus=12)


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'to_json'):
            return obj.to_json(orient='records')
        return json.JSONEncoder.default(self, obj)


def dump_to_json(df, path):
    with open(path, 'w') as fp:
        json.dump(df, fp, cls=JSONEncoder)


def generate_graphs(df, width, height, force, ptype):
    updated = 0
    for speaker_name, speaker_data in df.items():
        for origin, dataframe in speaker_data.items():
            for key in df[speaker_name][origin].keys():
                logging.debug('{:30s} {:20s} {:20s}'.format(speaker_name, origin, key))
                dfs_ref = df[speaker_name][origin][key]
                key_eq = '{0}_eq'.format(key)
                dfs_eq = df[speaker_name][origin].get(key_eq, None)
                updated = print_graphs(dfs_ref,
                                       dfs_eq,
                                       speaker_name, origin, metadata.origins_info, key,
                                       width, height, force, ptype)
    print('{:30s} {:2d}'.format(speaker_name, updated))


def generate_compare(df, width, height, force, ptype):
    print_compare(df, force, ptype)


if __name__ == '__main__':
    args = docopt(__doc__,
                  version='generate_graphs.py version 1.21',
                  options_first=True)

    width = 1200
    height = 600
    force = args['--force']
    ptype = None

    if args['--width'] is not None:
        width = int(args['--width'])

    if args['--height'] is not None:
        height = int(args['--height'])

    if args['--type'] is not None:
        ptype = args['--type']
        if ptype not in ('png', 'html', 'svg', 'json'):
            print('type %s is not recognize!'.format(ptype))
            exit(1)

    level = None
    if args['--log-level'] is not None:
        check_level = args['--log-level']
        if check_level in ['INFO', 'DEBUG', 'WARNING', 'ERROR']:
            level = check_level

    if level is not None:
        logging.basicConfig(
            format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d:%H:%M:%S',
            level=level)
    else:
        logging.basicConfig(
            format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d:%H:%M:%S')

    df = None
    if args['--speaker'] is not None and args['--origin'] is not None:
        speaker = args['--speaker']
        brand = metadata.speakers_info[speaker]['brand']
        origin = args['--origin']
        mversion = metadata.speakers_info[speaker]['default_measurement']
        if args['--mversion'] is not None:
            mversion = args['--mversion']
        mformat = metadata.speakers_info[speaker]['measurements'][mversion].get('format')

        df = {}
        df[speaker] = {}
        df[speaker][origin] = {}

        logging.info('Parsing: {} {} {} {}'.format(brand, speaker, mformat, mversion))
        df_ref = parse_graphs_speaker('./datas', brand, speaker, mformat, mversion)
        if df_ref is not None:
            df[speaker][origin][mversion] = df_ref
            df_eq = parse_eq_speaker(speaker, df_ref)
            if df_eq is not None:
                logging.info('Parsing: {} {} {} {} with eq'.format(brand, speaker, mformat, mversion))
                speaker_ns = speaker.replace(' ', '_')
                df[speaker_ns][origin]['{0}_eq'.format(mversion)] = df_eq
        else:
            logging.info('{0} {1} {2} {3} returned None'.format(brand, speaker, mformat, mversion))
        print('Speaker                         #updated')
        generate_graphs(df, width, height, force, ptype=ptype)
    else:
        origin = None
        if args['--origin'] is not None:
            origin = args['--origin']

        df = parse_all_speakers(metadata.speakers_info, origin)
        # dump_to_json(df, 'cache.parse_all_speakers.json')
        #with open('cache.parse_all_speakers.pkl', 'w') as fp:
        #    pickle.dump(df, fp)
        fl.save('cache.parse_all_speakers.h5', df)
        if args['--only-compare'] is not True:
            generate_graphs(df, width, height, force, ptype=ptype)

    if args['--speaker'] is None and args['--origin'] is None and args['--mversion'] is None:
        generate_compare(df, width, height, force, ptype=ptype)

    sys.exit(0)
        
