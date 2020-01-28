const swaggerJSDoc = require('swagger-jsdoc');

// options for the swagger docs
const options = {
  // import swaggerDefinitions
  definition: {
    openapi: '3.0.0', // Specification (optional, defaults to swagger: '2.0')
    info: {
      title: 'Companion', // Title (required)
      version: '1.0.0', // Version (required)
    },
  },
  // path to the API docs
  host: 'localhost:3000', // the host or url of the app
  apis: ['./docs/*.yaml'],
};
// initialize swagger-jsdoc
module.exports = swaggerJSDoc(options);