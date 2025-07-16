# frontend/Dockerfile

FROM node:18-alpine

# Set environment variables
ENV NODE_ENV=development
ENV REACT_APP_API_URL=http://localhost:8080
ENV PATH /app/node_modules/.bin:$PATH

# Install curl for healthcheck
RUN apk add --no-cache curl

# Set work directory
WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies using npm ci for more reliable installation
RUN npm ci --legacy-peer-deps

# Verify react-scripts installation
RUN npx react-scripts --version || npm install react-scripts@5.0.1 --legacy-peer-deps

# Copy application code
COPY . .

# Create required files if not present
RUN touch src/react-app-env.d.ts || true

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Start the application using npx to ensure it finds react-scripts
CMD ["npx", "react-scripts", "start"]