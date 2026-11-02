#!/usr/bin/env bash
set -euo pipefail
task_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
emulator_dir="${MICROEMU_HOME:-/tmp/opencode/microemulator-2.0.4}"
if [[ ! -f "$emulator_dir/microemulator.jar" ]]; then
  echo 'Definir MICROEMU_HOME vers une installation existante de MicroEmulator 2.0.4.' >&2
  exit 1
fi
mkdir -p "$task_dir/front/bin" "$task_dir/front/build"
mapfile -d '' source_files < <(find "$task_dir/front/src" -name '*.java' -print0)
javac --release 8 -cp "$emulator_dir/lib/midpapi20.jar:$emulator_dir/lib/cldcapi11.jar" -d "$task_dir/front/bin" "${source_files[@]}"
jar cfm "$task_dir/front/build/FAAIMARINANA.jar" "$task_dir/front/MANIFEST.MF" -C "$task_dir/front/bin" .
python3 - "$task_dir/front" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1])
manifest=(root/'MANIFEST.MF').read_text().replace('Manifest-Version: 1.0\n','').rstrip()
jar=root/'build/FAAIMARINANA.jar'
(root/'build/FAAIMARINANA.jad').write_text(manifest+'\nMIDlet-Jar-URL: FAAIMARINANA.jar\nMIDlet-Jar-Size: '+str(jar.stat().st_size)+'\n')
print('Distribution pour MicroEmulator :',jar)
PY
if [[ "${1:-}" != '--build' ]]; then
  exec java -cp "$emulator_dir/microemulator.jar:$task_dir/front/bin" org.microemu.app.Main Main
fi
