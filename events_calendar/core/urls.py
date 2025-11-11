from django.urls import path
from . import views # import our view functions
urlpatterns = [
    path("", views.home, name="home"), # "/" -> home page
    path("about/", views.about, name="about"), # "/about/" -> about page
    path("increment/", views.increment, name="increment"), # POST-only action
    # Calendar
    path('calendar/', views.calendar_view, name='calendar'),                     # default = today
    path('calendar/<int:year>/<int:month>/', views.calendar_view, name='calendar_month'),
    # Edit / Delete
    path('event/edit/<int:event_id>/', views.edit_event, name='edit_event'),
    path('event/delete/<int:event_id>/', views.delete_event, name='delete_event'),
    # Event list
    path('events/', views.event_list, name='event_list'),
]