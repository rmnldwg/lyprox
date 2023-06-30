FROM nginx:stable-alpine-slim

# copy the nginx configuration file to the available sites
COPY . /etc/nginx/sites-available

RUN mkdir -p /etc/nginx/sites-enabled
RUN ln -s /etc/nginx/sites-available/lyprox.conf /etc/nginx/sites-enabled/lyprox.conf
