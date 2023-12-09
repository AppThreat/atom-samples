import csv
import logging
import subprocess
import os
import argparse

from pathlib import Path


def build_args():
    """
    Builds and returns the argument parser for the program.
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
        default='/home/runner/work/src_repos',
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
    lang_parser_group = parser.add_mutually_exclusive_group()
    lang_parser_group.set_defaults(langs=['java', 'python', 'javascript'])
    lang_parser_group.add_argument(
        '-i',
        '--include-langs',
        choices=['java', 'python', 'javascript'],
        default=['java', 'python', 'javascript'],
        help='Languages to generate samples for',
        dest='langs',
        nargs='*',
    )
    lang_parser_group.add_argument(
        '-e',
        '--exclude-langs',
        choices=['java', 'python', 'javascript'],
        dest='elangs',
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
        dest='clone',
        default=True,
        help='Skip cloning the repositories (must be used with the --repo-dir '
             'argument)'
    )
    parser.add_argument(
        '--debug-cmds',
        action='store_true',
        dest='debug_cmds',
    )
    parser.add_argument(
        '--skip-build',
        action='store_true',
        dest='skip_build',
        default=False,
        help='Skip building the samples and just run atom. Should be used '
             'with --skip-clone'
    )
    return parser.parse_args()


def generate(repo_data, clone_dir, output_dir, slice_types, clone, debug_cmds,
             skip_build):
    """
    Iterates over sample repositories and gets commands for each.

    Args:
        repo_data (list): Repository data.
        clone_dir (pathlib.Path): The directory to clone the repositories.
        output_dir (pathlib.Path): The directory to output the slices.
        slice_types (list): Slice types to generate.
        clone (bool): Indicates whether to clone the repositories or not.
        debug_cmds (bool): Indicates whether to include print commands.
        skip_build (bool): Indicates whether to skip the pre-build step or not.

    Returns:
        None
    """
    if not skip_build:
        run_pre_builds(repo_data, output_dir, debug_cmds)

    commands = '\nsdk use java 20.0.2-tem'

    for repo in repo_data:
        commands += generate_slices(
            clone, clone_dir, output_dir, repo, skip_build, slice_types)
        commands += '\n\n'

    sh_path = Path.joinpath(output_dir, 'atom_commands.sh')
    use_script(sh_path, commands, debug_cmds)


def generate_slices(clone, clone_dir, output_dir, repo, skip_build,
                    slice_types):
    """
    Generates slices for a given clone of a repository.

    Args:
        clone (bool): Indicates whether to clone the repository.
        clone_dir (pathlib.Path): The directory where the clone is stored.
        output_dir (pathlib.Path): The directory for the generated slices.
        repo (dict): A dictionary containing information about the repository.
        skip_build (bool): Indicates whether to skip the build step.
        slice_types (list): A list of slice types to generate.

    Returns:
        str: The commands to generate the slices for a single repository.
    """
    project = repo['project']
    lang = repo['language']
    loc = os.getcwd()
    repo_dir = Path.joinpath(clone_dir, lang, project)
    commands = ''
    if clone:
        clone_repo(repo['link'], clone_dir, repo_dir)
    commands += f"\n{subprocess.list2cmdline(['cd', repo_dir])}"
    if not skip_build and len(repo['pre_build_cmd']) > 0:
        cmds = repo['pre_build_cmd'].split(';')
        cmds = [cmd.strip() for cmd in cmds]
        for cmd in cmds:
            new_cmd = list(cmd.split(' '))
            commands += f"\n{subprocess.list2cmdline(new_cmd)}"
    if not skip_build and len(repo['build_cmd']) > 0:
        cmds = repo['build_cmd'].split(';')
        cmds = [cmd.lstrip().rstrip() for cmd in cmds]
        for cmd in cmds:
            new_cmd = list(cmd.split(' '))
            commands += f"\n{subprocess.list2cmdline(new_cmd)}"
    commands += f"\n{subprocess.list2cmdline(['cd', loc])}"
    if lang == 'java':
        commands += '\nsdk use java 20.0.2-tem'
    for stype in slice_types:
        slice_file = Path.joinpath(
            output_dir, lang, f"{project}-{stype}.json")
        atom_file = Path.joinpath(repo_dir, f"{project}.atom")
        cmd = ['atom', stype, '-l', lang, '-o', atom_file, '-s', slice_file,
               repo_dir]
        commands += f"\n{subprocess.list2cmdline(cmd)}"
    return commands


def read_csv(csv_file, langs):
    """
    Read a CSV file and filters the data based on the provided languages.

    Parameters:
        csv_file (pathlib.Path): The path to the CSV file.
        langs (set): A list of languages to filter the data by.

    Returns:
        list: Repository list filtered by the provided languages.
    """
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        repo_data = list(reader)
    if len(langs) != 3:
        return [repo for repo in repo_data if repo['language'] in langs]
    return repo_data


def clone_repo(url, clone_dir, repo_dir):
    """
    Clones a repository from a given URL to a specified directory.

    Parameters:
        url (str): The URL of the repository to clone.
        clone_dir (pathlib.Path): Parent directory for all cloned repositories.
        repo_dir (pathlib.Path): Subdirectory of clone_dir for a single repo.

    Returns:
        None
    """
    os.chdir(clone_dir)
    if Path.exists(repo_dir):
        logging.warning(f'{repo_dir} already exists, skipping clone.')
        return
    clone_cmd = ['git', 'clone', url, repo_dir]
    subprocess.run(clone_cmd, shell=True, encoding='utf-8', check=False)


def run_pre_builds(repo_data, output_dir, debug_cmds):
    """
    Generate commands for pre-build steps.

    Parameters:
    - repo_data: Contains repository data.
    - output_dir (pathlib.Path): The output directory path.
    - debug_cmds: If True, print the commands to the console.

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
    commands = '\n'.join(commands)
    sh_path = Path.joinpath(output_dir, 'sdkman_installs.sh')
    use_script(sh_path, commands, debug_cmds)


