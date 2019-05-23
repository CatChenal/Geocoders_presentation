{% extends "html.tpl" %}
<style <link rel="stylesheet" href="style.min.css">
/>
{% block table %}
<h5>{{ table_title|default("") }}</h5>
{{ super() }}
{% endblock table %}