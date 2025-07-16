# frontend/Dockerfile

FROM node:18-alpine

# Set environment variables
ENV NODE_ENV=development
ENV REACT_APP_API_URL=http://localhost:8080

# Install curl for healthcheck
RUN apk add --no-cache curl

# Set work directory
WORKDIR /app

# Copy package.json and package-lock.json (if available)
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Start the application
CMD ["npm", "start"]