import logging
import re
from argparse import ArgumentParser

from github import Github


def parse_arguments():
    """ Parse command-line args """
    parser = ArgumentParser()

    parser.add_argument('-n',
                        '--name',
                        dest='git_repo_name',
                        required=True,
                        help='the full-name of the git repo, ex: "picwell/auto_pr_versioning"')

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


def get_current_commit_hash(git_branch):
    """ Get the current commit's sha hash for a given branch"""
    return git_branch.commit.sha


def get_commit_message(commit_hash, github):
    """ Get a given commit's message """
    commits = list(github.search_commits("", sha=commit_hash))

    if len(commits) != 1:
        raise Exception("More than one commit found for sha `{}`".format(commit_hash))

    return commits[0].commit.message


def get_current_tagged_version_parts(the_repo):
    """ Get the current major, minor, and patch version parts """
    all_tags = list(the_repo.get_tags())
    
    if len(all_tags) == 0:
        return None, None, None

    current_tag = all_tags[0].name

    major_version = re.search(r'\d+', current_tag, 0).group()
    _major_offset = current_tag.index(major_version) + len(major_version)
    minor_version = re.search(r'\d+', current_tag[_major_offset:]).group()
    _minor_offset = current_tag.index(minor_version, _major_offset) + len(minor_version)
    patch_version = re.search(r'\d+', current_tag[_minor_offset:]).group()

    return major_version, minor_version, patch_version


def add_new_tag(the_repo, commit_hash, version, message):
    """ Create and push a new tag """
    the_repo.create_git_tag_and_release(tag=version, tag_message=message, release_name=version,
                                        release_message=message,
                                        object=commit_hash, type='commit')


def process(args):
    _setup_logging()

    logging.info("Incrementing the version for `{}`".format(args.git_repo_name))

    # Log into GitHub API
    g = Github(args.token)

    the_repo = g.get_repo(args.git_repo_name)

    commit_hash = get_current_commit_hash(the_repo.get_branch('master'))
    major_version, minor_version, patch_version = get_current_tagged_version_parts(the_repo)

    pull_request_issue = get_pr_from_hash(commit_hash, g)

    # Get the title
    title = pull_request_issue.title if pull_request_issue is not None else \
        get_commit_message(commit_hash, g)

    if major_version is None:
        new_version = 'v0.0.0'
    elif pull_request_issue is not None:
        labels = [x.name for x in pull_request_issue.labels]

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
        logging.warning('Defaulting to patch increment')
        new_version = 'v{}.{}.{}'.format(major_version, minor_version, int(patch_version) + 1)

    add_new_tag(the_repo, commit_hash, new_version, '{}: auto-generated tag'.format(title))


if __name__ == '__main__':
    args = parse_arguments()

    process(args)
