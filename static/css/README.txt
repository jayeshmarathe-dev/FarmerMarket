Separate CSS files created:

- static/css/base.css        -> Global site styles (buttons, containers, utilities)
- static/css/products.css    -> Styles for product listing and cards
- static/css/auth.css        -> Login / Register forms
- static/css/dashboard.css   -> Layout & components for dashboards

How to use in templates:
1. Ensure your base.html contains: {{% block styles %}}{{% endblock %}} in the <head>.
2. In page templates, add:
   {{% block styles %}}
   <link rel="stylesheet" href="{{{{ url_for('static', filename='css/products.css') }}}}">
   {{% endblock %}}

Alternatively include the CSS files directly in base.html if you want them globally loaded.