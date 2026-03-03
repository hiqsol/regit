# reGit - Repeated Git

[![GitHub version](https://badge.fury.io/gh/hiqsol%2Fregit.svg)](https://badge.fury.io/gh/hiqsol%2Fregit)
[![Scrutinizer Code Coverage](https://img.shields.io/scrutinizer/coverage/g/hiqsol/regit.svg)](https://scrutinizer-ci.com/g/hiqsol/regit/)
[![Scrutinizer Code Quality](https://img.shields.io/scrutinizer/g/hiqsol/regit.svg)](https://scrutinizer-ci.com/g/hiqsol/regit/)

Git extensions for managing multiple repositories:

- `git up` - pull current repo and all the dependencies
- `git scan` - scan directory tree recursively to find unsynced repos
- `git grab` - clone with URL resolution
- `git lgrab` - clone using private source (GitLab by default)
- `git sync` - rsync only changed and untracked files to a given destination
- `git deps` - update dependencies

Also available as `regit up`, `regit scan`, etc.
Update regit itself with `regit self`.

## Installation

Single Python 3 executable, no dependencies.

```sh
git clone https://github.com/hiqsol/regit.git ~/.local/share/regit
ln -s ~/.local/share/regit/regit ~/.local/bin/regit
regit install
```

Make sure `~/.local/bin` is in your `PATH`.

`regit install` creates `git-*` symlinks so commands work as
`git up`, `git scan`, etc.
Update anytime with `regit self`.

To remove the symlinks: `regit uninstall`.

## Alternatives

I've really tried and spent lot of time looking for already existing
tool for the job. There are lots of them. Maybe you could find something
more suitable for your needs.

- [repo]:       helps manage many Git repositories (Python)
- [gita]:       manage multiple git repos in home (Python)
- [myrepos]:    manage all your version control repos (Perl)
- [gitbatch]:   text-based UI to manage multiple git repos (Go)
- [git-plus]:   run commands in multiple git repos (Python)
- [mu-repo]:    help working with multiple git repos (Python)
- [mugit]:      managing multiple git repositories (Python)
- [gr]:         managing multiple git repositories (JavaScript)
- [mgit]:       layered git repositories (Shell)

[repo]:         https://github.com/GerritCodeReview/git-repo
[gita]:         https://github.com/nosarthur/gita
[myrepos]:      https://github.com/RichiH/myrepos
[gitbatch]:     https://github.com/isacikgoz/gitbatch
[git-plus]:     https://github.com/tkrajina/git-plus
[mu-repo]:      https://github.com/fabioz/mu-repo/
[mugit]:        https://bitbucket.org/digitalstirling/mugit/
[gr]:           https://github.com/mixu/gr
[mgit]:         https://github.com/capr/mgit

## License

This project is released under the terms of the BSD-3-Clause
[license](LICENSE).
Read more [here](http://choosealicense.com/licenses/bsd-3-clause).

Copyright © 2021-2026, Andrii Vasyliev (<sol@solex.me>)
