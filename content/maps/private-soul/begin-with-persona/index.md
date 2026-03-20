+++
title = 'Begin with Persona'
date = 2025-03-17
draft = false
[taxonomies]
tags = ['website', 'blog']
categories = ['blogs', 'private-soul']
[extra]
excerpt = """
A step-by-step tutorial on how to start a website using the Persona theme: from installation and configuration to segment setup and full theme customization.
"""
bibliography = "references.bib"
+++

<p>This is a step-by-step tutorial on how to start a website using the Persona, a Zola theme <span class="citation" data-cites="zolathemes">[<a href="#ref-zolathemes" role="doc-biblioref">1</a>]</span>. It covers the basics of setting up your site, creating content, and customizing the appearance to make it your own.</p>
<h2 id="setting-up-your-site">Setting Up Your Site</h2>
<p>After <a href="https://github.com/hanson-hschang/Persona-Zola-Theme#-installation">installing Persona</a>, configure your <code>config.toml</code>:</p>
<div class="sourceCode" id="cb1"><pre class="sourceCode toml"><code class="sourceCode toml"><span id="cb1-1"><a href="#cb1-1" aria-hidden="true" tabindex="-1"></a><span class="co"># The URL this site will be built for</span></span>
<span id="cb1-2"><a href="#cb1-2" aria-hidden="true" tabindex="-1"></a><span class="dt">base_url</span> <span class="op">=</span> <span class="st">&quot;https://yourdomain.com&quot;</span></span>
<span id="cb1-3"><a href="#cb1-3" aria-hidden="true" tabindex="-1"></a></span>
<span id="cb1-4"><a href="#cb1-4" aria-hidden="true" tabindex="-1"></a><span class="co"># The basic site information</span></span>
<span id="cb1-5"><a href="#cb1-5" aria-hidden="true" tabindex="-1"></a><span class="dt">title</span> <span class="op">=</span> <span class="st">&quot;Your Site Name&quot;</span></span>
<span id="cb1-6"><a href="#cb1-6" aria-hidden="true" tabindex="-1"></a><span class="dt">author</span> <span class="op">=</span> <span class="st">&quot;Your Name&quot;</span></span>
<span id="cb1-7"><a href="#cb1-7" aria-hidden="true" tabindex="-1"></a><span class="dt">description</span> <span class="op">=</span> <span class="st">&quot;Your personal resume, portfolio and blog&quot;</span></span>
<span id="cb1-8"><a href="#cb1-8" aria-hidden="true" tabindex="-1"></a></span>
<span id="cb1-9"><a href="#cb1-9" aria-hidden="true" tabindex="-1"></a><span class="kw">[extra]</span></span>
<span id="cb1-10"><a href="#cb1-10" aria-hidden="true" tabindex="-1"></a></span>
<span id="cb1-11"><a href="#cb1-11" aria-hidden="true" tabindex="-1"></a><span class="kw">[extra.persona]</span></span>
<span id="cb1-12"><a href="#cb1-12" aria-hidden="true" tabindex="-1"></a><span class="co"># Note: landing page title and subtitles are configured in `content/_index.md`</span></span>
<span id="cb1-13"><a href="#cb1-13" aria-hidden="true" tabindex="-1"></a></span>
<span id="cb1-14"><a href="#cb1-14" aria-hidden="true" tabindex="-1"></a><span class="co"># Social links</span></span>
<span id="cb1-15"><a href="#cb1-15" aria-hidden="true" tabindex="-1"></a><span class="dt">social_links</span> <span class="op">=</span> <span class="op">[</span></span>
<span id="cb1-16"><a href="#cb1-16" aria-hidden="true" tabindex="-1"></a>  <span class="op">{ </span><span class="dt">name</span><span class="op"> =</span> <span class="st">&quot;GitHub&quot;</span><span class="op">, </span><span class="dt">url</span><span class="op"> =</span> <span class="st">&quot;https://github.com/yourusername&quot;</span><span class="op">, </span><span class="dt">icon_class</span><span class="op"> =</span> <span class="st">&quot;bi bi-github&quot;</span><span class="op"> },</span></span>
<span id="cb1-17"><a href="#cb1-17" aria-hidden="true" tabindex="-1"></a>  <span class="op">{ </span><span class="dt">name</span><span class="op"> =</span> <span class="st">&quot;LinkedIn&quot;</span><span class="op">, </span><span class="dt">url</span><span class="op"> =</span> <span class="st">&quot;https://linkedin.com/in/yourprofile&quot;</span><span class="op">, </span><span class="dt">icon_class</span><span class="op"> =</span> <span class="st">&quot;bi bi-linkedin&quot;</span><span class="op"> },</span></span>
<span id="cb1-18"><a href="#cb1-18" aria-hidden="true" tabindex="-1"></a>  <span class="op">{ </span><span class="dt">name</span><span class="op"> =</span> <span class="st">&quot;Twitter-X&quot;</span><span class="op">, </span><span class="dt">url</span><span class="op"> =</span> <span class="st">&quot;https://x.com/yourusername&quot;</span><span class="op">, </span><span class="dt">icon_class</span><span class="op"> =</span> <span class="st">&quot;bi bi-twitter-x&quot;</span><span class="op"> },</span></span>
<span id="cb1-19"><a href="#cb1-19" aria-hidden="true" tabindex="-1"></a><span class="op">]</span></span>
<span id="cb1-20"><a href="#cb1-20" aria-hidden="true" tabindex="-1"></a></span>
<span id="cb1-21"><a href="#cb1-21" aria-hidden="true" tabindex="-1"></a><span class="co"># Contact information</span></span>
<span id="cb1-22"><a href="#cb1-22" aria-hidden="true" tabindex="-1"></a><span class="dt">contact_infos</span> <span class="op">=</span> <span class="op">[</span></span>
<span id="cb1-23"><a href="#cb1-23" aria-hidden="true" tabindex="-1"></a>  <span class="op">{ </span><span class="dt">item</span><span class="op"> =</span> <span class="st">&quot;_navigation&quot;</span><span class="op">, </span><span class="dt">content</span><span class="op"> =</span> <span class="st">&quot;Contact&quot;</span><span class="op">, </span><span class="dt">icon_class</span><span class="op"> =</span> <span class="st">&quot;bi bi-chat-text&quot;</span><span class="op"> },</span> <span class="co"># Special item for header navigation (REQUIRED)</span></span>
<span id="cb1-24"><a href="#cb1-24" aria-hidden="true" tabindex="-1"></a>  <span class="op">{ </span><span class="dt">item</span><span class="op"> =</span> <span class="st">&quot;Name&quot;</span><span class="op">, </span><span class="dt">content</span><span class="op"> =</span> <span class="st">&quot;Your Name&quot;</span><span class="op">, </span><span class="dt">icon_class</span><span class="op"> =</span> <span class="st">&quot;bi bi-person&quot;</span><span class="op"> },</span></span>
<span id="cb1-25"><a href="#cb1-25" aria-hidden="true" tabindex="-1"></a>  <span class="op">{ </span><span class="dt">item</span><span class="op"> =</span> <span class="st">&quot;Location&quot;</span><span class="op">, </span><span class="dt">content</span><span class="op"> =</span> <span class="st">&quot;Your City, Country&quot;</span><span class="op">, </span><span class="dt">icon_class</span><span class="op"> =</span> <span class="st">&quot;bi bi-geo-alt&quot;</span><span class="op"> },</span></span>
<span id="cb1-26"><a href="#cb1-26" aria-hidden="true" tabindex="-1"></a>  <span class="op">{ </span><span class="dt">item</span><span class="op"> =</span> <span class="st">&quot;Email&quot;</span><span class="op">, </span><span class="dt">content</span><span class="op"> =</span> <span class="st">&quot;your.email@example.com&quot;</span><span class="op">, </span><span class="dt">icon_class</span><span class="op"> =</span> <span class="st">&quot;bi bi-envelope&quot;</span><span class="op"> },</span></span>
<span id="cb1-27"><a href="#cb1-27" aria-hidden="true" tabindex="-1"></a>  <span class="op">{ </span><span class="dt">item</span><span class="op"> =</span> <span class="st">&quot;Phone&quot;</span><span class="op">, </span><span class="dt">content</span><span class="op"> =</span> <span class="st">&quot;+0 (123) 456-7890&quot;</span><span class="op">, </span><span class="dt">icon_class</span><span class="op"> =</span> <span class="st">&quot;bi bi-phone&quot;</span><span class="op"> },</span></span>
<span id="cb1-28"><a href="#cb1-28" aria-hidden="true" tabindex="-1"></a><span class="op">]</span></span></code></pre></div>
<p>Modify the landing page content in <code>content/_index.md</code>:</p>
<div class="sourceCode" id="cb2"><pre class="sourceCode toml"><code class="sourceCode toml"><span id="cb2-1"><a href="#cb2-1" aria-hidden="true" tabindex="-1"></a><span class="dt">title</span> <span class="op">=</span> <span class="st">&quot;Presented Site Name&quot;</span></span>
<span id="cb2-2"><a href="#cb2-2" aria-hidden="true" tabindex="-1"></a><span class="dt">template</span> <span class="op">=</span> <span class="st">&quot;index.html&quot;</span></span>
<span id="cb2-3"><a href="#cb2-3" aria-hidden="true" tabindex="-1"></a><span class="kw">[extra]</span></span>
<span id="cb2-4"><a href="#cb2-4" aria-hidden="true" tabindex="-1"></a><span class="dt">icon_class</span> <span class="op">=</span> <span class="st">&quot;bi bi-house&quot;</span></span>
<span id="cb2-5"><a href="#cb2-5" aria-hidden="true" tabindex="-1"></a><span class="dt">subtitles</span> <span class="op">=</span> <span class="st">&quot;Item 1, Item 2, Item 3&quot;</span></span></code></pre></div>
<p>Also update your assets in <code>static/assets/img/</code>:</p>
<ul>
<li><a href="https://en.wiktionary.org/wiki/hero_image">hero image</a>: <code>background.jpg</code></li>
<li><a href="https://en.wikipedia.org/wiki/Favicon">favicon</a>: <code>favicon.ico</code></li>
<li><a href="https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariWebContent/ConfiguringWebApplications/ConfiguringWebApplications.html">apple touch icon</a>: <code>apple-touch-icon.png</code></li>
</ul>
<h2 id="creating-content">Creating Content</h2>
<p>Once your site is configured, you can start creating content by adding Markdown files to the <code>content</code> directory. Each file represents a page or blog post, and you can use frontmatter to specify metadata such as the title, date, tags, and categories.</p>
<h2 id="customizing-appearance">Customizing Appearance</h2>
<p>The Persona theme provides extensive options to customize colors and fonts by overriding CSS variables in <code>sass/assets/stylesheet/_custom.scss</code> without modifying the core theme files. For example, to change the accent color, heading color, and title font size, you can use the following CSS:</p>
<div class="sourceCode" id="cb3"><pre class="sourceCode css"><code class="sourceCode css"><span id="cb3-1"><a href="#cb3-1" aria-hidden="true" tabindex="-1"></a><span class="co">/* sass/assets/stylesheet/_custom.scss */</span></span>
<span id="cb3-2"><a href="#cb3-2" aria-hidden="true" tabindex="-1"></a><span class="in">:root</span> {</span>
<span id="cb3-3"><a href="#cb3-3" aria-hidden="true" tabindex="-1"></a>  <span class="va">--color-accent</span>: <span class="cn">#FF5F05</span><span class="op">;</span>   <span class="co">/* Override accent color to vibrant orange */</span></span>
<span id="cb3-4"><a href="#cb3-4" aria-hidden="true" tabindex="-1"></a>  <span class="va">--color-heading</span>: <span class="cn">#13294B</span><span class="op">;</span>  <span class="co">/* Override heading color to dark blue */</span></span>
<span id="cb3-5"><a href="#cb3-5" aria-hidden="true" tabindex="-1"></a>  <span class="va">--font-size-title</span>: <span class="dv">72</span><span class="dt">px</span><span class="op">;</span>   <span class="co">/* Increase title font size for more impact */</span></span>
<span id="cb3-6"><a href="#cb3-6" aria-hidden="true" tabindex="-1"></a>}</span></code></pre></div>
<p><strong>Available Customization Variables:</strong></p>
<p>Colors:</p>
<ul>
<li><code>--background-color</code>: Background color for the entire website</li>
<li><code>--default-color</code>: Default text color</li>
<li><code>--heading-color</code>: Color for headings and titles</li>
<li><code>--accent-color</code>: Brand color for buttons, links, and highlights</li>
<li><code>--surface-color</code>: Background for cards and boxed elements</li>
<li><code>--contrast-color</code>: Text color for use against accent colors</li>
</ul>
<p>Typography:</p>
<ul>
<li>Font Families
<ul>
<li><code>--default-font</code>: Main font family for body text</li>
<li><code>--heading-font</code>: Font family for headings</li>
<li><code>--nav-font</code>: Font family for navigation</li>
</ul></li>
<li>Font Sizes
<ul>
<li><code>--footer-font-size</code>: Footer text size (default: 14px)</li>
<li><code>--normal-font-size</code>: Base font size (default: 16px)</li>
<li><code>--subtitle-font-size</code>: Subtitle font size (default: 24px)</li>
<li><code>--heading-font-size</code>: Base font size for heading (default: 32px)</li>
<li><code>--title-font-size</code>: Base font size for title (default: 64px)</li>
</ul></li>
</ul>
<p>See <code>sass/assets/stylesheet/_variables.scss</code> for the complete list of customizable variables with detailed descriptions (the compiled CSS is emitted under <code>public/assets/stylesheet/</code> at build time).</p>
<h2 id="conclusion">Conclusion</h2>
<p>Starting a website with the Persona theme is a great way to share your thoughts and ideas with the world. With its user-friendly setup and extensive customization options, you can create a unique and engaging site that reflects your personality and style.</p>
<div id="refs" class="references csl-bib-body" role="list">
<h2 class="unnumbered" id="bibliography">Bibliography</h2>
<div id="ref-zolathemes" class="csl-entry" role="listitem">
<div class="csl-left-margin">[1] </div><div class="csl-right-inline"><a href="https://www.getzola.org/themes/">Zola themes</a>, </div>
</div>
</div>
