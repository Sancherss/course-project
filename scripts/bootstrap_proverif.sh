#!/bin/sh
# Local source build; requires Linux/POSIX, curl, tar, gcc and make.
set -eu
project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
tools_dir="$project_root/.tools"
mkdir -p "$tools_dir/src" "$tools_dir/proverif"
cd "$tools_dir/src"
if [ ! -f ocaml-4.14.2.tar.gz ]; then
  curl -fL --retry 2 -o ocaml-4.14.2.tar.gz https://github.com/ocaml/ocaml/archive/refs/tags/4.14.2.tar.gz
fi
if [ ! -f proverif2.05.tar.gz ]; then
  curl -fL --retry 2 -o proverif2.05.tar.gz https://bblanche.gitlabpages.inria.fr/proverif/proverif2.05.tar.gz
fi
sha256sum -c "$project_root/scripts/toolchain.sha256"
if [ ! -x "$tools_dir/ocaml/bin/ocamlopt" ]; then
  tar -xzf ocaml-4.14.2.tar.gz
  (cd ocaml-4.14.2 && ./configure --prefix="$tools_dir/ocaml" && make -j4 world.opt && make install)
fi
if [ ! -x "$tools_dir/proverif/proverif" ]; then
  tar -xzf proverif2.05.tar.gz
  (cd proverif2.05 && PATH="$tools_dir/ocaml/bin:$PATH" ./build -nointeract)
  cp proverif2.05/proverif "$tools_dir/proverif/proverif"
fi
"$tools_dir/proverif/proverif" -help
