FROM python:3.11-alpine
 
LABEL maintainer="patilchirag484@gmail.com" \
      description="DevOps Watchdog — System Health Monitor" \
      version="1.0.0"
 
RUN apk add --no-cache bash procps
 
WORKDIR /app
 
# Copy application files
COPY monitor.sh  ./
COPY report.py   ./
COPY alerts.conf ./
 
# Ensure script is executable
RUN chmod +x monitor.sh
 
# Create output directories (will be overridden by bind mounts at runtime)
RUN mkdir -p logs reports
 
RUN python3 -c "import report" 2>/dev/null || \
    python3 -c "import ast, sys; \
f=open('report.py'); \
ast.parse(f.read()); \
print('report.py syntax OK')"
 
CMD ["./monitor.sh"]
