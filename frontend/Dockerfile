FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application files
COPY . .

# Create necessary directories if they don't exist
RUN sh -c 'if [ -f create-directories.sh ]; then sh create-directories.sh; fi'

# Expose port
EXPOSE 3000

# Start development server
CMD ["npm", "run", "dev"]