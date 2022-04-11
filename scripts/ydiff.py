#!/usr/bin/env python3

import argparse
import pathlib

import yaml


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('a', type=pathlib.Path)
    parser.add_argument('b', type=pathlib.Path)

    args = parser.parse_args()

    a = yaml.safe_load(args.a)
    b = yaml.safe_load(args.b)

    print(a == b)


if __name__ == '__main__':
    main()

