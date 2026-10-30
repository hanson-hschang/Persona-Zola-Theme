"""Integration contracts for Persona's isolated Markdown build pipeline."""
from html import unescape
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from test_math import MathText

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import persona


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='persona-test-')
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name).resolve()
        self.root = self.directory / 'site'
        self.root.mkdir()
        self.write('config.toml', 'base_url = "https://example.org/project/"\n')
        self.write('templates/page.html', '{{ page.content | safe }}')
        self.write('templates/section.html', '{{ section.content | safe }}')
        self.write('content/_index.md', '+++\ntitle = "Home"\n+++\n')
        self.stage_path = self.directory / 'stage'

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def post(self, body='Hello', extra=''):
        return self.write('content/post.md', '+++\ntitle = "Post"\n' + extra + '\n+++\n\n' + body)

    def stage(self):
        stage = persona.Stage(self.root, self.stage_path)
        stage.sync()
        return stage

    def citation_fixture(self):
        path = self.root / 'citation-style' / 'ieee.csl'
        path.parent.mkdir()
        shutil.copyfile(SCRIPTS.parent / 'citation-style' / 'ieee.csl', path)
        self.write('config.toml', 'base_url="https://example.org/project/"\n[extra]\ncitation_style="ieee"')
        self.write('content/references.bib', '@online{example, title={A reference}, url={https://example.org}}')
        return path

    def test_stages_math_without_modifying_authored_source(self):
        expression = r'$$\begin{aligned}a_i&=\{x,y\}\\b_j&=\frac{{a}}{{b}}\end{aligned}$$'
        post = self.post(expression, '[extra.tex]')
        original = post.read_bytes()
        stage = self.stage()
        rendered = (self.stage_path / 'content/post.md').read_text()
        self.assertEqual(original, post.read_bytes())
        self.assertIn('<!-- persona-math-protected -->', rendered)
        self.assertIn(expression, unescape(rendered))
        self.assertNotIn('{{a}}', rendered)
        self.assertFalse(stage.sync())

    def test_plain_markdown_does_not_need_pandoc(self):
        post = self.post('A **normal** post with `$literal$` and a dollar $5.')
        with patch.object(persona, 'run_pandoc', side_effect=AssertionError('Unexpected Pandoc call')):
            self.stage()
        self.assertEqual(post.read_text(), (self.stage_path / 'content/post.md').read_text())

    def test_legacy_source_wins_then_falls_back_after_removal(self):
        self.post('ordinary')
        legacy = self.write('content/post.src.md', '+++\ntitle="Post"\n+++\nlegacy')
        stage = self.stage()
        target = self.stage_path / 'content/post.md'
        self.assertIn('legacy', target.read_text())
        self.assertFalse((self.stage_path / 'content/post.src.md').exists())
        legacy.unlink()
        stage.sync()
        self.assertIn('ordinary', target.read_text())

    def test_deleting_shadowed_markdown_does_not_remove_legacy_output(self):
        regular = self.post('ordinary')
        self.write('content/post.src.md', '+++\ntitle="Post"\n+++\nlegacy')
        stage = self.stage()
        regular.unlink()
        stage.sync()
        self.assertIn('legacy', (self.stage_path / 'content/post.md').read_text())

    def test_sync_propagates_additions_changes_and_deletions(self):
        post = self.post()
        asset = self.write('static/image.svg', '<svg>before</svg>')
        stage = self.stage()
        self.write('static/image.svg', '<svg>after</svg>')
        self.write('content/new.md', '+++\ntitle="New"\n+++\nNew')
        stage.sync()
        self.assertEqual('<svg>after</svg>', (self.stage_path / 'static/image.svg').read_text())
        self.assertTrue((self.stage_path / 'content/new.md').exists())
        post.unlink()
        asset.unlink()
        stage.sync()
        self.assertFalse((self.stage_path / 'content/post.md').exists())
        self.assertFalse((self.stage_path / 'static/image.svg').exists())

    def test_asset_directory_can_be_replaced_with_a_file(self):
        asset = self.write('static/asset/old.txt', 'old')
        stage = self.stage()
        asset.unlink()
        asset.parent.rmdir()
        self.write('static/asset', 'new file')
        stage.sync()
        self.assertEqual('new file', (self.stage_path / 'static/asset').read_text())

    def test_failed_processing_keeps_last_good_preview_and_recovers(self):
        self.post('before')
        stage = self.stage()
        good = (self.stage_path / 'content/post.md').read_text()
        self.write('content/post.md', '+++\ntitle=[invalid\n+++\nwrong')
        with self.assertRaises(persona.PipelineError):
            stage.sync()
        self.assertEqual(good, (self.stage_path / 'content/post.md').read_text())
        self.post('after')
        stage.sync()
        self.assertIn('after', (self.stage_path / 'content/post.md').read_text())

    def test_persistent_prepare_removes_stale_posts_on_next_run(self):
        post = self.post()
        self.stage()
        post.unlink()
        self.stage()
        self.assertFalse((self.stage_path / 'content/post.md').exists())

    def test_refuses_unowned_or_authored_staging_directories(self):
        self.stage_path.mkdir()
        sentinel = self.stage_path / 'keep.txt'
        sentinel.write_text('keep')
        for destination in (self.stage_path, self.root, self.root / 'content/build'):
            with self.subTest(destination=destination), self.assertRaises(persona.PipelineError):
                persona.Stage(self.root, destination)
        self.assertEqual('keep', sentinel.read_text())

    def test_static_dotfiles_and_public_named_sections_survive(self):
        self.write('static/.well-known/security.txt', 'Contact: example')
        self.write('static/.nojekyll', '')
        self.write('content/public/index.md', '+++\ntitle="Public"\n+++\nPublished')
        self.write('public/stale.html', 'generated')
        self.write('.git/config', 'private')
        self.stage()
        self.assertTrue((self.stage_path / 'static/.well-known/security.txt').is_file())
        self.assertTrue((self.stage_path / 'static/.nojekyll').is_file())
        self.assertTrue((self.stage_path / 'content/public/index.md').is_file())
        self.assertFalse((self.stage_path / 'public').exists())
        self.assertFalse((self.stage_path / '.git').exists())

    def test_zola_toml_precedes_config_toml(self):
        self.write('zola.toml', 'title="preferred"')
        self.assertEqual('preferred', persona.configuration(self.root)['title'])

    def test_output_paths_never_overlap_authored_directories(self):
        for name in ('content', 'content/posts', 'templates', 'static/site', '.', '..'):
            with self.subTest(name=name), self.assertRaises(persona.PipelineError):
                persona.configured_output(self.root, name)
        self.assertEqual(self.root / 'build', persona.configured_output(self.root, 'build'))

    def test_forwarded_output_directories_resolve_against_source_site(self):
        for argument in (['--output-dir', 'dist'], ['--output-dir=dist'], ['-o', 'dist']):
            with self.subTest(argument=argument):
                actual = persona.build_arguments(self.root, argument)
                self.assertIn(str(self.root / 'dist'), ' '.join(actual))
                self.assertNotIn('--force', actual)

    def test_clean_preserves_authored_and_unowned_files(self):
        post = self.post()
        self.write('public/generated.html', 'output')
        self.stage_path = self.root / '.persona-build'
        self.stage()
        persona.clean(self.root)
        self.assertTrue(post.is_file())
        self.assertFalse((self.root / 'public').exists())
        self.assertFalse(self.stage_path.exists())
        self.stage_path.mkdir()
        sentinel = self.stage_path / 'keep.txt'
        sentinel.write_text('keep')
        with self.assertRaises(persona.PipelineError):
            persona.clean(self.root)
        self.assertTrue(sentinel.is_file())

    def test_csl_precedence_and_missing_explicit_style(self):
        post = self.post()
        custom = self.write('citation-style/custom.csl', 'custom')
        local = self.write('content/style.csl', 'local')
        self.assertEqual(custom, persona.resolve_style(self.root, post, {'citation_style': 'custom'}, {}))
        self.assertEqual(local, persona.resolve_style(self.root, post, {}, {'extra': {'citation_style': 'custom'}}))
        local.unlink()
        self.assertEqual(custom, persona.resolve_style(self.root, post, {}, {'theme': 'missing', 'extra': {'persona': {'citation_style': 'custom'}}}))
        self.write('themes/persona/theme.toml', '[extra]\ncitation_style="custom"')
        self.assertEqual(custom, persona.resolve_style(self.root, post, {}, {'theme': 'persona'}))
        with self.assertRaises(persona.PipelineError):
            persona.resolve_style(self.root, post, {'citation_style': 'missing'}, {})

    def test_missing_bibliography_reports_source_path(self):
        self.post('Citation [@missing]', '[extra]\nbibliography="missing.bib"')
        with self.assertRaisesRegex(persona.PipelineError, 'missing.bib'):
            self.stage()

    @unittest.skipUnless(shutil.which('pandoc'), 'Pandoc not installed')
    def test_citations_preserve_math_components_links_and_heading_ids(self):
        self.citation_fixture()
        expression = r'$$\begin{aligned}a_i&=\{x,y\}\\b_j&=\frac{{a}}{{b}} < c & d\end{aligned}$$'
        component = '{{ <post.embed src="https://example.org" title="A }} B" /> }}'
        raw = '{% raw %}\n```tera\n{{ <example caption="$x_i$" /> }}\n```\n{% endraw %}'
        self.post('## Heading {#custom-id}\n\n[Internal](@/target.md) [@example].\n\n' + expression + '\n\n' + component + '\n\n' + raw, '[extra]\ncitation_style="ieee"\n[extra.tex]')
        self.stage()
        rendered = (self.stage_path / 'content/post.md').read_text()
        self.assertIn('## Heading {#custom-id}', rendered)
        self.assertIn('(@/target.md)', rendered)
        self.assertIn(expression, unescape(rendered))
        self.assertNotIn('{{a}}', rendered)
        self.assertIn(component, rendered)
        self.assertIn(raw, rendered)
        self.assertIn('<!-- persona-bibliography -->', rendered)
        self.assertIn('id="ref-example"', rendered)
        self.assertIn('<h2', rendered)
        self.assertNotIn('PERSONA_MARKUP_', rendered)

    @unittest.skipUnless(shutil.which('pandoc'), 'Pandoc not installed')
    def test_bibliography_changes_regenerate_unchanged_posts(self):
        self.citation_fixture()
        self.post('Citation [@example].')
        stage = self.stage()
        target = self.stage_path / 'content/post.md'
        self.assertIn('A reference', target.read_text())
        self.write('content/references.bib', '@online{example, title={Updated title}, url={https://example.org}}')
        stage.sync()
        self.assertIn('Updated title', target.read_text())
        self.assertNotIn('A reference', target.read_text())

    @unittest.skipUnless(shutil.which('pandoc') and shutil.which('zola'), 'Pandoc and Zola required')
    def test_citation_build_preserves_real_inline_math_and_heading_ids(self):
        self.citation_fixture()
        inline = r'$a_i + b_j \in \Real{2}$'
        display = r'$$\frac{{x}}{{y}} + \{a,b\}$$'
        self.post('## Heading {#custom-id}\n\nInline ' + inline + ' [@example].\n\n'
                  + display + '\n\n{# A Tera comment after the heading #}\n\n'
                  + r'Literal `$x_i$` and \$5 or \$10.', '[extra.tex]')
        self.assertEqual(0, persona.main(['build', '--root', str(self.root)]))
        html = (self.root / 'public/post/index.html').read_text()
        self.assertEqual([inline, display], MathText(html).math)
        self.assertNotIn('{=html}', html)
        self.assertNotIn('<code>&lt;span', html)
        self.assertIn('id="custom-id"', html)
        self.assertIn('id="ref-example"', html)
        self.assertIn('<code>$x_i$</code>', html)
        self.assertIn('$5 or $10', html)

    @unittest.skipUnless(shutil.which('zola'), 'Zola not installed')
    def test_encoded_math_does_not_inflate_displayed_reading_time(self):
        shutil.copytree(SCRIPTS.parent / 'templates/components', self.root / 'templates/components')
        self.write('templates/page.html', '{{ <render.article_meta page={page} /> }}{{ page.content | safe }}')
        self.post('A short post.\n\n$' + 'a_i + b_j + ' * 30 + 'c_k$', '[extra.tex]')
        self.assertEqual(0, persona.main(['build', '--root', str(self.root)]))
        html = (self.root / 'public/post/index.html').read_text()
        self.assertIn('class="article-meta__reading-time">1 min read</span>', html)

    @unittest.skipUnless(shutil.which('zola'), 'Zola not installed')
    def test_real_build_is_repeatable_and_internal_links_keep_base_path(self):
        self.post('## Heading\n\n[Target](@/target.md)\n\n$u_i + v_j$', '[extra.tex]')
        self.write('content/target.md', '+++\ntitle="Target"\n+++\nTarget')
        original = (self.root / 'content/post.md').read_bytes()
        for _ in range(2):
            self.assertEqual(0, persona.main(['build', '--root', str(self.root)]))
        html = (self.root / 'public/post/index.html').read_text()
        self.assertIn('https://example.org/project/target/', html)
        self.assertIn('$u_i + v_j$', unescape(html))
        self.assertEqual(original, (self.root / 'content/post.md').read_bytes())

    def test_serve_syncs_edits_recovers_errors_and_stops_child_on_sigterm(self):
        self.post('before')
        binary = self.directory / 'bin'
        binary.mkdir()
        state = self.directory / 'child.json'
        stopped = self.directory / 'stopped'
        fake = binary / 'zola'
        fake.write_text('#!' + sys.executable + '\nimport json,os,pathlib,signal,time\n'
                        + f'pathlib.Path({str(state)!r}).write_text(json.dumps({{"cwd":os.getcwd(),"pid":os.getpid()}}))\n'
                        + f'def stop(*args):\n pathlib.Path({str(stopped)!r}).write_text("stopped")\n raise SystemExit(0)\n'
                        + 'signal.signal(signal.SIGTERM,stop)\nwhile True: time.sleep(.1)\n')
        fake.chmod(0o755)
        process = subprocess.Popen([sys.executable, '-B', str(SCRIPTS / 'persona.py'), 'serve', '--root', str(self.root)], env={**os.environ, 'PATH': str(binary) + os.pathsep + os.environ['PATH']}, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        def stop():
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
            process.communicate()
        self.addCleanup(stop)
        def until(predicate):
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if predicate():
                    return
                if process.poll() is not None:
                    self.fail('Preview exited unexpectedly: ' + process.communicate()[1])
                time.sleep(.05)
            self.fail('Timed out waiting for preview synchronization')
        until(state.exists)
        stage = Path(json.loads(state.read_text())['cwd'])
        staged_post = stage / 'content/post.md'
        self.post('after')
        until(lambda: 'after' in staged_post.read_text())
        self.write('config.toml', 'invalid = [')
        time.sleep(.7)
        self.assertIsNone(process.poll())
        self.assertIn('after', staged_post.read_text())
        self.write('config.toml', 'base_url="https://example.org/"')
        self.post('recovered')
        until(lambda: 'recovered' in staged_post.read_text())
        (self.root / 'content/post.md').unlink()
        until(lambda: not staged_post.exists())
        process.terminate()
        self.assertEqual(0, process.wait(timeout=10))
        self.assertTrue(stopped.is_file())
        self.assertFalse(stage.exists())


if __name__ == '__main__':
    unittest.main()
