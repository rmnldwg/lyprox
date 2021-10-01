{% load mytags %}

# How to use this dashboard

This tab is designed to give an overview over patterns of lymphatic metastatic involvement in head & neck cancer. It can - for example - be used to identify correlations between risk factors and occurence of metastases, but also give indications which lymph node levels (LNLs) are frequently involved together.

## Components

### Patient details (top left)

{% include_md 'dashboard/help_patient.md' %}

### Primary tumor (bottom left)

{% include_md 'dashboard/help_tumor.md' %}

### Modalities (center top)

{% include_md 'dashboard/help_modalities.md' %}

### contra- (center left) & ipsilateral (center right)

Here the most important information is visualized. For each side of the neck (ipsilateral being the same side as the tumor, contralateral the opposite) it displays a row for each LNL. From left to right, that row consists of its roman numeral label, a three-way toggle-button to select a subset with a particular involvement pattern and a horizontal stacked bar that displays the ratio of patients with reports of metastases in that LNL (red) to patients with a healthily appearing LNL (green). Numbers to the left and right of that bar plot indicate the absolute numbers and give a brief explanation when hovering over them with a mouse pointer.

### Buttons (bottom right)

{% include_md 'dashboard/help_buttons.md' %}