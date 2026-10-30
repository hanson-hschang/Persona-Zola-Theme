#!/usr/bin/env python3
"""Stage Persona sources before Zola, without changing authored Markdown."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import tomllib

from persona_math import protect_math

MARKER = '.persona-stage.json'
EXCLUDED = {'.git', '.hg', '.svn', '.DS_Store', '__pycache__', 'node_modules', '.venv', 'venv', '.cache', '.persona-build', '.codex', '.agents', '.aws', '.env', 'target'}


class PipelineError(Exception):
    pass


def configuration(root: Path) -> dict:
    for name in ('zola.toml', 'config.toml'):
        path = root / name
        if path.is_file():
            return tomllib.loads(path.read_text())
    raise PipelineError(f'No config.toml or zola.toml in {root}')


def split_post(text: str) -> tuple[str, dict, str]:
    match = re.match(r'\A(\+\+\+\r?\n)(.*?)(\r?\n\+\+\+\s*\r?\n)', text, re.S)
    if not match:
        return '', {}, text
    return match.group(0), tomllib.loads(match.group(2)), text[match.end():]


def theme_root(root: Path, config: dict) -> Path:
    return root / 'themes' / config['theme'] if config.get('theme') else root


def resolve_style(root: Path, post: Path, extra: dict, config: dict) -> Path:
    theme = theme_root(root, config)
    directories = [post.parent, root / 'citation-style', root, theme / 'citation-style', theme]

    def find(value):
        if not isinstance(value, str) or not value:
            return None
        candidate = Path(value)
        for directory in directories:
            for name in (candidate, candidate.with_suffix('.csl')):
                path = directory / name
                if path.is_file():
                    return path.resolve()
        return None

    if extra.get('citation_style'):
        result = find(extra['citation_style'])
        if result:
            return result
        raise PipelineError(f"Citation style {extra['citation_style']!r} not found for {post}")
    local = post.parent / 'style.csl'
    if local.is_file():
        return local
    def configured_style(settings):
        site_extra = settings.get('extra', {})
        return site_extra.get('citation_style') or site_extra.get('persona', {}).get('citation_style')

    candidate = configured_style(config)
    if candidate:
        result = find(candidate)
        if not result:
            raise PipelineError(f'Configured citation style {candidate!r} was not found')
        return result
    if theme != root:
        for name in ('zola.toml', 'config.toml', 'theme.toml'):
            path = theme / name
            if path.is_file():
                candidate = configured_style(tomllib.loads(path.read_text()))
                if candidate:
                    result = find(candidate)
                    if result:
                        return result
                    raise PipelineError(f'Configured citation style {candidate!r} was not found')
    raise PipelineError(f'No citation style available for {post}; set [extra].citation_style or add style.csl')


def run_pandoc(arguments: list[str], text: str) -> str:
    try:
        result = subprocess.run(['pandoc', *arguments], input=text, text=True, capture_output=True, check=False)
    except FileNotFoundError as error:
        raise PipelineError('Pandoc is required for posts with a bibliography. Install Pandoc and retry.') from error
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    if result.returncode:
        raise PipelineError('Pandoc could not process the post')
    return result.stdout


def mask_markup(body: str) -> tuple[str, dict[str, str]]:
    """Shield Tera calls and encoded math from Pandoc's HTML normalization."""
    placeholders = {}
    prefix = 'PERSONA_MARKUP_'
    while prefix in body:
        prefix += '_'
    output = []
    index = 0
    while index < len(body):
        end = None
        if body.startswith('<span class="persona-math">', index):
            close = body.find('</span>', index)
            if close >= 0:
                end = close + len('</span>')
        elif body[index:index + 2] in ('{{', '{%', '{#'):
            opener = body[index:index + 2]
            heading_id = re.match(r'\{#[^{}\s]+\}', body[index:]) if opener == '{#' else None
            if heading_id:
                output.append(heading_id.group(0))
                index += heading_id.end()
                continue
            closer = {'{{': '}}', '{%': '%}', '{#': '#}'}[opener]
            quote = None
            cursor = index + 2
            while cursor < len(body):
                char = body[cursor]
                if quote:
                    if char == "\\":
                        cursor += 2
                        continue
                    if char == quote:
                        quote = None
                elif body.startswith(closer, cursor):
                    end = cursor + 2
                    break
                elif char in ("'", '"') and opener != '{#':
                    quote = char
                cursor += 1
            if end and re.fullmatch(r'{%\s*raw\s*%}', body[index:end]):
                raw_end = re.search(r'{%\s*endraw\s*%}', body[end:])
                if raw_end:
                    end += raw_end.end()
        if end:
            token = f'<!-- {prefix}{len(placeholders)} -->'
            placeholders[token] = body[index:end]
            output.append(token)
            index = end
        else:
            output.append(body[index])
            index += 1
    return ''.join(output), placeholders


