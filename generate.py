import csv
import logging
import pathlib
import subprocess
import os
import argparse

from pathlib import Path


def build_args():
    """
    Builds the argument parser for the command line interface (CLI).
    """
    parser = argparse.ArgumentParser()
    parser.set_defaults(slice_types=['usages', 'reachables'])
    parser.add_argument(
        '--repo-csv',
        type=Path,
        default='sources.csv',
        help='Path to sources.csv',
        dest='repo_csv'
    )
    parser.add_argument(
        '--clone-dir',
        type=Path,
        default=Path('/home/runner/work/src_repos'),
        help='Path to src_repos',
        dest='clone_dir'
    )
    parser.add_argument(
        '-o',
        '--output-dir',
        type=Path,
        default='/home/runner/work/atom-samples/atom-samples',
        help='Path to output',
        dest='output_dir',
    )
    filter_parser_group = parser.add_mutually_exclusive_group()
    filter_parser_group.set_defaults(langs=['java', 'python', 'javascript'])
    filter_parser_group.add_argument(
        '-i',
        '--include-langs',
        choices=['java', 'python', 'javascript'],
        default=['java', 'python', 'javascript'],
        help='Languages to generate samples for',
        dest='langs',
        nargs='*',
    )
    filter_parser_group.add_argument(
        '-e',
        '--exclude-langs',
        choices=['java', 'python', 'javascript'],
        help='Languages to exclude from samples',
        dest='elangs',
        nargs='*'
    )
    filter_parser_group.add_argument(
        '-p',
        '--projects',
        help='Filter to these sample projects',
        dest='projects',
        nargs='*'
    )
    parser.add_argument(
        '-s',
        '--slice-type',
        choices=['usages', 'reachables'],
        help='Slice type to generate',
        dest='slice_types',
        const=['usages', 'reachables'],
        nargs='?'
    )
    parser.add_argument(
        '--skip-clone',
        action='store_false',
        dest='skip_clone',
        default=True,
        help='Skip cloning the repositories (must be used with the --repo-dir argument)'
    )
    parser.add_argument(
        '--debug-cmds',
        action='store_true',
        dest='debug_cmds',
        help='For use in workflow'
    )
    parser.add_argument(
        '--skip-build',
        action='store_true',
        dest='skip_build',
        default=False,
        help='Skip building the samples and just run atom. Should be used with --skip-clone'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        dest='cleanup',
        default=False,
        help='Remove slices that are <= 1kb or > 100MB.'
    )
    return parser.parse_args()


def generate(args):
    """
    Generate commands for executing a series of tasks on a repository.

    Args:
        args (argparse.Namespace): The parsed arguments

    Returns:
        None
    """
    if args.projects:
        args.langs = ['java', 'python', 'javascript']
    langs = set(args.langs)
    if args.output_dir == '.':
        args.output_dir = pathlib.Path.cwd()
    if args.elangs:
        langs = langs - set(args.elangs)
    if not args.debug_cmds:
        check_dirs(args.skip_clone, args.clone_dir, args.output_dir)

    repo_data = read_csv(args.repo_csv, langs, args.projects, args.clone_dir)
    processed_repos = process_repo_data(repo_data, args.clone_dir, langs)

    if not args.skip_build:
        run_pre_builds(repo_data, args.output_dir, args.debug_cmds)

    commands = ''.join(
        exec_on_repo(
            args.skip_clone,
            args.output_dir,
            args.skip_build,
            args.slice_types
            if isinstance(args.slice_types, list)
            else [args.slice_types],
            repo,
        )
        for repo in processed_repos
    )
    sh_path = Path.joinpath(args.output_dir, 'atom_commands.sh')
    write_script_file(sh_path, commands, args.debug_cmds)


def add_repo_dirs(clone_dir, repo_data):
    """
    Adds a key for the repository directory to the repository data.

    Args:
        clone_dir (pathlib.Path): The directory to store sample repositories.
        repo_data (list[dict]): Contains the sample repository data

    Returns:
        list[dict]: The updated repository data with the 'repo_dir' key
    """
    new_data = []
    for r in repo_data:
        r['repo_dir'] = Path.joinpath(clone_dir, r['language'], r['project'])
        new_data.append(r)
    return new_data


