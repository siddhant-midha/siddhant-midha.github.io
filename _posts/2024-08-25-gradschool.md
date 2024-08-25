---
layout: distill
title: Ph.D. applications
description: a mini-guide 
tags: distill formatting
giscus_comments: true
date: 2024-08-25
featured: true

authors:
  - name: Siddhant
    url: "siddhant-midha.github.io"
    affiliations:
      name: IITB

bibliography:  

# Optionally, you can add a table of contents to your post.
# NOTES:
#   - make sure that TOC names match the actual section names
#     for hyperlinks within the post to work correctly.
#   - we may want to automate TOC generation in the future using
#     jekyll-toc plugin (https://github.com/toshimaru/jekyll-toc).
toc:
  # - name: 
    # if a section has subsections, you can add them as follows:
    # subsections:
    #   - name: Example Child Subsection 1
    #   - name: Example Child Subsection 2

# Below is an example of injecting additional post-specific styles.
# If you use this post as a template, delete this _styles block.
_styles: >
  .fake-img {
    background: #bbb;
    border: 1px solid rgba(0, 0, 0, 0.1);
    box-shadow: 0 0px 4px rgba(0, 0, 0, 0.1);
    margin-bottom: 12px;
  }
  .fake-img p {
    font-family: monospace;
    color: white;
    text-align: left;
    margin: 12px 0;
    text-align: center;
    font-size: 16px;
  }

---
compilation of results in the MIPT arena.

## Random quantum circuits

1. [Quantum Zeno Effect and the Many-body Entanglement Transition](https://arxiv.org/pdf/1808.06134.pdf): This paper is one of those starting the discussion on MIPT explicitly: they provide numerics for entanglement entropy dynamics in large-scale Clifford and small Haar-random models sprinkled with measurements. Notably, they perform a scaling analysis of the steady-state EE as well as the dynamics.
2. [Measurement-driven entanglement transition in hybrid quantum circuits](https://arxiv.org/pdf/1901.08092.pdf): This paper continues the discussion initiated previously with extensive numerics on multiple models. What I like most here is the distribution of the stabilizer lengths as the measurement strength is varied -- the entanglement phase transition is _clearly_ elucidated because of continuous vanishing of the peak in the distribution at 'large' lengths. Moreover, the logarithmic correction in the volume law is clearly outlined, and can be explained by this length distribution! Lastly, they carry over the RQC analysis to systematic models -- which lack randomness in (i) measurement locations and/or (ii) unitaries, attempting to make the point that such hybrid circuits will generically show a volume-law to area-law transition. Also, initial state independence. Wink, wink.

## Fermionic Systems

1. [Entanglement in a free fermion chain under continuous monitoring](https://arxiv.org/abs/1804.04638): This paper studies the entanglement dynamics in a free fermion chain under continuous measurement of all occupation numbers with a quasiparticle pair approach. They point out that the volume law is unstable to _any_ $p > 0$ measurement strength, because of finite coherent lifetime under measurement.
2. [Growth of entanglement entropy under local projective measurements](https://arxiv.org/pdf/2109.10837.pdf): If $1/\tau$ is the measurement rate, then these guys show that for a fermionic chain with PBC and monitoring of local number operator, then the critical time $\tau_c$ for the switchover from area to volume law diverges with the length, hence the thermodynamic limit would only exhibit an area-law of the saturated EE!

## Emergent quantum codes

1. [Quantum Error Correction in Scrambling Dynamics and Measurement-Induced Phase Transition](https://arxiv.org/abs/1903.05124)
2. [Dynamical purification phase transitions induced by quantum measurements](https://arxiv.org/abs/1905.05195): This paper formalizes the emergent quantum error correcting code formed by monitored circuits, and lays out the theory for such codes by quantifying the channel capacity in the thermodynamic limit.

## Miscellaneous

1. [Optimized trajectory unraveling for classical simulation of noisy quantum dynamics](https://arxiv.org/pdf/2306.17161.pdf): The MIPT setting is now used in the viewpoint of _simulability_ of the monitored system. The idea is that the volume-law phase is classically difficult to simulate while the area-law is not, so if one can _decrease_ the critical measurement strength required to enter area-law, one makes the quantum system simulable for a larger parameter setting. This paper thus discusses optimized unravellings to perform this task, in both RQCs (by mapping to stat-mech models) and an Ising chain far from integrability.
2. [A numerical study of measurement-induced phase transitions in the Sachdev-Ye-Kitaev model](https://arxiv.org/pdf/2301.05195.pdf): The authors study the MIPT in the all-to-all coupled SYK model by Jordan-Wigner'ing to spins and performing exact diagonalization. Their measurement model consists of first a coin flip to decide whether or not a measurement happens (w/ rate $\Gamma$), then sampling from a Binomial distribution (parameter $p$) to decide which spins to measure. This gives a 2D phase diagram, and it is pointed out that even at $p = 1$ there is a non-zero measurement rate for the entanglement MIPT, whereas the purification MIPT is trivial, marking a concrete distinction.