def render_citations(body: str, bibliography: list[Path], csl: Path) -> str:
    masked, placeholders = mask_markup(body)
    arguments = ['--from=markdown-smart', '--to=json', '--citeproc', '--mathjax', '--metadata=link-citations:true', '--metadata=reference-section-title:Bibliography', f'--csl={csl}']
    arguments.extend(f'--bibliography={path}' for path in bibliography)
    document = json.loads(run_pandoc(arguments, masked))
    # Keep Zola's Markdown heading/link processing while rendering the bibliography
    # as one raw block that the theme can move below its optional Citation section.
    blocks = document['blocks']
    for index, block in enumerate(blocks):
        if block.get('t') == 'Div' and block['c'][0][0] == 'refs':
            bibliography_blocks = [block]
            if index and blocks[index - 1].get('t') == 'Header' and blocks[index - 1]['c'][1][0] == 'bibliography':
                heading = blocks.pop(index - 1)
                index -= 1
                heading['c'][0] = 2
                block['c'][1].insert(0, heading)
            fragment = {**document, 'blocks': bibliography_blocks}
            rendered = run_pandoc(['--from=json', '--to=html', '--wrap=none', '--mathjax'], json.dumps(fragment))
            blocks[index] = {'t': 'RawBlock', 'c': ['html', '<!-- persona-bibliography -->\n' + rendered]}
            break
    # Zola understands raw HTML and heading IDs, but not Pandoc's
    # `inline HTML`{=html} syntax. Keep actual HTML for protected inline math.
    rendered = run_pandoc(['--from=json', '--to=commonmark_x-raw_attribute', '--wrap=none'], json.dumps(document))
    for token, original in placeholders.items():
        rendered = rendered.replace(token, original)
    return rendered


def process_post(source: Path, root: Path, config: dict) -> str:
    text = source.read_text()
    frontmatter, metadata, body = split_post(text)
    extra = metadata.get('extra', {})
    if 'tex' in extra:
        body = protect_math(body)
    configured = extra.get('bibliography')
    bibliography = []
    if configured:
        values = configured if isinstance(configured, list) else [configured]
        for value in values:
            path = source.parent / value
            if not path.is_file():
                raise PipelineError(f'Bibliography not found: {path}')
            bibliography.append(path.resolve())
    elif (source.parent / 'references.bib').is_file():
        bibliography = [(source.parent / 'references.bib').resolve()]
    if bibliography:
        body = render_citations(body, bibliography, resolve_style(root, source, extra, config))
    if 'tex' in extra:
        body = '<!-- persona-math-protected -->\n\n' + body
    return frontmatter + body


def source_files(root: Path, destination: Path, config: dict) -> dict[Path, tuple[int, int]]:
    """Follow file symlinks into independent copies; reject directory cycles."""
    output = (root / config.get('output_dir', 'public')).resolve()
    snapshot = {}
    for directory, names, files in os.walk(root, followlinks=False):
        directory = Path(directory)
        names[:] = [name for name in names if name not in EXCLUDED and (directory / name).resolve() not in (destination.resolve(), output, (theme_root(root, config) / 'public').resolve())]
        for name in names:
            if (directory / name).is_symlink():
                raise PipelineError(f'Directory symlink is not supported in staged sources: {directory / name}')
        for name in files:
            path = directory / name
            if name in EXCLUDED or name == MARKER or name.endswith(('.pyc', '.swp', '.tmp')):
                continue
            stat = path.stat()
            snapshot[path.relative_to(root)] = (stat.st_mtime_ns, stat.st_size)
    return snapshot


