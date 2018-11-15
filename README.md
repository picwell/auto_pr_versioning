# auto_pr_versioning
This is a tool for automatically versioning GitHub repositories using only
pull requests and their labels as the system.

## How will this work
The current idea is to use something akin to a
[CodePipeline](https://aws.amazon.com/codepipeline/) to trigger
this on master branch updates.

We already (hopefully) only merge into the **master** branch using pull
requests since we care about code reviews.
[Labels](https://help.github.com/articles/creating-a-label/) can
be assigned to PRs to help organize them, and that provides a means for 
[semantic version](https://semver.org) control.

The goal, once setup, is that the entire versioning flow for a repo consists
solely of putting a label on the PR going into master. This will ensure a
consistent versioning schema and remove the need to remember and update your
version.

## What's needed to set this up
I'll write this assuming we use CodePipeling, but really anything that can
act as a post-hook for master changes works just as well.

1. Create 3 labels in your GitHub repo: "major", "minor", and "patch".
2. Setup a CodePipeline to trigger on changes to the **master** branch of
your repo.
3. Configure the pipeline to clone your repo, and pass that directory to 
this tool as an argument.
4. Change your `setup.py` to calculate the version from git using
something akin to
```
process = subprocess.Popen(['git', 'describe', '--tags', '--abbrev=0'], stdout=subprocess.PIPE)
_VERSION = process.communicate()[0]
_VERSION = _VERSION.strip() if _VERSION else 'v0.0.0'
```
instead of hard coding it

That's really it. Steps 2 and 3 will only need to be created once, then it
should be reusable for new repos.

## How to version your repo then

1. When you have a PR going into master, put one of the labels created
above on it before merging.
  * "major" will increment `v0.0.0` to `v1.0.0`
  * "minor" will increment `v0.0.0` to `v0.1.0`
  * "patch" will increment `v0.0.0` to `v0.0.1`
  
## How this will work on the backend
A commit to master will trigger the following in the pipeline:

1. Clone your repo down
2. That directory will be passed to this tool
3. This tool will create and push a new tag to your repo based on the 
label in the corresponding PR

Additional steps your pipeline could take now, automatically:
* create a new distribution of your package, and push it to our PyPi
server
* create new docker images for your repo, push them out to staging
* Slack teammates with a changelog so they can decide to update
* MAYBE we can even trigger test runs of the tools that use your package,
running their tests to see if they can update.... 