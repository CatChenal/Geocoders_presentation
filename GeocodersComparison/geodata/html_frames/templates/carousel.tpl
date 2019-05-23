{% extends "html.tpl" %}
<style <link rel="stylesheet" href="carousel.css">
/>
{% block body %}
<div > {{ carousel_div.html }} </div >
{{ super() }}
{% endblock %}