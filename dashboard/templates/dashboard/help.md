{% load mytags %}

# The Dashboard

Here, one can visualize the patients in the database. The aim is to make it easy to see and understand a complex dataset with regard to lymphatic involvement in head & neck cancer. Ideally, it is "hypothesis-generating", meaning that you, the user, becomes curious and asks questions about certain correlations (or even causations). Some of them will be explorable using this interface, while others maybe not. In the latter case we encourage you to [download]({% url 'patients:download' %}) the database and test your ideas and hypotheses with your own tools.

<p class="notification is-warning is-light">
    <strong>Note:</strong> This is NOT a risk prediction. All we do here is visualize data of previously seen patients. For actual risk predictions for individual and newly diagnosed patients, check out our <a href="https://www.nature.com/articles/s41598-021-91544-1">paper on modelling tumor progression</a> or wait a bit, since we are thinking about implementing it also here.
</p>

## Components

### Patient details (top left)

{% include_md 'dashboard/help_patient.md' %}

### Primary tumor (bottom left)

{% include_md 'dashboard/help_tumor.md' %}

### Modalities (center top)

{% include_md 'dashboard/help_modalities.md' %}

### contra- (center left) & ipsilateral (center right)

{% include_md 'dashboard/help_involvement.md' %}

### Buttons (bottom right)

{% include_md 'dashboard/help_buttons.md' %}