# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

# Standard library imports
from ast import literal_eval
import os

# Third party imports
import yaml

# Local imports
from spyder.dependencies import DESCRIPTIONS, OPTIONAL

# Constants
HERE = os.path.abspath(os.path.dirname(__file__))
ROOT_PATH = os.path.dirname(os.path.dirname(HERE))
ENV_FPATH = os.path.join(ROOT_PATH, 'binder', 'environment.yml')
REQ_FPATH = os.path.join(ROOT_PATH, 'requirements', 'conda.txt')
REQ_TEST_FPATH = os.path.join(ROOT_PATH, 'requirements', 'tests.txt')
SETUP_FPATH = os.path.join(ROOT_PATH, 'setup.py')


def parse_requirements(fpath):
    """
    Parse a requirements file and return a dict of deps and versions.
    """
    with open(fpath, 'r') as fh:
        data = fh.read()

    lines = data.split('\n')
    lines = [line.strip() for line in lines if line and line[0] != '#']

    deps = {}
    for line in lines:
        parts = line.split(' ')
        if len(parts) > 1:
            ver = parts[-1]
            if ver[0] == '=':
                ver = '=' + ver

            deps[parts[0].lower()] = ver
        else:
            deps[parts[0].lower()] = None

    return deps


def parse_environment_yaml(fpath):
    """
    Parse an environment yaml file and return a dict of deps and versions.
    """
    with open(fpath, 'r') as fh:
        data = yaml.load(fh, Loader=yaml.FullLoader)

    deps = {}
    yaml_deps = data.get('dependencies')
    for dep in yaml_deps:
        if isinstance(dep, dict):
            continue
        elif dep == 'websockify':
            continue
        else:
            parts = dep.split(' ')
            if len(parts) > 1:
                ver = parts[-1]
                if ver[0] == '=':
                    ver = '=' + ver

                deps[parts[0]] = ver
            else:
                deps[parts[0]] = None

    return deps


def parse_spyder_dependencies():
    """
    Parse Spyder dependencies and return a dict of deps and versions.
    """
    deps = {}
    for dep in DESCRIPTIONS:
        if dep.get('kind', None) == OPTIONAL:
            continue

        ver = dep['required_version']
        if ver:
            if ';' in ver:
                ver = ver.replace(';', ',')
            elif ver[0] == '=':
                ver = '=' + ver

        deps[dep['package_name'].lower()] = ver

    return deps


def parse_setup_install_requires(fpath):
    """
    Parse Spyder setup.py and return a dict of deps and versions.
    """
    deps = {}
    with open(fpath, 'r') as fh:
        data = fh.read()

    lines = data.split('\n')
    start = None
    end = None
    for idx, line in enumerate(lines):
        if line.startswith('install_requires = '):
            start = idx + 1

        if start is not None and line.startswith(']'):
            end = idx
            break

    dep_list = literal_eval('[' + '\n'.join(lines[start:end + 1]))
    dep_list = [item for item in dep_list if item[0] != '#']
    for dep in dep_list:
        dep = dep.split(';')[0]
        name, ver = None, None

        for sep in ['>=', '==', '<=', '<', '>']:
            if sep in dep:
                idx = dep.index(sep)
                name = dep[:idx]
                ver = dep[idx:]
                break

        if name is not None:
            name = name.split('[')[0]
        else:
            name = dep.split('[')[0]

        # Transform pypi to conda name
        if name == 'pyqt5':
            name = 'pyqt'

        deps[name] = ver

    return deps


def parse_setup_extra_requires(fpath):
    """
    Parse Spyder setup.py and return a dict of deps and versions.
    """
    deps = {}
    with open(fpath, 'r') as fh:
        data = fh.read()

    lines = data.split('\n')
    start = None
    end = None
    for idx, line in enumerate(lines):
        if line.startswith('extras_require = '):
            start = idx + 1

        if start is not None and line.startswith('}'):
            end = idx
            break

    dep_dict = literal_eval('{' + '\n'.join(lines[start:end + 1]))
    dep_list = dep_dict.get('test')
    dep_list = [item for item in dep_list if item[0] != '#']
    for dep in dep_list:
        dep = dep.split(';')[0]
        name, ver = None, None

        for sep in ['>=', '==', '<=', '<', '>']:
            if sep in dep:
                idx = dep.index(sep)
                name = dep[:idx]
                ver = dep[idx:]
                break

        if name is not None:
            name = name.split('[')[0]
        else:
            name = dep.split('[')[0]

        # Transform pypi to conda name
        if name == 'pyqt5':
            name = 'pyqt'

        deps[name] = ver
    print(deps)
    return deps


def test_dependencies_for_binder_in_sync():
    """
    Binder environment yaml should be the sum of conda.txt and tests.txt
    requirements.
    """
    spyder_env = parse_environment_yaml(ENV_FPATH)
    spyder_reqs = parse_requirements(REQ_FPATH)
    test_reqs = parse_requirements(REQ_TEST_FPATH)

    # xvfb is only available on linux (which binder runs on)
    if 'pytest-xvfb' in spyder_env:
        spyder_env.pop('pytest-xvfb')

    # Check that the requirement files match the environment yaml file
    full_reqs = {}
    full_reqs.update(test_reqs)
    full_reqs.update(spyder_reqs)

    assert spyder_env == full_reqs


def test_dependencies_for_spyder_dialog_in_sync():
    """
    Spyder dependencies dialog should share deps with conda.txt.
    """
    spyder_deps = parse_spyder_dependencies()
    spyder_reqs = parse_requirements(REQ_FPATH)

    if 'pyqt' in spyder_reqs:
        spyder_reqs.pop('pyqt')
    if 'pyqtwebengine' in spyder_reqs:
        spyder_reqs.pop('pyqtwebengine')

    assert spyder_deps == spyder_reqs


def test_dependencies_for_spyder_setup_install_requires_in_sync():
    """
    Spyder setup.py should share deps with conda.txt.
    """
    spyder_setup = parse_setup_install_requires(SETUP_FPATH)
    spyder_reqs = parse_requirements(REQ_FPATH)

    assert spyder_setup == spyder_reqs


def test_dependencies_for_spyder_setup_extras_requires_in_sync():
    """
    Spyder setup.py extra_requires should share deps with tests.txt.
    """
    spyder_extras_setup = parse_setup_extra_requires(SETUP_FPATH)
    spyder_test_reqs = parse_requirements(REQ_TEST_FPATH)

    assert spyder_extras_setup == spyder_test_reqs
