# How to use this dashboard

This tab is designed to give an overview over patterns of lymphatic metastatic involvement in head & neck cancer. It can - for example - be used to identify correlations between risk factors and occurence of metastases, but also give indications which lymph node levels (LNLs) are frequently involved together.

## Components

### Patient details (top left)

Restrict the included patients by their patient-specific information. E.g. smoking status, whether they have had a neck dissection etc.

<p class="notification is-primary is-light">
    <strong>Note:</strong> All selection criteria here are represented by <i>three-way toggle-buttons</i>. These are buttons that can be in one of three states: <i>positive</i> (+, left), meaning all patients that match this criteria are selected, <i>negative</i> (-, right), meaning all patients that do not show this characteristic are selected and finally the striked "O" which indicates that with respect to this criteria, no selection will be made.
</p>

### Primary tumor (bottom left)

Filter the dataset further by tumor-specific details, like the lateralization of a patient's primary tumor, its location and/or T-category.

Next to the selected subsites and T-categories, this panel also displays how many patients presented with a tumor in the respective subsite / T-category.

<p class="notification is-primary is-light">
    <strong>Note:</strong> Both the subsite and T-category are (de)selected by clicking on the respective label. If it appears white on dark blue ground, it is selected. If it appears dark blue on light blue background, it is deselected.
</p>

### Modalities (center top)

Choose which of the available modalities to include in the visualization. Only patients are considered that have at least one of the selected diagnoses available. One may choose how to combine these - possibly conflicting - diagnoses: 

- logical ``OR``: A lymph node level (LNL) is reported as _metastatic_ or _involved_ as soon as one of the selected diagnoses reports a positive finding. Anything else is reported as _healthy_.
- logical ``AND``: LNL's are reported as involved only when **all** diagnoses agree on positive findings. If that is not the case, meaning that none or not all agree on such a finding, it is reported (rather optimistically) as _healthy_.

### contra- (center left) & ipsilateral (center right)

Here the most important information is visualized. For each side of the neck (ipsilateral being the same side as the tumor, contralateral the opposite) it displays a row for each LNL. From left to right, that row consists of its roman numeral label, a three-way toggle-button to select a subset with a particular involvement pattern and a horizontal stacked bar that displays the ratio of patients with reports of metastases in that LNL (red) to patients with a healthily appearing LNL (green). Numbers to the left and right of that bar plot indicate the absolute numbers and give a brief explanation when hovering over them with a mouse pointer.

### Buttons (bottom right)

From left to right the three buttons here are

- the help button in light blue, opening this very menu
- an info button in light orange that shows how many patients are in the currently narrowed-down subset and that redirects to a list of patients in that subset when pressed
- the compute button in bright orange, which sends a request with the current selections to the server for an update of the visualized statistics