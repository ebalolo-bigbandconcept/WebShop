FROM node:18

# Set the working directory inside the container
WORKDIR /app

# Copy the package.json file
COPY frontend/package.json .

# Install dependencies
RUN npm install

# Copy the rest of the frontend code
COPY frontend/ .

# Start the React development server
CMD ["npm", "start"]