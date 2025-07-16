# frontend/Dockerfile

FROM node:18-alpine

# Set environment variables
ENV NODE_ENV=development
ENV REACT_APP_API_URL=http://vapter.szini.it:8080
ENV PATH /app/node_modules/.bin:$PATH

# Install curl for healthcheck
RUN apk add --no-cache curl

# Set work directory
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY .npmrc ./

# Clear npm cache and install dependencies
RUN npm cache clean --force
RUN npm install --legacy-peer-deps --verbose

# Verify react-scripts installation
RUN ls -la node_modules/.bin/ | grep react-scripts || echo "react-scripts not found"
RUN npm list react-scripts

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Start the application
CMD ["npm", "start"]