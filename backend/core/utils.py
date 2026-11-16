import importlib

from django.conf import settings
from watercrawl_plugin import AbstractPlugin


def generate_crawl_result_file_path(instance, filename):
    return f"crawls/{instance.request_id}/results/{instance.pk}.json"


def generate_crawl_result_attachment_path(instance, filename):
    return f"crawls/{instance.crawl_result.request_id}/results/{instance.crawl_result.uuid}/attachments/{filename}"


def search_result_file_path(instance, filename):
    return f"searches/{instance.uuid}/result.json"


def sitemap_result_file_path(instance, filename):
    return f"sitemaps/{instance.uuid}/result.json"


def generate_crawl_request_sitemap_path(instance, filename):
    return f"crawls/{instance.uuid}/sitemap.json"


def get_active_plugins() -> list[type["AbstractPlugin"]]:
    """
    Get a list of active plugins
    :return: AbstractPlugin[]
    """
    result = []
    plugins = settings.WATERCRAWL_PLUGINS
    if not isinstance(plugins, list):
        plugins = plugins.split(",")

    for plugin_class in plugins:
        module_name, class_name = plugin_class.rsplit(".", 1)

        # Import the module
        module = importlib.import_module(module_name)

        # Get the class from the module
        cls = getattr(module, class_name)
        result.append(cls)

    return result


def cast_bool(value):
    return value.lower() in ("true", "1", "t")