def exec_on_repo(clone, output_dir, skip_build, slice_types, repo):
    """
    Determines a sequence of commands on a repository.

    Args:
        clone (bool): Indicates whether to clone the repository.
        output_dir (pathlib.Path): The directory to output the slices.
        skip_build (bool): Indicates whether to skip the build phase.
        slice_types (list): The types of slices to be generated.
        repo (dict): The repository information.


    Returns:
        str: The sequence of commands to be executed.
    """
    project = repo['project']
    lang = repo['language']
    loc = Path.cwd()
    repo_dir = repo['repo_dir']
    gen_api = repo['gen_api']
    commands = ''

    if clone:
        commands += f'\n{clone_repo(repo["link"], repo_dir)}'
    commands += f'\n{subprocess.list2cmdline(["cd", repo_dir])}'
    if not skip_build and len(repo['pre_build_cmd']) > 0:
        cmds = repo['pre_build_cmd'].split(';')
        cmds = [cmd.lstrip().rstrip() for cmd in cmds]
        for cmd in cmds:
            new_cmd = list(cmd.split(' '))
            commands += f"\n{subprocess.list2cmdline(new_cmd)}"
    if not skip_build and len(repo['build_cmd']) > 0:
        cmds = repo['build_cmd'].split(';')
        cmds = [cmd.lstrip().rstrip() for cmd in cmds]
        for cmd in cmds:
            new_cmd = list(cmd.split(' '))
            commands += f"\n{subprocess.list2cmdline(new_cmd)}"
    if repo.get('cdxgen_cmd'):
        commands += f"\n{repo['cdxgen_cmd']}"
    commands += f'\n{subprocess.list2cmdline(["cd", loc])}'
    commands += f'\n{subprocess.list2cmdline(["sdk", "use", "java", "21.0.1-zulu"])}'
    for stype in slice_types:
        slice_file = Path.joinpath(output_dir, lang, f'{project}-{stype}.json')
        atom_file = Path.joinpath(repo_dir, f'{project}.atom')
        if stype == 'usages' and gen_api:
            commands += generate_openapi(project, output_dir, lang, slice_file, atom_file, repo_dir)
            continue
        cmd = ['atom', stype,'-l', lang, '-o', atom_file, '-s', slice_file, repo_dir]
        commands += f'\n{subprocess.list2cmdline(cmd)}'
    commands += '\n\n'
    return commands


def generate_openapi(project, output_dir, lang, slice_file, atom_file, repo_dir):
    cmds = ''
    cmd = ['atom', 'usages', '--extract-endpoints', '-l', lang, '-o', atom_file, '-s', slice_file,
           repo_dir]
    cmds += f'\n{subprocess.list2cmdline(cmd)}'
    openapi_file = Path.joinpath(repo_dir, 'openapi.generated.json')
    cmd = ['mv', openapi_file, Path.joinpath(output_dir, lang, f'{project}_openapi.json')]
    cmds += f'\n{subprocess.list2cmdline(cmd)}'
    return cmds


def read_csv(csv_file, langs, projects, clone_dir):
    """
    Reads a CSV file and filters the data based on a list of languages.

    Parameters:
        csv_file (pathlib.Path): The path to the CSV file.
        langs (set): A set of programming languages.
        projects (list): A list of projects names to filter on.
        clone_dir (pathlib.Path): The directory storing the cloned repositories.

    Returns:
        list: A filtered list of repository data.
    """
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        repo_data = list(reader)
    if projects:
        repo_data = [repo for repo in repo_data if repo['project'] in projects]
    elif 'java' not in langs or 'javascript' not in langs or 'python' not in langs:
        repo_data = [repo for repo in repo_data if repo['language'] in langs]
    return add_repo_dirs(clone_dir, repo_data)


def clone_repo(url, repo_dir):
    """
    Clones a repository from a given URL to a specified directory.

    Args:
        url (str): The URL of the repository to clone.
        repo_dir (pathlib.Path): The directory to store the cloned repository.

    Returns:
        str: The command to clone the repository.
    """
    if Path.exists(repo_dir):
        logging.info('%s already exists, skipping clone.', repo_dir)
        return ''

    clone_cmd = ['git', 'clone', url, repo_dir]
    return subprocess.list2cmdline(clone_cmd)


