import logging
import os
import re
import subprocess
from argparse import ArgumentParser

from github import Github


def parse_arguments():
    """ Parse command-line args """
    parser = ArgumentParser()

    parser.add_argument('-d',
                        '--directory',
                        dest='git_repo_dir',
                        required=True,
                        help='path the top-level directory of the git repo')

    parser.add_argument('-t',
                        '--token',
                        dest='token',
                        required=True,
                        help='The personal access token used to connect to the API')

    return parser.parse_args()


def _setup_logging():
    """ Setup basic logging """
    format_str = '%(asctime)s %(levelname)-8s %(message)s'
    formatter = logging.Formatter(fmt=format_str, datefmt='%Y-%m-%d %H:%M:%S')

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)
    logging.getLogger().addHandler(sh)


def get_pr_from_hash(commit_hash, github):
    """ Find the pull request corresponding to a given sha hash """
    matching_issues = list(github.search_issues("", sha=commit_hash))

    if len(matching_issues) > 1:
        raise Exception('Multiple issues found')
    elif len(matching_issues) == 0:
        logging.warning("No associated PR, likely a direct commit to master :(")

    return matching_issues[0] if matching_issues else None


def get_commit_hash():
    """ Get the current commit's sha hash """
    process = subprocess.Popen(['git', 'rev-parse', '--verify', 'HEAD'], stdout=subprocess.PIPE)

    return process.communicate()[0].strip()


def get_commit_message(commit_hash, github):
    commits = list(github.search_commits("", sha=commit_hash))

    if len(commits) != 1:
        raise Exception("More than one commit found for sha `{}`".format(commit_hash))

    return commits[0].commit.message


def get_current_tagged_version_parts():
    """ Get the current major, minor, and patch version parts """
    process = subprocess.Popen(['git', 'describe', '--tags', '--abbrev=0'], stdout=subprocess.PIPE)
    current_tag = process.communicate()[0].strip()

    major_version = re.search(r'\d+', current_tag, 0).group()
    _major_offset = current_tag.index(major_version) + len(major_version)
    minor_version = re.search(r'\d+', current_tag[_major_offset:]).group()
    _minor_offset = current_tag.index(minor_version, _major_offset) + len(minor_version)
    patch_version = int(re.search(r'\d+', current_tag[_minor_offset:]).group())

    return major_version, minor_version, patch_version


def add_new_tag(version, message):
    """ Create and push a new tag """
    subprocess.check_call(['git', 'tag', '-a', version, '-m', message])

    subprocess.check_call(['git', 'push', '--tags'])


def process(args):
    _setup_logging()

    # cd into the directory
    if not os.path.isdir(args.git_repo_dir):
        logging.error("`{}` is not a directory".format(args.git_repo_dir))

    os.chdir(args.git_repo_dir)

    # Make sure its a git repo
    try:
        with open(os.devnull, 'w') as FNULL:
            assert subprocess.check_call(['git', 'branch'], stdout=FNULL,
                                         stderr=subprocess.STDOUT) == 0
    except subprocess.CalledProcessError as e:
        logging.exception("`{}` is not a git repo".format(args.git_repo_dir))

    commit_hash = get_commit_hash()
    major_version, minor_version, patch_version = get_current_tagged_version_parts()

    # Log into GitHub API
    g = Github(args.token)

    pull_request_issue = get_pr_from_hash(commit_hash, g)

    if pull_request_issue is not None:
        labels = [x.name for x in pull_request_issue.labels]
        title = pull_request_issue.title

        # Figure out increment
        if 'major' in labels:
            new_version = 'v{}.{}.{}'.format(int(major_version) + 1, minor_version, patch_version)
        elif 'minor' in labels:
            new_version = 'v{}.{}.{}'.format(major_version, int(minor_version) + 1, patch_version)
        elif 'patch' in labels:
            new_version = 'v{}.{}.{}'.format(major_version, minor_version, int(patch_version) + 1)
        else:
            logging.warning('No label found, defaulting to patch increment')
            new_version = 'v{}.{}.{}'.format(major_version, minor_version, int(patch_version) + 1)
    else:
        title = get_commit_message(commit_hash, g)
        logging.warning('No PR found, defaulting to patch increment')
        new_version = 'v{}.{}.{}'.format(major_version, minor_version, int(patch_version) + 1)

    add_new_tag(new_version, '{}: auto-generated tag'.format(title))


if __name__ == '__main__':
    args = parse_arguments()

    process(args)
