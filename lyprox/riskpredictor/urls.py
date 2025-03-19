"""URLs related to the `riskpredictor` prediction app.

This app is reachable under the URL ``https://lyprox.org/riskpredictor``. Like the
`dataexplorer`, this includes a dashboard and a help page.
"""

from django.urls import path

from lyprox.riskpredictor import views

app_name = "riskpredictor"
urlpatterns = [
    path("add/", views.AddCheckpointModelView.as_view(), name="add"),
    path("list/", views.ChooseCheckpointModelView.as_view(), name="list"),
    path("<int:checkpoint_pk>/", views.render_risk_prediction, name="dashboard"),
    path("<int:checkpoint_pk>/ajax/", views.update_risk_prediction, name="ajax"),
    path("help/", views.help_view, name="help"),
    path("test/", views.test_view, name="test"),
]
