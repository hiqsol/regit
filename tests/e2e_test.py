#!/usr/bin/env python3

import os
import shutil
import subprocess
import tempfile

import pytest

REGIT = os.path.join(os.path.dirname(__file__), "..", "regit")


def run_regit(*args, cwd=None, env=None):
    return subprocess.run(
        [REGIT] + list(args),
        cwd=cwd, env=env,
        capture_output=True, text=True,
    )


def make_bare_repo(path, files=None, env=None):
    subprocess.run(["git", "init", "--bare", path],
                   check=True, capture_output=True, env=env)
    if files:
        tmp = tempfile.mkdtemp()
        try:
            subprocess.run(["git", "clone", path, tmp],
                           check=True, capture_output=True, env=env)
            for name, content in files.items():
                filepath = os.path.join(tmp, name)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "w") as f:
                    f.write(content)
            subprocess.run(["git", "-C", tmp, "add", "."],
                           check=True, capture_output=True, env=env)
            subprocess.run(["git", "-C", tmp, "commit", "-m", "initial"],
                           check=True, capture_output=True, env=env)
            subprocess.run(["git", "-C", tmp, "push"],
                           check=True, capture_output=True, env=env)
        finally:
            shutil.rmtree(tmp)


def push_commit(bare_path, filename, content, msg="update", env=None):
    tmp = tempfile.mkdtemp()
    try:
        subprocess.run(["git", "clone", bare_path, tmp],
                       check=True, capture_output=True, env=env)
        with open(os.path.join(tmp, filename), "w") as f:
            f.write(content)
        subprocess.run(["git", "-C", tmp, "add", filename],
                       check=True, capture_output=True, env=env)
        subprocess.run(["git", "-C", tmp, "commit", "-m", msg],
                       check=True, capture_output=True, env=env)
        subprocess.run(["git", "-C", tmp, "push"],
                       check=True, capture_output=True, env=env)
    finally:
        shutil.rmtree(tmp)


@pytest.fixture
def env(tmp_path):
    remotes = tmp_path / "remotes"
    remotes.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    test_env = os.environ.copy()
    test_env["HOME"] = str(home)
    test_env["GIT_AUTHOR_NAME"] = "Test"
    test_env["GIT_AUTHOR_EMAIL"] = "test@test.com"
    test_env["GIT_COMMITTER_NAME"] = "Test"
    test_env["GIT_COMMITTER_EMAIL"] = "test@test.com"

    gitconfig = home / ".gitconfig"
    gitconfig.write_text("[user]\nname = Test\nemail = test@test.com\n"
                         "[init]\ndefaultBranch = master\n")

    make_bare_repo(str(remotes / "main-repo"),
                   files={"README.md": "# Main\n", "app.py": "print('hello')\n"},
                   env=test_env)
    make_bare_repo(str(remotes / "dep-a"),
                   files={"lib.py": "def helper(): pass\n"},
                   env=test_env)

    config_dir = home / ".config" / "regit"
    config_dir.mkdir(parents=True)
    (config_dir / "config").write_text(
        "[known-repos]\n"
        "dep-a = file://{}/dep-a\n".format(remotes)
    )

    # Add .regit to main-repo
    clone_tmp = tmp_path / "setup-clone"
    subprocess.run(
        ["git", "clone", str(remotes / "main-repo"), str(clone_tmp)],
        check=True, capture_output=True, env=test_env,
    )
    (clone_tmp / ".regit").write_text("[repos]\ndep-a\n")
    subprocess.run(["git", "-C", str(clone_tmp), "add", ".regit"],
                   check=True, capture_output=True, env=test_env)
    subprocess.run(
        ["git", "-C", str(clone_tmp), "commit", "-m", "add .regit"],
        check=True, capture_output=True, env=test_env,
    )
    subprocess.run(["git", "-C", str(clone_tmp), "push"],
                   check=True, capture_output=True, env=test_env)
    shutil.rmtree(str(clone_tmp))

    return {
        "remotes": remotes,
        "workspace": workspace,
        "home": home,
        "env": test_env,
    }


class TestGrab:
    def test_standard(self, env):
        repo_url = "file://{}/main-repo".format(env["remotes"])
        result = run_regit("grab", repo_url,
                           cwd=str(env["workspace"]), env=env["env"])
        assert result.returncode == 0
        cloned = env["workspace"] / "main-repo"
        assert (cloned / ".git").is_dir()
        assert (cloned / "README.md").is_file()
        assert (cloned / "dep-a").is_dir()

    def test_custom_path(self, env):
        repo_url = "file://{}/main-repo".format(env["remotes"])
        result = run_regit("grab", repo_url, "mydir",
                           cwd=str(env["workspace"]), env=env["env"])
        assert result.returncode == 0
        cloned = env["workspace"] / "mydir"
        assert (cloned / ".git").is_dir()
        assert (cloned / "README.md").is_file()

    def test_dot(self, env):
        repo_url = "file://{}/main-repo".format(env["remotes"])
        target = env["workspace"] / "dot-test"
        target.mkdir()
        result = run_regit("grab", repo_url, ".",
                           cwd=str(target), env=env["env"])
        assert result.returncode == 0
        assert (target / ".git").is_dir()
        assert (target / "README.md").is_file()

    def test_dotgit(self, env):
        repo_url = "file://{}/main-repo".format(env["remotes"])
        target = env["workspace"] / "dotgit-test"
        target.mkdir()
        result = run_regit("grab", repo_url, ".git",
                           cwd=str(target), env=env["env"])
        assert result.returncode == 0
        assert (target / ".git").is_dir()
        assert not (target / "README.md").exists()

    def test_dotgit_rejects_existing(self, env):
        repo_url = "file://{}/dep-a".format(env["remotes"])
        target = env["workspace"] / "has-git"
        target.mkdir()
        (target / ".git").mkdir()
        result = run_regit("grab", repo_url, ".git",
                           cwd=str(target), env=env["env"])
        assert result.returncode != 0


