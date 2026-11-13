"""Check the addon version: README.txt names it, the changelog has its entry, and an addon change bumps it.

  python tools/check_version.py                    the KodoTimes/README.txt header and changelog entry
  python tools/check_version.py --base origin/main  also: a change under KodoTimes/ since <base> needs a higher
                                                    ## Version in KodoTimes/KodoTimes.toc than <base> has
  python tools/check_version.py --notes            print the changelog entry of the current version (release notes)

Everything under KodoTimes/ goes into the released ZIP, so every change there needs a new version and changelog entry.
The decisions are pure functions, checked against built-in cases on every run. Standard library only.
"""
from pathlib import Path
import argparse
import re
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
TOC = 'KodoTimes/KodoTimes.toc'
README = 'KodoTimes/README.txt'
VERSION_RE = re.compile(r'^## Version:\s*(\S+)', re.MULTILINE)   # as in tools/package_addon.py
HISTORY = re.compile(r'^(\d+\.\d+(?:\.\d+)?):')                   # as in tools/check_rename.py


def toc_version(text):
    """The ## Version of a TOC text, or None."""
    m = VERSION_RE.search(text or '')
    return m.group(1) if m else None


def version_key(version):
    """0.10.6 -> (0, 10, 6); None when it is not dotted numbers."""
    return tuple(int(p) for p in version.split('.')) if version and re.fullmatch(r'\d+(?:\.\d+)*', version) else None


def changelog_entry(text, version):
    """The changelog lines of version: its '<version>:' line and the continuation lines (starting with a space)."""
    entry, inside = [], False
    for line in text.splitlines():
        m = HISTORY.match(line)
        if m:
            inside = m.group(1) == version
        elif not line.startswith(' '):
            inside = False
        if inside:
            entry.append(line)
    return '\n'.join(entry)


def readme_failures(text, version):
    """What is wrong with README.txt for this version: its first line must name it and the changelog must hold it."""
    failures = []
    first = text.splitlines()[0] if text else ''
    if not re.search(rf'(?<![\d.]){re.escape(version)}(?![\d.])', first):
        failures.append(f'{README} line 1 does not name version {version}: {first!r}')
    if not changelog_entry(text, version):
        failures.append(f'{README} has no "{version}:" changelog entry')
    return failures


def bump_failure(changed, base_version, head_version):
    """Why the change needs a version bump (None when fine): files under KodoTimes/ changed, the version did not rise."""
    addon = [path for path in changed if path.startswith('KodoTimes/')]
    if not addon or base_version is None:   # nothing shipped changed, or the base had no addon yet
        return None
    base, head = version_key(base_version), version_key(head_version)
    raised = base < head if base is not None and head is not None else head_version != base_version
    if raised:
        return None
    return (f'{len(addon)} file(s) under KodoTimes/ changed ({", ".join(addon[:5])}{", ..." if len(addon) > 5 else ""}) '
            f'but ## Version in {TOC} is {head_version}, base has {base_version}: raise it and add a changelog entry '
            f'to {README}')


def self_test():
    """The built-in cases of the pure functions; returns the failing ones."""
    failures = []

    def case(got, want, what):
        if got != want:
            failures.append(f'self-test {what}: got {got!r}, expected {want!r}')

    # the bump check: an addon change without a higher version fails, everything else passes
    case(bump_failure(['KodoTimes/Pals.lua'], '0.10.6', '0.10.6') is not None, True, 'addon change, same version fails')
    case(bump_failure(['README.md', 'KodoTimes/README.txt'], '0.10.6', '0.10.6') is not None, True,
         'README.txt typo fix, same version fails')
    case(bump_failure(['KodoTimes/Pals.lua'], '0.10.6', '0.10.5') is not None, True, 'addon change, lower version fails')
    case(bump_failure(['KodoTimes/Pals.lua', 'KodoTimes/KodoTimes.toc'], '0.10.6', '0.10.7'), None,
         'addon change, raised version passes')
    case(bump_failure(['KodoTimes/Pals.lua'], '0.10.9', '0.10.10'), None, 'raised version compares by number')
    case(bump_failure(['README.md', 'tools/check_version.py', '.github/workflows/checks.yml'], '0.10.6', '0.10.6'), None,
         'no change under KodoTimes/ passes')
    case(bump_failure([], '0.10.6', '0.10.6'), None, 'empty change passes')
    case(bump_failure(['KodoTimesExtra/x.lua'], '0.10.6', '0.10.6'), None, 'only the KodoTimes/ folder counts')
    case(bump_failure(['KodoTimes/Pals.lua'], None, '0.10.6'), None, 'base without an addon passes')

    # the README.txt header and changelog
    sample = ('Kodo Times 1.2.3 - WoW Forever (Interface 16001)\n'
              'intro\n'
              '1.2.3: first line of the entry,\n'
              '        its continuation.\n'
              '1.2.2: older entry\n'
              '        older continuation\n'
              'NOT A CONTINUATION\n')
    case(changelog_entry(sample, '1.2.3'), '1.2.3: first line of the entry,\n        its continuation.',
         'entry with its continuation line')
    case(changelog_entry(sample, '1.2.2'), '1.2.2: older entry\n        older continuation',
         'entry ends at an unindented line')
    case(changelog_entry(sample, '1.2.4'), '', 'missing entry')
    case(readme_failures(sample, '1.2.3'), [], 'header and entry present')
    case(len(readme_failures(sample, '1.2.2')), 1, 'header names another version')
    case(len(readme_failures(sample, '1.2')), 2, 'a prefix of the header version is not the version')
    case(toc_version('## Interface: 16001\n## Version: 0.10.6\n'), '0.10.6', 'TOC version')
    case(toc_version(''), None, 'TOC without a version')
    return failures


def git(*args):
    return subprocess.run(['git', *args], cwd=root, capture_output=True, text=True, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description='Check the KodoTimes version, its changelog entry and the version bump.')
    parser.add_argument('--base', help='git ref to compare with: a change under KodoTimes/ needs a higher version')
    parser.add_argument('--notes', action='store_true', help='print the changelog entry of the current version')
    args = parser.parse_args()

    version = toc_version((root / TOC).read_text(encoding='utf-8'))
    readme = (root / README).read_text(encoding='utf-8')
    if args.notes:
        entry = changelog_entry(readme, version)
        if not entry:
            sys.exit(f'FAIL: {README} has no "{version}:" changelog entry')
        print(entry)
        return

    failures = self_test()
    if version is None:
        failures.append(f'{TOC} has no ## Version')
    else:
        failures += readme_failures(readme, version)
    summary = f'{README} names {version} and has its changelog entry'
    if args.base:
        diff = git('diff', '--name-only', f'{args.base}...HEAD')
        if diff.returncode != 0:
            failures.append(f'git diff {args.base}...HEAD failed (needs the full history): {diff.stderr.strip()}')
        else:
            changed = diff.stdout.split('\n')
            shown = git('show', f'{args.base}:{TOC}')
            base_version = toc_version(shown.stdout) if shown.returncode == 0 else None
            problem = bump_failure([p for p in changed if p], base_version, version)
            if problem:
                failures.append(problem)
            summary += f'; version {base_version} -> {version} against {args.base}'
    if failures:
        print('FAIL:\n  ' + '\n  '.join(failures))
        sys.exit(1)
    print(f'PASS: {summary}; built-in bump and changelog cases hold')


if __name__ == '__main__':
    main()