def use_script(file_path, commands, debug_cmds):
    """
    Write the given commands to a file specified by `file_path`.

    Args:
        file_path (pathlib.Path): File where the commands will be written.
        commands (str): The commands to be written to the file.
        debug_cmds (bool): If True, print the commands to the console.
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        sdkman_path = os.path.join('$SDKMAN_DIR', 'bin', 'sdkman-init.sh')
        f.write(f'#!/usr/bin/bash\nsource {sdkman_path}\n\n')
        f.write('sdk use java 20.0.2-tem\n')
        f.write(commands)
    if debug_cmds:
        logging.info(commands)


def check_dirs(clone_dir, output_dir):
    """
    Create directories if they don't exist.

    Args:
        clone_dir (pathlib.Path): Path to the clone directory.
        output_dir (pathlib.Path): Path to the output directory.
    """
    if not Path.exists(clone_dir):
        Path.mkdir(clone_dir)
    if not Path.exists(output_dir):
        Path.mkdir(output_dir)


def main():
    """
    Executes the main logic of the program.

    This function performs the following steps:
    1. Builds the command line arguments.
    2. Sets up the set of programming languages.
    3. Sets the output directory if it is the current directory.
    4. Filters out excluded programming languages.
    5. Checks and creates the necessary directories.
    6. Reads the repository data from a CSV file.
    7. Generates atom slices based on the repository data.

    """
    args = build_args()
    if args.output_dir == '.':
        args.output_dir = Path.cwd()
    langs = set(args.langs)
    if args.elangs:
        langs = langs - set(args.elangs)
    if args.clone:
        check_dirs(args.clone_dir, args.output_dir)
    repo_data = read_csv(args.repo_csv, langs)
    generate(
        repo_data,
        args.clone_dir,
        args.output_dir,
        args.slice_types,
        args.clone,
        args.debug_cmds,
        args.skip_build
    )


if __name__ == '__main__':
    main()