class TestDeps:
    def test_clones_dependencies(self, env):
        repo_url = "file://{}/main-repo".format(env["remotes"])
        run_regit("grab", repo_url,
                  cwd=str(env["workspace"]), env=env["env"])
        cloned = env["workspace"] / "main-repo"
        assert (cloned / "dep-a").is_dir()
        assert (cloned / "dep-a" / "lib.py").is_file()


class TestGrabViaSymlink:
    def test_deps_resolve_correctly(self, env):
        bin_dir = env["workspace"] / "bin"
        bin_dir.mkdir()
        symlink = bin_dir / "git-grab"
        symlink.symlink_to(os.path.realpath(REGIT))

        repo_url = "file://{}/main-repo".format(env["remotes"])
        result = subprocess.run(
            [str(symlink), repo_url],
            cwd=str(env["workspace"]),
            env=env["env"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        cloned = env["workspace"] / "main-repo"
        assert (cloned / ".git").is_dir()
        assert (cloned / "dep-a").is_dir(), \
            "deps must be cloned, not misinterpreted as grab argument"


class TestScan:
    def test_detects_untracked(self, env):
        repo_url = "file://{}/main-repo".format(env["remotes"])
        scan_dir = env["workspace"] / "scan-dirty"
        scan_dir.mkdir()
        subprocess.run(
            ["git", "clone", repo_url, str(scan_dir / "dirty")],
            check=True, capture_output=True, env=env["env"],
        )
        (scan_dir / "dirty" / "new.txt").write_text("x\n")

        result = run_regit("scan", cwd=str(scan_dir), env=env["env"])
        assert "dirty" in result.stdout
        assert "untracked" in result.stdout

    def test_clean_is_silent(self, env):
        repo_url = "file://{}/main-repo".format(env["remotes"])
        scan_dir = env["workspace"] / "scan-clean"
        scan_dir.mkdir()
        subprocess.run(
            ["git", "clone", repo_url, str(scan_dir / "clean")],
            check=True, capture_output=True, env=env["env"],
        )

        result = run_regit("scan", cwd=str(scan_dir), env=env["env"])
        assert "clean" not in result.stdout


class TestUp:
    def test_pulls_new_commits(self, env):
        repo_url = "file://{}/main-repo".format(env["remotes"])
        clone_dir = env["workspace"] / "up-test"
        subprocess.run(
            ["git", "clone", repo_url, str(clone_dir)],
            check=True, capture_output=True, env=env["env"],
        )

        push_commit(str(env["remotes"] / "main-repo"),
                     "new.txt", "new\n", env=env["env"])

        result = run_regit("up", cwd=str(clone_dir), env=env["env"])
        assert result.returncode == 0
        assert (clone_dir / "new.txt").is_file()


class TestSync:
    def test_copies_changed_files(self, env):
        repo_url = "file://{}/main-repo".format(env["remotes"])
        src = env["workspace"] / "sync-src"
        subprocess.run(
            ["git", "clone", repo_url, str(src)],
            check=True, capture_output=True, env=env["env"],
        )
        (src / "untracked.txt").write_text("hello\n")
        (src / "README.md").write_text("# Modified\n")

        dest = env["workspace"] / "sync-dest"
        dest.mkdir()
        result = run_regit("sync", str(dest), cwd=str(src), env=env["env"])
        assert result.returncode == 0
        assert (dest / "untracked.txt").read_text() == "hello\n"
        assert (dest / "README.md").read_text() == "# Modified\n"


class TestInstall:
    def test_creates_symlinks(self, env):
        bin_dir = env["workspace"] / "inst-bin"
        bin_dir.mkdir()
        regit_copy = bin_dir / "regit"
        shutil.copy2(REGIT, str(regit_copy))
        regit_copy.chmod(0o755)

        result = subprocess.run(
            [str(regit_copy), "install"],
            cwd=str(env["workspace"]),
            env=env["env"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        for cmd in ["up", "scan", "grab", "lgrab", "sync", "deps"]:
            assert (bin_dir / ("git-" + cmd)).is_symlink()

    def test_uninstall_removes(self, env):
        bin_dir = env["workspace"] / "uninst-bin"
        bin_dir.mkdir()
        regit_copy = bin_dir / "regit"
        shutil.copy2(REGIT, str(regit_copy))
        regit_copy.chmod(0o755)

        subprocess.run(
            [str(regit_copy), "install"],
            cwd=str(env["workspace"]),
            env=env["env"],
            capture_output=True, text=True,
        )
        result = subprocess.run(
            [str(regit_copy), "uninstall"],
            cwd=str(env["workspace"]),
            env=env["env"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        for cmd in ["up", "scan", "grab", "lgrab", "sync", "deps"]:
            assert not (bin_dir / ("git-" + cmd)).exists()
