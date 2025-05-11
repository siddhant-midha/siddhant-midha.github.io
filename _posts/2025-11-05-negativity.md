---
layout: distill
title: Entanglement Negativity
description: 
tags: etna
giscus_comments: true
date: 2025-05-11
featured: true

authors:
  - name: Siddhant
    url: "siddhant-midha.github.io"
    affiliations:
      name: PU

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

## Setting 

We are interested in quantum systems defined on a system $$S = A \cup B$$, and quantifying the entanglement between the A and B subsystems. Let $$\mathcal{H}_X$$ denote the Hilbert space of register $$X$$, so $$\mathcal{H}_S = \mathcal{H}_A \otimes \mathcal{H}_B$$. A quantum state on $$X$$ is a unit-trace positive operator $$\rho\in \mathcal{D}(\mathcal{H}_X)$$. A state is pure if it is rank-one, $$\rho = |\psi\rangle \langle \psi|$$. Owing to the annoyance caused by writing kets and bras without the ``physics`` package, I will just write $$\psi$$ to denote the density matrix of a pure state.

Let us first set the ground and talk about the simpler case. For _pure_ states, the notion of entanglement is very well defined and well captured by von-Neumann entropy. Specifically, if I define the reduced state of A as $$\rho_A = tr_B(\psi)$$, then the entropy $$S(\rho_A) = -tr(\rho_A \log{\rho_A})$$ captures the amount of entanglement in the bipartition $$A \cup B$$. This is often called the entropy of entanglement. Operationally, in the limit of a large number of copies of the state, this quantity quantifies 

- _dilution_ the asymptotic number of Bell pairs between A and B needed (per copy) to prepare the state via local operations and classical communications (LOCC)
- _distillation_ the asymptotic number of Bell pairs that can be created (per copy) from the state via LOCC

Hence, the entropy of entanglement is a fundamental quantity for pure states, and does a good job at characterizing the entanglement.

## Mixed States 

It is trivial to see that the von-Neumann entropy, or any Renyi entropy for that matter, is not a good object to characterize mixed-state entanglement. A counter example is given by the fully mixed state, exhibiting no correlations of any kind yet scoring high on entropies. To build up the story for mixed state, we must first understand what's _not_ entangled. Well, a pure state is not entangled if it can be written as a product across that bipartition. It turns out a mixed state is not entangled if it can be written in the following form,

\begin{equation}
    \rho_{AB} = \sum_i p_i \rho_A^i \otimes \rho_B^i
\end{equation}

and any state of the form above is said to be _separable_ (with respect to that bipartition). The reason any such object is not entangled (again, across that bipartition!) is because such a state can always be prepared by LOCC on that bipartition, and hence displays classical correlations. One cannot create entanglement via LOCC. Specifically, there _could be_ correlations in the state, but they are classical and the extent of those correlations is quantified by the Shannon entropy of the distribution $$p$$. 

## PPT Test

Well then, I give you the state $$\rho_{AB}$$, how do you tell me if it is entangled? One way, and perhaps the most prominent way, to answer this question was given in [1] by Peres. Specifically, they outline the following: **if a state is separable, it's partial transpose must be positive**. Let us unpack this. What is the transpose? Well, it's a map $$A \mapsto A^{T}$$ such that $$[A^{T}]_{ij} := [A]_{ji}$$. A _partial_ transpose is when we transpose only the $$A(B)$$ subsystem, we denote this as $$\rho^{T_A}$$. 


The proof is trivial, note that if $$\sigma$$ is a valid density matrix, then so is $$\sigma^T$$. Hence, upon partial transposing a separable state, we get another valid density matrix, which must be positive. Hence, any separable state has a positive partial tranpose---we say that it _passes_ the PPT test. 


If a state does not pass PPT, we denote it to be NPT. Then, we can say that a state which is NPT must be entangled. However, the chain of impliciations must be paid attention to. There _do exist_ entangled states which are PPT. Thus, if I give you a state and it passes PPT, a priori we cannot say if it is entangled or not. However, if it _violates_ PPT and is thus NPT, then we say that it is entangled.

\begin{equation}
\text{Separable} \implies \text{PPT}
\end{equation}

\begin{equation}
\text{NPT} \implies \text{Entangled}
\end{equation}

## Negativity
We then perform the following task. Take the state $$\rho_{AB}$$, partial transpose it $$\rho_{AB}^{T_A}$$, and find it's spectrum $$\Lambda(\rho_{AB}^{T_A}) = \{\lambda_i\}_i$$. Then, define,

\begin{equation}
\mathcal{N}(\rho_{AB}) := \sum_{\lambda_i : \lambda_i < 0} |\lambda_i|
\end{equation}

If this quantity is positive, we have entanglement. This is called _negativity_. A nicer way to write this down is,

\begin{equation}
\mathcal{N}(\rho_{AB}) := \frac{\|\rho_{AB}^{T_A}\|_1 - 1}{2}
\end{equation}


where $$\|O\|_1 := tr\sqrt{O^{\dagger}O}$$ is the trace norm. 

## References

[1] Peres, Asher. "Separability criterion for density matrices." Physical Review Letters 77.8 (1996): 1413.
[2] Horodecki, Michał, Paweł Horodecki, and Ryszard Horodecki. "Separability of n-particle mixed states: necessary and sufficient conditions in terms of linear maps." Physics Letters A 283.1-2 (2001): 1-7.