import 'dotenv/config';
import app from './app.js';
import pool from './config/db.js';

const port = Number(process.env.PORT) || 3000;
const server = app.listen(port, () => {
  console.log(`User Profile API listening on port ${port}`);
});

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => {
    server.close(async () => {
      await pool.end();
      process.exit(0);
    });
  });
}