def write_changed(path: Path, content: str):
    if path.is_file() and path.read_text() == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.persona-tmp')
    temporary.write_text(content)
    temporary.replace(path)


class Stage:
    def __init__(self, root: Path, destination: Path):
        self.root = root.resolve()
        self.destination = destination.resolve()
        if self.destination == self.root or self.destination in self.root.parents:
            raise PipelineError('The staging directory must be separate from the source site')
        for name in ('content', 'themes', 'templates', 'sass', 'static', 'citation-style', 'scripts', 'tests', 'docs', '.git', '.codex', '.agents', '.aws'):
            source_directory = self.root / name
            if self.destination == source_directory or source_directory in self.destination.parents:
                raise PipelineError(f'Staging cannot be placed inside authored sources: {self.destination}')
        if self.destination.exists() and any(self.destination.iterdir()):
            marker = self.destination / MARKER
            if not marker.is_file() or json.loads(marker.read_text()).get('source') != str(self.root):
                raise PipelineError(f'Refusing to overwrite unowned staging directory: {self.destination}')
            shutil.rmtree(self.destination)
        self.destination.mkdir(parents=True, exist_ok=True)
        (self.destination / MARKER).write_text(json.dumps({'source': str(self.root)}))
        self.snapshot = {}
        self.generated = set()
        self.sources = {}

    def sync(self) -> bool:
        config = configuration(self.root)
        current = source_files(self.root, self.destination, config)
        if current == self.snapshot:
            return False
        changed = {path for path, value in current.items() if self.snapshot.get(path) != value}
        # Reprocess every post when bibliography/style/config changes; ordinary
        # template and image edits only need copying. Failed processing keeps the
        # last good staged Markdown and is retried on the next source change.
        dependencies_changed = not self.snapshot or any(path.suffix in ('.bib', '.csl', '.toml') for path in changed | (self.snapshot.keys() - current.keys()))
        posts = {}
        for path in current:
            if path.parts[0] != 'content' or path.suffix != '.md':
                continue
            output = path.with_name(path.name.removesuffix('.src.md') + '.md') if path.name.endswith('.src.md') else path
            if output not in posts or path.name.endswith('.src.md'):
                posts[output] = path
        prepared = {}
        for output, source in posts.items():
            if dependencies_changed or source in changed or self.sources.get(output) != source:
                try:
                    prepared[output] = process_post(self.root / source, self.root, config)
                except (ValueError, OSError, PipelineError) as error:
                    raise PipelineError(f'{source}: {error}') from error
        generated = set(posts)
        for path in ((self.snapshot.keys() - current.keys()) | (self.generated - generated)) - generated:
            target = self.destination / path
            if target.is_file() or target.is_symlink():
                target.unlink()
        for path in changed:
            if path.parts[0] == 'content' and path.suffix == '.md':
                continue
            target = self.destination / path
            if target.is_dir():
                shutil.rmtree(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.root / path, target, follow_symlinks=True)
        for path, content in prepared.items():
            write_changed(self.destination / path, content)
        self.snapshot, self.generated, self.sources = current, generated, posts
        return True


def configured_output(root: Path, value: str | None = None) -> Path:
    root = root.resolve()
    output = (root / (value or configuration(root).get('output_dir', 'public'))).resolve()
    if output == root or output in root.parents:
        raise PipelineError(f'Unsafe generated output directory: {output}')
    for name in ('content', 'themes', 'templates', 'sass', 'static', 'citation-style', 'scripts', 'tests', 'docs', '.git', '.codex', '.agents', '.aws'):
        authored = root / name
        if output == authored or authored in output.parents or output in authored.parents:
            raise PipelineError(f'Generated output overlaps authored sources: {output}')
    return output