def run_pre_builds(repo_data, output_dir, debug_cmds):
    """
    Generates a list of commands to be executed before the build process.

    Args:
        repo_data (list[dict]): Contains the sample repository data
        output_dir (pathlib.Path): Root directory for slices export
        debug_cmds (bool): Flag indicating whether to include debug output

    Returns:
        None
    """
    cmds = []
    [
        cmds.extend(row['pre_build_cmd'].split(';'))
        for row in repo_data
        if row['pre_build_cmd']
    ]
    cmds = [cmd.lstrip().rstrip() for cmd in cmds]
    cmds = set(cmds)

    commands = [c.replace('use', 'install') for c in cmds]
    commands.append('sdk install java 21.0.1-zulu')
    commands = '\n'.join(commands)
    sh_path = Path.joinpath(output_dir, 'sdkman_installs.sh')
    write_script_file(sh_path, commands, debug_cmds)


def write_script_file(file_path, commands, debug_cmds):
    """
    Write a script to execute a series of commands in a file.

    Args:
        file_path (pathlib.Path): The path to write the file to
        commands (str): The commands to be written to the file
        debug_cmds (bool): Flag indicating whether to include debug output

    Returns:
        None
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        sdkman_path = Path.joinpath(Path('$SDKMAN_DIR'), 'bin', 'sdkman-init.sh')
        f.write(f'#!/usr/bin/bash\nsource {sdkman_path}\n\n')
        f.write(commands)
    if debug_cmds:
        print(commands)


def check_dirs(clone, clone_dir, output_dir):
    """
    Create directories if they don't exist.

    Args:
        clone (bool): Whether to create the clone directory or not.
        clone_dir (pathlib.Path): The path to the clone directory.
        output_dir (pathlib.Path): The path to the output directory.

    Returns:
        None
    """
    if clone and not Path.exists(clone_dir):
        Path.mkdir(clone_dir)
    if not Path.exists(output_dir):
        Path.mkdir(output_dir)


def cleanup(output_dir):
    """
    Remove slice files 1kb or less, or 100MB or more (due to GitHub limits).

    Args:
        output_dir (pathlib.Path): The path to the output directory.

    Returns:
        None
    """
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file.endswith('.json'):
                path = os.path.join(root, file)
                size = os.path.getsize(path)
                if size <= 1024:
                    os.remove(path)
                elif size > 100000000:
                    os.remove(path)
                    logging.warning('File %s exceeds the GitHub size limit of 100MB.', path)


def run_cdxgen(repos):
    """
    Generates cdxgen commands.

    Args:
        repos (list[dict]): Repository data

    Returns:
        str: The repository data with cdxgen commands
    """
    new_repos = []
    for r in repos:
        if r['language'] in ['java', 'javascript']:
            cdxgen_cmd = [
                'cdxgen',
                '-t',
                r['language'],
                '--deep',
                '-o',
                Path.joinpath(r['repo_dir'], 'bom.json'),
                r['repo_dir']
            ]
            r['cdxgen_cmd'] = subprocess.list2cmdline(cdxgen_cmd)
        else:
            r['cdxgen_cmd'] = None
        new_repos.append(r)

    return new_repos


def process_repo_data(repo_data, clone_dir, langs):
    """
    Process the repo data, adding the 'repo_dir' key and filtering as required.

    Args:
        repo_data (list[dict]): Repository data
        clone_dir (pathlib.Path): Destination for cloned repo.
        langs (set): Filter data to these languages

    Returns:
        list[dict]: The processed repository data
    """
    new_data = []
    for r in repo_data:
        r['repo_dir'] = Path.joinpath(clone_dir, r['language'], r['project'])
        new_data.append(r)
    if 'java' in langs or 'javascript' in langs:
        new_data = run_cdxgen(new_data)
    return new_data


def main():
    """
    Runs the main function of the program.
    """
    args = build_args()
    if args.cleanup:
        cleanup(args.output_dir)
    else:
        generate(args)


if __name__ == '__main__':
    main()
