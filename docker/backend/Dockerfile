ARG VERSION
# Use the official WaterCrawl image as the base image
FROM watercrawl/watercrawl:${VERSION:-v0.12.2}

# Set working directory
WORKDIR /var/www

# Copy the extra requirements file
COPY extra_requirements.txt /var/www/extra_requirements.txt

# Install any additional packages
RUN poetry run pip install -r /var/www/extra_requirements.txt

# Apply custom patches: SearXNG search backend + configurable search backend
COPY patches/searxng_search.py /var/www/spider/spiders/searxng_search.py
COPY patches/spider_settings.py /var/www/spider/settings.py
COPY patches/django_settings.py /var/www/watercrawl/settings.py
COPY patches/core_services.py /var/www/core/services.py

# The rest of the configuration is inherited from the base image
# The entrypoint and command should be defined in docker-compose.yml
