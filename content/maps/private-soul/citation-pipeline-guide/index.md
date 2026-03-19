+++
title = 'How to Use Citation in Persona'
date = 2025-03-19
draft = false
[taxonomies]
tags = ['citation', 'pandoc', 'bibtex']
categories = ['private-soul']
[extra]
excerpt = """
A practical guide for writing citation-enabled posts in Persona with Pandoc and BibTeX.
"""
citation_style = "apa"
bibliography = "references.bib"
+++

<p>Persona supports <code>[@cite]</code> through a Pandoc preprocessing pipeline. This post is the working example for authoring and building citation-enabled content <span class="citation" data-cites="zolathemes">(<a href="#ref-zolathemes" role="doc-biblioref">Zola themes</a>)</span>.</p>
<h2 id="prerequisites">Prerequisites</h2>
<p>Install Pandoc and watchexec:</p>
<div class="sourceCode" id="cb1"><pre class="sourceCode bash"><code class="sourceCode bash"><span id="cb1-1"><a href="#cb1-1" aria-hidden="true" tabindex="-1"></a><span class="co"># macOS</span></span>
<span id="cb1-2"><a href="#cb1-2" aria-hidden="true" tabindex="-1"></a><span class="ex">brew</span> install pandoc watchexec</span>
<span id="cb1-3"><a href="#cb1-3" aria-hidden="true" tabindex="-1"></a></span>
<span id="cb1-4"><a href="#cb1-4" aria-hidden="true" tabindex="-1"></a><span class="co"># Ubuntu / Debian</span></span>
<span id="cb1-5"><a href="#cb1-5" aria-hidden="true" tabindex="-1"></a><span class="fu">sudo</span> apt install pandoc</span>
<span id="cb1-6"><a href="#cb1-6" aria-hidden="true" tabindex="-1"></a><span class="ex">cargo</span> install watchexec-cli</span></code></pre></div>
<h2 id="file-structure">File structure</h2>
<p>Keep these files in the same folder:</p>
<ul>
<li><code>index.src.md</code> (authoring source)</li>
<li><code>references.bib</code> (BibTeX database)</li>
<li><code>index.md</code> (generated output, do not edit manually)</li>
</ul>
<h2 id="write-citations-in-.src.md">Write citations in <code>.src.md</code></h2>
<p>Use Pandoc citation syntax in Markdown:</p>
<div class="sourceCode" id="cb2"><pre class="sourceCode markdown"><code class="sourceCode markdown"><span id="cb2-1"><a href="#cb2-1" aria-hidden="true" tabindex="-1"></a>Climate change is accelerating<span class="co">[</span><span class="ot">@ipcc2021</span><span class="co">]</span>.</span>
<span id="cb2-2"><a href="#cb2-2" aria-hidden="true" tabindex="-1"></a>Multiple studies confirm this<span class="co">[</span><span class="ot">@ipcc2021; @nasa2023</span><span class="co">]</span>.</span></code></pre></div>
<p>Set optional citation config in frontmatter under <code>[extra]</code>:</p>
<ul>
<li><code>citation_style = "apa"</code></li>
<li><code>bibliography = "references.bib"</code></li>
</ul>
<h2 id="build-and-serve">Build and serve</h2>
<ul>
<li><p>Generate <code>*.md</code> from all <code>*.src.md</code> files:</p>
<div class="sourceCode" id="cb3"><pre class="sourceCode bash"><code class="sourceCode bash"><span id="cb3-1"><a href="#cb3-1" aria-hidden="true" tabindex="-1"></a><span class="fu">bash</span> scripts/build.sh</span></code></pre></div></li>
<li><p>Live rebuild + local server:</p>
<div class="sourceCode" id="cb4"><pre class="sourceCode bash"><code class="sourceCode bash"><span id="cb4-1"><a href="#cb4-1" aria-hidden="true" tabindex="-1"></a><span class="co"># In one terminal, watch for changes and rebuild:</span></span>
<span id="cb4-2"><a href="#cb4-2" aria-hidden="true" tabindex="-1"></a><span class="fu">bash</span> scripts/watch.sh</span></code></pre></div>
<div class="sourceCode" id="cb5"><pre class="sourceCode bash"><code class="sourceCode bash"><span id="cb5-1"><a href="#cb5-1" aria-hidden="true" tabindex="-1"></a><span class="co"># In a separate terminal, serve with Zola:</span></span>
<span id="cb5-2"><a href="#cb5-2" aria-hidden="true" tabindex="-1"></a><span class="ex">zola</span> serve</span></code></pre></div></li>
</ul>
<h2 id="citation-style-resolution-order">Citation style resolution order</h2>
<p>Priority from highest to lowest:</p>
<ol type="1">
<li>Post frontmatter: <code>[extra] citation_style = "..."</code></li>
<li>Site-level <code>config.toml</code> <code>[extra.persona].citation_style</code></li>
<li>Theme config <code>themes/persona/config.toml</code> <code>[extra.persona].citation_style</code></li>
</ol>
<p>Bundled styles in <code>citation-style/</code>: <code>ieee</code>, <code>apa</code>. Custom styles can be added by placing <code>.csl</code> files in <code>citation-style/</code> and referencing them in frontmatter.</p>
<h2 id="output-and-styling">Output and styling</h2>
<p>The pipeline emits HTML citations and bibliography blocks so SCSS can style stable classes:</p>
<ul>
<li><code>.citation</code></li>
<li><code>.references</code></li>
<li><code>.csl-entry</code></li>
<li><code>.csl-left-margin</code></li>
<li><code>.csl-right-inline</code></li>
</ul>
<p>Inline citations anchor to bibliography entries, and the bibliography heading is rendered inside the refs container as “Bibliography”.</p>
<div id="refs" class="references csl-bib-body hanging-indent" data-entry-spacing="0" data-line-spacing="2" role="list">
<h2 class="unnumbered" id="bibliography">Bibliography</h2>
<div id="ref-zolathemes" class="csl-entry" role="listitem">
Zola themes. <a href="https://www.getzola.org/themes/">https://www.getzola.org/themes/</a>
</div>
</div>
