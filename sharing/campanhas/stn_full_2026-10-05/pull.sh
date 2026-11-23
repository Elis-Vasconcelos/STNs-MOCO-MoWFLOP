#!/usr/bin/env bash
# pull.sh <bambu|bambu3> <front> <scheme> <fam>  -> results/stn_2026-10-05/<front>/<scheme>/<originals|sparse>/, md5-checked
set -euo pipefail
host=$1 front=$2 scheme=$3 fam=$4
famdir=$([ "$fam" = orig ] && echo originals || echo sparse)
camp=full_${front}_${scheme}_${fam}_2026-10-05
dest=/home/elis/Projects/TCC/results/stn_2026-10-05/$front/$scheme/$famdir
ssh_() { if [ "$host" = bambu ]; then SSH_ASKPASS=/usr/bin/ksshaskpass SSH_ASKPASS_REQUIRE=force DISPLAY=${DISPLAY:-:0} ssh -o ConnectTimeout=15 -o NumberOfPasswordPrompts=1 bambu "$@"; else ssh -o BatchMode=yes bambu3 "$@"; fi; }
[ -e "$dest" ] && { echo "exists: $dest"; exit 1; }
mkdir -p "$dest"
ssh_ "cd ~/STNs-MOCO-MoWFLOP/campanhas/$camp && LC_ALL=C find . -type f -print0 | sort -z | xargs -0 md5sum" 2>/dev/null | grep -E '^[0-9a-f]{32}  ' > "$dest.md5"
ssh_ "tar cf - -C ~/STNs-MOCO-MoWFLOP/campanhas/$camp ." 2>/dev/null | tar xf - -C "$dest"
(cd "$dest" && md5sum --quiet -c "$dest.md5") && echo "OK $camp -> $dest: $(wc -l < "$dest.md5") files, $(du -sh "$dest" | cut -f1)"
mv "$dest.md5" "$dest/../${famdir}_md5_server.txt"
