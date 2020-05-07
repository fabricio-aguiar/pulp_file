import os
import sys

from git import Repo


new_version = sys.argv[1]
pulpcore_version = sys.argv[2]
next_pulpcore_version = sys.argv[3]

release_path = os.path.dirname(os.path.abspath(__file__))
plugin_path = release_path
if ".travis" in release_path:
    plugin_path = os.path.dirname(release_path)

print("\n\nHave you checked the output of: $towncrier --version x.y.z --draft")
print(f"\n\nRepo path: {plugin_path}")
repo = Repo(plugin_path)
git = repo.git

git.checkout("HEAD", b=f"release_{new_version}")

# First commit: changelog
os.system(f"towncrier --yes --version {new_version}")
git.add(".")
git.commit("-m", f"Building changelog for {new_version}\n\n[noissue]")

# Second commit: release version
with open(f"{plugin_path}/setup.py", "rt") as setup_file:
    setup_lines = setup_file.readlines()

with open(f"{plugin_path}/setup.py", "wt") as setup_file:
    for line in setup_lines:
        if "version=" in line:
            line = line.replace(".dev", "")
        if "pulpcore" in line:
            sep = "'" if len(line.split('"')) == 1 else '"'
            for word in line.split(sep):
                if "pulpcore" in word:
                    pulpcore_word = word

            line = line.replace(
                pulpcore_word, f"pulpcore>={pulpcore_version},<{next_pulpcore_version}"
            )

        setup_file.write(line)

plugin_name = plugin_path.split("/")[-1]
with open(f"{plugin_path}/{plugin_name}/__init__.py", "rt") as init_file:
    init_lines = init_file.readlines()

with open(f"{plugin_path}/{plugin_name}/__init__.py", "wt") as init_file:
    for line in init_lines:
        init_file.write(line.replace(".dev", ""))

git.add(".")
git.commit("-m", f"Releasing {new_version}\n\n[noissue]")

sha = repo.head.object.hexsha
short_sha = git.rev_parse(sha, short=4)

# Third commit: bump to .dev
dev_version = f"{new_version}.dev"
with open(f"{plugin_path}/setup.py", "wt") as setup_file:
    for line in setup_lines:
        if "version=" in line:
            line = f'version="{dev_version}",'
        if "pulpcore" in line:
            sep = "'" if len(line.split('"')) == 1 else '"'
            for word in line.split(sep):
                if "pulpcore" in word:
                    pulpcore_word = word

            line = line.replace(pulpcore_word, f"pulpcore>={pulpcore_version}")

        setup_file.write(line)

with open(f"{plugin_path}/{plugin_name}/__init__.py", "wt") as init_file:
    for line in init_lines:
        if "__version__":
            line = f'__version__ = "{dev_version}"'
        init_file.write(line)

git.add(".")
git.commit("-m", f"Bump to {dev_version}\n\n[noissue]")

print(f"Release commit == {short_sha}")
