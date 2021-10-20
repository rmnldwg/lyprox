![img](./core/static/github-social-card.png)


## What is LyProX?

It is a [Django](https://www.djangoproject.com/) web app that displays the detailed patterns of lymphatic metastases in head & neck cancer and allows one to explore the underlying dataset(s) in much detail. It is hosted under the URL [http://www.lyprox.org](https://www.lyprox.org).


## Our Goal

With the interface we primarily aim to make our extracted dataset easily accessible (it can also be downloaded as CSV table as soon as we have submitted our paper on the work) and motivate other clinical researchers on the field to also share their raw data.

This, in turn would enable us (or anyone, really) to build more accurate and precise tumor progression models. E.g. like previous work on using Bayesian networks to predict the personalized probability of involvement by [Pouymayou et al., 2019](https://doi.org/10.1088/1361-6560/ab2a18) or our recent publication on this issue using hidden Markov models and thereby introducing an explicit way of modelling time by [Ludwig et al., 2021](https://doi.org/10.1038/s41598-021-91544-1).


## How to contribute

There are two ways you can contribute to this project:

1. If you are a clinical researcher in the field and would like to share your data with us, please get in touch with us via email: [roman.ludwig@usz.ch](mailto:roman.ludwig@usz.ch).
2. The other way is by contributing to this repository, e.g. if you are a software developer. I guess this is somewhat unlikely, due to the very specific scope of this Django app, but we still welcome any contribution.


## Run this interface locally

If you want to host your data yourself or try how your data looks in the web app without committing to an upload, feel free to follow [these instructions](run-local.md) to get it up and running on your local machine.