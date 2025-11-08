# Start with the official, lightweight Nginx image from Docker Hub
FROM nginx:1.25-alpine

# Remove the default Nginx configuration file that comes with the image
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom nginx.conf file from our local directory
# into the location where Nginx looks for configuration files inside the container.
COPY nginx.conf /etc/nginx/conf.d/