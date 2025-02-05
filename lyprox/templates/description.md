# The Goal

Head & neck squamous cell carcinomas (HNSCCs) frequently metastasize through the lymphatic network. Hence, radiation oncologists often have to decide whether to include clinically healthy lymph node levels into the clinical target volume (CTV). Similarly, surgeons have to decide which lymph node levels to resect.

To aid them in their decision, the prevalence of metastatic involvement for HNSCC has been reported in numerous publications ([1],[2],[3],[4],[5]). However, the detailed patterns of progression, i.e. correlations between frequently metastatic lymph node levels as well as primary tumor characteristics, remain insufficiently quantified. As a consequence, clinical guidelines on elective CTV definition are mostly based on prevalence of lymph node level involvement. Data that would allow for further personalization of CTV definition based on a patient's individual state of tumor progression is not available.

To tackle this, we extracted a dataset of 287 oropharyngal SCC patients treated at the University Hospital Zürich. We report on a patient-individual basis the patterns of lymphatic metastatic progression together with primary tumor and patient risk factors. This dataset has been [described and published]({% url 'index' %}#publications) in great detail.

To make this data more accessible and especially easier to understand and draw conclusions from, we developed this web-based interface and in particular the [data explorer dashboard]({% url 'dataexplorer:dashboard' %}) where one can interact with the underlying data in a more intuitive way.

More recently, we have received the underlying data of a study published by [Bauwens _et al._](https://doi.org/10.1016/j.radonc.2021.01.028) via communications with Prof. Vincent Grégoire. Their dataset is now also freely explorable in LyProX. Beyond that, we are in the process of visualizing even more datasets from other institutions in the near future.


[1]: https://doi.org/10.1016/j.radonc.2019.01.018
[2]: https://doi.org/10.1002/1097-0142(197206)29:6<1446::AID-CNCR2820290604>3.0.CO;2-C
[3]: https://doi.org/10.1016/j.ijom.2006.10.014
[4]: https://doi.org/10.1002/hed.2880120302
[5]: https://doi.org/10.1002/1097-0142(19900701)66:1<109::AID-CNCR2820660120>3.0.CO;2-A


# Features

Currently, the functions that have been implemented in this web-based application are as follows: Anyone can freely

- view the details of every patient in the two public datasets in the "[Patients]({# url 'patients:list' #})" tab
- export and download the two public datasets as CSV files via the "[Datasets]({# url 'patients:dataset_list' #})" tab
- visualize the correlations in the patterns of lymphatic progression in an interactive dashboard under the "[Data Explorer]({% url 'dataexplorer:dashboard' %})" tab
- choose a model and get predictions for the risk of microscopic involvement, given a personalized diagnosis in the "[Risk Predictor]({# url 'riskpredictor:list' #})" tab.


# Roadmap

As hinted at earlier, more data is planned to be released. We have received another two additional datasets of detailed lymphatic progression patterns that we will publish in the coming months. We will also collect more data at our own institution, the University Hospital Zurich, that we will share on LyProX. And we have signed data sharing agreements or are in discussions with yet another two research groups. The goal is to have a multi-centric, multinational dataset of several thousand patients, each with detailed information on their lymphatic involvement patterns.

In the long term, we would also like to extend the functionality of the interface to allow our collaborators and us to directly enter patient data into LyProX. That way, multiple institutions and researchers could collectively add data in a seamless manner.

If you are interested in our project and would like to learn more, and/or contribute to it in some form, feel free to reach out to us via an email to [roman.ludwig@usz.ch](mailto:roman.ludwig@usz.ch).