def build_arguments(root: Path, forwarded: list[str]) -> list[str]:
    arguments = list(forwarded)
    found = False
    for index, value in enumerate(arguments):
        if value in ('--output-dir', '-o'):
            if index + 1 == len(arguments):
                raise PipelineError(f'{value} needs a directory')
            arguments[index + 1] = str(configured_output(root, arguments[index + 1]))
            found = True
        elif value.startswith('--output-dir='):
            arguments[index] = '--output-dir=' + str(configured_output(root, value.partition('=')[2]))
            found = True
    if not found:
        arguments = ['--output-dir', str(configured_output(root)), *arguments]
    # Zola requires --force for a nonempty absolute output directory. The site's
    # conventional public/ is generated; custom directories retain Zola's guard.
    for index, value in enumerate(arguments):
        output = arguments[index + 1] if value in ('--output-dir', '-o') else value.partition('=')[2] if value.startswith('--output-dir=') else None
        if output and Path(output) == root / 'public' and Path(output).is_dir() and '--force' not in arguments:
            arguments.append('--force')
            break
    return arguments


def clean(root: Path):
    output = configured_output(root)
    if output.exists():
        if output != root / 'public':
            raise PipelineError(f'Refusing to clean custom output directory automatically: {output}')
        shutil.rmtree(output)
    stage = root / '.persona-build'
    if stage.exists():
        marker = stage / MARKER
        if not marker.is_file() or json.loads(marker.read_text()).get('source') != str(root):
            raise PipelineError(f'Refusing to clean unowned staging directory: {stage}')
        shutil.rmtree(stage)


def main(argv=None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    forwarded = []
    if '--' in arguments:
        boundary = arguments.index('--')
        forwarded, arguments = arguments[boundary + 1:], arguments[:boundary]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'check', 'serve', 'prepare', 'clean'))
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, help='Persistent staging directory (prepare only)')
    args = parser.parse_args(arguments)
    if args.output and args.command != 'prepare':
        parser.error('--output is only supported by prepare; use -- --output-dir for a build')
    root = args.root.resolve()
    try:
        configuration(root)
        if args.command == 'clean':
            clean(root)
            return 0
        if args.command == 'prepare':
            destination = args.output or Path('.persona-build')
            if not destination.is_absolute():
                destination = root / destination
            stage = Stage(root, destination)
            stage.sync()
            print(f'[persona] Prepared {destination}')
            return 0
        with tempfile.TemporaryDirectory(prefix='persona-') as temporary:
            stage = Stage(root, Path(temporary))
            stage.sync()
            command = ['zola', args.command]
            command += build_arguments(root, forwarded) if args.command == 'build' else forwarded
            if args.command != 'serve':
                return subprocess.run(command, cwd=stage.destination, check=False).returncode
            print(f'[persona] Watching authored sources in {root}', flush=True)
            process = subprocess.Popen(command, cwd=stage.destination)
            def interrupted(signum, frame):
                raise KeyboardInterrupt
            old_handler = signal.signal(signal.SIGTERM, interrupted)
            try:
                failed_snapshot = None
                last_error = None
                while process.poll() is None:
                    time.sleep(0.4)
                    current = None
                    try:
                        current = source_files(root, stage.destination, configuration(root))
                        if current != failed_snapshot:
                            stage.sync()
                            failed_snapshot = None
                            last_error = None
                    except (PipelineError, OSError, ValueError) as error:
                        if str(error) != last_error:
                            print(f'[persona] {error}; waiting for the next edit', file=sys.stderr)
                        last_error = str(error)
                        failed_snapshot = current
            finally:
                signal.signal(signal.SIGTERM, old_handler)
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            return process.returncode or 0
    except KeyboardInterrupt:
        return 0
    except (PipelineError, OSError, ValueError) as error:
        print(f'[persona] {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
