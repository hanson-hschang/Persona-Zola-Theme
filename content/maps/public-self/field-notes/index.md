+++
title = "Field Notes: from observations to reproducible results"
description = "An illustrative academic project showing how to present a research question, a method, and its evidence with Persona."
date = 2026-09-21
template = "post.html"
weight = 1

[extra.post]
draft = false # Set true to hide from automatic lists while keeping this URL available.
thumbnail = "workflow.svg"
thumbnail_alt = "Observation-to-evidence workflow"
kind = "Template demonstration"
subtitle = "A clear path through the question, the method, and the evidence."
authors = [
  { name = "Alex Morgan", affiliations = "1", equal = true },
  { name = "Sam Rivera", affiliations = "1", equal = true },
]
affiliations = [{ id = "1", name = "Example Research Lab" }]
author_note = "* Equal contribution. Illustrative project and authors."
links = [
  { name = "Read the overview", url = "#post-abstract", icon_class = "bi bi-file-earmark-text" },
  { name = "Source", url = "https://github.com/hanson-hschang/Persona-Zola-Theme", icon_class = "bi bi-github" },
  { name = "Cite", url = "#post-citation", icon_class = "bi bi-quote" },
]
related = [{ title = "More from Public Self", url = "@/maps/public-self/_index.md" }]
abstract = """
Research is easier to understand when the connection between a question and its
evidence is visible. **Field Notes** is an illustrative project about making that
connection explicit: record observations, describe the transformations applied to
them, and preserve the context needed to interpret the result.

This page demonstrates a reusable research presentation. Its diagrams describe a
workflow, rather than measured experimental results. Replace the example text and
assets with your own research.
"""
gallery_title = "A closer look"
gallery = [
  { src = "workflow.svg", alt = "Three stages linked from left to right: observe, organize, and explain.", width = 1200, height = 480, caption = "**The full workflow.** Each stage retains a connection to the observations that came before it." },
  { src = "evidence.svg", alt = "Three rows connect a research question to its supporting record and an interpretation.", width = 1200, height = 600, caption = "**An evidence map.** Trace each interpretation back to the record that supports it." },
]
bibtex = """
@misc{fieldnotes_example,
  title  = {Field Notes: From Observations to Reproducible Results},
  author = {Morgan, Alex and Rivera, Sam},
  note   = {Illustrative project for the Persona theme; not a publication}
}
"""

[extra.post.teaser]
src = "workflow.svg"
alt = "A workflow moving from observations through organized records to an explanation, with provenance retained throughout."
width = 1200
height = 480
caption = "From a first observation to a shareable result, keep the reasoning visible."
+++

## The research question

How can a research page help a reader follow an idea all the way from its motivation
to its evidence? Start with the question, explain what the method does, and give the
reader a way to inspect the supporting material.

The page should serve both readers who need a quick overview and those who want to
reproduce the work. The abstract introduces the idea; the sections below provide
space for the details.

## Method

1. **Observe.** Describe what was collected, how it was collected, and what was left out.
2. **Organize.** Make the transformations and assumptions explicit.
3. **Explain.** Connect each conclusion to the record that supports it.

Keep figures close to the argument they support. Use captions to say what the reader
should notice, and alternative text to describe the information in the figure.

## What to report

| Part of the study | Details to include |
| :--- | :--- |
| Data | Collection conditions, coverage, and access |
| Method | Assumptions, transformations, and implementation |
| Evaluation | Baselines, uncertainty, and failure cases |
| Reproduction | Dependencies, instructions, and artifacts |

### Scope and limitations

This is a template example, not an empirical study. There are no measured outcomes
or performance claims. For your own project, use this space to explain where the
method works, where it fails, and which questions remain open.
