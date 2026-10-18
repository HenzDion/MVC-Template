import express from 'express';
import userRoutes from './routes/userRoutes.js';

const app = express();

app.use(express.json());
app.use('/api/users', userRoutes);

app.use((_request, response) => {
  response.status(404).json({ error: 'Route not found.' });
});

app.use((error, _request, response, _next) => {
  if (error.type === 'entity.parse.failed') {
    return response.status(400).json({ error: 'Request body contains invalid JSON.' });
  }
  if (error.code === '23505') {
    return response.status(409).json({ error: 'A user with this email already exists.' });
  }

  const status = Number.isInteger(error.status) ? error.status : 500;
  if (status >= 500) console.error(error);
  response.status(status).json({
    error: status >= 500 ? 'Internal server error.' : error.message,
  });
});

export default app;