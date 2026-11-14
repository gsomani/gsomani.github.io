---
layout: post
title: "Are emotions against logic?"
date: 2026-11-14
tags: [decision-making, reinforcement-learning, bayesian, statistics]
math: true
---

It's common to say that emotions work against logic. The picture I ended up with is more interesting: emotions and reasoning are two parts of one decision system, and the conflicts between them come from a mismatch of tuning, not a war of principles.

## Logic needs something to aim at

Logic only tells you what follows from your premises. It cannot tell you what to want. Goals and values have to come from somewhere, and emotions supply many of them. People whose emotional processing is damaged while their reasoning stays intact often decide *worse*, not better. They can deliberate endlessly over trivial choices because nothing feels more important than anything else.

## Value functions and search

Chess makes the structure clearer. A strong player has intuition for good positions, which is a learned **value function**. They also calculate, searching a game tree a few moves deep and then trusting intuition at the end of each line. Nobody can search to the end of the game, so every real player combines the two. AlphaZero is built exactly this way: a value network for intuition plus tree search for calculation.

Seen this way, intuition and logic aren't opponents. They play the roles of value function and search, and the real question is how far to look ahead before trusting the estimate.

## Levels of greed

Everyone runs something like a greedy algorithm. What differs is the level of greed: how far into the future you look. Some people value things by their present state; others invest with no guarantee, judging value by what they can calculate about the future.

Neither extreme works. Zero lookahead ignores consequences. Infinite lookahead is impossible, and the future grows more uncertain the further you go, because the world, like a chess opponent, keeps moving. There should be a balance point.

Reinforcement learning makes this precise with the **discount factor** $$\gamma \in [0, 1]$$. A reward $$k$$ steps ahead is weighted by $$\gamma^k$$. $$\gamma = 0$$ is pure greed, and $$\gamma$$ near 1 weighs the far future almost equally with the present. Choosing the horizon is also a bias–variance tradeoff. Short horizons rely heavily on your value estimate, which may be biased. Long horizons stack up many uncertain steps, which adds variance.

## Uncertainty produces discounting

Suppose that at each step there is an independent probability $$p$$ that the world changes under you: the game ends, or your plan becomes worthless. To collect the reward $$r_t$$ at step $$t$$, you must survive $$t$$ such checks, which happens with probability $$(1-p)^t$$. By linearity of expectation:

$$
\mathbb{E}[\text{total}] = \sum_{t} (1-p)^t \, r_t
$$

This is exactly a discounted sum with $$\gamma = 1 - p$$.

So discounting the future isn't impatience. It is the correct response to uncertainty. The effective planning horizon is about $$1/p$$ steps: if there's a 10% chance per step that things shift, looking far beyond 10 steps ahead buys little.

## Proxies and Goodhart's law

The same idea applies to the problem itself. Who says the problem we are solving is the real problem? Usually it's a proxy for some deeper goal, and choosing to optimize it is itself a greedy step.

This is **Goodhart's law**: when a measure becomes a target, it stops being a good measure. It's the same mechanism as before. A proxy objective is an estimate of the true goal, just as a position evaluation is an estimate of who will win. Optimization pressure amplifies whatever errors the estimate has. A deep chess search against a flawed evaluation steers straight into the positions where the evaluation is most wrong, and choosing the best of many noisy estimates tends to pick the overestimated ones. Horizon and proxy are two faces of one problem: how much to trust an estimate in place of the real thing.

## Intuition as a prior

Another way to see all this is Bayesian. Intuition acts like a prior: it lets you decide well from few samples. If the prior is well tuned, you converge quickly. If you know nothing, Jaynes' maximum entropy principle says to start from the least committal prior consistent with what you do know.

This can be made exact in bits. If the truth is one hypothesis and your prior gives it probability $$q$$, you need roughly $$-\log_2 q$$ bits of evidence to become confident in it. Low entropy alone doesn't help; what matters is how much probability you put on the truth. A confident prior on the *wrong* answer makes $$q$$ tiny and costs many bits. Averaged over possible truths $$p$$, the cost is the cross-entropy, which splits into two parts:

$$
H(p, q) = H(p) + D_{\mathrm{KL}}(p \,\|\, q)
$$

The entropy term is how uncertain the world really is. The KL term is how wrong your prior is. Good intuition means low KL, not just low entropy.

This also separates *deciding* from *proving*. To act, you only need to believe one option beats the others in expectation, and ten samples might do that. To convince other people, your evidence has to overcome *their* priors, which can take a hundred.

## Do frequentists use priors too?

On the face of it, frequentist methods use no priors. In practice, choosing a model class, a regularizer, or a significance threshold all encode prior beliefs. Even a "flat" prior isn't neutral: flat in $$\theta$$ is not flat in $$\log \theta$$.

Ridge regression is the cleanest example. It minimizes

$$
\|y - Xw\|^2 + \lambda \|w\|^2,
$$

which prefers small weights. That preference is itself a bet about the world: outputs usually depend smoothly on inputs, and huge weights often come from fragile cancellations between nearly collinear features rather than from real effects. With the SVD $$X = U \Sigma V^\top$$, least squares gives each component as $$w_i = u_i^\top y / \sigma_i$$, so noise along directions with tiny $$\sigma_i$$ is amplified enormously. Ridge tames exactly those directions.

Two exercises I'm still working through by hand:

1. Show that ridge regression is the MAP estimate of $$w$$ under Gaussian noise and a Gaussian prior on $$w$$, and find $$\lambda$$ in terms of the two variances.
2. Find what replaces $$1/\sigma_i$$ in the ridge solution $$w = (X^\top X + \lambda I)^{-1} X^\top y$$, and check its behavior when $$\sigma_i^2 \gg \lambda$$ and when $$\sigma_i^2 \ll \lambda$$.

## Back to the question

Emotions discount the future steeply because they were calibrated for a world where $$p$$ was high. Food spoiled, predators appeared, and life was short, so grabbing the immediate reward was close to rational. For many modern decisions, such as savings, careers, and long projects, $$p$$ is much lower, and the same setting now looks like irrationality.

So emotions aren't fundamentally against logic. Their logic is sound, an accumulating value estimate with a discount factor and a prior, but their parameters were tuned for a different world. Conflict appears when the situation is out of distribution: delayed rewards, abstract stakes, or a world more stable than the one our instincts expect.
