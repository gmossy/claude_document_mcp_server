FROM nginx:1.27-alpine

# Copy custom nginx configuration
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Install wget for healthcheck
RUN apk add --no-cache wget

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/healthz || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

