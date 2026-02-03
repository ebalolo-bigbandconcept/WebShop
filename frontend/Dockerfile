FROM node:18

# Set the working directory inside the container
WORKDIR /app

# Copy the package.json and package-lock.json files
COPY frontend/package.json .
COPY frontend/package-lock.json .

# Install dependencies
RUN npm ci

# Copy the rest of the frontend code
COPY frontend/ .

# Start the React development server
CMD ["npm", "start"]